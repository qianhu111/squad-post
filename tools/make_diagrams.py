#!/usr/bin/env python3
"""Author-side SVG diagram generator for the Youchai course site.

The generated SVGs are plain vector assets, not model-generated bitmaps.
They are copied into dist/assets/images by tools/build.py.
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "source" / "static" / "images"
FONT = "'Microsoft YaHei','PingFang SC','Noto Sans SC',sans-serif"
COL = {
    "gray": "#5b6875",
    "blue": "#1f5d78",
    "red": "#b42318",
    "amber": "#d97706",
    "green": "#2f7d5b",
}


def txt(x: int, y: int, s: str, cls: str = "l", anchor: str = "start", fill: str | None = None) -> str:
    f = f' fill="{fill}"' if fill else ""
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"{f}>{s}</text>'


def arrow(x1: int, y1: int, x2: int, y2: int, c: str = "gray", dash: str | None = None, w: int = 3) -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{COL[c]}" '
        f'stroke-width="{w}"{d} marker-end="url(#ar-{c})"/>'
    )


def svg(title: str, desc: str, body: str) -> str:
    markers = "".join(
        f'<marker id="ar-{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="{color}"/></marker>'
        for name, color in COL.items()
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" role="img" aria-labelledby="ttl dsc">
<title id="ttl">{title}</title><desc id="dsc">{desc}</desc>
<rect width="800" height="450" rx="16" fill="#f7f9fb"/>
<defs>{markers}</defs>
<style>text{{font-family:{FONT};fill:#16212b}}.muted{{fill:#5b6875}}.s{{font-size:14px}}.l{{font-size:16px;font-weight:700}}.t{{font-size:20px;font-weight:800}}</style>
{body}
</svg>
'''


def threat_rings() -> str:
    body = (
        txt(40, 42, "威胁圈：先判断谁能在多远处打到你", "t")
        + '<circle cx="230" cy="315" r="230" fill="none" stroke="#b42318" stroke-width="2" stroke-dasharray="8 7"/>'
        + '<circle cx="230" cy="315" r="150" fill="none" stroke="#d97706" stroke-width="2" stroke-dasharray="8 7"/>'
        + '<circle cx="230" cy="315" r="72" fill="#eaf5ef" stroke="#2f7d5b" stroke-width="2"/>'
        + '<circle cx="230" cy="315" r="10" fill="#1f5d78"/>'
        + txt(230, 352, "你", "s", "middle")
        + txt(230, 275, "安全区", "s", "middle", "#2f7d5b")
        + txt(230, 190, "观察区", "s", "middle", "#d97706")
        + txt(230, 100, "交火区", "s", "middle", "#b42318")
        + '<path d="M60 250 C230 170 420 150 745 105" fill="none" stroke="#5b6875" stroke-width="2" stroke-dasharray="10 6"/>'
        + txt(610, 86, "锋线", "s", "middle", "#5b6875")
        + '<line x1="430" y1="315" x2="760" y2="315" stroke="#5b6875" stroke-width="2" stroke-dasharray="4 6"/>'
        + txt(706, 340, "腰线", "s", "middle", "#5b6875")
        + '<circle cx="640" cy="140" r="11" fill="#b42318"/>'
        + txt(660, 145, "敌方火力", "s")
        + txt(40, 420, "内圈先保命，中圈先观察，外圈才考虑交火。", "s", "start", "#5b6875")
    )
    return svg("威胁圈与锋线腰线", "以自己为圆心画出安全区、观察区和交火区，并标出锋线与腰线。", body)


def los_cover() -> str:
    def panel(x: int, title: str, kind: str) -> str:
        s = f'<rect x="{x}" y="70" width="240" height="340" rx="12" fill="#ffffff" stroke="#dfe6ee"/>'
        s += txt(x + 120, 105, title, "l", "middle")
        s += f'<rect x="{x + 150}" y="150" width="18" height="190" rx="3" fill="#5b6875"/>'
        s += f'<circle cx="{x + 80}" cy="245" r="10" fill="#1f5d78"/>' + txt(x + 80, 275, "你", "s", "middle")
        s += f'<circle cx="{x + 205}" cy="245" r="10" fill="#b42318"/>' + txt(x + 205, 275, "威胁", "s", "middle")
        if kind == "sight":
            s += f'<line x1="{x + 90}" y1="245" x2="{x + 148}" y2="245" stroke="#1f5d78" stroke-width="2" stroke-dasharray="6 5"/>'
            s += f'<path d="M{x + 141} 236 l14 14 M{x + 155} 236 l-14 14" stroke="#b42318" stroke-width="3"/>'
            s += txt(x + 120, 360, "视线被墙截断", "s", "middle", "#1f5d78")
        elif kind == "bullet":
            s += f'<line x1="{x + 195}" y1="245" x2="{x + 170}" y2="245" stroke="#b42318" stroke-width="2" stroke-dasharray="6 5"/>'
            s += f'<path d="M{x + 161} 236 l14 14 M{x + 175} 236 l-14 14" stroke="#b42318" stroke-width="3"/>'
            s += txt(x + 120, 360, "射线被墙挡住", "s", "middle", "#b42318")
        else:
            s += f'<circle cx="{x + 205}" cy="245" r="30" fill="#fff1f0" stroke="#b42318" stroke-width="2"/>'
            for dx, dy in [(-42, 0), (42, 0), (0, -42), (0, 42), (-30, -30), (30, -30), (-30, 30), (30, 30)]:
                s += f'<line x1="{x + 205}" y1="245" x2="{x + 205 + dx}" y2="{245 + dy}" stroke="#d97706" stroke-width="2"/>'
            s += txt(x + 120, 360, "墙后挡破片", "s", "middle", "#d97706")
        s += txt(x + 120, 388, ["看得到", "打得到", "炸得到"][["sight", "bullet", "blast"].index(kind)], "s", "middle", "#5b6875")
        return s

    body = txt(40, 42, "视线、射线、爆炸掩护不是一回事", "t") + panel(20, "视线", "sight") + panel(280, "射线", "bullet") + panel(540, "爆炸", "blast")
    return svg("视线、射线与爆炸掩护", "三块面板分别说明墙体如何阻挡观察、子弹和爆炸破片。", body)


def spawn_layers() -> str:
    body = (
        txt(40, 42, "复活层级：主基地、FOB、HAB、队包", "t")
        + '<rect x="55" y="215" width="70" height="70" rx="10" fill="#e8f2f6" stroke="#1f5d78" stroke-width="2"/>'
        + txt(90, 305, "主基地", "s", "middle")
        + arrow(130, 250, 292, 250, "blue")
        + txt(211, 236, "≥400 米", "s", "middle", "#1f5d78")
        + '<circle cx="390" cy="250" r="112" fill="none" stroke="#1f5d78" stroke-width="2" stroke-dasharray="8 6"/>'
        + '<rect x="358" y="222" width="64" height="56" rx="8" fill="#e8f2f6" stroke="#1f5d78" stroke-width="2"/>'
        + txt(390, 208, "FOB 电台", "s", "middle")
        + '<rect x="368" y="234" width="44" height="32" rx="5" fill="#ffffff" stroke="#1f5d78" stroke-width="2"/>'
        + txt(390, 288, "HAB", "s", "middle")
        + txt(390, 330, "建造圈 150 米", "s", "middle", "#1f5d78")
        + arrow(505, 250, 638, 250, "green")
        + txt(571, 236, "小队", "s", "middle", "#2f7d5b")
        + '<circle cx="690" cy="250" r="48" fill="#eaf5ef" stroke="#2f7d5b" stroke-width="2" stroke-dasharray="6 5"/>'
        + '<path d="M690 214 v34" stroke="#2f7d5b" stroke-width="3"/><path d="M690 214 l17 8 -17 8z" fill="#2f7d5b"/>'
        + txt(690, 322, "队包", "s", "middle", "#2f7d5b")
        + txt(690, 342, "60 秒一波", "s", "middle")
        + txt(40, 410, "越靠前复活越快，但越容易被压制、被踩或被毁。", "s", "start", "#5b6875")
    )
    return svg("复活层级", "主基地到 FOB 电台、HAB 兵站和队包的层级关系及距离提示。", body)


def fob_radius() -> str:
    def fob(cx: int, label: str) -> str:
        s = f'<circle cx="{cx}" cy="255" r="130" fill="#e8f2f6" stroke="#1f5d78" stroke-width="2" stroke-dasharray="8 6" opacity="0.75"/>'
        s += f'<rect x="{cx - 22}" y="235" width="44" height="42" rx="6" fill="#1f5d78"/>'
        s += txt(cx, 225, label, "s", "middle")
        s += f'<rect x="{cx - 50}" y="286" width="30" height="20" rx="3" fill="#d97706"/>' + txt(cx - 35, 321, "HAB", "s", "middle")
        s += f'<rect x="{cx + 24}" y="286" width="30" height="20" rx="3" fill="#2f7d5b"/>' + txt(cx + 39, 321, "弹药", "s", "middle")
        s += f'<rect x="{cx - 10}" y="160" width="20" height="20" rx="3" fill="#b42318"/>' + txt(cx, 152, "维修", "s", "middle")
        return s

    body = (
        txt(40, 42, "FOB 选址：两个圈，一条线", "t")
        + fob(220, "FOB A") + fob(580, "FOB B")
        + '<line x1="352" y1="255" x2="448" y2="255" stroke="#b42318" stroke-width="3" marker-end="url(#ar-red)"/>'
        + txt(400, 240, "≥400 米", "s", "middle", "#b42318")
        + txt(40, 410, "两个 FOB 的建造圈不要连成一片；电台被毁 −20 票，主动拆不扣票。", "s", "start", "#5b6875")
    )
    return svg("FOB 间距与建造圈", "两个 FOB 电台至少相距 400 米，各自拥有 150 米建造圈。", body)


def hab_suppression() -> str:
    body = (
        txt(40, 42, "HAB 压制：人数越多，压制圈越大", "t")
        + '<circle cx="330" cy="270" r="200" fill="none" stroke="#b42318" stroke-width="2" stroke-dasharray="8 7"/>'
        + '<circle cx="330" cy="270" r="133" fill="none" stroke="#d97706" stroke-width="2" stroke-dasharray="8 7"/>'
        + '<circle cx="330" cy="270" r="44" fill="none" stroke="#5b6875" stroke-width="2" stroke-dasharray="6 5"/>'
        + '<rect x="305" y="245" width="50" height="50" rx="6" fill="#e8f2f6" stroke="#1f5d78" stroke-width="2"/>'
        + txt(330, 275, "HAB", "s", "middle")
        + txt(330, 334, "20 米", "s", "middle", "#5b6875")
        + txt(470, 270, "60 米", "s", "start", "#d97706")
        + txt(537, 270, "90 米", "s", "start", "#b42318")
        + '<circle cx="330" cy="226" r="9" fill="#b42318"/>' + txt(330, 213, "2 人", "s", "middle", "#b42318")
        + '<circle cx="463" cy="270" r="9" fill="#b42318"/>' + txt(463, 294, "4 人", "s", "middle", "#b42318")
        + '<circle cx="330" cy="137" r="9" fill="#b42318"/>' + txt(330, 125, "6 人", "s", "middle", "#b42318")
        + '<circle cx="530" cy="270" r="9" fill="#b42318"/>' + txt(530, 294, "9 人", "s", "middle", "#b42318")
        + txt(590, 120, "2 人 20 米起", "s")
        + txt(590, 146, "每多 1 人 +10 米", "s")
        + txt(590, 172, "最高 9 人 90 米", "s")
        + txt(590, 212, "倒地敌人、载具内敌人", "s", "start", "#b42318")
        + txt(590, 234, "不计入压制", "s", "start", "#b42318")
        + txt(590, 274, "解除后 30 秒恢复复活", "s", "start", "#d97706")
        + txt(40, 420, "压制没解除就复活，出来也是送票。", "s", "start", "#5b6875")
    )
    return svg("HAB 压制阶梯", "HAB 周围敌人数量与距离决定压制范围，最多 9 人 90 米。", body)


def fireteam_formations() -> str:
    def dot(x: int, y: int, n: str) -> str:
        return f'<circle cx="{x}" cy="{y}" r="15" fill="#1f5d78"/><text x="{x}" y="{y + 6}" class="s" text-anchor="middle" fill="#ffffff">{n}</text>'

    body = (
        txt(40, 42, "1-2 与 2-1：队形按视线和威胁方向选", "t")
        + '<rect x="30" y="80" width="350" height="300" rx="14" fill="#ffffff" stroke="#dfe6ee"/>'
        + txt(205, 112, "1-2 队形", "l", "middle")
        + dot(205, 160, "1") + dot(145, 285, "2") + dot(265, 285, "3")
        + arrow(205, 180, 205, 235, "blue", "6 5")
        + arrow(145, 265, 145, 220, "gray", "4 5")
        + arrow(265, 265, 265, 220, "gray", "4 5")
        + txt(205, 350, "前方观察，后方火力", "s", "middle", "#5b6875")
        + '<rect x="420" y="80" width="350" height="300" rx="14" fill="#ffffff" stroke="#dfe6ee"/>'
        + txt(595, 112, "2-1 队形", "l", "middle")
        + dot(545, 165, "1") + dot(645, 165, "2") + dot(595, 290, "3")
        + arrow(545, 185, 545, 235, "gray", "4 5")
        + arrow(645, 185, 645, 235, "gray", "4 5")
        + arrow(595, 270, 595, 225, "blue", "6 5")
        + txt(595, 350, "双人前沿，一人支援", "s", "middle", "#5b6875")
        + txt(40, 420, "狭窄地形收紧，开阔地拉开；不要为了整齐牺牲射界。", "s", "start", "#5b6875")
    )
    return svg("1-2 与 2-1 队形", "两种三人队形的站位、推进方向和适用场景。", body)


def room_clearing() -> str:
    body = (
        txt(40, 42, "房间清理：先远角，后近角，不在门口停", "t")
        + '<rect x="140" y="90" width="520" height="270" rx="4" fill="#ffffff" stroke="#5b6875" stroke-width="4"/>'
        + '<rect x="140" y="330" width="220" height="30" fill="#f7f9fb"/>'
        + '<rect x="440" y="330" width="220" height="30" fill="#f7f9fb"/>'
        + '<polygon points="360,330 440,330 415,285 385,285" fill="#b42318" opacity="0.14"/>'
        + '<circle cx="375" cy="392" r="11" fill="#1f5d78"/><circle cx="405" cy="392" r="11" fill="#1f5d78"/><circle cx="435" cy="392" r="11" fill="#1f5d78"/>'
        + arrow(405, 380, 405, 345, "blue")
        + '<text x="170" y="120" class="l" fill="#b42318">1</text>'
        + '<text x="620" y="120" class="l" fill="#b42318">2</text>'
        + '<text x="170" y="345" class="l" fill="#b42318">3</text>'
        + '<text x="620" y="345" class="l" fill="#b42318">4</text>'
        + '<path d="M405 330 C330 250 260 160 190 130" fill="none" stroke="#1f5d78" stroke-width="2" stroke-dasharray="6 5" marker-end="url(#ar-blue)"/>'
        + '<path d="M405 300 C470 220 560 160 615 130" fill="none" stroke="#1f5d78" stroke-width="2" stroke-dasharray="6 5" marker-end="url(#ar-blue)"/>'
        + txt(400, 310, "致命漏斗", "s", "middle", "#b42318")
        + txt(40, 430, "门口停留越久越危险；进房前先分工看远角、近角和身后。", "s", "start", "#5b6875")
    )
    return svg("房间清理顺序", "从门口进入房间后按远角、近角、侧后顺序清理，门口是致命漏斗。", body)


def mortar_correction() -> str:
    body = (
        txt(40, 42, "迫击炮修正：一次只报一个方向和一个量", "t")
        + '<circle cx="120" cy="360" r="14" fill="#2f7d5b"/>' + txt(120, 392, "观察位", "s", "middle", "#2f7d5b")
        + '<line x1="134" y1="352" x2="518" y2="214" stroke="#2f7d5b" stroke-width="2" stroke-dasharray="5 5"/>'
        + '<path d="M508 204 l24 20 M532 204 l-24 20" stroke="#b42318" stroke-width="4"/>' + txt(532, 205, "目标", "s", "#b42318")
        + '<circle cx="610" cy="278" r="13" fill="#d97706"/>' + txt(625, 284, "落点", "s", "#d97706")
        + arrow(600, 270, 540, 250, "amber") + txt(570, 242, "左修 20 米", "s", "middle", "#d97706")
        + arrow(520, 240, 520, 214, "amber") + txt(505, 230, "加 50 米", "s", "end", "#d97706")
        + '<circle cx="700" cy="120" r="36" fill="#ffffff" stroke="#5b6875" stroke-width="2"/>'
        + '<path d="M700 90 v22 M700 128 v22 M670 120 h22 M708 120 h22" stroke="#5b6875" stroke-width="3"/>'
        + txt(700, 78, "方位", "s", "middle", "#5b6875")
        + txt(40, 420, "先报方向，再报距离；炮手修正后再报下一次，不要一口气报三个变量。", "s", "start", "#5b6875")
    )
    return svg("迫击炮落点修正", "观察位、目标与落点的关系，以及先方向后距离的修正顺序。", body)


def vehicle_infantry() -> str:
    body = (
        txt(40, 42, "步载协同：车看远处，步兵补盲区", "t")
        + '<rect x="300" y="165" width="200" height="120" rx="18" fill="#dce8ee" stroke="#1f5d78" stroke-width="3"/>'
        + txt(400, 232, "步战车 / 装甲车", "l", "middle", "#1f5d78")
        + '<path d="M500 190 C570 190 590 260 500 260 Z" fill="#b42318" opacity="0.16"/>'
        + '<path d="M300 190 C230 190 210 260 300 260 Z" fill="#b42318" opacity="0.16"/>'
        + txt(590, 210, "车体盲区", "s", "start", "#b42318")
        + txt(210, 210, "车体盲区", "s", "end", "#b42318")
        + '<circle cx="260" cy="130" r="13" fill="#1f5d78"/><circle cx="540" cy="130" r="13" fill="#1f5d78"/>'
        + '<circle cx="260" cy="320" r="13" fill="#1f5d78"/><circle cx="540" cy="320" r="13" fill="#1f5d78"/>'
        + txt(260, 112, "步兵观察", "s", "middle", "#1f5d78")
        + txt(540, 112, "步兵观察", "s", "middle", "#1f5d78")
        + arrow(300, 300, 240, 300, "blue", "6 5") + arrow(500, 300, 560, 300, "blue", "6 5")
        + txt(400, 330, "下车后先占两侧", "s", "middle", "#1f5d78")
        + txt(40, 420, "车不能替你占点，也不能替你看所有角度；步兵下车后先建立观察和火力。", "s", "start", "#5b6875")
    )
    return svg("步载协同与盲区", "装甲车前后存在盲区，步兵在车外两侧补观察并在下车后展开。", body)


def review_loop() -> str:
    body = (
        txt(40, 42, "复盘闭环：事实 → 判断 → 动作 → 结果 → 下次改什么", "t")
        + '<circle cx="400" cy="235" r="145" fill="none" stroke="#dfe6ee" stroke-width="2" stroke-dasharray="6 6"/>'
        + '<path d="M400 90 A145 145 0 1 1 399 90" fill="none" stroke="#1f5d78" stroke-width="3" marker-end="url(#ar-blue)"/>'
        + '<circle cx="400" cy="235" r="54" fill="#e8f2f6" stroke="#1f5d78" stroke-width="2"/>'
        + txt(400, 242, "复盘", "l", "middle", "#1f5d78")
        + '<circle cx="400" cy="90" r="34" fill="#ffffff" stroke="#1f5d78" stroke-width="2"/>' + txt(400, 96, "事实", "s", "middle")
        + '<circle cx="538" cy="190" r="34" fill="#ffffff" stroke="#1f5d78" stroke-width="2"/>' + txt(538, 196, "判断", "s", "middle")
        + '<circle cx="485" cy="352" r="34" fill="#ffffff" stroke="#1f5d78" stroke-width="2"/>' + txt(485, 358, "动作", "s", "middle")
        + '<circle cx="315" cy="352" r="40" fill="#ffffff" stroke="#1f5d78" stroke-width="2"/>' + txt(315, 358, "结果", "s", "middle")
        + '<circle cx="262" cy="190" r="46" fill="#ffffff" stroke="#1f5d78" stroke-width="2"/>' + txt(262, 196, "下次改", "s", "middle")
        + txt(40, 425, "复盘不是追责；每一轮只留下一个下一局能执行的动作。", "s", "start", "#5b6875")
    )
    return svg("复盘闭环", "从事实、判断、动作、结果到下次改进的五步循环。", body)


def ticket_ledger() -> str:
    def card(x: int, y: int, w: int, h: int, title: str, big: str, note: str) -> str:
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#ffffff" stroke="#dfe6ee"/>'
            + txt(x + 22, y + 34, title, "l")
            + txt(x + 22, y + 86, big, "t", "start", "#1f5d78")
            + txt(x + 22, y + 120, note, "s", "start", "#5b6875")
        )

    body = (
        txt(40, 42, "票数账本：先看净摆动，再看绝对值", "t")
        + card(30, 80, 350, 150, "抢占敌方已占点", "+30 / −30", "净摆动 60 票")
        + card(420, 80, 350, 150, "占领中立点", "+20", "拉白不加分，占领成功才结算")
        + '<rect x="30" y="260" width="740" height="80" rx="14" fill="#fff5e6" stroke="#d97706"/>'
        + txt(50, 295, "FOB 电台被毁 −20 票；主动拆除不扣票。", "l", "start", "#d97706")
        + txt(50, 322, "别把“敌方掉票”记成“我方得分”，写账时把两边分开。", "s", "start", "#5b6875")
        + txt(40, 420, "同一段时间只够做一件事时，用净摆动比较，而不是用单边数字比较。", "s", "start", "#5b6875")
    )
    return svg("票数账本", "抢占敌方点位的 +30 与 −30、中立点 +20，以及电台损失的记账方式。", body)


def jungle_flank() -> str:
    trees = [(90, 110), (180, 90), (260, 130), (120, 210), (210, 200), (300, 230), (90, 320), (180, 330), (280, 320), (380, 110), (470, 90), (560, 120), (640, 160), (700, 250), (600, 300), (500, 340), (400, 360)]
    body = txt(40, 42, "丛林：短视线把侧翼和节点放大", "t")
    for x, y in trees:
        body += f'<circle cx="{x}" cy="{y}" r="26" fill="#2f7d5b" opacity="0.18"/><circle cx="{x}" cy="{y}" r="11" fill="#2f7d5b" opacity="0.55"/>'
    body += '<path d="M120 380 C220 340 280 300 360 260 C440 220 520 190 620 150" fill="none" stroke="#1f5d78" stroke-width="4" stroke-dasharray="9 6" marker-end="url(#ar-blue)"/>'
    body += '<circle cx="120" cy="380" r="11" fill="#1f5d78"/><circle cx="360" cy="260" r="11" fill="#1f5d78"/><circle cx="620" cy="150" r="11" fill="#1f5d78"/>'
    body += txt(120, 410, "小队", "s", "middle", "#1f5d78") + txt(360, 240, "节点", "s", "middle", "#1f5d78")
    body += arrow(740, 320, 540, 240, "red") + txt(700, 350, "侧翼威胁", "s", "middle", "#b42318")
    body += txt(560, 80, "短视线", "s", "middle", "#5b6875")
    body += txt(40, 430, "队形收紧，侧翼先设观察；低频通信，用预设手势和节点回报。", "s", "start", "#5b6875")
    return svg("丛林侧翼与节点", "丛林中视线很短，队伍沿节点推进，侧翼需要单独观察。", body)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    diagrams = {
        "threat-rings.svg": threat_rings(),
        "los-cover.svg": los_cover(),
        "spawn-layers.svg": spawn_layers(),
        "fob-radius.svg": fob_radius(),
        "hab-suppression.svg": hab_suppression(),
        "fireteam-formations.svg": fireteam_formations(),
        "room-clearing.svg": room_clearing(),
        "mortar-correction.svg": mortar_correction(),
        "vehicle-infantry.svg": vehicle_infantry(),
        "review-loop.svg": review_loop(),
        "ticket-ledger.svg": ticket_ledger(),
        "jungle-flank.svg": jungle_flank(),
    }
    for name, content in diagrams.items():
        (OUT / name).write_text(content, encoding="utf-8", newline="\n")
    print(f"wrote {len(diagrams)} diagrams to {OUT}")


if __name__ == "__main__":
    main()
