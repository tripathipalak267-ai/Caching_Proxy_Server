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
    # Use uvicorn to run the FastAPI app in the foreground when invoked via CLI
    try:
        import uvicorn
        # run will block current thread and serve the app
        uvicorn.run("server:app", host="0.0.0.0", port=port)
    except Exception:
        # Fallback: attempt to create the server object (used by GUI) and run it
        server = start_proxy_server(port)
        # server.run() is a blocking call in newer uvicorn versions
        try:
            server.run()
        except Exception:
            # As a last resort, call serve() (async) within an event loop
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

