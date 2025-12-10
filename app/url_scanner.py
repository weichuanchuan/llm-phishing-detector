from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Set
from urllib.parse import urlparse, urlunparse

import aiohttp
import tldextract

from .config import HTTP_TIMEOUT, MAX_REDIRECTS, URL_RED_FLAGS


@dataclass
class RedirectHop:
    status: Optional[int]
    url: str


@dataclass
class UrlScan:
    url: str
    final_url: str
    http_status: Optional[int]
    redirect_chain: List[RedirectHop] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)


async def _fetch_url(session: aiohttp.ClientSession, url: str) -> UrlScan:
    redirects: List[RedirectHop] = []
    issues: List[str] = []
    parsed = urlparse(url)
    if not parsed.scheme:
        parsed = parsed._replace(scheme="https")
    normalized_url = urlunparse(parsed)

    try:
        async with session.get(normalized_url, allow_redirects=True, max_redirects=MAX_REDIRECTS) as resp:
            history = [RedirectHop(status=hop.status, url=str(hop.url)) for hop in resp.history]
            redirects.extend(history)
            if resp.url and str(resp.url) != normalized_url:
                redirects.append(RedirectHop(status=resp.status, url=str(resp.url)))
            body_used = resp.status and resp.status >= 400
            if resp.status and resp.status >= 400:
                issues.append(f"Endpoint returned HTTP {resp.status}.")
            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type.lower():
                issues.append("Destination is not serving HTML content.")
            text_snippet = await resp.text(errors="ignore") if body_used else ""
            for keyword in URL_RED_FLAGS:
                if keyword in text_snippet.lower():
                    issues.append("Body contains phishing-related keyword.")
                    break
            return UrlScan(
                url=url,
                final_url=str(resp.url) if resp.url else normalized_url,
                http_status=resp.status,
                redirect_chain=redirects,
                issues=issues,
            )
    except asyncio.TimeoutError:
        issues.append("Timed out while fetching URL.")
    except aiohttp.ClientError as exc:  # network errors
        issues.append(f"Network error: {exc}")
    return UrlScan(url=url, final_url=normalized_url, http_status=None, redirect_chain=redirects, issues=issues)


async def crawl_urls(urls: Iterable[str], whitelist: Set[str]) -> List[UrlScan]:
    tasks: List[asyncio.Task[UrlScan]] = []
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT)) as session:
        for url in urls:
            domain = _normalized_domain(url)
            if domain and domain in whitelist:
                continue
            tasks.append(asyncio.create_task(_fetch_url(session, url)))
        if not tasks:
            return []
        return await asyncio.gather(*tasks)


def _normalized_domain(url: str) -> Optional[str]:
    extracted = tldextract.extract(url)
    if not extracted.domain:
        return None
    return f"{extracted.domain}.{extracted.suffix}" if extracted.suffix else extracted.domain
