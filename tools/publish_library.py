#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 docs/wish-library.json 发布成对外只读接口 library/v1.json。

- 只输出 App 需要的字段，且**只出心愿**（计划留到 v1.1）
- 每条带上 App 六类 `appType`（tangible / experience / skill / health / finance / event），
  App 端不再自己猜类型
- 生成后由 deploy.yml 一起发布到 GitHub Pages

    python3 tools/publish_library.py
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "wish-library.json")
OUT_DIR = os.path.join(ROOT, "library")
OUT = os.path.join(OUT_DIR, "v1.json")

# 网站六类 → App 六类（GoodsCategory）
TYPE_MAP = {
    "material": "tangible",
    "experience": "experience",
    "growth": "skill",
    "relationship": "event",
    "selfcare": "health",
    "vision": "tangible",
}

# 逐条人工指定：笼统映射会偏，尤其「钱」「学做菜」「戒习惯」这类
ITEM_APP_TYPE = {
    "W-V01": "skill",       # 做一件属于自己的作品
    "W-V02": "finance",     # 副业养活自己
    "W-V03": "experience",  # 搬到有阳台的城市
    "W-V04": "experience",  # 换一种活法
    "W-V05": "tangible",    # 自己的工作室
    "W-V06": "health",      # 跑完十公里
    "W-V07": "event",       # 互相托底的朋友
    "W-V08": "event",       # 让爸妈骄傲的事
    "W-V09": "finance",     # 不再为钱做不想做的事
    "W-V10": "skill",       # 留下一本记录
    # 物质里其实是「攒一笔钱」的
    "W-M01": "finance",     # 存下第一笔一万元
    "W-M09": "finance",     # 存够一台咖啡机的钱
    # 体验里其实是「学一门本事」的
    "W-E07": "skill",       # 学做一道能端上桌的菜
    # 成长里其实偏「照顾自己 / 一件要办成的事」
    "W-G09": "health",      # 戒掉一个偷走时间的习惯
    "W-G10": "event",       # 在别人面前讲一次
    # 关系里其实是一次身体照顾
    "W-R02": "health",      # 带妈妈去做一次体检
    # 自我关怀里其实是「买一件东西」
    "W-S08": "tangible",    # 给自己买一束花
}


def app_type(item):
    if item["id"] in ITEM_APP_TYPE:
        return ITEM_APP_TYPE[item["id"]]
    return TYPE_MAP[item["type"]]


def main():
    d = json.load(open(SRC, encoding="utf-8"))
    items = [
        {
            "id": w["id"],
            "category": w["type"],
            "appType": app_type(w),
            "zh": w["zh"],
            "en": w["en"],
        }
        for w in d["wishes"]
    ]
    payload = {
        "schema": 1,
        "version": "1.0.0",
        "updated": d.get("generated", ""),
        "source": "https://riverdriven.github.io/DearMe/#/library",
        "license": "文案由 DearMe / lobus 改写整理，供 DearMe App 内展示使用。",
        "counts": {"wishes": len(items), "plans": 0},
        "items": items,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.write("\n")
    dist = {}
    for it in items:
        dist[it["appType"]] = dist.get(it["appType"], 0) + 1
    print("published", len(items), "wishes →", OUT)
    print("appType 分布:", dist)


if __name__ == "__main__":
    main()
