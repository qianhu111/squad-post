#!/usr/bin/env python3
"""Build the static Youchai course site from source files.

The output directory `dist/` is the publish root for Cloudflare Pages Direct
Upload. No build service is used: this script runs locally and writes plain
HTML/CSS/JS.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from pathlib import Path

from markdown_lite import inline, render, section_index
from features import feed, reading, seo, sitemap, tags as tag_features

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"
DIST = ROOT / "dist"
META_PATH = SOURCE / "meta.json"

THEME_BOOT = """(function(){try{var k='youchai-theme';var s=localStorage.getItem(k);var m=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches;document.documentElement.dataset.theme=s||(m?'dark':'light');var f=localStorage.getItem('youchai-font');if(f==='1'||f==='1.08'||f==='1.16'){document.documentElement.style.setProperty('--reading-scale',f)}if(localStorage.getItem('youchai-reading')==='1'){document.documentElement.setAttribute('data-reading','1')}}catch(e){document.documentElement.dataset.theme='light'}})();"""


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


QQ_GROUPS = [
    ("邮差公会玩家群", "637704265", "玩家群"),
    ("邮差好友公会新兵营", "914864419", "新兵营"),
]


def qq_link(num: str) -> str:
    return (
        "mqqapi://card/show_pslcard?src_type=internal&amp;version=1"
        f"&amp;uin={num}&amp;card_type=group&amp;source=qrcode"
    )


def qq_footer(root: str) -> str:
    links = "".join(
        f'<a class="qq-group" href="{qq_link(num)}" aria-label="{e(name)} {num}，点击申请加群">'
        f'<span>{e(name)}</span><span class="qq-num">{e(num)}</span></a>'
        for name, num, _tag in QQ_GROUPS
    )
    footer_links = (
        f'<nav class="footer-links" aria-label="站点链接">'
        f'<a href="{seo.pretty_href(root, "progress/index.html")}">学习进度</a>'
        f'<a href="{seo.pretty_href(root, "changelog/index.html")}">更新日志</a>'
        f'<a href="{seo.pretty_href(root, "tags/index.html")}">标签</a>'
        f'<a href="{root}feed.xml">RSS</a>'
        f'</nav>'
    )
    return f"""<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-brand"><strong>邮差战队课程集</strong><span>由「邮差好友公会」制作</span>{footer_links}</div>
    <div class="footer-groups"><span class="footer-label">点击群号申请加群</span>{links}</div>
  </div>
</footer>"""


def qq_cards() -> str:
    cards = []
    for name, num, tag in QQ_GROUPS:
        cards.append(
            f"""      <div class="qq-card">
        <span class="qq-tag">{e(tag)}</span>
        <strong>{e(name)}</strong>
        <span class="qq-number">{e(num)}</span>
        <div class="qq-actions">
          <a class="qq-join" href="{qq_link(num)}">点击申请加群</a>
          <button class="qq-copy" type="button" data-copy="{e(num)}">复制群号</button>
        </div>
      </div>"""
        )
    return "\n".join(cards)


ASSET_VERSION = "dev"


def content_version() -> str:
    """Short content hash used to cache-bust CSS/JS after each content change."""
    digest = hashlib.sha256()
    paths = [META_PATH]
    paths += sorted((SOURCE / "lessons").glob("*.md"))
    paths += sorted((SOURCE / "pages").glob("*"))
    paths += sorted((SOURCE / "static").rglob("*"))
    for path in paths:
        if path.is_file():
            digest.update(path.name.encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()[:10]


def load_meta() -> dict:
    with META_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def rel_root(depth: int) -> str:
    return "../" * depth if depth else "./"


def page_source(name: str) -> str:
    path = SOURCE / "pages" / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def stage_by_id(meta: dict, stage_id: str) -> dict:
    for stage in meta["stages"]:
        if stage["id"] == stage_id:
            return stage
    raise KeyError(stage_id)


def course_by_num(meta: dict, num: int) -> dict | None:
    for course in meta["courses"]:
        if course["num"] == num:
            return course
    return None


NAV_ICONS = {
    "home": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1z"/></svg>',
    "book": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5z"/><path d="M4 18.5A2.5 2.5 0 0 1 6.5 16H20"/></svg>',
    "bolt": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13 2 4 14h6l-1 8 9-12h-6z"/></svg>',
    "check": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/></svg>',
    "tag": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 13 13 20 4 11V4h7z"/><circle cx="8" cy="8" r="1.5"/></svg>',
}


def nav_link(root: str, path: str, label: str, active: bool, icon: str) -> str:
    marker = ' aria-current="page"' if active else ""
    return f'<a href="{seo.pretty_href(root, path)}"{marker}>{NAV_ICONS[icon]}<span>{label}</span></a>'


def shell(
    meta: dict,
    *,
    title: str,
    description: str,
    root: str,
    body_page: str,
    content: str,
    aside: str = "",
    breadcrumb: str = "",
    is_course: bool = False,
    prev_course: dict | None = None,
    next_course: dict | None = None,
    current_course: dict | None = None,
    page_path: str = "",
    page_type: str = "website",
    json_ld: str = "",
    noindex: bool = False,
    extra_scripts: str = "",
    data_root: str | None = None,
    runtime_assets: bool = False,
) -> str:
    site = meta["site"]
    is_lesson = body_page in {c["id"] for c in meta["courses"]}
    full_title = f"{title}｜{site['title']}"
    seo_block = seo.seo_head(
        site,
        title=full_title,
        description=description,
        path=page_path,
        og_type=page_type,
        json_ld=json_ld,
        noindex=noindex,
    )
    if runtime_assets:
        head_assets = f"""<script>
