"""sitemap.xml and robots.txt generation."""

from __future__ import annotations

import html

from features.seo import absolute_url


def _entry(site: dict, path: str, lastmod: str) -> str:
    loc = html.escape(absolute_url(site, path), quote=False)
    mod = html.escape(str(lastmod), quote=False)
    return f"  <url><loc>{loc}</loc><lastmod>{mod}</lastmod></url>"


def build_sitemap(meta: dict, courses: list[dict]) -> str:
    site = meta["site"]
    default = site.get("updated", "2026-11-20")
    pages: list[tuple[str, str]] = [
        ("index.html", default),
        ("courses/index.html", default),
    ]
    for course in courses:
        pages.append((course["file"], course.get("updated", default)))
    pages.extend([
        ("reference/index.html", default),
        ("reference/sources.html", default),
        ("quiz/beginner.html", default),
        ("quiz/advanced.html", default),
    ])
    body = "\n".join(_entry(site, path, lastmod) for path, lastmod in pages)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n"
    )


def build_robots(meta: dict) -> str:
    base = meta["site"]["url"].rstrip("/")
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin/\n"
        "Disallow: /api/\n"
        "\n"
        f"Sitemap: {base}/sitemap.xml\n"
    )
