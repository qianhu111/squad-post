"""Small Markdown subset used by the Youchai course site.

No third-party dependencies. Supports headings, paragraphs, lists, tables,
blockquotes, fenced code, images, inline emphasis/code/links, and the site's
::: block directives.
"""

from __future__ import annotations

import html
import re
from urllib.parse import urlparse

BLOCK_RE = re.compile(r"^:::\s*([a-zA-Z][\w-]*)\s*(.*)$")
HEAD_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$")
UL_RE = re.compile(r"^[-*]\s+(.+)$")
OL_RE = re.compile(r"^\d+[.)]\s+(.+)$")
IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")

ALLOWED_IMAGE_HOSTS = {
    "images.steamusercontent.com",
    "shared.fastly.steamstatic.com",
}


def _attr(value: str) -> str:
    return html.escape(value, quote=True)


def _safe_url(url: str, image: bool = False) -> str:
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https"):
        if image and parsed.netloc not in ALLOWED_IMAGE_HOSTS:
            return ""
        return url
    if parsed.scheme == "" and not parsed.netloc:
        return url
    return ""


def inline(text: str) -> str:
    """Render one line of inline Markdown to HTML."""
    saved: list[str] = []

    def keep(replacement: str) -> str:
        saved.append(replacement)
        return f"\x00{len(saved) - 1}\x00"

    def image_replace(match: re.Match[str]) -> str:
        alt = match.group(1).strip() or "Squad 游戏截图"
        url = _safe_url(match.group(2), image=True)
        if not url:
            return match.group(1)
        return keep(
            f'<img src="{_attr(url)}" alt="{_attr(alt)}" '
            f'loading="lazy" decoding="async" referrerpolicy="no-referrer">'
        )

    def link_replace(match: re.Match[str]) -> str:
        url = _safe_url(match.group(2))
        if not url:
            return match.group(1)
        label = html.escape(match.group(1), quote=False)
        return keep(f'<a href="{_attr(url)}">{label}</a>')

    raw = IMG_RE.sub(image_replace, text)
    raw = LINK_RE.sub(link_replace, raw)
    out = html.escape(raw, quote=False)
    out = CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", out)
    out = BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", out)

    for index, replacement in enumerate(saved):
        out = out.replace(f"\x00{index}\x00", replacement)
    return out


def _slug(state: dict, level: int) -> str:
    if level == 2:
        state["section"] += 1
        state["sub"] = 0
        return f"s{state['section']}"
    state["sub"] += 1
    return f"s{state['section']}-{state['sub']}"


def _is_special(line: str) -> bool:
    stripped = line.strip()
    return (
        not stripped
        or bool(BLOCK_RE.match(stripped))
        or bool(HEAD_RE.match(stripped))
        or bool(UL_RE.match(stripped))
        or bool(OL_RE.match(stripped))
        or stripped.startswith("|")
        or stripped.startswith(">")
        or stripped.startswith("```")
        or stripped.strip() == "---"
    )


def _render_table(lines: list[str], start: int) -> tuple[str, int]:
    rows: list[list[str]] = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        rows.append(cells)
        i += 1
    if len(rows) < 2:
        return "", i
    sep = rows[1]
    if not all(re.fullmatch(r":?-{3,}:?", c) for c in sep):
        return "", i
    head = rows[0]
    body = rows[2:]
    thead = "".join(f"<th>{inline(c)}</th>" for c in head)
    tbody = "".join(
        "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>"
        for row in body
    )
    return f'<div class="table-wrap"><table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table></div>', i


def _render_list(lines: list[str], start: int) -> tuple[str, int]:
    first = lines[start].strip()
    ordered = bool(OL_RE.match(first))
    pattern = OL_RE if ordered else UL_RE
    items: list[str] = []
    i = start
    while i < len(lines):
        match = pattern.match(lines[i].strip())
        if not match:
            break
        items.append(match.group(1))
        i += 1
    tag = "ol" if ordered else "ul"
    body = "".join(f"<li>{inline(item)}</li>" for item in items)
    return f"<{tag}>{body}</{tag}>", i


def render(markdown: str, state: dict | None = None) -> str:
    """Render Markdown to HTML. `state` is optional heading-counter state."""
    state = state if state is not None else {"section": 0, "sub": 0}
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    open_sections: list[int] = []
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()

        if not stripped:
            i += 1
            continue

        block = BLOCK_RE.match(stripped)
        if block:
            kind = block.group(1)
            title = block.group(2).strip()
            i += 1
            inner: list[str] = []
            while i < len(lines) and lines[i].strip() != ":::":
                inner.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            body = render("\n".join(inner), state)
            heading = f"<h3>{inline(title)}</h3>" if title else ""
            if kind == "figure":
                inner_html = body
                if inner_html.startswith("<p>") and inner_html.endswith("</p>"):
                    inner_html = inner_html[3:-4]
                caption = f"<figcaption>{inline(title)}</figcaption>" if title else ""
                out.append(f'<figure class="lesson-figure">{inner_html}{caption}</figure>')
            elif kind == "takeaway" and open_sections:
                out.append(f'<div class="takeaway">{heading}{body}</div>')
            else:
                out.append(f'<div class="block block-{html.escape(kind)}">{heading}{body}</div>')
            continue

        if stripped.startswith("```"):
            i += 1
            code: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            out.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
            continue

        head = HEAD_RE.match(stripped)
        if head:
            level = len(head.group(1))
            while len(open_sections) >= level:
                out.append("</section>")
                open_sections.pop()
            ident = _slug(state, level)
            out.append(f'<section id="{ident}"><h{level} id="{ident}-title">{inline(head.group(2))}</h{level}>')
            open_sections.append(level)
            i += 1
            continue

        if stripped.startswith("|"):
            table_html, i = _render_table(lines, i)
            if table_html:
                out.append(table_html)
                continue

        if UL_RE.match(stripped) or OL_RE.match(stripped):
            list_html, i = _render_list(lines, i)
            out.append(list_html)
            continue

        if stripped.startswith(">"):
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(f"<blockquote>{inline(' '.join(quote))}</blockquote>")
            continue

        if stripped == "---":
            out.append("<hr>")
            i += 1
            continue

        paragraph: list[str] = []
        while i < len(lines) and not _is_special(lines[i]):
            paragraph.append(lines[i].strip())
            i += 1
        if paragraph:
            out.append(f"<p>{inline(' '.join(paragraph))}</p>")

    while open_sections:
        out.append("</section>")
        open_sections.pop()
    return "\n".join(out)