(function(){{
  var r = location.protocol === 'file:' ? './' : '/';
  document.write('<link rel="icon" type="image/svg+xml" href="' + r + 'assets/images/favicon.svg">');
  document.write('<link rel="stylesheet" href="' + r + 'assets/css/site.css?v={ASSET_VERSION}">');
  document.write('<link rel="alternate" type="application/atom+xml" title="{e(site['title'])}" href="' + r + 'feed.xml">');
}})();
</script>
<noscript><link rel="stylesheet" href="/assets/css/site.css?v={ASSET_VERSION}"></noscript>"""
        bottom_scripts = f"""<script>
(function(){{
  var r = location.protocol === 'file:' ? './' : '/';
  ['search-index', 'site', 'courses-data', 'courses'].forEach(function(name){{
    document.write('<script src="' + r + 'assets/js/' + name + '.js?v={ASSET_VERSION}"><\\/script>');
  }});
}})();
</script>"""
    else:
        head_assets = f"""<link rel="icon" type="image/svg+xml" href="{root}assets/images/favicon.svg">
<link rel="stylesheet" href="{root}assets/css/site.css?v={ASSET_VERSION}">
<link rel="alternate" type="application/atom+xml" title="{e(site['title'])}" href="{root}feed.xml">"""
        bottom_scripts = f"""<script src="{root}assets/js/search-index.js?v={ASSET_VERSION}"></script>
<script src="{root}assets/js/site.js?v={ASSET_VERSION}"></script>
<script src="{root}assets/js/courses-data.js?v={ASSET_VERSION}"></script>
<script src="{root}assets/js/courses.js?v={ASSET_VERSION}"></script>
{extra_scripts}"""

    data_root_value = data_root if data_root is not None else root

    reading_tools = ""
    if is_course:
        reading_tools = """    <button class="icon-btn" id="reading-toggle" type="button" aria-label="进入阅读模式" aria-pressed="false" title="阅读模式">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5z"/><path d="M4 18.5A2.5 2.5 0 0 1 6.5 16H20"/></svg>
    </button>
    <button class="icon-btn font-btn" id="font-toggle" type="button" aria-label="切换正文字号" title="切换正文字号">
      <span class="font-glyph" aria-hidden="true">Aa</span>
    </button>
"""
    nav = "\n    ".join([
        nav_link(root, "index.html", "首页", body_page == "home", "home"),
        nav_link(root, "courses/index.html", "课程", body_page == "courses" or is_lesson, "book"),
        nav_link(root, "reference/index.html", "速查", body_page in {"reference", "sources"}, "bolt"),
        nav_link(root, "tags/index.html", "标签", body_page == "tags", "tag"),
        nav_link(root, "quiz/beginner.html", "能力自检 Ⅰ", body_page == "quiz-beginner", "check"),
        nav_link(root, "quiz/advanced.html", "能力自检 Ⅱ", body_page == "quiz-advanced", "check"),
    ])

    crumb = f'<nav class="breadcrumb" aria-label="面包屑">{breadcrumb}</nav>' if breadcrumb else ""
    sidebar = f'<aside class="sidebar">{aside}</aside>' if aside else ""
    layout_class = "layout wrap with-sidebar" if aside else "layout wrap"

    lesson_nav = ""
    if is_course and (prev_course or next_course):
        prev_html = ""
        next_html = ""
        if prev_course:
            prev_html = (
                f'<a id="prev-lesson" href="{seo.pretty_href(root, prev_course["file"])}">'
                f'<span>← 上一课 · {e(prev_course["num"]):0>2}</span>'
                f'<strong>{e(prev_course["title"])}</strong></a>'
            )
        else:
            prev_html = '<span id="prev-lesson" class="disabled" aria-hidden="true"></span>'
        if next_course:
            next_html = (
                f'<a id="next-lesson" class="next" href="{seo.pretty_href(root, next_course["file"])}">'
                f'<span>下一课 · {e(next_course["num"]):0>2} →</span>'
                f'<strong>{e(next_course["title"])}</strong></a>'
            )
        else:
            next_html = '<span id="next-lesson" class="disabled next" aria-hidden="true"></span>'
        lesson_nav = f'<div class="lesson-nav">{prev_html}{next_html}</div>'

    marker = ""
    if current_course:
        marker = (
            '<button class="visited-marker" type="button" data-visited-marker '
            f'data-key="{e(current_course["id"])}" aria-label="标记本课完成">'
            '<span class="marker-dot" aria-hidden="true"></span><span class="marker-text">标记完成</span></button>'
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description)}">
{seo_block}
<meta name="color-scheme" content="light dark">
{head_assets}
<script>{THEME_BOOT}</script>
</head>
<body data-page="{e(body_page)}" data-root="{e(data_root_value)}">
<a class="skip-link" href="#main">跳到正文</a>
<div class="progress" id="progress" aria-hidden="true"><span></span></div>
<header class="topbar">
  <a class="brand" href="{seo.pretty_href(root, 'index.html')}">邮差战队课程集 <span>/ Squad 10.6.x</span></a>
  <nav class="topnav" aria-label="主导航">{nav}</nav>
  <div class="top-actions">
    <a class="icon-btn" id="progress-link" href="{seo.pretty_href(root, 'progress/index.html')}" aria-label="学习进度" title="学习进度"{' aria-current="page"' if body_page == 'progress' else ''}>
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/></svg>
    </a>
    <button class="icon-btn" id="search-open" type="button" aria-label="打开搜索" title="搜索（Ctrl/⌘ + K）">
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><path d="M20 20l-3.5-3.5"></path></svg>
    </button>
{reading_tools}    <button class="icon-btn" id="theme-toggle" type="button" aria-label="切换主题" title="切换主题">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a9 9 0 1 0 9 9c0-.4 0-.8-.1-1.2A7 7 0 0 1 12 3z"></path></svg>
    </button>
  </div>
</header>
{crumb}
<div class="{layout_class}">
  {sidebar}
  <main class="content" id="main">
{content}
    {marker}
    {lesson_nav}
  </main>
</div>
{qq_footer(root)}
<button class="backtop" id="backtop" type="button" aria-label="返回顶部">↑</button>
<div class="search-panel" id="search-panel" role="dialog" aria-modal="true" aria-label="站内搜索" hidden>
  <div class="search-backdrop" data-search-close></div>
  <div class="search-box">
    <div class="search-head">
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><path d="M20 20l-3.5-3.5"></path></svg>
      <input id="search-input" type="search" placeholder="搜索课次、标题、小节、正文或关键词…" autocomplete="off" aria-label="搜索关键词">
      <button type="button" id="search-close" aria-label="关闭搜索">Esc</button>
    </div>
    <div class="search-results" id="search-results" aria-live="polite"></div>
    <p class="search-hint">输入课次或关键词，例如“压制”“FOB”“迫击炮”。</p>
  </div>
</div>
{bottom_scripts}
</body>
</html>
"""


