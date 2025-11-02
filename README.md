# Caching Proxy Server

A feature-rich HTTP caching proxy server built with FastAPI and httpx, offering both CLI and GUI interfaces. 
It forwards client requests to origin servers, caches responses, and includes advanced features like user authentication, 
URL filtering, and real-time analytics.

## Features

### Core Functionality
- Forwards requests to origin servers with response caching
- Intelligent cache management with HIT/MISS tracking
- Handles redirects and rewrites Location headers
- Real-time analytics and monitoring
- Built-in logging and debug support

### Authentication & Security
- Role-based access control (Admin/Student/Teacher)
- Basic HTTP authentication
- URL filtering based on user roles
- Configurable blocked sites per role

### Modern GUI Interface
- User-friendly proxy management
- Real-time server status monitoring
- Password-protected login
- Response viewing area
- Admin panel for user management
- Show/hide password toggle

### CLI Support
- Start/stop server with custom port
- Manual cache clearing
- Analytics viewing
- Server configuration

## Tech Stack

- **Framework**: FastAPI
- **HTTP Client**: httpx (async)
- **CLI Tool**: Typer
- **GUI**: Tkinter with ttkthemes
- **Runtime**: Uvicorn

## Installation

1. Clone the repository:
```bash
git clone https://github.com/tripathipalak267-ai/Caching_Proxy_Server.git
cd Caching_Proxy_Server
```

2. Create and activate a Virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
```

3. Install Dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### GUI Interface

1. Start the GUI application:
```bash
python gui.py
```

2. Using the GUI:
   - Login with your credentials
   - Use the server control panel to start/stop the proxy
   - Enter URLs in the input field to browse through the proxy
   - View responses in the built-in response area
   - Administrators can access the user management panel

### CLI Interface

1. Start the Proxy Server:
```bash
python main.py run --port 3001
```
This starts the proxy on http://localhost:3001.

2. Make requests via proxy:
```bash
curl.exe -u user:pass "http://localhost:3001/?url=<OriginURL>"
```
Example: `curl.exe -u user:pass "http://localhost:3001/?url=https://api.example.com/data"`

3. View analytics:
```bash
curl.exe -u user:pass "http://localhost:3001/analytics"
```
Shows cache hits, misses, and total requests.

4. Clear the cache:
```bash
python main.py clear-cache-cmd
```

## User Roles and Permissions

### Admin
- Full access to all features
- Can manage users (add/view)
- Can view analytics
- No URL restrictions

### Teacher
- Can use proxy services
- Can view analytics
- Some URL restrictions

### Student
- Basic proxy usage
- Limited URL access
- Cannot view analytics

## Configuration

### User Management
Users are configured in `users.json`:
```json
{
  "users": [
    {
      "username": "admin",
      "password": "admin123",
      "role": "Admin"
    }
  ]
}
```

### URL Filtering
Blocked sites are configured in `blocked_sites.json`:
```json
{
  "Student": ["facebook.com", "instagram.com"],
  "Teacher": ["gaming.com"]
}
```

## Project Structure

- `main.py`: CLI entry point and command definitions
- `server.py`: FastAPI server implementation
- `auth.py`: Authentication logic
- `cache.py`: Caching system implementation
- `gui.py`: Graphical user interface
- `blocked_sites.json`: URL filtering configuration
- `users.json`: User credentials and roles
- `logging_conf.py`: Logging configuration

## Requirements

The project requires Python 3.8+ and the following main packages:
- FastAPI
- uvicorn
- httpx
- typer
- requests
- ttkthemes
- pillow

See `requirements.txt` for complete list with versions.