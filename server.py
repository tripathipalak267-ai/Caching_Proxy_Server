from fastapi import FastAPI, Request, Depends
import httpx
import logging
from cache import get_from_cache, add_to_cache, analytics
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
        return {
            "error": "Access Denied",
            "blocked_url": target_url,
            "role": user_role,
            "reason": f"{user_role} role is not allowed to access this site."
        }

    # Check cache
    cached_response = get_from_cache(target_url)
    if cached_response:
        return cached_response

    # Forward request
    async with httpx.AsyncClient() as client:
        method = request.method.lower()
        data = await request.body()
        headers = dict(request.headers)
        response = await client.request(method, target_url, data=data, headers=headers)
        content = response.text

        add_to_cache(target_url, content)
        return content


def start_proxy_server(port: int, config=None):
    import uvicorn
    if config is None:
        config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)
    return server
