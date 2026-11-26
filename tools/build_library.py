#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 docs/wish-library.json 内联进 index.html 的 #libData（站内 #/library 页用）。
文案只在这里流动：真源 docs/wish-library.md → json → 内联。不写进 data-key 体系。

    python3 tools/build_library.py
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")
SRC = os.path.join(ROOT, "docs", "wish-library.json")

LABELS = {
    "nav": {"zh": "灵感库", "en": "Library"},
    "eyebrow": {"zh": "灵感库 · 100 条", "en": "Library · 100 entries"},
    "title": {"zh": "不知道许什么愿，先看这 100 条", "en": "Not sure what to wish for? Start with these 100."},
    "lead": {
        "zh": "60 条心愿、40 条计划，来自真实的人在公开清单里写下的东西。我们把它们读成一句话：一条能直接写进 DearMe 的许愿句式——不承诺结果，只把「想要」说得具体一点。",
        "en": "60 wishes and 40 plans, collected from lists real people post in public. Each one is written as a sentence you could type into DearMe: no promises about outcomes, just a slightly more specific way of saying what you want.",
    },
    "statW": {"zh": "心愿文案", "en": "Wishes"},
    "statP": {"zh": "计划文案", "en": "Plans"},
    "statCat": {"zh": "心愿类型", "en": "Wish types"},
    "statFreq": {"zh": "频次档位", "en": "Rhythms"},
    "tabW": {"zh": "心愿", "en": "Wishes"},
    "tabP": {"zh": "计划", "en": "Plans"},
    "all": {"zh": "全部", "en": "All"},
    "basis": {"zh": "为什么这句能立住", "en": "Why it holds"},
    "evTitle": {"zh": "22 条热度依据", "en": "22 sources behind this"},
    "evNote": {
        "zh": "点开标题可看原帖。这里只保留标题与链接，不列作者昵称与点赞数。",
        "en": "Each title opens the original post. Titles and links only — no author names or like counts.",
    },
    "ctaTitle": {"zh": "挑一条，写进你的第一个心愿", "en": "Pick one. Make it your first wish."},
    "ctaSub": {"zh": "打开 DearMe，六类心愿随你选；写下来之后，它自己会长出下一步。",
               "en": "Open DearMe, pick a type, write it down — the next step grows from there."},
    "ctaBtn": {"zh": "下载 App", "en": "Get the app"},
    "ctaLink": {"zh": "先看看功能", "en": "See features"},
    "cat": {
        "material": {"zh": "物质", "en": "Material"},
        "experience": {"zh": "体验", "en": "Experience"},
        "growth": {"zh": "成长", "en": "Growth"},
        "relationship": {"zh": "关系", "en": "Relationship"},
        "selfcare": {"zh": "自我关怀", "en": "Self-care"},
        "vision": {"zh": "愿景", "en": "Vision"},
    },
    "freq": {
        "once": {"zh": "单次", "en": "Once"},
        "daily": {"zh": "每日", "en": "Daily"},
        "weekly": {"zh": "每周", "en": "Weekly"},
        "monthly": {"zh": "每月", "en": "Monthly"},
        "yearly": {"zh": "每年", "en": "Yearly"},
    },
    "kind": {
        "习惯": {"zh": "习惯", "en": "Habit"},
        "任务": {"zh": "任务", "en": "Task"},
        "项目": {"zh": "项目", "en": "Project"},
        "清单": {"zh": "清单", "en": "Checklist"},
        "陪伴": {"zh": "陪伴", "en": "Company"},
    },
}


def main():
    d = json.load(open(SRC, encoding="utf-8"))
    payload = {
        "labels": LABELS,
        "wishes": [{"id": w["id"], "t": w["type"], "zh": w["zh"], "en": w["en"], "b": w["basis"]} for w in d["wishes"]],
        "plans": [{"id": p["id"], "f": p["frequency"], "k": p["kind"], "zh": p["zh"], "en": p["en"], "b": p["basis"]} for p in d["plans"]],
        "evidence": [{"id": e["id"], "title": e["title"], "likes": e["likes"], "url": e["url"]} for e in d["evidence"]],
    }
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = open(HTML, encoding="utf-8").read()
    pattern = re.compile(r"(<!-- LIB-DATA-START -->\s*<script type=\"application/json\" id=\"libData\">)(.*?)(</script>\s*<!-- LIB-DATA-END -->)", re.S)
    if not pattern.search(html):
        raise SystemExit("index.html 缺少 LIB-DATA 标记")
    html = pattern.sub(lambda m: m.group(1) + blob + m.group(3), html, count=1)
    open(HTML, "w", encoding="utf-8").write(html)
    print("libData:", len(payload["wishes"]), "wishes,", len(payload["plans"]), "plans,", len(payload["evidence"]), "evidence")


if __name__ == "__main__":
    main()
