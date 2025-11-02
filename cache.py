import logging
logger = logging.getLogger(__name__)

cache = {}
analytics = {
    "requests": 0,
    "cache_hits": 0,
    "cache_misses": 0
}

def get_from_cache(url):
    analytics["requests"] += 1
    if url in cache:
        analytics["cache_hits"] += 1
        logger.info(f"Cache hit for {url}")
        return cache[url]
    analytics["cache_misses"] += 1
    logger.info(f"Cache miss for {url}")
    return None

def add_to_cache(url, data):
    cache[url] = data
    logger.info(f"Added to cache: {url}")

def clear_cache():
    cache.clear()
    analytics["requests"] = analytics["cache_hits"] = analytics["cache_misses"] = 0
    logger.info("Cache cleared successfully")

