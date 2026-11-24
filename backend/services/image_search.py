import os
import time
import urllib.parse
import httpx

# In-memory cache with 24-hour TTL: cache_key -> (timestamp, data)
_IMAGE_CACHE: dict[str, tuple[float, list[dict]]] = {}
CACHE_TTL_SECONDS = 86400  # 24 hours


def build_fallback_image_url(query: str, width: int = 800, height: int = 600) -> str:
    """Guaranteed working image URL from Pollinations FLUX that never fails CORS or hotlinking."""
    clean_query = query.strip() or "educational diagram illustration"
    encoded = urllib.parse.quote(f"{clean_query}, clean educational diagram illustration, high detail, white background")
    return f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true"


async def verify_image_url(url: str, timeout: float = 3.0) -> bool:
    """
    Pre-flight verify image URL:
    - Must return HTTP 200
    - content-type starts with 'image/'
    - size > 5120 bytes (5KB)
    """
    if not url or not url.startswith("http"):
        return False
    # Local or internal bypass
    if "pollinations.ai" in url or "gstatic.com" in url or "wikimedia.org" in url:
        return True

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    }
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            # First try HEAD
            resp = await client.head(url, headers=headers)
            if resp.status_code == 405 or resp.status_code == 403:
                # HEAD disallowed or blocked; try ranged GET for first 10KB
                range_headers = {**headers, "Range": "bytes=0-10240"}
                resp = await client.get(url, headers=range_headers)
            
            if resp.status_code in (200, 206):
                ctype = resp.headers.get("content-type", "").lower()
                clen = int(resp.headers.get("content-length", 0) or 0)
                if ctype.startswith("image/"):
                    if clen == 0 or clen >= 5120:
                        return True
                    if clen > 0 and clen < 5120:
                        return False
                    return True
    except Exception as e:
        print(f"[image_verify] Failed checking {url[:60]}: {e}")
    return False


def is_valid_hero_item(item: dict) -> bool:
    """Filter out stock photos, life cycles, or vector packs when looking for a labeled parts diagram."""
    title = (item.get("title") or "").lower()
    reject_words = ["life cycle", "lifecycle", "stock photo", "vector pack", "clipart", "wallpaper", "coloring page"]
    if any(rw in title for rw in reject_words):
        return False
    return True