def related_courses(meta: dict, course: dict, limit: int = 4) -> list[tuple[dict, set[str]]]:
    tags = set(course.get("tags", []))
    scored = []
    for other in meta["courses"]:
        if other["num"] == course["num"]:
            continue
        shared = tags & set(other.get("tags", []))
        if not shared:
            continue
        score = len(shared) * 10 + (3 if other["stage"] == course["stage"] else 0)
        scored.append((score, other["num"], other, shared))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [(other, shared) for _score, _num, other, shared in scored[:limit]]


def related_lessons_html(meta: dict, course: dict) -> str:
    related = related_courses(meta, course)
    if not related:
        return ""
    cards = []
    for other, shared in related:
        stage = stage_by_id(meta, other["stage"])
        labels = "、".join(f"#{tag_features.tag_name(meta, slug)}" for slug in sorted(shared))
        cards.append(
            f"""        <a class="related-card" href="{seo.pretty_href('../../', other['file'])}">
          <span>{e(stage['num'])} · 第 {other['num']:02d} 课</span>
          <strong>{e(other['title'])}</strong>
          <small>共同标签：{e(labels)}</small>
        </a>"""
        )
    return f"""    <section class="related-lessons" aria-labelledby="related-title">
      <h2 id="related-title">相关课程<a class="heading-anchor" href="#related-title" aria-label="链接到本节">#</a></h2>
      <div class="related-grid">
{chr(10).join(cards)}
      </div>
    </section>"""


