import logging
logger = logging.getLogger(__name__)

cache = {}  # {username: {url: response}}
analytics = {}  # {username: {"requests": int, "cache_hits": int, "cache_misses": int}}

def get_from_cache(username, url):
    if username not in analytics:
        analytics[username] = {"requests": 0, "cache_hits": 0, "cache_misses": 0}
    if username not in cache:
        cache[username] = {}
    analytics[username]["requests"] += 1
    if url in cache[username]:
        analytics[username]["cache_hits"] += 1
        logger.info(f"Cache hit for {username}: {url}")
        return cache[username][url]
    analytics[username]["cache_misses"] += 1
    logger.info(f"Cache miss for {username}: {url}")
    return None

def add_to_cache(username, url, data):
    if username not in cache:
        cache[username] = {}
    cache[username][url] = data
    logger.info(f"Added to cache for {username}: {url}")

def clear_cache(username):
    cache[username] = {}
    analytics[username] = {"requests": 0, "cache_hits": 0, "cache_misses": 0}
    logger.info(f"Cache cleared successfully for {username}")

