#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""由 docs/wish-library.json 生成两页固定画布 HTML（心愿库 / 计划库+依据）。
重新生成：python3 tools/make_wish_library_html.py
"""
import json, html, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, "docs/wish-library.json"), encoding="utf-8"))

ICON = "https://aka.doubaocdn.com/s/bXfmRbKhMO"
W = 900

CAT = {
    "material":    ("物质", "MATERIAL",      "让「想要」落到每天用的东西上"),
    "experience":  ("体验", "EXPERIENCE",    "允许自己只是在场，不必有产出"),
    "growth":      ("成长", "GROWTH",        "完成一件，胜过同时开始五件"),
    "relationship":("关系", "RELATIONSHIP",  "关心要具体到一件事、一个日期"),
    "selfcare":    ("自我关怀", "SELF-CARE", "先修睡眠，再谈状态"),
    "vision":      ("愿景", "VISION",        "用生活场景描述，而不是「变好」"),
    "once":        ("单次", "ONCE",          "有日子的事，做完就收"),
    "daily":       ("每日", "DAILY",         "最小的一步，一天一格"),
    "weekly":      ("每周", "WEEKLY",        "给节奏留一个固定位置"),
    "monthly":     ("每月", "MONTHLY",       "整块的注意力，按月回收"),
    "yearly":      ("每年", "YEARLY",        "只放一两件，才放得下"),
}
ORDER_WISH = ["material", "experience", "growth", "relationship", "selfcare", "vision"]
ORDER_PLAN = ["once", "daily", "weekly", "monthly", "yearly"]

CSS = """
*{box-sizing:border-box;}
html,body{margin:0;padding:0;}
body{background:#FFFBF8;color:#2A2433;font-family:"PingFang SC","Helvetica Neue",Arial,sans-serif;
 -webkit-font-smoothing:antialiased;}