def build_course(meta: dict, course: dict, courses: list[dict]) -> str:
    source_path = ROOT / course["source"]
    if not source_path.exists():
        raise FileNotFoundError(f"Missing lesson source: {source_path}")
    md = source_path.read_text(encoding="utf-8")
    body = render(md)
    word_count = reading.count_cjk(md)
    read_minutes = reading.reading_minutes(md)

    stage = stage_by_id(meta, course["stage"])
    tag_chips = "".join(
        f'<a class="tag-chip" href="../../tags/{e(slug)}">#{e(tag_features.tag_name(meta, slug))}</a>'
        for slug in course.get("tags", [])
    )
    num = f'{course["num"]:02d}'
    idx = courses.index(course)
    prev_course = courses[idx - 1] if idx > 0 else None
    next_course = courses[idx + 1] if idx < len(courses) - 1 else None

    crumb = (
        f'<a href="../../">首页</a><span>/</span>'
        f'<a href="../">学习阶梯</a><span>/</span>'
        f'{e(stage["num"])} {e(stage["name"])}<span>/</span>'
        f'第 {num} 课 {e(course["title"])}'
    )

    aside = f"""
    <div class="sidebar-toggle" id="sidebar-toggle" type="button" role="button" tabindex="0" aria-expanded="false">目录与阶梯 <span>展开</span></div>
    <div class="sidebar-inner" id="sidebar-inner">
      <nav class="ladder" id="course-toc" aria-label="学习阶梯"></nav>
      <nav class="local-toc" id="local-toc" aria-label="本课小节"></nav>
    </div>"""

    content = f"""    <p class="kicker">{e(stage['num'])} · {e(stage['name'])} · 第 {num} 课</p>
    <h1>{e(course['title'])}</h1>
    <p class="lead">{e(course['subtitle'])}</p>
    <div class="lesson-meta">
      <span class="pill">第 {num} 课 / 共 {len(courses):02d} 课</span>
      <span class="pill">{e(stage['num'])} {e(stage['name'])}</span>
      <span class="pill">建议学习 {e(course['minutes'])} 分钟</span>
      <span class="pill">前置：{e(course['prereq'])}</span>
      <span class="pill">更新于 {e(course['updated'])}</span>
    </div>
    <p class="reading-meta">正文约 {word_count:,} 字 · 阅读约 {read_minutes} 分钟</p>
    <div class="tag-list"><span class="tag-list-label">标签</span>{tag_chips}</div>
    <div class="lesson-progress" id="lesson-progress" aria-label="本课进度"><span></span></div>
    <article class="prose">
{body}
    </article>
{related_lessons_html(meta, course)}"""

    lesson_url = seo.absolute_url(meta["site"], course["file"])
    lesson_json_ld = seo.json_ld_learning_resource(meta["site"], course, stage, lesson_url)

    return shell(
        meta,
        title=f'{num} {course["title"]}',
        description=f'{course["title"]}：{course["subtitle"]}。{stage["num"]}{stage["name"]}第 {num} 课。',
        root="../../",
        body_page=course["id"],
        content=content,
        aside=aside,
        breadcrumb=crumb,
        is_course=True,
        prev_course=prev_course,
        next_course=next_course,
        current_course=course,
        page_path=course["file"],
        page_type="article",
        json_ld=lesson_json_ld,
    )


def stage_cards(meta: dict, root: str) -> str:
    cards = []
    for stage in meta["stages"]:
        first = next(c for c in meta["courses"] if c["stage"] == stage["id"])
        cards.append(
            f"""      <a class="stage-card" href="{seo.pretty_href(root, first['file'])}">
        <span class="stage-num">{e(stage['num'])}</span>
        <h3>{e(stage['name'])}</h3>
        <p class="stage-range">第 {e(stage['range'])} 课</p>
        <p>{e(stage['summary'])}</p>
        <span class="stage-link">从第 {first['num']:02d} 课开始 →</span>
      </a>"""
        )
    return "\n".join(cards)


def course_rows(meta: dict, root: str) -> str:
    parts = []
    for stage in meta["stages"]:
        parts.append(f'      <tr class="stage-row"><th colspan="4">{e(stage["num"])} · {e(stage["name"])}（{e(stage["range"])}）</th></tr>')
        for course in [c for c in meta["courses"] if c["stage"] == stage["id"]]:
            parts.append(
                f"""      <tr>
        <td class="num">{course['num']:02d}</td>
        <td><a href="{seo.pretty_href(root, course['file'])}">{e(course['title'])}</a></td>
        <td>{e(course['subtitle'])}</td>
        <td class="minutes">{e(course['minutes'])} 分钟</td>
      </tr>"""
            )
    return "\n".join(parts)


