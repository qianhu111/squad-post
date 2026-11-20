"""Atom feed generation."""

from __future__ import annotations

import html

from features.seo import absolute_url


def _xml(value: object) -> str:
    return html.escape(str(value), quote=False)


def _updated(value: str) -> str:
    return f"{value}T00:00:00Z"


def build_feed(meta: dict, courses: list[dict]) -> str:
    site = meta["site"]
    base = site["url"].rstrip("/") + "/"
    entries = sorted(courses, key=lambda c: (c.get("updated", ""), c["num"]), reverse=True)
    latest = entries[0].get("updated", site.get("updated", "2026-11-20")) if entries else site.get("updated", "2026-11-20")

    parts = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f'<title>{_xml(site["title"])}</title>',
        f'<subtitle>{_xml(site.get("description", ""))}</subtitle>',
        f'<link href="{_xml(base + "feed.xml")}" rel="self"/>',
        f'<link href="{_xml(base)}"/>',
        f'<id>{_xml(base)}</id>',
        f'<updated>{_updated(latest)}</updated>',
        f'<author><name>{_xml(site.get("author", site["title"]))}</name></author>',
    ]
    for course in entries:
        url = absolute_url(site, course["file"])
        title = f'{course["num"]:02d} {course["title"]}'
        parts.extend([
            "<entry>",
            f'<title>{_xml(title)}</title>',
            f'<link href="{_xml(url)}"/>',
            f'<id>{_xml(url)}</id>',
            f'<updated>{_updated(course.get("updated", latest))}</updated>',
            f'<summary>{_xml(course.get("subtitle", ""))}</summary>',
            "</entry>",
        ])
    parts.append("</feed>")
    return "\n".join(parts) + "\n"
