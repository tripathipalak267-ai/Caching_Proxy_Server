from fastapi import FastAPI, Request
import httpx
import logging
from cache import get_from_cache, add_to_cache, analytics

logger = logging.getLogger(__name__)
app = FastAPI()

@app.get("/analytics")
def get_analytics():
    """Return analytics info."""
    return analytics

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(request: Request, full_path: str):
    """Generic proxy for any domain using ?url= parameter."""
    target_url = request.query_params.get("url")
    if not target_url:
        return {"error": "Please provide ?url=<full target URL>"}

    logger.info(f"Proxying request to {target_url}")
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
    """Run FastAPI proxy."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)

