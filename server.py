from fastapi import FastAPI, Request
import httpx
import logging
from cache import get_from_cache, add_to_cache, analytics

logger = logging.getLogger(__name__)

app = FastAPI()
origin_server = None  # not needed for browser proxy but we keep for compatibility


@app.get("/analytics")
def get_analytics():
    """Return analytics info."""
    return analytics


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(request: Request, path: str):
    """Handle proxy requests directly from browser (HTTP only)."""
    # Extract the full URL from the request
    full_url = str(request.url)
    if full_url.startswith(f"http://{request.client.host}:{request.url.port}"):
        # Firefox sends http://localhost:3001/http://example.com
        # So extract real URL after the proxy's own part
        full_url = full_url.split("http://", 1)[-1]
        full_url = "http://" + full_url.split("/", 1)[-1]

    logger.info(f"Proxying request for {full_url}")

    # Check cache
    cached_response = get_from_cache(full_url)
    if cached_response:
        return cached_response

    # Forward the request
    async with httpx.AsyncClient() as client:
        method = request.method.lower()
        if method == "get":
            response = await client.get(full_url)
        elif method == "post":
            body = await request.body()
            response = await client.post(full_url, data=body)
        elif method == "put":
            body = await request.body()
            response = await client.put(full_url, data=body)
        elif method == "delete":
            response = await client.delete(full_url)
        else:
            return {"error": f"Unsupported method: {method}"}

        data = response.text  # keep it text for HTML pages
        add_to_cache(full_url, data)
        return data


def start_proxy_server(port: int, origin: str = None):
    """Start FastAPI app."""
    global origin_server
    origin_server = origin
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
