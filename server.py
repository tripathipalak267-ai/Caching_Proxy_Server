from fastapi import FastAPI, Request, Depends
from fastapi.responses import Response, JSONResponse
import httpx
import logging
from cache import get_from_cache, add_to_cache, analytics
from cache import clear_cache as clear_cache_func, cache as cache_store
from auth import get_current_user
import json
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
app = FastAPI(title="Authenticated Proxy Server")

# ==========================
# Load blocked sites JSON
# ==========================
def load_blocked_sites():
    with open("blocked_sites.json", "r") as f:
        return json.load(f)

blocked_sites = load_blocked_sites()

def is_blocked(role: str, target_url: str) -> bool:
    """Check if URL is blocked for this role"""

    domain = urlparse(target_url).netloc.lower()
    path = urlparse(target_url).path.lower()

    for blocked in blocked_sites.get(role, []):
        blocked = blocked.lower()

        # Partial match allows subdomain and keyword blocking
        if blocked in domain or blocked in path:
            return True

    return False

# ==========================
# Routes
# ==========================

@app.get("/analytics")
def get_analytics(current_user: dict = Depends(get_current_user)):
    logger.info(f"User {current_user['username']} accessed analytics.")
    return {
        "user": current_user["username"],
        "role": current_user["role"],
        "analytics": analytics
    }


@app.post("/clear_cache")
def clear_cache_endpoint(current_user: dict = Depends(get_current_user)):
    # Only allow Admins to clear cache
    if current_user.get("role") != "Admin":
        return JSONResponse(content={"error": "Forbidden"}, status_code=403)
    before = len(cache_store)
    clear_cache_func()
    after = len(cache_store)
    return {"status": "ok", "message": "Cache cleared successfully", "before": before, "after": after}


@app.get("/cache_stats")
def cache_stats(current_user: dict = Depends(get_current_user)):
    # Return analytics (safe for any authenticated user)
    return {"analytics": analytics}


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(
    request: Request,
    full_path: str,
    current_user: dict = Depends(get_current_user)
):
    target_url = request.query_params.get("url")
    if not target_url:
        return {"error": "Please provide ?url=<full target URL>"}

    user_role = current_user["role"]
    username = current_user["username"]

    logger.info(f"User {username} ({user_role}) proxying request to {target_url}")

    # ==========================
    #  Blocked site check HERE
    # ==========================
    if is_blocked(user_role, target_url):
        logger.warning(f"BLOCKED REQUEST: {username} attempted {target_url}")
        # Return a proper 403 response with JSON payload describing the block
        payload = {
            "error": "Access Denied",
            "blocked_url": target_url,
            "role": user_role,
            "reason": f"{user_role} role is not allowed to access this site."
        }
        return JSONResponse(content=payload, status_code=403)

    # Check cache
    cached_response = get_from_cache(target_url)
    if cached_response:
        # Return cached content with header indicating a cache HIT
        return Response(content=cached_response, media_type="text/plain", headers={"X-Cache": "HIT"})

    # Forward request
    async with httpx.AsyncClient() as client:
        method = request.method.lower()
        data = await request.body()
        headers = dict(request.headers)
        response = await client.request(method, target_url, data=data, headers=headers)
        # Preserve upstream response content and status code
        # response.content is bytes; response.text decodes it
        content_bytes = response.content
        # Add to cache (store as text to keep previous behavior)
        try:
            add_to_cache(target_url, response.text)
        except Exception:
            # Non-fatal; continue
            logger.exception("Failed to add to cache")

        # Return the upstream response content and include X-Cache: MISS header
        media_type = response.headers.get("content-type", "text/plain")
        return Response(content=content_bytes, status_code=response.status_code, media_type=media_type, headers={"X-Cache": "MISS"})


def start_proxy_server(port: int, config=None):
    import uvicorn
    if config is None:
        config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)
    return server
