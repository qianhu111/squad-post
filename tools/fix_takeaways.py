#!/usr/bin/env python3
"""Add missing ::: takeaway blocks to all lesson sections."""

from pathlib import Path

TAKEAWAYS = {
    "学完能做到什么": "掌握本课列出的学习目标，作为自学和自检的依据。",
    "决策速查": "这些是本课最常用的快速判断规则，实战中优先参考。",
    "实战案例": "案例展示了理论在实际战斗中的应用，重点看决策过程和结果。",
    "常见错误": "避免这些错误比学习新技巧更快提升胜率。",
    "实战练习": "完成这些练习标志着你掌握了本课的核心技能。",
    "自检 3 问": "能回答这三个问题，说明本课基础已合格，可进入下一课。",
}

lessons_dir = Path("source/lessons")
fixed = 0
for md in sorted(lessons_dir.glob("*.md")):
    text = md.read_text(encoding="utf-8")
    lines = text.splitlines()
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            section_name = line[3:].strip()
            block_lines = [line]
            i += 1
            while i < len(lines) and not lines[i].startswith("## "):
                block_lines.append(lines[i])
                i += 1
            block = "\n".join(block_lines)
            if "::: takeaway" not in block and section_name in TAKEAWAYS:
                block_lines.append("")
                block_lines.append("::: takeaway")
                block_lines.append(TAKEAWAYS[section_name])
                block_lines.append(":::")
                fixed += 1
                print(f"{md.name}: added takeaway to {section_name}")
            new_lines.extend(block_lines)
        else:
            new_lines.append(line)
            i += 1
    md.write_text("\n".join(new_lines), encoding="utf-8")

print(f"\nTotal takeaways added: {fixed}")