def build_home(meta: dict) -> str:
    notes = page_source("home.md")
    extra = render(notes) if notes.strip() else ""
    content = f"""    <header class="hero">
      <div class="hero-bg" style="background-image:url('https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/393380/ss_62314ae7cc786d5f4ce67f191d37e9a1520d4cb4.1920x1080.jpg?t=1792423549')"></div>
      <div class="hero-inner">
        <p class="kicker">POST Courses · Squad 10.6.x</p>
        <h1>先把第一局打明白，<br>再把队伍带起来。</h1>
        <p class="lead">36 课按六阶战场能力阶梯连续展开：先会活下来，再会看战场，接着理解复活与票账，最后学会带队、协同和复盘。</p>
        <div class="hero-actions">
          <a class="btn primary" id="hero-primary" href="./courses/beginner/01-first-match">从第 01 课开始</a>
          <a class="btn ghost" href="./courses/">查看完整阶梯</a>
        </div>
        <div class="hero-meta"><span>36 课</span><span>六阶能力阶梯</span><span>2 套能力自检</span><span>由邮差好友公会制作</span></div>
      </div>
    </header>
    <section class="intro-section">
      <h2 id="home-s1">一条连续的成长路线<a class="heading-anchor" href="#home-s1" aria-label="链接到本节">#</a></h2>
      <p>36 课串成一条从第一次进服到带队复盘的成长路线。你只需要从第 01 课往前走：每一阶解决一类问题，每一课都留给你可以直接带进下一局的动作。</p>
      <div class="stage-grid">
{stage_cards(meta, './')}
      </div>
      <div class="takeaway">顺序学习就从第 01 课开始；带着问题回来，就按课次跳到对应阶段。</div>
    </section>
    <section class="intro-section">
      <h2 id="home-s2">完整课程表<a class="heading-anchor" href="#home-s2" aria-label="链接到本节">#</a></h2>
      <div class="table-wrap course-table"><table>
        <thead><tr><th>课次</th><th>标题</th><th>一句话目标</th><th>时长</th></tr></thead>
        <tbody>
{course_rows(meta, './')}
        </tbody>
      </table></div>
    </section>
{extra}
    <section class="intro-section tools-section">
      <h2 id="home-s3">顺便带上的工具<a class="heading-anchor" href="#home-s3" aria-label="链接到本节">#</a></h2>
      <div class="tool-grid">
        <a class="tool-card" href="./progress/"><strong>学习进度</strong><span>看 36 课完成到哪，接着上一课继续。</span></a>
        <a class="tool-card" href="./reference/"><strong>速查表</strong><span>票值、复活、压制、报点模板，一页查完。</span></a>
        <a class="tool-card" href="./reference/sources"><strong>资料说明</strong><span>每课根据哪些材料改写，哪些材料只作背景。</span></a>
        <a class="tool-card" href="./tags/"><strong>标签索引</strong><span>按主题找课：医疗、FOB、巷战、载具……</span></a>
        <a class="tool-card" href="./changelog/"><strong>更新日志</strong><span>最近补了哪些课、改了哪些功能。</span></a>
        <a class="tool-card" href="./feed.xml"><strong>RSS 订阅</strong><span>用阅读器订阅课程更新。</span></a>
        <a class="tool-card" href="./quiz/beginner"><strong>能力自检 Ⅰ</strong><span>个人基础、观察报点与资源规则。</span></a>
        <a class="tool-card" href="./quiz/advanced"><strong>能力自检 Ⅱ</strong><span>小队行动、专业协同与指挥复盘。</span></a>
      </div>
    </section>
    <section class="intro-section qq-section">
      <h2 id="home-s4">加入邮差好友公会<a class="heading-anchor" href="#home-s4" aria-label="链接到本节">#</a></h2>
      <p>课程集由邮差好友公会制作和维护。想跟队实战、找人带第一局，或者刚进游戏需要问路，点下面的群卡片直接申请加群。</p>
      <div class="qq-grid">
{qq_cards()}
      </div>
      <div class="takeaway">加群时说明“看到课程集来的”，管理员会把你分到合适的群。</div>
    </section>"""
    home_json_ld = seo.json_ld_website(meta["site"], meta["site"]["description"])
    return shell(
        meta,
        title="首页",
        description=meta["site"]["description"],
        root="./",
        body_page="home",
        content=content,
        page_path="index.html",
        json_ld=home_json_ld,
    )


def build_progress(meta: dict) -> str:
    stage_blocks = []
    for stage in meta["stages"]:
        stage_courses = [c for c in meta["courses"] if c["stage"] == stage["id"]]
        rows = []
        for course in stage_courses:
            rows.append(
                f"""        <li class="progress-item" data-progress-course="{e(course['id'])}">
          <button class="progress-check" type="button" data-progress-toggle="{e(course['id'])}" aria-pressed="false" aria-label="标记第 {course['num']:02d} 课完成"><span class="check-dot" aria-hidden="true"></span><span class="check-text">标记完成</span></button>
          <a class="progress-course" href="{seo.pretty_href('../', course['file'])}"><strong>{course['num']:02d} · {e(course['title'])}</strong><span>{e(course['subtitle'])}</span></a>
          <span class="progress-time">{e(course['minutes'])} 分钟</span>
        </li>"""
            )
        stage_blocks.append(
            f"""    <section class="stage-progress" data-progress-stage="{e(stage['id'])}">
      <div class="stage-progress-head">
        <span class="stage-num">{e(stage['num'])}</span>
        <div><h2 id="progress-{e(stage['id'])}">{e(stage['name'])}<a class="heading-anchor" href="#progress-{e(stage['id'])}" aria-label="链接到本节">#</a></h2><p>{e(stage['summary'])}</p></div>
        <span class="stage-count" data-stage-count="{e(stage['id'])}">0 / {len(stage_courses)}</span>
      </div>
      <div class="stage-bar" aria-hidden="true"><span data-stage-bar="{e(stage['id'])}"></span></div>
      <ul class="progress-list">
{chr(10).join(rows)}
      </ul>
    </section>"""
        )
    first = meta["courses"][0]
    total = len(meta["courses"])
    content = f"""    <div class="progress-hero">
      <span class="progress-hero-mark" aria-hidden="true">✓</span>
      <p class="kicker">学习进度</p>
      <h1 id="progress-title">{total} 课，走到哪了<a class="heading-anchor" href="#progress-title" aria-label="链接到本节">#</a></h1>
      <p class="lead">完成标记保存在当前浏览器。换设备、换浏览器或清理站点数据后，进度不会跟随。</p>
    </div>
    <section class="progress-summary" aria-label="总进度">
      <div class="progress-ring" id="progress-ring" style="--p:0%"><span id="progress-percent">0%</span></div>
      <div class="progress-copy">
        <p class="kicker">当前进度</p>
        <strong id="progress-count">0 / {total} 课</strong>
        <p id="progress-next">下一课：第 {first['num']:02d} 课 · {e(first['title'])}</p>
        <div class="progress-bar" aria-hidden="true"><span id="progress-bar-fill"></span></div>
      </div>
      <div class="progress-actions">
        <a class="btn primary" id="progress-continue" href="{seo.pretty_href('../', first['file'])}">继续第 {first['num']:02d} 课</a>
        <button class="btn ghost" type="button" id="progress-reset">清空进度</button>
      </div>
    </section>
    <p class="progress-warning" id="progress-warning" hidden>浏览器拒绝了本地存储，完成状态无法保存；关闭隐私模式或允许站点存储后再试。</p>
    <noscript><p class="progress-warning">需要启用 JavaScript 才能读取和保存本地进度。</p></noscript>
    <div class="progress-stages">
{chr(10).join(stage_blocks)}
    </div>"""
    desc = f"按六阶查看 {total} 课的完成进度、下一课和每阶完成情况。"
    url = seo.absolute_url(meta["site"], "progress/index.html")
    json_ld = seo.json_ld_webpage(meta["site"], "学习进度", desc, url)
    return shell(
        meta,
        title="学习进度",
        description=desc,
        root="../",
        body_page="progress",
        content=content,
        page_path="progress/index.html",
        json_ld=json_ld,
        extra_scripts=f'<script src="../assets/js/progress.js?v={ASSET_VERSION}"></script>',
    )


