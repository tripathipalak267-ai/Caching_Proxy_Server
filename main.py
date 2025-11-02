import typer
from server import start_proxy_server
from cache import clear_cache
from logging_conf import configure_logging

app = typer.Typer()
configure_logging()

@app.command()
def run(
    port: int = typer.Option(3001, "--port", "-p", help="Port to run the proxy server on"),
    origin: str = typer.Option("https://dummyjson.com", "--origin", "-o", help="Origin server URL")
):
    """Run the caching proxy server."""
    typer.echo(f"Starting caching proxy server on port {port} for origin {origin}")
    start_proxy_server(port, origin)

@app.command()
def clear_cache_cmd():
    """Clear the in-memory cache."""
    clear_cache()
    typer.echo("Cache cleared successfully!")

if __name__ == "__main__":
    app()

