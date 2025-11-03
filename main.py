import typer
from server import start_proxy_server
from cache import clear_cache
from logging_conf import configure_logging

app = typer.Typer()
configure_logging()

@app.command()
def run(
    port: int = typer.Option(3001, "--port", "-p", help="Port to run the proxy server on"),
):
    """Run the caching proxy server."""
    try:
        import uvicorn
        uvicorn.run("server:app", host="0.0.0.0", port=port)
    except Exception:
        
        server = start_proxy_server(port)

        try:
            server.run()
        except Exception:
 
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(server.serve())
            loop.close()

@app.command()
def clear_cache_cmd():
    """Clear the in-memory cache."""
    clear_cache()
    typer.echo("Cache cleared successfully!")

if __name__ == "__main__":
    app()

