#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DearMe 官网文案表工具（零依赖，Python 3 标准库）。

    python3 tools/copy.py extract    # 从 index.html 抽文案 → copy/copy.json，并补 data-key
    python3 tools/copy.py verify     # 校验 html 与 copy.json 是否一致（CI 用）
    python3 tools/copy.py report     # 生成 docs/copy-review.html（中英对照 + 搜索 + 版本记录）
    python3 tools/copy.py apply      # 把 copy.json 写回 index.html（属性 + 正文）
    python3 tools/copy.py apply --from ~/Downloads/copy.json   # 先导入再写回
    python3 tools/copy.py diff "改了什么"   # 与上次快照比对，写版本记录，并刷新 report
    python3 tools/copy.py all "改了什么"    # extract → diff → report 一条龙

文案只存在于 index.html 的 data-zh / data-en 属性里，copy.json 是由它导出的镜像，
所以 html 永远是唯一的数据源，json 用来汇总、比对、留痕。
"""

import datetime
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")
DIR = os.path.join(ROOT, "copy")
COPY = os.path.join(DIR, "copy.json")
SNAP = os.path.join(DIR, "snapshots", "latest.json")
HIST = os.path.join(DIR, "history.json")
DOCS = os.path.join(ROOT, "docs")
REPORT = os.path.join(DOCS, "copy-review.html")
CHANGELOG = os.path.join(DOCS, "copy-changelog.md")

# 属性值里的引号一律是 &quot;，所以 `>` / `"` 都不会截断标签匹配
TAG_RE = re.compile(r'<(/)?([A-Za-z][\w:-]*)((?:[^>"\']|"[^"]*"|\'[^\']*\')*)>')
ZH_RE = re.compile(r'\bdata-zh="([^"]*)"')
EN_RE = re.compile(r'\bdata-en="([^"]*)"')
KEY_RE = re.compile(r'\bdata-key="([^"]*)"')
HTML_RE = re.compile(r'\bdata-html="([^"]*)"')
CLASS_RE = re.compile(r'\bclass="([^"]*)"')
ID_RE = re.compile(r'\bid="([^"]*)"')
PROTECT_RE = re.compile(r'<(script|style)\b[^>]*>.*?</\1>', re.S)

VIEW_IDS = {"view-home": "home", "view-features": "features", "view-story": "story"}

# class 关键字 → 区块名（None 表示按出现顺序编号）
BLOCK_CLASSES = {
    "page-hero": "hero",
    "hero": "hero",
    "quote": "quote",
    "feat": "feat",
    "blk": "blk",
    "story-hero": "intro",
    "cta-band": "cta",
}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}


def read_html():
    with open(HTML, encoding="utf-8") as f:
        return f.read()


def write_html(text):
    with open(HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")


def git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return ""


# ---------------------------------------------------------------- 解析 html

def scan(html):
    """返回条目列表；每条含 key（没有 data-key 时为推导 key）、zh、en、block、标签位置。"""
    protected = [(m.start(), m.end()) for m in PROTECT_RE.finditer(html)]
    entries = []
    stack = []              # [{tag, prev_label}]，出栈时恢复上一层的区块标签
    view = "site"
    label = None
    block_seq = {}          # (view, base) -> 递增序号
    ordinals = {}           # (prefix, block) -> 已用序号

    for m in TAG_RE.finditer(html):
        if any(s <= m.start() < e for s, e in protected):
            continue
        tag = m.group(2).lower()
        attrs = m.group(3)

        if m.group(1):
            while stack:
                top = stack.pop()
                label = top["prev_label"]
                if top["entry"]:
                    inner = html[top["open_end"]:m.start()]
                    top["entry"]["content"] = (top["open_end"], m.start())
                    top["entry"]["nested"] = "<" in inner
                if top["tag"] == tag:
                    break
            continue

        prev_label = label

        for i in ID_RE.findall(attrs):
            if i in VIEW_IDS:
                view = VIEW_IDS[i]

        if tag == "header":
            label = ("site", "nav")
        elif "modal" in " ".join(CLASS_RE.findall(attrs)).split():
            label = ("site", "modal")
        elif tag == "footer":
            label = ("site", "footer")
        for c in " ".join(CLASS_RE.findall(attrs)).split():
            if c in VIEW_IDS:
                view = VIEW_IDS[c]
            base = BLOCK_CLASSES.get(c)
            if base:
                k2 = (view, base)
                block_seq[k2] = block_seq.get(k2, 0) + 1
                block = "hero" if base == "hero" else f"{base}{block_seq[k2]}"
                label = (view, block)

        zh = ZH_RE.search(attrs)
        if zh:
            key_attr = KEY_RE.search(attrs)
            if key_attr:
                key = key_attr.group(1)
            else:
                pref, blk = label or (view, "misc")
                n = ordinals.get((pref, blk), 0) + 1
                ordinals[(pref, blk)] = n
                key = f"{pref}.{blk}.{n:02d}"
            en = EN_RE.search(attrs)
            entries.append({
                "key": key,
                "zh": zh.group(1),
                "en": en.group(1) if en else "",
                "html": bool(HTML_RE.search(attrs)),
                "block": f"{label[0]}.{label[1]}" if label else view,
                "span": (m.start(), m.end()),
                "tag": tag,
                "has_key": bool(key_attr),
            })

        if tag not in VOID:
            stack.append({"tag": tag, "prev_label": prev_label, "open_end": m.end(),
                          "entry": (entries[-1] if zh else None)})
            if attrs.rstrip().endswith("/"):
                stack.pop()
                label = prev_label
    return entries


def assign_keys(html):
    """给还没有 data-key 的标签补上 key，返回 (新html, entries)。"""
    entries = scan(html)
    out, last = [], 0
    added = 0
    for e in entries:
        if e["has_key"]:
            continue
        s, t = e["span"]
        name_len = len(e["tag"])
        start = s + 1 + name_len  # `<tag` 之后
        out.append(html[last:start])
        out.append(' data-key="%s"' % e["key"])
        last = start
        added += 1
    out.append(html[last:])
    return "".join(out), added


# ---------------------------------------------------------------- 命令

def cmd_extract():
    html = read_html()
    html, added = assign_keys(html)
    if added:
        write_html(html)
    entries = scan(html)
    strings = {}
    for e in entries:
        strings[e["key"]] = {
            "zh": e["zh"],
            "en": e["en"],
            "block": e["block"],
            "html": e["html"],
        }
    dump_json(COPY, {"version": 1, "strings": strings})
    print(f"extract: {len(strings)} 条文案，补 data-key {added} 个 → copy/copy.json")
    return strings


def cmd_apply(front=""):
    """把 copy/copy.json 写回 index.html（属性 + 正文）。--from 可先导入外部 json。"""
    if front:
        src = os.path.expanduser(front)
        if not os.path.exists(src):
            print(f"apply: 找不到 {src}")
            return 1
        data = load_json(src, None)
        if not isinstance(data, dict) or "strings" not in data:
            print("apply: 不是 copy.json 格式")
            return 1
        dump_json(COPY, data)
        print(f"apply: 导入 {os.path.basename(src)} → copy/copy.json")

    strings = load_json(COPY, {"strings": {}})["strings"]
    html = read_html()
    entries = scan(html)
    edits, nested = [], []
    for e in entries:
        ref = strings.get(e["key"])
        if not ref:
            continue
        s, t = e["span"]
        mz, me = ZH_RE.search(html, s, t), EN_RE.search(html, s, t)
        if mz and mz.group(1) != ref["zh"]:
            edits.append((mz.start(1), mz.end(1), ref["zh"]))
        if me and me.group(1) != ref["en"]:
            edits.append((me.start(1), me.end(1), ref["en"]))
        if e.get("nested"):
            nested.append(e["key"])
        elif "content" in e and html[e["content"][0]:e["content"][1]] != ref["zh"]:
            edits.append((e["content"][0], e["content"][1], ref["zh"]))

    for start, end, text in sorted(edits, reverse=True):
        html = html[:start] + text + html[end:]
    changed = len(edits)
    if changed:
        write_html(html)
        print(f"apply: 写回 {changed} 处")
    else:
        print("apply: 页面与文案表已一致，无需写回")
    if nested:
        print(f"apply: {len(nested)} 条含内嵌标签，只更新属性不动正文：{', '.join(nested)}")
    return cmd_verify()


def cmd_verify():
    html = read_html()
    entries = scan(html)
    strings = load_json(COPY, {"strings": {}})["strings"]
    errs = []
    missing_key = [e for e in entries if not e["has_key"]]
    for e in missing_key:
        errs.append(f"缺少 data-key：{e['zh'][:24]}")
    for e in entries:
        if not e["has_key"]:
            continue
        ref = strings.get(e["key"])
        if not ref:
            errs.append(f"copy.json 缺 key：{e['key']}")
            continue
        if ref["zh"] != e["zh"]:
            errs.append(f"中文不一致：{e['key']}")
        if ref["en"] != e["en"]:
            errs.append(f"英文不一致：{e['key']}")
    html_keys = {e["key"] for e in entries}
    for k in strings:
        if k not in html_keys:
            errs.append(f"copy.json 里有、页面里没有：{k}")
    dup = len(entries) - len(html_keys)
    if dup:
        errs.append(f"data-key 重复 {dup} 个")
    if errs:
        print(f"verify: {len(errs)} 个问题")
        for e in errs[:40]:
            print("  -", e)
        return 1
    print(f"verify: ok，{len(strings)} 条文案与页面一致")
    return 0


def diff_payload(old, new):
    changes = []
    for k, v in new.items():
        if k not in old:
            changes.append({"key": k, "type": "added", "after": v})
        elif old[k]["zh"] != v["zh"] or old[k]["en"] != v["en"]:
            changes.append({"key": k, "type": "changed", "before": old[k], "after": v})
    for k, v in old.items():
        if k not in new:
            changes.append({"key": k, "type": "removed", "before": v})
    return changes


def cmd_diff(message):
    strings = load_json(COPY, {"strings": {}})["strings"]
    if not strings:
        print("copy.json 为空，先跑 extract")
        return 1
    old = load_json(SNAP, {"strings": {}})["strings"]
    changes = diff_payload(old, strings)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    history = load_json(HIST, [])
    history.append({
        "date": now,
        "commit": git_commit(),
        "message": message or ("初版" if not old else "更新文案"),
        "counts": {
            "added": sum(1 for c in changes if c["type"] == "added"),
            "changed": sum(1 for c in changes if c["type"] == "changed"),
            "removed": sum(1 for c in changes if c["type"] == "removed"),
        },
        "changes": changes,
    })
    dump_json(HIST, history)
    dump_json(SNAP, {"version": 1, "strings": strings})
    write_markdown(history)
    write_report(strings, history)
    print(f"diff: 新增 {history[-1]['counts']['added']} / 修改 {history[-1]['counts']['changed']} / 删除 {history[-1]['counts']['removed']}")
    return 0


def cmd_report():
    strings = load_json(COPY, {"strings": {}})["strings"]
    history = load_json(HIST, [])
    write_report(strings, history)
    print(f"report: → {os.path.relpath(REPORT, ROOT)}")
    return 0


# ---------------------------------------------------------------- 输出

def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def write_markdown(history):
    lines = ["# 文案版本记录", "", "由 `python3 tools/copy.py diff` 自动生成，请勿手改。", ""]
    for h in reversed(history):
        c = h["counts"]
        lines.append(f"## {h['date']} · {h['message']}")
        meta = f"`{h['commit']}`" if h.get("commit") else "未提交"
        lines.append("")
        lines.append(f"{meta} · 新增 {c['added']} / 修改 {c['changed']} / 删除 {c['removed']}")
        lines.append("")
        if not h["changes"]:
            lines.append("无变化。")
            lines.append("")
            continue
        for ch in h["changes"]:
            k = ch["key"]
            if ch["type"] == "added":
                lines.append(f"- **新增** `{k}`：{ch['after']['zh']}")
            elif ch["type"] == "removed":
                lines.append(f"- **删除** `{k}`：{ch['before']['zh']}")
            else:
                lines.append(f"- **修改** `{k}`")
                if ch["before"]["zh"] != ch["after"]["zh"]:
                    lines.append(f"  - 中：{ch['before']['zh']} → {ch['after']['zh']}")
                if ch["before"]["en"] != ch["after"]["en"]:
                    lines.append(f"  - 英：{ch['before']['en']} → {ch['after']['en']}")
        lines.append("")
    os.makedirs(DOCS, exist_ok=True)
    with open(CHANGELOG, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


def write_report(strings, history):
    groups = {}
    for k, v in strings.items():
        groups.setdefault(v["block"], []).append((k, v))

    def block_order(b):
        view_rank = {"home": 0, "features": 1, "story": 2, "site": 3}
        return (view_rank.get(b.split(".")[0], 9), b)

    zh_chars = sum(len(re.sub(r"<[^>]+>", "", v["zh"])) for v in strings.values())
    en_words = sum(len(v["en"].split()) for v in strings.values())
    untranslated = sum(1 for v in strings.values() if not v["en"].strip())

    rows = []
    for b in groups:  # 保持文档顺序
        items = groups[b]
        rows.append(f'<h2 data-block="{esc(b)}">{esc(b)} <small>{len(items)} 条</small></h2>')
        rows.append('<table><thead><tr><th class="k">key</th><th>中文</th><th>English</th></tr></thead><tbody>')
        for k, v in items:
            lock = ' class="zh locked"' if v.get("html") else ' class="zh"'
            lock_en = ' class="en locked"' if v.get("html") else ' class="en"'
            tip = ' title="这条含 HTML 标签，请在 index.html 里改"' if v.get("html") else ""
            rows.append(
                '<tr><td class="k">%s</td>'
                '<td%s data-k="%s" data-f="zh" contenteditable="true"%s>%s</td>'
                '<td%s data-k="%s" data-f="en" contenteditable="true"%s>%s</td></tr>'
                % (esc(k), lock, esc(k), tip, esc(v["zh"]),
                   lock_en, esc(k), tip, esc(v["en"]) or '<span class="miss">（缺）</span>')
            )
        rows.append("</tbody></table>")

    hist_rows = []
    for h in reversed(history):
        c = h["counts"]
        head = f'<div class="hentry"><b>{esc(h["date"])}</b> <span class="msg">{esc(h["message"])}</span>'
        head += f'<span class="tag">+{c["added"]} ~{c["changed"]} -{c["removed"]}</span>'
        if h.get("commit"):
            head += f'<span class="sha">{esc(h["commit"])}</span>'
        head += "</div>"
        hist_rows.append(head)
        if h["changes"]:
            hist_rows.append(f'<details><summary>{len(h["changes"])} 处改动</summary><ul class="hc">')
            for ch in h["changes"]:
                if ch["type"] == "added":
                    hist_rows.append(f'<li><i class="a">新增</i> <code>{esc(ch["key"])}</code> {esc(ch["after"]["zh"])}</li>')
                elif ch["type"] == "removed":
                    hist_rows.append(f'<li><i class="r">删除</i> <code>{esc(ch["key"])}</code> {esc(ch["before"]["zh"])}</li>')
                else:
                    zh = ch["before"]["zh"]
                    if zh != ch["after"]["zh"]:
                        hist_rows.append(f'<li><i class="c">改中</i> <code>{esc(ch["key"])}</code> {esc(zh)} → {esc(ch["after"]["zh"])}</li>')
                    if ch["before"]["en"] != ch["after"]["en"]:
                        hist_rows.append(f'<li><i class="c">改英</i> <code>{esc(ch["key"])}</code> {esc(ch["before"]["en"])} → {esc(ch["after"]["en"])}</li>')
            hist_rows.append("</ul></details>")

    # 同一句中文出现在多个 key 上：双语站最容易漏改其中一处
    by_zh = {}
    for k, v in strings.items():
        by_zh.setdefault(v["zh"], []).append(k)
    dups = [(zh, ks) for zh, ks in by_zh.items() if len(ks) > 1]
    dup_html = ""
    if dups:
        dup_items = "".join(
            f'<li><code>{esc(zh[:40])}</code> <span class="reuse">{len(ks)} 处 · {", ".join(esc(k) for k in ks)}</span></li>'
            for zh, ks in dups[:30]
        )
        dup_html = (
            f'<h2 id="dups">重复文案 <small>{len(dups)} 组</small></h2>'
            f'<div class="hist"><ul class="hc">{dup_items}</ul></div>'
        )

    tpl = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DearMe 文案表</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#FFFBF7;color:#2C2436;font:14px/1.6 -apple-system,"PingFang SC","Noto Sans SC",sans-serif}
header{position:sticky;top:0;z-index:5;background:rgba(255,251,247,.96);border-bottom:1px solid #EFE4F0;padding:18px 28px}
h1{margin:0 0 6px;font-size:20px}
h1 small{font-weight:400;color:#8A8095;font-size:12px;margin-left:8px}
.stats{color:#6E6477;font-size:12px}
.wrap{max-width:1180px;margin:0 auto;padding:20px 28px 80px}
#q{width:100%;padding:10px 14px;margin:14px 0 0;border:1px solid #E8DEEF;border-radius:10px;font:inherit;background:#fff}
h2{margin:34px 0 10px;font-size:14px;letter-spacing:.12em;text-transform:uppercase;color:#B39DDB}
h2 small{color:#A79DB2;letter-spacing:0;text-transform:none;font-weight:400;margin-left:6px}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #F0E7F2;border-radius:12px;overflow:hidden}
th,td{padding:9px 14px;text-align:left;vertical-align:top;border-bottom:1px solid #F5EFF7}
th{background:#FBF6FC;font-weight:600;font-size:12px;color:#8A8095}
td.k{width:170px;font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#8A8095;white-space:nowrap}
td.zh{width:47%}
td.en{color:#5E5568}
tr:last-child td{border-bottom:0}
.miss{color:#D9536F}
.hist{background:#fff;border:1px solid #F0E7F2;border-radius:12px;padding:6px 18px}
.hentry{padding:10px 0;border-bottom:1px dashed #F2E9F4;display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}
.hentry:last-child{border-bottom:0}
.msg{color:#4A4154}
.tag{font-size:11px;color:#fff;background:#C9B6E6;border-radius:6px;padding:1px 6px}
.sha{font-family:ui-monospace,Menlo,monospace;font-size:11px;color:#A79DB2}
.hc{margin:0 0 10px 6px;padding-left:18px;color:#5E5568;font-size:13px}
.hc li{margin:2px 0}
.hc i{font-style:normal;font-size:11px;border-radius:4px;padding:0 4px;margin-right:4px}
.hc i.a{background:#DFF3E6;color:#25764A}
.hc i.c{background:#FDF0D6;color:#8A5A00}
.hc i.r{background:#FBE0E5;color:#A2243C}
code{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#8A8095}
.hc li .reuse{color:#A79DB2;font-size:11px;margin-left:6px}
.toc{display:flex;gap:16px;margin:16px 0 4px;font-size:12px}
.toc a{color:#8A7FB0;text-decoration:none;border-bottom:1px solid #E7DDF4;padding-bottom:1px}
h2{scroll-margin-top:110px}
details{margin:0 0 12px 8px}
summary{cursor:pointer;font-size:12px;color:#8A7FB0}
details[open] summary{margin-bottom:6px}
.bar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:14px 0 0}
button{font:inherit;font-size:12px;padding:7px 14px;border:1px solid #E4D8F2;background:#fff;color:#6E5F8C;border-radius:9px;cursor:pointer}
button:hover{background:#FBF6FF}
button.primary{background:#F7C6DE;border-color:#F7C6DE;color:#6B3550}
#stat{font-size:12px;color:#8A8095}
.how{font-size:11.5px;color:#A79DB2;font-family:ui-monospace,Menlo,monospace}
td[contenteditable="true"]{cursor:text}
td[contenteditable="true"]:focus{outline:2px solid #F3B6D2;outline-offset:-2px;background:#FFFDF9}
td.edited{background:#FFF6E4}
td.locked{color:#9C93A8;cursor:not-allowed}
body.zh-only td.en{opacity:.35}
</style></head><body>
<header>
  <h1>DearMe 文案表 <small>数据源 index.html · 共 __TOTAL__ 条</small></h1>
  <div class="stats">中文 __ZHCH__ 字 · 英文 __ENW__ 词 · 缺英文 __MISS__ 条</div>
  <input id="q" placeholder="搜索 key / 中文 / 英文…">
</header>
<div class="wrap">
  <div class="toc"><a href="#copy">文案表</a><a href="#dups">重复文案</a><a href="#history">版本记录</a></div>
  <div class="bar">
    <button class="primary" id="exp">导出 copy.json</button>
    <button id="reset">重置修改</button>
    <span id="stat">未修改</span>
    <span class="how">导出后：python3 tools/copy.py apply --from ~/Downloads/copy.json</span>
  </div>
  <div id="copy"></div>
  __ROWS__
  __DUPS__
  <h2 id="history">版本记录 <small>__HCOUNT__ 次改动</small></h2>
  <div class="hist">__HIST__</div>
</div>
<script id="copy-data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('copy-data').textContent);
const orig = {};
Object.entries(DATA.strings).forEach(([k, v]) => { orig[k] = { zh: v.zh, en: v.en }; });
const stat = document.getElementById('stat');
const dirty = new Set();
const cells = [...document.querySelectorAll('td[data-k]')];
const syncStat = () => { stat.textContent = dirty.size ? '已修改 ' + dirty.size + ' 条 · 未导出' : '未修改'; };

cells.forEach(td => {
  if (td.classList.contains('locked')) { td.setAttribute('contenteditable', 'false'); return; }
  td.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); td.blur(); } });
  td.addEventListener('paste', e => {
    e.preventDefault();
    const t = (e.clipboardData || window.clipboardData).getData('text');
    document.execCommand('insertText', false, t.split(String.fromCharCode(10)).join(' ').split(String.fromCharCode(13)).join(' '));
  });
  td.addEventListener('input', () => {
    const k = td.dataset.k, f = td.dataset.f;
    if (td.textContent !== orig[k][f]) { dirty.add(k); td.classList.add('edited'); }
    else {
      td.classList.remove('edited');
      if (!cells.some(x => x.dataset.k === k && x.classList.contains('edited'))) dirty.delete(k);
    }
    syncStat();
  });
});

const escHtml = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

document.getElementById('exp').addEventListener('click', () => {
  const out = JSON.parse(JSON.stringify(DATA));
  cells.filter(td => !td.classList.contains('locked')).forEach(td => {
    const k = td.dataset.k, f = td.dataset.f, raw = td.textContent;
    if (raw !== orig[k][f]) out.strings[k][f] = escHtml(raw);
  });
  const blob = new Blob([JSON.stringify(out, null, 2) + String.fromCharCode(10)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'copy.json';
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  stat.textContent = dirty.size ? '已导出（' + dirty.size + ' 条改动）' : '已导出（无改动）';
});
document.getElementById('reset').addEventListener('click', () => location.reload());

const q = document.getElementById('q');
q.addEventListener('input', () => {
  const v = q.value.trim().toLowerCase();
  document.querySelectorAll('tbody tr').forEach(tr => {
    tr.style.display = v && !tr.textContent.toLowerCase().includes(v) ? 'none' : '';
  });
  document.querySelectorAll('h2[data-block]').forEach(h => {
    const t = h.nextElementSibling;
    if (!t) return;
    const any = [...t.querySelectorAll('tbody tr')].some(r => r.style.display !== 'none');
    h.style.display = any || !v ? '' : 'none';
    t.style.display = any || !v ? '' : 'none';
  });
});
</script>
</body></html>"""

    tpl = (tpl.replace("__TOTAL__", str(len(strings)))
              .replace("__ZHCH__", str(zh_chars))
              .replace("__ENW__", str(en_words))
              .replace("__MISS__", str(untranslated))
              .replace("__HCOUNT__", str(len(history)))
              .replace("__HIST__", "".join(hist_rows) or "<p>还没有记录。</p>")
              .replace("__DUPS__", dup_html)
              .replace("__DATA__", json.dumps({"version": 1, "strings": strings}, ensure_ascii=False))
              .replace("__ROWS__", "".join(rows)))
    os.makedirs(DOCS, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write(tpl)


# ---------------------------------------------------------------- 入口

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    cmd = sys.argv[1]
    msg = sys.argv[2] if len(sys.argv) > 2 else ""
    if cmd == "extract":
        cmd_extract()
        return 0
    if cmd == "verify":
        return cmd_verify()
    if cmd == "apply":
        rest = sys.argv[2:]
        front = rest[rest.index("--from") + 1] if "--from" in rest and rest.index("--from") + 1 < len(rest) else ""
        return cmd_apply(front)
    if cmd == "diff":
        return cmd_diff(msg)
    if cmd == "report":
        return cmd_report()
    if cmd == "all":
        cmd_extract()
        cmd_diff(msg)
        return cmd_verify()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