def build_courses_index(meta: dict) -> str:
    parts = []
    for stage in meta["stages"]:
        courses = [c for c in meta["courses"] if c["stage"] == stage["id"]]
        cards = []
        for c in courses:
            cards.append(
                f"""        <a class="course-card" href="{seo.pretty_href('../', c['file'])}">
          <span class="course-num">{c['num']:02d}</span>
          <span class="course-body"><strong>{e(c['title'])}</strong><span>{e(c['subtitle'])}</span></span>
          <span class="course-time">{e(c['minutes'])}′</span>
        </a>"""
            )
        parts.append(
            f"""    <section class="stage-section" id="{e(stage['id'])}">
      <div class="stage-head">
        <span class="stage-num">{e(stage['num'])}</span>
        <div><h2 id="{e(stage['id'])}-title">{e(stage['name'])}<a class="heading-anchor" href="#{e(stage['id'])}" aria-label="链接到本节">#</a></h2><p>{e(stage['summary'])}</p></div>
        <span class="stage-range">第 {e(stage['range'])} 课</span>
      </div>
      <div class="course-list">
{chr(10).join(cards)}
      </div>
      <div class="takeaway">{e(stage['name'])}这一阶的重点：{e(stage['summary'])}</div>
    </section>"""
        )
    content = """    <p class="kicker">学习阶梯 · 36 课</p>
    <h1>从会活下来，到能带队复盘</h1>
    <p class="lead">全站按一条连续的六阶能力阶梯组织。课次是全局编号，上一课 / 下一课也按这条顺序切换。</p>
    <div class="note"><b>怎么用</b>第一次学按 01 → 36 顺序走；已经打过一段时间，可以先做两套能力自检，缺哪课补哪课；准备带训练时重点看第四阶到第六阶。</div>
""" + "\n".join(parts)
    overview_desc = "邮差战队课程集完整课程表：六阶能力阶梯，36 课由浅入深。"
    overview_url = seo.absolute_url(meta["site"], "courses/index.html")
    overview_json_ld = seo.json_ld_collection(meta["site"], "课程总览", overview_desc, overview_url)
    return shell(
        meta,
        title="课程总览",
        description=overview_desc,
        root="../",
        body_page="courses",
        content=content,
        page_path="courses/index.html",
        json_ld=overview_json_ld,
    )


def build_tags_index(meta: dict) -> str:
    counts = tag_features.tag_counts(meta)
    cards = []
    for tag in meta.get("tags", []):
        count = counts.get(tag["slug"], 0)
        cards.append(
            f"""      <a class="tag-card" href="./{e(tag['slug'])}">
        <span class="tag-count">{count} 课</span>
        <strong>#{e(tag['name'])}</strong>
        <span>{e(tag['description'])}</span>
      </a>"""
        )
    content = f"""    <div class="tag-hero">
      <span class="tag-hero-mark" aria-hidden="true">#</span>
      <p class="kicker">标签</p>
      <h1>按主题找课</h1>
      <p class="lead">{len(meta.get('tags', []))} 个标签覆盖 {len(meta['courses'])} 课。想补哪一块，就从标签进入。</p>
      <span class="tag-count">{len(meta.get('tags', []))} 个标签</span>
    </div>
    <div class="tag-grid">
{chr(10).join(cards)}
    </div>"""
    url = seo.absolute_url(meta["site"], "tags/index.html")
    json_ld = seo.json_ld_collection(meta["site"], "标签", "按主题浏览邮差战队课程集。", url)
    return shell(
        meta,
        title="标签",
        description="按主题浏览邮差战队课程集：医疗、FOB、巷战、载具、迫击炮等。",
        root="../",
        body_page="tags",
        content=content,
        page_path="tags/index.html",
        json_ld=json_ld,
    )


