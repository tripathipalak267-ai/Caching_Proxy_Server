
# Caching Proxy Server
A CLI-powered HTTP caching proxy server built with FastAPI and httpx.
It forwards client requests to an origin server, caches the responses, and serves cached content on repeated requests — improving performance and reducing load on the origin.

---

## Features
- CLI to start the proxy server with custom port and origin URL
- Forwards requests to the origin server and caches responses
- Returns cached responses for identical repeated requests
- Adds X-Cache: HIT or X-Cache: MISS to indicate cache status
- Manual cache clearing via CLI command
- Handles redirects and rewrites Location headers
- Added Authentication
- Analytics with realtime cache hit/miss
- Built-in logging and debug support
---

## Tech Stack

- **Framework**: FastAPI
- **HTTP Client**: httpx(async)
- **CLI TOOL**: Typer
- **RunTime**: Uvicorn


---

## Installation

1. Clone the repository

```bash
git clone https://github.com/eniolaomotee/Caching_Proxy_Server.git
cd caching-proxy-server
```

2. Create and activate a Virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
```

3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

1. Start the Proxy Server
```bash
python main.py run --port 3001
```
This starts the proxy on http://localhost:3001.

2. Make requests via proxy


Sends a request to OriginURL:
```bash
curl.exe -u user:pass "http://localhost:3001/?url=<OriginURL>"
```
It will be forwarded to origin url (e.g. https://dummyjson.com/products/2)

You’ll get an X-Cache: MISS on the first request and X-Cache: HIT on repeated identical requests.

3. To view the analytics:
```bash
curl.exe -u user:pass "http://localhost:3001/analytics"
```
It will show the number of cache hit and cache miss and number of request forwardedb.


4. Clear the cache
```bash
python main.py clear-cache-cmd
```

## Current User Profiles
- Student
- Faculty
- Admin