[data-canvas-root]{background:#FFFBF8;position:relative;overflow:hidden;}
[data-canvas-root]::before{content:"";position:absolute;inset:0 0 auto 0;height:520px;
 background:
  radial-gradient(680px 320px at 88% -60px, rgba(255,128,171,.28), rgba(255,128,171,0) 70%),
  radial-gradient(520px 300px at 4% 40px, rgba(179,157,219,.28), rgba(179,157,219,0) 72%);
 pointer-events:none;}
.wrap{position:relative;padding:0 56px;}
.topbar{height:78px;display:flex;align-items:center;gap:12px;border-bottom:1px solid #F0E7F1;}
.mark{width:40px;height:40px;border-radius:12px;object-fit:cover;box-shadow:0 6px 16px rgba(179,157,219,.28);}
.brand{font-family:Georgia,"Songti SC",serif;font-size:16px;letter-spacing:.16em;color:#2A2433;}
.brand-sub{font-size:11px;letter-spacing:.14em;color:#9A90A6;text-transform:uppercase;margin-left:2px;}
.topbar .spacer{flex:1;}
.pill{font-size:10.5px;letter-spacing:.1em;color:#8C6F8F;border:1px solid #F0D9E6;background:#FFF6FA;
 border-radius:999px;padding:6px 12px;text-transform:uppercase;}
.hero{padding-top:34px;}
.kicker{font-size:10.5px;letter-spacing:.22em;color:#B08BC7;text-transform:uppercase;}
h1{font-family:"Songti SC","Source Han Serif CN",Georgia,serif;font-weight:600;font-size:42px;
 line-height:54px;margin:10px 0 0;letter-spacing:.01em;color:#241E2D;}
.lead{font-size:15px;line-height:26px;color:#6F6579;margin:12px 0 0;max-width:612px;}
.stats{display:flex;gap:0;margin-top:22px;}
.stat{padding-right:26px;margin-right:26px;border-right:1px solid #EFE4F0;}
.stat:last-child{border-right:0;margin-right:0;padding-right:0;}
.stat b{display:block;font-family:Georgia,serif;font-size:22px;line-height:26px;color:#2A2433;font-weight:600;}
.stat span{display:block;font-size:10.5px;letter-spacing:.08em;color:#9A90A6;margin-top:4px;}
.usage{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0 28px;margin-top:28px;padding-bottom:26px;}
.ucard{border-left:2px solid #FFB3CB;padding:2px 0 2px 14px;}
.un{font-family:Georgia,serif;font-size:11px;letter-spacing:.16em;color:#C79BD4;}
.ut{font-size:13.5px;line-height:21px;font-weight:600;margin:6px 0 0;}
.ud{font-size:11.5px;line-height:18px;color:#7C7188;margin:5px 0 0;}
.sect-head{display:flex;align-items:flex-end;justify-content:space-between;
 padding-bottom:10px;border-bottom:2px solid #2A2433;margin-top:12px;}
.sect-head h2{font-family:"Songti SC",Georgia,serif;font-size:24px;line-height:30px;margin:0;font-weight:600;}
.sect-head .en{font-size:10.5px;letter-spacing:.2em;color:#A296AC;margin-left:10px;text-transform:uppercase;}
.sect-head .count{font-size:11px;letter-spacing:.08em;color:#8C8197;}
.block{margin-top:30px;}
.bhead{height:62px;display:flex;align-items:center;gap:14px;}
.bnum{font-family:Georgia,serif;font-size:30px;line-height:1;color:#E3C9E8;width:44px;}
.bname{font-size:19px;line-height:24px;font-weight:600;}
.ben{font-size:10px;letter-spacing:.18em;color:#A296AC;text-transform:uppercase;margin-top:3px;}
.bdesc{font-size:11.5px;color:#7C7188;margin-left:14px;padding-left:14px;border-left:1px solid #EADFEE;}
.bhead .spacer{flex:1;}
.bcount{font-family:Georgia,serif;font-size:13px;color:#8C8197;}
ul.entries{margin:0;padding:0;list-style:none;}
.entry{display:grid;grid-template-columns:46px 1fr 236px;column-gap:18px;height:68px;
 padding:9px 0;border-top:1px solid #EFE7F2;align-items:start;}
.eid{font-family:"SF Mono",Menlo,monospace;font-size:10px;letter-spacing:.06em;color:#B08BC7;padding-top:4px;}
.zh{font-size:15.5px;line-height:22px;font-weight:500;margin:0;color:#241E2D;}
.en{font-family:Georgia,serif;font-style:italic;font-size:12.5px;line-height:17px;color:#7C7188;margin:1px 0 0;}
.kind{display:inline-block;font-size:9.5px;letter-spacing:.06em;color:#8C6F8F;border:1px solid #EEDCE7;
 background:#FFF8FA;border-radius:4px;padding:2px 6px;margin-right:7px;vertical-align:2px;}
.basis{font-size:11.5px;line-height:15.5px;color:#6F6579;margin:0;padding:2px 0 0 12px;border-left:1px solid #F6DCE9;}
.freq{display:grid;grid-template-columns:repeat(5,1fr);gap:0 1px;margin-top:22px;background:#EFE4F0;border:1px solid #EFE4F0;}
.fitem{background:#FFFDFB;padding:12px 14px;}
.fname{font-size:13px;font-weight:600;}
.fgloss{font-size:10.5px;line-height:16px;color:#7C7188;margin-top:4px;}
table.heat{width:100%;border-collapse:collapse;margin-top:4px;}
.heat th{font-size:10px;letter-spacing:.12em;color:#A296AC;font-weight:500;text-align:left;padding:9px 0;border-bottom:1px solid #EADFEE;text-transform:uppercase;}
.heat td{font-size:12.5px;padding:11px 0;border-bottom:1px solid #F1E9F3;color:#3A3242;vertical-align:top;}
.heat .aid{width:46px;font-family:"SF Mono",Menlo,monospace;font-size:10px;color:#B08BC7;}
.heat .atitle{width:auto;padding-right:18px;line-height:18px;}
.heat .auth{width:112px;color:#7C7188;font-size:11.5px;}
.heat .alk{width:64px;text-align:right;font-family:Georgia,serif;color:#B08BC7;}
.heat .alink{width:26px;text-align:right;}
.heat a{color:#B06A8E;text-decoration:none;font-size:13px;}
.note{font-size:11px;line-height:18px;color:#8C8197;margin-top:14px;}
.tips{margin-top:8px;}
.tip{display:grid;grid-template-columns:40px 1fr;column-gap:14px;padding:10px 0;border-top:1px solid #F1E9F3;}
.tipn{font-family:Georgia,serif;font-size:12px;color:#C79BD4;letter-spacing:.08em;}
.tipt{font-size:13px;line-height:20px;color:#3A3242;}
.footer{margin-top:34px;padding:18px 0 22px;border-top:1px solid #EFE4F0;display:flex;justify-content:space-between;
 font-size:10.5px;letter-spacing:.06em;color:#A296AC;}
"""


def esc(s):
    return html.escape(s, quote=True)


def entry_rows(items, show_kind):
    out = []
    for it in items:
        kind = f'<span class="kind">{esc(it["kind"])}</span>' if show_kind else ""
        out.append(
            f'<li class="entry"><span class="eid">{esc(it["id"])}</span>'
            f'<div class="ecopy"><p class="zh">{kind}{esc(it["zh"])}</p>'
            f'<p class="en">{esc(it["en"])}</p></div>'
            f'<p class="basis">{esc(it["basis"])}</p></li>'
        )
    return "\n".join(out)


def block(idx, key, items, show_kind):
    zh, en, desc = CAT[key]
    return (
        f'<section class="block" id="{key}">'
        f'<div class="bhead"><div class="bnum">{idx:02d}</div>'
        f'<div><div class="bname">{zh}</div><div class="ben">{en}</div></div>'
        f'<div class="bdesc">{desc}</div><div class="spacer"></div>'
        f'<div class="bcount">{len(items)} 条</div></div>'
        f'<ul class="entries">{entry_rows(items, show_kind)}</ul></section>'
    )


def topbar(right_text):
    return (
        f'<header class="topbar"><img class="mark" src="{ICON}" alt="DearMe">'
        f'<div><div class="brand">LOBUS</div><div class="brand-sub">DearMe · iOS</div></div>'
        f'<div class="spacer"></div><div class="pill">{right_text}</div></header>'
    )


def page1(height):
    wishes = DATA["wishes"]
    grouped = {k: [w for w in wishes if w["type"] == k] for k in ORDER_WISH}
    blocks = "".join(block(i + 1, k, grouped[k], False) for i, k in enumerate(ORDER_WISH))
    body = f"""
<div class="wrap">
{topbar('Copy Library · v1.0')}
<section class="hero">
  <div class="kicker">Wish &amp; Plan · Copy Library</div>
  <h1>心愿与计划文案库</h1>
  <p class="lead">60 条心愿，六类各 10 条；中英对照，每条带一句「为什么这句能立住」。素材来自小红书公开搜索页，只做主题归纳，不复述原帖。</p>
  <div class="stats">
    <div class="stat"><b>60</b><span>心愿文案</span></div>
    <div class="stat"><b>6</b><span>心愿类型</span></div>
    <div class="stat"><b>22</b><span>热度依据</span></div>
    <div class="stat"><b>2026.11.20</b><span>检索日期</span></div>
  </div>
</section>
<section class="usage">
  <div class="ucard"><div class="un">01</div><p class="ut">只当种子，不当任务。</p>
    <p class="ud">用户点开后才填金额与时间，不要把它做成一份必须完成的清单。</p></div>
  <div class="ucard"><div class="un">02</div><p class="ut">不承诺结果。</p>
    <p class="ud">写的是「这件事值得」，不是「你一定能做到」。做到与放下都算走完一段。</p></div>
  <div class="ucard"><div class="un">03</div><p class="ut">不要一次全放。</p>
    <p class="ud">官网每类 2&nbsp;条、App 空态 5&nbsp;条，按时间轮换，其余收进「换一批」。</p></div>
</section>
<section>
  <div class="sect-head"><div><h2>心愿库</h2><span class="en">Wish Library</span></div>
    <div class="count">六类 · 60 条 · 中英对照</div></div>
  {blocks}
</section>
<footer class="footer"><div>DearMe · lobus ｜ 心愿与计划文案库 v1.0</div><div>第二页：计划库与热度依据</div></footer>
</div>"""
    return shell("心愿与计划文案库 · DearMe", height, body)


def page2(height):
    plans = DATA["plans"]
    grouped = {k: [p for p in plans if p["frequency"] == k] for k in ORDER_PLAN}
    blocks = "".join(block(i + 1, k, grouped[k], True) for i, k in enumerate(ORDER_PLAN))
    freq = "".join(
        f'<div class="fitem"><div class="fname">{CAT[k][0]}</div><div class="fgloss">{CAT[k][2]}</div></div>'
        for k in ORDER_PLAN
    )
    heat_rows = "".join(
        f'<tr><td class="aid">{esc(e["id"])}</td><td class="atitle">{esc(e["title"])}</td>'
        f'<td class="auth">{esc(e["author"])}</td><td class="alk">{esc(e["likes"])}</td>'
        f'<td class="alink"><a href="{esc(e["url"])}" target="_blank" rel="noopener">↗</a></td></tr>'
        for e in DATA["evidence"]
    )
    tips = [
        ("01", "官网功能页：每类取 2 条做「可以这样许愿」示例带，配图标，不做成按钮。"),
        ("02", "App 心愿空态：六类各 1 条轮换，点选后进入表单并预填标题，用户仍可改。"),
        ("03", "App 计划空态：按「今天想动一下 / 这周想稳一点 / 这个月想做成一件」给 3 条。"),
        ("04", "分享图标题：取愿景组与每年组文案做纪念页标题备选。"),
    ]
    tip_rows = "".join(f'<div class="tip"><div class="tipn">{n}</div><div class="tipt">{t}</div></div>' for n, t in tips)
    body = f"""
<div class="wrap">
{topbar('Plan Library · v1.0')}
<section class="hero">
  <div class="kicker">Plan Library &amp; Evidence</div>
  <h1>计划库与热度依据</h1>
  <p class="lead">40 条计划，五档频次各 8 条，覆盖习惯、任务、项目、清单、陪伴。频次不是要求，是节奏；跳过不进分母，中断不显示零。</p>
  <div class="stats">
    <div class="stat"><b>40</b><span>计划文案</span></div>
    <div class="stat"><b>5</b><span>频次档位</span></div>
    <div class="stat"><b>5</b><span>计划类型</span></div>
    <div class="stat"><b>22</b><span>可点开的依据</span></div>
  </div>
</section>
<div class="freq">{freq}</div>
<section>
  <div class="sect-head" style="margin-top:32px"><div><h2>计划库</h2><span class="en">Plan Library</span></div>
    <div class="count">五档 · 40 条 · 中英对照</div></div>
  {blocks}
</section>
<section style="margin-top:40px">
  <div class="sect-head"><div><h2>热度依据</h2><span class="en">Evidence</span></div>
    <div class="count">22 条 · 搜索页可见点赞量级</div></div>
  <table class="heat"><thead><tr><th>ID</th><th>笔记标题</th><th>作者</th><th style="text-align:right">量级</th><th></th></tr></thead>
  <tbody>{heat_rows}</tbody></table>
  <p class="note">口径：量级只看搜索页展示的点赞数，收藏数平台不公开、未估算；显示「赞」的笔记不进本表。卡片抓取出现过标题与直链错位，本表只保留标题与卡片文本逐字一致的记录。</p>
</section>
<section style="margin-top:34px">
  <div class="sect-head"><div><h2>落位建议</h2><span class="en">Where to use</span></div>
    <div class="count">官网 + App + 分享图</div></div>
  <div class="tips">{tip_rows}</div>
</section>
<footer class="footer"><div>DearMe · lobus ｜ 计划库与热度依据 v1.0</div><div>第一页：心愿库 60 条</div></footer>
</div>"""
    return shell("计划库与热度依据 · DearMe", height, body)


def shell(title, height, body):
    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-canvas-width="{W}" data-canvas-height="{height}" style="width:{W}px;height:{height}px;">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body style="width:{W}px;height:{height}px;">
<main data-canvas-root id="canvas-root" style="width:{W}px;height:{height}px;">
{body}
</main>
</body>
</html>
"""


H1 = 78 + 34 + 18 + 54 + 12 + 26 + 22 + 26 + 22 + 26 + 28 + 100 + 28 + 40 + 6 * (62 + 10 * 68 + 30) - 30 + 34 + 22 + 96
H2 = 78 + 34 + 18 + 54 + 12 + 26 + 22 + 26 + 22 + 26 + 22 + 96 + 32 + 40 + 5 * (62 + 8 * 68 + 30) - 30 + 40 + 40 + 22 * 46 + 40 + 30 + 4 * 60 + 34 + 22 + 96

# 上面是估算式；实际用显式常量保证可复现
H1 = 5254
H2 = 5132

if __name__ == "__main__":
    p1 = os.path.join(ROOT, "docs", "wish-library-01-wishes.html")
    p2 = os.path.join(ROOT, "docs", "wish-library-02-plans.html")
    open(p1, "w", encoding="utf-8").write(page1(H1))
    open(p2, "w", encoding="utf-8").write(page2(H2))
    print(p1, p2)