def build_tag_page(meta: dict, tag: dict) -> str:
    courses = tag_features.courses_for_tag(meta["courses"], tag["slug"])
    cards = []
    for course in courses:
        stage = stage_by_id(meta, course["stage"])
        cards.append(
            f"""        <a class="course-card" href="{seo.pretty_href('../', course['file'])}">
          <span class="course-num">{course['num']:02d}</span>
          <span class="course-body"><strong>{e(course['title'])}</strong><span>{e(stage['name'])} · {e(course['subtitle'])}</span></span>
          <span class="course-time">{e(course['minutes'])}′</span>
        </a>"""
        )
    content = f"""    <div class="tag-hero">
      <span class="tag-hero-mark" aria-hidden="true">#</span>
      <p class="kicker">标签</p>
      <h1>{e(tag['name'])}</h1>
      <p class="lead">{e(tag['description'])}</p>
      <span class="tag-count">共 {len(courses)} 课</span>
    </div>
    <div class="course-list">
{chr(10).join(cards)}
    </div>
    <p><a class="tag-back" href="./">← 全部标签</a></p>"""
    url = seo.absolute_url(meta["site"], f"tags/{tag['slug']}.html")
    json_ld = seo.json_ld_collection(meta["site"], f"标签：{tag['name']}", tag["description"], url)
    return shell(
        meta,
        title=f"标签：{tag['name']}",
        description=f"{tag['name']}：{tag['description']}",
        root="../",
        body_page="tags",
        content=content,
        page_path=f"tags/{tag['slug']}.html",
        json_ld=json_ld,
    )


def build_markdown_page(meta: dict, *, source_name: str, out: str, title: str, desc: str, root: str, body_page: str, noindex: bool = False, data_root: str | None = None, runtime_assets: bool = False) -> str:
    md = page_source(source_name)
    if not md.strip():
        raise FileNotFoundError(f"Missing page source: {source_name}")
    page_url = seo.absolute_url(meta["site"], out)
    page_json_ld = "" if noindex else seo.json_ld_webpage(meta["site"], title, desc, page_url)
    return shell(
        meta,
        title=title,
        description=desc,
        root=root,
        body_page=body_page,
        content=render(md),
        page_path=out,
        page_type="article" if not noindex else "website",
        json_ld=page_json_ld,
        noindex=noindex,
        data_root=data_root,
        runtime_assets=runtime_assets,
    )


def build_changelog(meta: dict) -> str:
    body = render(page_source("changelog.md"))
    total = len(meta["courses"])
    content = f"""    <div class="progress-hero">
      <span class="progress-hero-mark" aria-hidden="true">↻</span>
      <p class="kicker">更新日志</p>
      <h1 id="changelog-title">站点与课程更新<a class="heading-anchor" href="#changelog-title" aria-label="链接到本节">#</a></h1>
      <p class="lead">按日期记录 {total} 课的内容调整与站点功能变化。</p>
    </div>
    <article class="prose">
{body}
    </article>"""
    desc = "邮差战队课程集的内容与功能更新记录。"
    url = seo.absolute_url(meta["site"], "changelog/index.html")
    json_ld = seo.json_ld_webpage(meta["site"], "更新日志", desc, url)
    return shell(
        meta,
        title="更新日志",
        description=desc,
        root="../",
        body_page="changelog",
        content=content,
        page_path="changelog/index.html",
        page_type="article",
        json_ld=json_ld,
    )


