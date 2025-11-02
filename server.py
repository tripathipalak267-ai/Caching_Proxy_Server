from fastapi import FastAPI, Request, Depends
import httpx
import logging
from cache import get_from_cache, add_to_cache, analytics
from auth import get_current_user

logger = logging.getLogger(__name__)
app = FastAPI(title="Authenticated Proxy Server")

@app.get("/analytics")
def get_analytics(current_user: dict = Depends(get_current_user)):
    """Return analytics info (requires authentication)."""
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
    """Generic proxy for any domain using ?url= parameter (requires authentication)."""
    target_url = request.query_params.get("url")
    if not target_url:
        return {"error": "Please provide ?url=<full target URL>"}

    logger.info(f"User {current_user['username']} proxying request to {target_url}")

    cached_response = get_from_cache(target_url)
    if cached_response:
        return cached_response

    async with httpx.AsyncClient() as client:
        method = request.method.lower()
        data = await request.body()
        headers = dict(request.headers)
        response = await client.request(method, target_url, data=data, headers=headers)
        content = response.text
        add_to_cache(target_url, content)
        return content

def start_proxy_server(port: int):
    """Run FastAPI proxy with auth."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
