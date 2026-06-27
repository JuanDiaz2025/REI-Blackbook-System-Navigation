"""
CDN asset cache: downloads mastercdn.atm.gs and other blocked CDN assets
via curl (which uses the system proxy) and serves them to Playwright via
route interception, bypassing Chromium's inability to reach the CDN directly.
"""
import os
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse


CACHE_DIR = Path(tempfile.gettempdir()) / "rei_cdn_cache"
CACHE_DIR.mkdir(exist_ok=True)

# CDN domains to intercept and proxy
INTERCEPTED_DOMAINS = {
    "mastercdn.atm.gs",
    "cdn.jsdelivr.net",
    "unpkg.com",
}

# Domains to block (trackers — saves bandwidth and avoids networkidle hangs)
BLOCKED_PATTERNS = [
    "*google-analytics*",
    "*googletagmanager*",
    "*facebook.net*",
    "*fbcdn*",
    "*hubspot*",
    "*hs-scripts*",
    "*adroll*",
    "*profitwell*",
    "*linkedin.com/li*",
    "*doubleclick.net*",
    "*hotjar*",
]


def _url_to_cache_path(url: str) -> Path:
    parsed = urlparse(url)
    safe = (parsed.netloc + parsed.path).replace("/", "_").replace("?", "__").replace("=", "_")
    return CACHE_DIR / safe[:200]


def fetch_via_curl(url: str) -> bytes | None:
    """Download a URL through the system proxy using curl."""
    path = _url_to_cache_path(url)
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes()
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "30", "--fail", "-o", str(path), url],
            capture_output=True,
            timeout=35,
        )
        if result.returncode == 0 and path.exists() and path.stat().st_size > 0:
            return path.read_bytes()
    except Exception as e:
        print(f"  [cdn_cache] curl failed for {url}: {e}")
    return None


def _content_type_for(url: str) -> str:
    if url.endswith(".css"):
        return "text/css"
    if url.endswith(".js"):
        return "application/javascript"
    if url.endswith(".json"):
        return "application/json"
    if url.endswith(".woff2"):
        return "font/woff2"
    if url.endswith(".woff"):
        return "font/woff"
    if url.endswith(".ttf"):
        return "font/ttf"
    if ".css" in url:
        return "text/css"
    if ".js" in url:
        return "application/javascript"
    return "application/octet-stream"


def make_cdn_route_handler(route, request):
    """Playwright route handler: fetch via curl and fulfill the request."""
    url = request.url
    parsed = urlparse(url)
    if parsed.netloc not in INTERCEPTED_DOMAINS:
        route.continue_()
        return

    body = fetch_via_curl(url)
    if body is not None:
        route.fulfill(
            status=200,
            body=body,
            headers={"content-type": _content_type_for(url), "access-control-allow-origin": "*"},
        )
    else:
        print(f"  [cdn_cache] Could not fetch {url}, aborting")
        route.abort()


def install_routes(context):
    """Install CDN intercept and tracker-block routes on a browser context."""
    for pat in BLOCKED_PATTERNS:
        context.route(pat, lambda route: route.abort())

    # Intercept CDN domains
    for domain in INTERCEPTED_DOMAINS:
        context.route(
            f"https://{domain}/**",
            lambda route, request: make_cdn_route_handler(route, request),
        )
    # Also catch Google Fonts (CSS is fine; font binaries just get proxied)
    context.route(
        "https://fonts.googleapis.com/**",
        lambda route, request: make_cdn_route_handler(route, request),
    )
    context.route(
        "https://fonts.gstatic.com/**",
        lambda route, request: make_cdn_route_handler(route, request),
    )