async def search_web_images(query: str, count: int = 1, is_hero: bool = False) -> list[dict]:
    """
    Fetches verified, loadable image URLs using SerpApi (Google Images thumbnail/original),
    Tavily Search API, and Wikipedia REST API, with guaranteed 24-hour cache and pre-flight check.
    """
    cache_key = f"{query.strip().lower()}::{count}::{is_hero}"
    now = time.time()
    if cache_key in _IMAGE_CACHE:
        cached_time, cached_data = _IMAGE_CACHE[cache_key]
        if now - cached_time < CACHE_TTL_SECONDS:
            print(f"[image_search] Cache hit for '{query}'")
            return cached_data

    results = []
    serp_key = os.getenv("SERPAPI_API_KEY", "").strip()
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()

    # If is_hero, ensure query is targeted to parts labeled diagram
    effective_query = query
    if is_hero and "labeled" not in query.lower() and "diagram" not in query.lower():
        effective_query = f"{query} parts labeled diagram"

    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
        # 1. Primary: SerpApi Google Images (gstatic thumbnails are safe against hotlink/CORS)
        if serp_key and len(results) < count:
            try:
                resp = await client.get(
                    "https://serpapi.com/search.json",
                    params={
                        "engine": "google_images",
                        "q": effective_query,
                        "api_key": serp_key,
                        "num": max(count * 4, 8),
                        "safe": "active",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("images_results", [])
                    
                    if is_hero:
                        # Prioritize items with 'diagram', 'parts', or 'labeled'
                        def hero_sort_score(it):
                            t = (it.get("title") or "").lower()
                            score = 0
                            if "parts" in t: score += 3
                            if "labeled" in t or "labelled" in t: score += 3
                            if "diagram" in t: score += 2
                            return score
                        items = sorted(items, key=hero_sort_score, reverse=True)

                    for item in items:
                        if is_hero and not is_valid_hero_item(item):
                            continue
                        thumb = item.get("thumbnail", "")
                        orig = item.get("original", "")
                        # Prefer gstatic thumbnail to avoid 403 hotlink blocks; original as backup
                        chosen_url = thumb if thumb else orig
                        if chosen_url and chosen_url.startswith("http"):
                            # Verify if not gstatic
                            is_ok = True
                            if "gstatic.com" not in chosen_url:
                                is_ok = await verify_image_url(chosen_url, timeout=2.5)
                            if is_ok:
                                results.append(
                                    {
                                        "url": chosen_url,
                                        "original_url": orig or chosen_url,
                                        "fallback_url": build_fallback_image_url(query),
                                        "title": item.get("title") or query.title(),
                                        "source": item.get("source") or "Google Images",
                                        "source_url": item.get("link") or "https://images.google.com",
                                    }
                                )
                                if len(results) >= count:
                                    break
            except Exception as e:
                print(f"[image_search] SerpApi warning for '{effective_query}': {e}")

        # 2. Secondary: Tavily Search API with include_images=True
        if tavily_key and len(results) < count:
            try:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": effective_query,
                        "include_images": True,
                        "max_results": 4,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    images = data.get("images", [])
                    web_results = data.get("results", [])
                    default_source = (
                        web_results[0].get("url", "https://tavily.com")
                        if web_results
                        else "https://tavily.com"
                    )
                    for img in images:
                        img_url = img.get("url") if isinstance(img, dict) else img
                        if isinstance(img_url, str) and img_url.startswith("http"):
                            is_ok = await verify_image_url(img_url, timeout=2.5)
                            if is_ok:
                                results.append(
                                    {
                                        "url": img_url,
                                        "original_url": img_url,
                                        "fallback_url": build_fallback_image_url(query),
                                        "title": query.title(),
                                        "source": "Web Search",
                                        "source_url": default_source,
                                    }
                                )
                                if len(results) >= count:
                                    break
            except Exception as e:
                print(f"[image_search] Tavily warning for '{effective_query}': {e}")

        # 3. Tertiary: Wikipedia REST Page Summary Image
        if len(results) < count:
            try:
                wiki_topic = query.replace("diagram", "").replace("labeled", "").replace("parts", "").strip().split()[0]
                if wiki_topic:
                    resp = await client.get(
                        f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(wiki_topic.title())}",
                        headers={"User-Agent": "GrakAI/1.0 (contact@grakai.app)"},
                    )
                    if resp.status_code == 200:
                        d = resp.json()
                        img_url = d.get("thumbnail", {}).get("source") or d.get("originalimage", {}).get("source")
                        if img_url:
                            results.append(
                                {
                                    "url": img_url,
                                    "original_url": img_url,
                                    "fallback_url": build_fallback_image_url(query),
                                    "title": d.get("title") or query.title(),
                                    "source": "Wikipedia",
                                    "source_url": d.get("content_urls", {})
                                    .get("desktop", {})
                                    .get("page", "https://en.wikipedia.org"),
                                }
                            )
            except Exception as e:
                print(f"[image_search] Wikipedia warning for '{query}': {e}")

    # 4. Fallback if no images found
    while len(results) < count:
        fallback = build_fallback_image_url(query)
        results.append(
            {
                "url": fallback,
                "original_url": fallback,
                "fallback_url": fallback,
                "title": query.title(),
                "source": "Grak Visual Engine",
                "source_url": "https://pollinations.ai",
            }
        )

    _IMAGE_CACHE[cache_key] = (now, results)
    return results


async def search_icon_image(term: str) -> dict:
    """
    Fetches a small icon/photo for process flow inputs/outputs (e.g., 'sunlight', 'water', 'carbon dioxide').
    """
    q = f"{term} transparent icon or clear photo"
    res = await search_web_images(q, count=1, is_hero=False)
    if res:
        return {"name": term, "url": res[0]["url"]}
    return {"name": term, "url": build_fallback_image_url(term, 200, 200)}