def build_quiz(meta: dict, *, source_name: str, out: str, title: str, desc: str, root: str, body_page: str, intro: str) -> str:
    path = SOURCE / "pages" / source_name
    if not path.exists():
        raise FileNotFoundError(f"Missing quiz source: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    questions = data.get("questions", [])
    blocks = []
    for i, q in enumerate(questions, start=1):
        options = "".join(
            f'<li{" class=correct" if j == q["answer"] else ""}>{e(chr(65 + j))}. {inline(opt)}</li>'
            for j, opt in enumerate(q["options"])
        )
        explain = q.get("explain", "")
        explain_html = f'<p class="quiz-explain">{inline(explain)}</p>' if explain else ""
        blocks.append(
            f"""      <details>
        <summary>{i}. {inline(q['q'])}</summary>
        <ol class="quiz-options">{options}</ol>
        <p class="quiz-answer">答：{e(chr(65 + q['answer']))}。{inline(q.get('answer_text', q['options'][q['answer']]))}</p>
        {explain_html}
      </details>"""
        )
    content = f"""    <p class="kicker">能力自检</p>
    <h1>{e(title)}</h1>
    <p class="lead">{e(desc)}</p>
    <div class="note"><b>怎么用</b>先自己回答，再展开答案。错题回到对应课次重看一遍，下一局只练一个动作。</div>
    <div class="quiz-list">
{chr(10).join(blocks)}
    </div>
    <div class="takeaway">自检不是考试排名，是找出下一局最值得练的那一个动作。</div>"""
    quiz_url = seo.absolute_url(meta["site"], out)
    quiz_json_ld = seo.json_ld_webpage(meta["site"], title, desc, quiz_url)
    return shell(
        meta,
        title=title,
        description=desc,
        root=root,
        body_page=body_page,
        content=content,
        page_path=out,
        json_ld=quiz_json_ld,
    )


def build_js(meta: dict) -> None:
    courses_payload = {
        "stages": [
            {"id": s["id"], "num": s["num"], "name": s["name"], "range": s["range"]}
            for s in meta["stages"]
        ],
        "courses": [
            {
                "num": c["num"],
                "id": c["id"],
                "stage": c["stage"],
                "file": seo.pretty_path(c["file"]),
                "title": c["title"],
                "subtitle": c["subtitle"],
                "minutes": c["minutes"],
                "goal": c["goal"],
                "keywords": c["keywords"],
                "tags": [tag_features.tag_name(meta, slug) for slug in c.get("tags", [])],
                "prereq": c["prereq"],
            }
            for c in meta["courses"]
        ],
    }
    search_payload = []
    for course in meta["courses"]:
        source = ROOT / course["source"]
        sections = []
        if source.exists():
            sections = section_index(source.read_text(encoding="utf-8"))
        search_payload.append({
            "num": course["num"],
            "id": course["id"],
            "stage": stage_by_id(meta, course["stage"])["name"],
            "title": course["title"],
            "subtitle": course["subtitle"],
            "path": seo.pretty_path(course["file"]),
            "keywords": course["keywords"],
            "tags": [tag_features.tag_name(meta, slug) for slug in course.get("tags", [])],
            "sections": sections,
        })
    write(DIST / "assets/js/courses-data.js", "window.YOUCHAI_COURSES = " + json.dumps(courses_payload, ensure_ascii=False, indent=2) + ";\n")
    write(DIST / "assets/js/search-index.js", "window.YOUCHAI_SEARCH_INDEX = " + json_for_script(search_payload) + ";\n")


def json_for_script(payload: object) -> str:
    """Serialize JSON without indent and neutralize characters that can end a script."""
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def copy_static() -> None:
    for rel in ["assets/css/site.css", "assets/js/site.js", "assets/js/courses.js", "assets/js/progress.js"]:
        src = SOURCE / "static" / rel.replace("assets/", "")
        if not src.exists():
            raise FileNotFoundError(f"Missing static source: {src}")
        dst = DIST / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    images_src = SOURCE / "static" / "images"
    if images_src.is_dir():
        shutil.copytree(images_src, DIST / "assets/images", dirs_exist_ok=True)
    headers_src = ROOT / "_headers"
    if headers_src.exists():
        shutil.copyfile(headers_src, DIST / "_headers")
    else:
        write(DIST / "_headers", "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n\n/*.html\n  Cache-Control: max-age=0, must-revalidate\n\n/assets/*\n  Cache-Control: public, max-age=604800\n")


def main() -> None:
    global ASSET_VERSION
    meta = load_meta()
    courses = meta["courses"]
    DIST.mkdir(parents=True, exist_ok=True)
    ASSET_VERSION = content_version()

    write(DIST / "index.html", build_home(meta))
    write(DIST / "404.html", build_markdown_page(
        meta,
        source_name="404.md",
        out="404.html",
        title="页面不存在",
        desc="这个页面不存在，回到课程阶梯继续学习。",
        root="/",
        body_page="404",
        noindex=True,
        data_root="./",
        runtime_assets=True,
    ))
    write(DIST / "courses/index.html", build_courses_index(meta))
    for course in courses:
        target = DIST / course["file"]
        write(target, build_course(meta, course, courses))
    write(DIST / "reference/index.html", build_markdown_page(
        meta,
        source_name="reference.md",
        out="reference/index.html",
        title="速查表",
        desc="Squad 票数、复活、压制、队包、迫击炮刻度与报点模板速查。",
        root="../",
        body_page="reference",
    ))
    write(DIST / "reference/sources.html", build_markdown_page(
        meta,
        source_name="sources.md",
        out="reference/sources.html",
        title="资料说明",
        desc="邮差战队课程集如何把 33 份教材改写为 36 课。",
        root="../",
        body_page="sources",
    ))
    write(DIST / "quiz/beginner.html", build_quiz(
        meta,
        source_name="quiz-beginner.json",
        out="quiz/beginner.html",
        title="能力自检 Ⅰ：个人基础",
        desc="个人基础、观察报点、复活与资源规则。",
        root="../",
        body_page="quiz-beginner",
        intro="",
    ))
    write(DIST / "quiz/advanced.html", build_quiz(
        meta,
        source_name="quiz-advanced.json",
        out="quiz/advanced.html",
        title="能力自检 Ⅱ：小队指挥",
        desc="小队行动、专业协同与指挥复盘。",
        root="../",
        body_page="quiz-advanced",
        intro="",
    ))
    write(DIST / "progress/index.html", build_progress(meta))
    write(DIST / "changelog/index.html", build_changelog(meta))
    write(DIST / "tags/index.html", build_tags_index(meta))
    for tag in meta.get("tags", []):
        write(DIST / f"tags/{tag['slug']}.html", build_tag_page(meta, tag))
    write(DIST / "feed.xml", feed.build_feed(meta, courses))
    write(DIST / "sitemap.xml", sitemap.build_sitemap(meta, courses))
    write(DIST / "robots.txt", sitemap.build_robots(meta))
    build_js(meta)
    copy_static()
    html_pages = sum(1 for _ in DIST.rglob("*.html"))
    print(f"built {len(courses)} lessons and {html_pages} HTML pages into {DIST}")


if __name__ == "__main__":
    main()
