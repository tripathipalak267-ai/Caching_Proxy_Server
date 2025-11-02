from fastapi import FastAPI
import httpx
import logging
from cache import get_from_cache, add_to_cache, analytics

logger = logging.getLogger(__name__)

app = FastAPI()
origin_server = None  # set later when starting

@app.get("/analytics")
def get_analytics():
    """Return analytics information."""
    return analytics

@app.get("/{path:path}")
async def proxy_request(path: str):
    """Proxy GET requests with caching."""
    url = f"{origin_server}/{path}"
    cached_response = get_from_cache(url)
    if cached_response:
        return cached_response

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        add_to_cache(url, data)
        return data

def start_proxy_server(port: int, origin: str):
    """Start FastAPI app using uvicorn."""
    global origin_server
    origin_server = origin
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
