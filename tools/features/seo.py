"""Canonical URLs, Open Graph, Twitter Card and JSON-LD helpers."""

from __future__ import annotations

import html
import json


def pretty_path(path: str) -> str:
    """Turn a generated .html path into the clean URL used by canonical/sitemap."""
    p = path.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    if p == "index.html":
        return ""
    if p.endswith("/index.html"):
        return p[: -len("index.html")]
    if p.endswith(".html"):
        return p[:-5]
    return p


def absolute_url(site: dict, path: str) -> str:
    base = str(site.get("url", "")).rstrip("/")
    pretty = pretty_path(path).lstrip("/")
    return f"{base}/{pretty}" if pretty else f"{base}/"


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _json_ld(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # Prevent a literal </script> inside JSON from closing the tag.
    raw = raw.replace("<", "\\u003c")
    return f'<script type="application/ld+json">{raw}</script>'


def _organization(site: dict) -> dict:
    return {"@type": "Organization", "name": site.get("author", site.get("title", ""))}


def json_ld_website(site: dict, description: str) -> str:
    return _json_ld({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": site["title"],
        "url": site["url"].rstrip("/") + "/",
        "description": description,
        "inLanguage": site.get("locale", "zh-CN"),
        "publisher": _organization(site),
    })


def json_ld_collection(site: dict, name: str, description: str, url: str) -> str:
    return _json_ld({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": name,
        "description": description,
        "url": url,
        "inLanguage": site.get("locale", "zh-CN"),
        "isPartOf": {"@type": "WebSite", "name": site["title"], "url": site["url"].rstrip("/") + "/"},
    })


def json_ld_learning_resource(site: dict, course: dict, stage: dict, url: str) -> str:
    return _json_ld({
        "@context": "https://schema.org",
        "@type": "LearningResource",
        "name": course["title"],
        "description": course["subtitle"],
        "url": url,
        "inLanguage": site.get("locale", "zh-CN"),
        "learningResourceType": "Course",
        "educationalLevel": f'{stage["num"]} {stage["name"]}',
        "isPartOf": {"@type": "Course", "name": site["title"], "url": site["url"].rstrip("/") + "/"},
        "provider": _organization(site),
    })


def json_ld_webpage(site: dict, name: str, description: str, url: str) -> str:
    return _json_ld({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": name,
        "description": description,
        "url": url,
        "inLanguage": site.get("locale", "zh-CN"),
        "isPartOf": {"@type": "WebSite", "name": site["title"], "url": site["url"].rstrip("/") + "/"},
    })


def seo_head(
    site: dict,
    *,
    title: str,
    description: str,
    path: str,
    og_type: str = "website",
    image: str | None = None,
    json_ld: str = "",
    noindex: bool = False,
) -> str:
    url = absolute_url(site, path)
    image_url = image or site.get("ogImage", "")
    if image_url and not image_url.startswith(("http://", "https://")):
        image_url = absolute_url(site, image_url)

    rows = [
        f'<link rel="canonical" href="{_esc(url)}">' if not noindex else "",
        f'<meta name="author" content="{_esc(site.get("author", ""))}">',
        f'<meta name="robots" content="{"noindex, nofollow" if noindex else "index, follow"}">',
        f'<meta property="og:site_name" content="{_esc(site["title"])}">',
        f'<meta property="og:type" content="{_esc(og_type)}">',
        f'<meta property="og:title" content="{_esc(title)}">',
        f'<meta property="og:description" content="{_esc(description)}">',
        f'<meta property="og:url" content="{_esc(url)}">',
        '<meta property="og:locale" content="zh_CN">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{_esc(title)}">',
        f'<meta name="twitter:description" content="{_esc(description)}">',
    ]
    if image_url:
        rows.append(f'<meta property="og:image" content="{_esc(image_url)}">')
        rows.append(f'<meta name="twitter:image" content="{_esc(image_url)}">')
    if json_ld:
        rows.append(json_ld)
    return "\n".join(row for row in rows if row)
