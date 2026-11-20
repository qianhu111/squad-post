#!/usr/bin/env python3
"""Validate the Youchai course site source and generated dist tree."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from markdown_lite import outline  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"
DIST = ROOT / "dist"
META_PATH = SOURCE / "meta.json"

BANNED_PHRASES = [
    "你是哪种状态？",
    "新人线",
    "进阶线",
    "勘误",
    "旧教案",
    "为什么重写",
    "原攻略说",
    "上一版",
]

REQUIRED_SECTIONS = [
    "学完能做到什么",
    "决策速查",
    "实战案例",
    "常见错误",
    "实战练习",
    "自检 3 问",
]

WORD_TARGETS = {
    "s1": 2600,
    "s2": 3000,
    "s3": 3500,
    "s4": 4000,
    "s5": 4000,
    "s6": 3500,
}

ALLOWED_IMAGE_HOSTS = {
    "images.steamusercontent.com",
    "shared.fastly.steamstatic.com",
}

CLASS_RE = re.compile(r"(?:class|id)\s*=\s*[\"']([^\"']+)[\"']", re.I)
SCRIPT_RE = re.compile(r"<script\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)[\"']", re.I)
LINK_RE = re.compile(r"<a\b[^>]*\bhref\s*=\s*[\"']([^\"']+)[\"']", re.I)
ASSET_RE = re.compile(r"(?:src|href)\s*=\s*[\"']([^\"']+)[\"']", re.I)
BODY_TEXT_RE = re.compile(r"<body\b.*?</body>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
CJK_RE = re.compile(r"[一-鿿]")


class IdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key == "id" and value:
                self.ids.append(value)


def problems() -> list[str]:
    return []


def check_meta(meta: dict) -> tuple[list[str], list[dict]]:
    issues: list[str] = []
    stages = meta.get("stages", [])
    courses = meta.get("courses", [])
    site = meta.get("site", {})
    site_url = str(site.get("url", ""))
    if not site_url.startswith("https://"):
        issues.append("meta: site.url must start with https://")
    if site_url.endswith("/"):
        issues.append("meta: site.url must not end with /")
    if not site.get("author"):
        issues.append("meta: site.author is missing")

    tags = meta.get("tags", [])
    tag_slugs = [tag.get("slug") for tag in tags]
    if len(tag_slugs) != len(set(tag_slugs)):
        issues.append("meta: duplicate tag slug")
    for tag in tags:
        for key in ("slug", "name", "description"):
            if not tag.get(key):
                issues.append(f"meta: tag missing {key}")
        if tag.get("slug") and not re.fullmatch(r"[a-z0-9-]+", str(tag["slug"])):
            issues.append(f"meta: invalid tag slug {tag['slug']}")
    tag_set = set(tag_slugs)
    if len(stages) != 6:
        issues.append(f"meta: expected 6 stages, got {len(stages)}")
    if len(courses) != 36:
        issues.append(f"meta: expected 36 courses, got {len(courses)}")

    seen_nums = set()
    seen_ids = set()
    seen_files = set()
    seen_sources = set()
    expected = list(range(1, 37))
    actual = [c.get("num") for c in courses]
    if sorted(actual) != expected:
        issues.append("meta: course numbers are not 1-36 exactly once")

    for c in courses:
        num = c.get("num")
        if num in seen_nums:
            issues.append(f"meta: duplicate course num {num}")
        seen_nums.add(num)
        if c.get("id") in seen_ids:
            issues.append(f"meta: duplicate course id {c.get('id')}")
        seen_ids.add(c.get("id"))
        if c.get("file") in seen_files:
            issues.append(f"meta: duplicate output file {c.get('file')}")
        seen_files.add(c.get("file"))
        if c.get("source") in seen_sources:
            issues.append(f"meta: duplicate lesson source {c.get('source')}")
        seen_sources.add(c.get("source"))
        if c.get("stage") not in {s.get("id") for s in stages}:
            issues.append(f"meta: course {num} has unknown stage {c.get('stage')}")
        if not (ROOT / c.get("source", "")).exists():
            issues.append(f"meta: missing lesson source {c.get('source')}")
        for key in ("title", "subtitle", "goal", "keywords", "prereq", "minutes", "updated", "tags"):
            if key not in c:
                issues.append(f"meta: course {num} missing {key}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(c.get("updated", ""))):
            issues.append(f"meta: course {num} has invalid updated date")
        if not c.get("tags"):
            issues.append(f"meta: course {num} has no tags")
        for slug in c.get("tags", []):
            if slug not in tag_set:
                issues.append(f"meta: course {num} has unknown tag {slug}")
    return issues, courses


def check_lessons(meta: dict) -> list[str]:
    issues: list[str] = []
    stage_map = {s["id"]: s for s in meta["stages"]}
    for course in meta["courses"]:
        path = ROOT / course["source"]
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        h2 = [(i, line[3:].strip()) for i, line in enumerate(lines) if line.startswith("## ")]
        names = [name for _, name in h2]
        if not names or names[0] != "学完能做到什么":
            issues.append(f"lesson {course['num']:02d}: first section is not 学完能做到什么")
        if not names or names[-1] != "自检 3 问":
            issues.append(f"lesson {course['num']:02d}: last section is not 自检 3 问")
        for required in REQUIRED_SECTIONS:
            if required not in names:
                issues.append(f"lesson {course['num']:02d}: missing section {required}")

        for index, (start, name) in enumerate(h2):
            end = h2[index + 1][0] if index + 1 < len(h2) else len(lines)
            block = "\n".join(lines[start:end])
            if "::: takeaway" not in block:
                issues.append(f"lesson {course['num']:02d}: section {name} has no takeaway")

        words = len(CJK_RE.findall(text))
        target = WORD_TARGETS.get(course["stage"], 2500)
        if words < target:
            issues.append(f"lesson {course['num']:02d}: only {words} CJK chars, target >= {target}")

        for phrase in BANNED_PHRASES:
            if phrase in text:
                issues.append(f"lesson {course['num']:02d}: banned phrase {phrase}")

        if course["num"] == 26 and "社区经验值，以游戏内为准" not in text:
            issues.append("lesson 26: missing mortar disclaimer")

    return issues


def check_search_index(meta: dict) -> list[str]:
    issues: list[str] = []
    path = DIST / "assets/js/search-index.js"
    if not path.exists():
        return ["search: missing assets/js/search-index.js"]
    raw = path.read_text(encoding="utf-8")
    if "</script" in raw.lower():
        issues.append("search: index contains a literal script terminator")
    prefix = "window.YOUCHAI_SEARCH_INDEX = "
    if not raw.startswith(prefix) or not raw.rstrip().endswith(";"):
        return issues + ["search: index is not a single static assignment"]
    try:
        payload = json.loads(raw[len(prefix):].rstrip().rstrip(";"))
    except json.JSONDecodeError as exc:
        return issues + [f"search: index is not valid JSON ({exc})"]
    if len(payload) != len(meta["courses"]):
        issues.append(f"search: expected {len(meta['courses'])} records, found {len(payload)}")
    by_id = {item.get("id"): item for item in payload}
    for course in meta["courses"]:
        item = by_id.get(course["id"])
        if item is None:
            issues.append(f"search: missing record for {course['id']}")
            continue
        if item.get("path") != course["file"][:-5]:
            issues.append(f"search: wrong path for {course['id']}")
        outline_ids = [h["id"] for h in outline((ROOT / course["source"]).read_text(encoding="utf-8")) if h["level"] == 2]
        section_ids = [s.get("id") for s in item.get("sections", [])]
        if section_ids != outline_ids:
            issues.append(f"search: section ids for {course['id']} do not match outline")
        for section in item.get("sections", []):
            text = str(section.get("text", "")).strip()
            if not text:
                issues.append(f"search: empty text in {course['id']} {section.get('id')}")
            # ":::" alone is legitimate prose here (e.g. a table row like '<50 米');
            # only fail when no readable text remains after stripping the syntax.
            stripped = text
            for token in (":::", "![", "](http", "</", "<p>", "<li>", "##", "**", "`"):
                stripped = stripped.replace(token, "")
            if len(re.findall(r"[一-鿿A-Za-z0-9]", stripped)) < 20:
                issues.append(f"search: unreadable text in {course['id']} {section.get('id')}")
    return issues


def check_dist(meta: dict, courses: list[dict]) -> list[str]:
    issues: list[str] = []
    if not DIST.exists():
        return ["dist: directory does not exist"]

    expected = {"index.html", "404.html", "_headers", "sitemap.xml", "robots.txt", "feed.xml", "tags/index.html"}
    expected.update(c["file"] for c in courses)
    for tag in meta.get("tags", []):
        expected.add(f"tags/{tag['slug']}.html")
    expected.update({
        "courses/index.html",
        "reference/index.html",
        "reference/sources.html",
        "quiz/beginner.html",
        "quiz/advanced.html",
        "progress/index.html",
        "changelog/index.html",
        "assets/css/site.css",
        "assets/js/site.js",
        "assets/js/courses.js",
        "assets/js/progress.js",
        "assets/js/courses-data.js",
        "assets/js/search-index.js",
    })
    site_url = str(meta["site"]["url"]).rstrip("/")
    html_count = 0
    for rel in sorted(expected):
        path = DIST / rel
        if not path.is_file():
            issues.append(f"dist: missing {rel}")
            continue
        data = path.read_bytes()
        if data.startswith(b"\xef\xbb\xbf"):
            issues.append(f"dist: UTF-8 BOM in {rel}")
        if rel.endswith(".html"):
            html_count += 1
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                issues.append(f"dist: invalid UTF-8 in {rel}")
                continue
            if '<meta charset="UTF-8">' not in text:
                issues.append(f"dist: missing charset in {rel}")
            issues.extend(check_html(rel, text, courses, site_url))
    expected_html = 43 + 3 + len(meta.get("tags", []))
    if html_count != expected_html:
        issues.append(f"dist: expected {expected_html} HTML files, found {html_count}")

    for path in DIST.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(DIST).as_posix()
        if rel.startswith("."):
            issues.append(f"dist: hidden file {rel}")
        if path.suffix.lower() in {".md", ".py", ".pdf", ".docx", ".doc", ".txt", ".xlsx"} and rel != "robots.txt":
            issues.append(f"dist: forbidden file type {rel}")
        if "__pycache__" in rel:
            issues.append(f"dist: forbidden cache path {rel}")

    for rel, needles in {
        "courses/beginner/06-spawns-fob-hab.html": ["9 人 90 米", "30 秒"],
        "courses/resources/15-hab-and-rally.html": ["15 米内至少 1 名本队队员", "15 米内至少 3 名本队队员"],
        "courses/beginner/17-tickets-supplies.html": ["+50", "−10", "净摆动 60 票", "+20"],
        "courses/advanced/05-ticket-math.html": ["+50", "−10", "净摆动 60 票"],
        "courses/advanced/07-mortar-spotting.html": ["社区经验值，以游戏内为准", "21"],
        "reference/index.html": [
            "9 人 90 米",
            "倒地敌人、载具内敌人不计入压制",
            "30 秒恢复复活",
            "15 米内至少 3 名本队队员",
            "净摆动 60 票",
            "净摆动 −60 票",
            "我方 +50，敌方 −10",
            "我方 −10，敌方 +50",
            "社区经验值，以游戏内为准",
        ],
        "quiz/beginner.html": ["社区经验值，以游戏内为准", "净摆动 60 票", "我方 +50，敌方 −10", "我方 −10，敌方 +50"],
        "quiz/advanced.html": ["净摆动 60 票", "我方 +50，敌方 −10"],
    }.items():
        path = DIST / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                issues.append(f"dist: {rel} missing key value {needle}")

    sitemap_path = DIST / "sitemap.xml"
    if sitemap_path.exists():
        try:
            root = ET.fromstring(sitemap_path.read_text(encoding="utf-8"))
            ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            locs = [el.text or "" for el in root.findall(".//s:loc", ns)]
            expected_locs = 44 + 1 + len(meta.get("tags", []))
            if len(locs) != expected_locs:
                issues.append(f"dist: sitemap expected {expected_locs} URLs, found {len(locs)}")
            for loc in locs:
                if not loc.startswith(site_url + "/"):
                    issues.append(f"dist: sitemap URL not under site.url: {loc}")
        except ET.ParseError as exc:
            issues.append(f"dist: sitemap.xml is not valid XML: {exc}")

    feed_path = DIST / "feed.xml"
    if feed_path.exists():
        try:
            feed_root = ET.fromstring(feed_path.read_text(encoding="utf-8"))
            ns = {"a": "http://www.w3.org/2005/Atom"}
            entries = feed_root.findall("a:entry", ns)
            if len(entries) != len(courses):
                issues.append(f"dist: feed expected {len(courses)} entries, found {len(entries)}")
            for link in feed_root.findall("a:entry/a:link", ns):
                href = link.get("href", "")
                if not href.startswith(site_url + "/"):
                    issues.append(f"dist: feed entry URL not under site.url: {href}")
        except ET.ParseError as exc:
            issues.append(f"dist: feed.xml is not valid XML: {exc}")

    robots_path = DIST / "robots.txt"
    if robots_path.exists():
        robots = robots_path.read_text(encoding="utf-8")
        for needle in (f"Sitemap: {site_url}/sitemap.xml", "Disallow: /admin/", "Disallow: /api/"):
            if needle not in robots:
                issues.append(f"dist: robots.txt missing {needle}")

    return issues


def resolve_relative(page: Path, target: str) -> Path | None:
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return None
    if not parsed.path:
        return None
    path = unquote(parsed.path)
    if path.startswith("/"):
        return None
    candidate = (page.parent / path).resolve()
    if candidate.exists():
        return candidate
    if path.endswith("/"):
        index = candidate / "index.html"
        if index.exists():
            return index
    html_candidate = candidate.with_name(candidate.name + ".html")
    if html_candidate.exists():
        return html_candidate
    return candidate


def check_html(rel: str, text: str, courses: list[dict], site_url: str) -> list[str]:
    issues: list[str] = []
    page = (DIST / rel).resolve()

    parser = IdParser()
    parser.feed(text)
    if len(parser.ids) != len(set(parser.ids)):
        issues.append(f"html {rel}: duplicate id")

    canonical = re.search(r'<link[^>]*\brel=["\']canonical["\'][^>]*>', text, re.I)
    if rel == "404.html":
        if canonical:
            issues.append(f"html {rel}: 404 should not have canonical")
        if 'name="robots" content="noindex' not in text:
            issues.append(f"html {rel}: 404 missing noindex")
    else:
        if not canonical:
            issues.append(f"html {rel}: missing canonical")
        else:
            href = re.search(r'\bhref=["\']([^"\']+)["\']', canonical.group(0), re.I)
            if not href or not href.group(1).startswith(site_url + "/"):
                issues.append(f"html {rel}: canonical not under site.url")

    for prop in ("og:site_name", "og:type", "og:title", "og:description", "og:url", "og:image"):
        if f'property="{prop}"' not in text:
            issues.append(f"html {rel}: missing {prop}")
    if 'name="twitter:card"' not in text:
        issues.append(f"html {rel}: missing twitter:card")
    if 'type="application/atom+xml"' not in text:
        issues.append(f"html {rel}: missing feed alternate link")

    ld_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)
    if rel != "404.html" and not ld_blocks:
        issues.append(f"html {rel}: missing JSON-LD")
    for block in ld_blocks:
        try:
            json.loads(block)
        except json.JSONDecodeError as exc:
            issues.append(f"html {rel}: invalid JSON-LD ({exc})")

    for match in re.finditer(r'<h([23])\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</h\1>', text, re.S):
        heading_html = match.group(3)
        anchor = re.search(r'<a[^>]*class="heading-anchor"[^>]*href="#([^"]+)"', heading_html)
        if not anchor:
            issues.append(f"html {rel}: heading {match.group(2)} missing anchor")
        elif anchor.group(1) not in parser.ids:
            issues.append(f"html {rel}: heading anchor #{anchor.group(1)} missing target")

    body = BODY_TEXT_RE.search(text)
    visible = TAG_RE.sub(" ", body.group(0)) if body else text
    for phrase in BANNED_PHRASES:
        if phrase in visible:
            issues.append(f"html {rel}: banned phrase {phrase}")

    for pattern in [r"fetch\s*\(", r"XMLHttpRequest\s*\(", r"type\s*=\s*[\"']module[\"']", r"navigator\.serviceWorker"]:
        if re.search(pattern, text, re.I):
            issues.append(f"html {rel}: forbidden runtime API")

    for match in ASSET_RE.finditer(text):
        target = match.group(1)
        if target.startswith("#") or target.startswith("data:") or target.startswith("mailto:"):
            continue
        resolved = resolve_relative(page, target)
        if resolved is not None and not resolved.exists():
            issues.append(f"html {rel}: missing local target {target}")

    for match in LINK_RE.finditer(text):
        href = match.group(1)
        if "#" not in href:
            continue
        parsed = urlparse(href)
        if parsed.scheme or parsed.netloc:
            continue
        fragment = unquote(parsed.fragment)
        if not fragment:
            continue
        target_path = resolve_relative(page, parsed.path) if parsed.path else page
        if target_path is None or not target_path.is_file():
            continue
        try:
            target_text = target_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        target_parser = IdParser()
        target_parser.feed(target_text)
        if fragment not in target_parser.ids:
            issues.append(f"html {rel}: missing anchor #{fragment} in {parsed.path or rel}")

    for match in re.finditer(r"<img\b[^>]*>", text, re.I):
        tag = match.group(0)
        src = re.search(r"\bsrc\s*=\s*[\"']([^\"']+)[\"']", tag, re.I)
        if not src:
            issues.append(f"html {rel}: img without src")
            continue
        parsed = urlparse(src.group(1))
        if parsed.scheme in ("http", "https") and parsed.netloc not in ALLOWED_IMAGE_HOSTS:
            issues.append(f"html {rel}: image host not allowed {parsed.netloc}")
        for attr in ("alt", "loading", "decoding", "referrerpolicy", "width", "height"):
            if not re.search(rf"\b{attr}\s*=", tag, re.I):
                issues.append(f"html {rel}: img missing {attr}")
        for attr in ("width", "height"):
            if not re.search(rf'\b{attr}\s*=\s*["\']\d+["\']', tag, re.I):
                issues.append(f"html {rel}: img {attr} is not a positive integer")

    if rel.startswith("courses/") and rel != "courses/index.html":
        scripts = [urlparse(s).path for s in SCRIPT_RE.findall(text)]
        base = ["assets/js/search-index.js", "assets/js/site.js", "assets/js/courses-data.js", "assets/js/courses.js"]
        positions = []
        for wanted in base:
            matches = [i for i, s in enumerate(scripts) if s.endswith(wanted)]
            if not matches:
                issues.append(f"html {rel}: missing script {wanted}")
                positions.append(-1)
            else:
                positions.append(matches[0])
        if positions != sorted(positions) or -1 in positions:
            issues.append(f"html {rel}: script order is wrong")

    return issues


def main() -> int:
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    meta_issues, courses = check_meta(meta)
    issues = meta_issues + check_lessons(meta) + check_dist(meta, courses) + check_search_index(meta)

    if issues:
        print(f"FAILED: {len(issues)} issue(s)")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("PASS: source, dist structure, links, anchors, scripts, values, and banned text")
    return 0


if __name__ == "__main__":
    sys.exit(main())
