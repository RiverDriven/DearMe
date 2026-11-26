#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 docs/wish-library.json 发布成对外只读接口 library/v1.json。

- 输出 App 需要的字段：心愿 v1.0 + 计划 v1.1（2026-11-26 计划板块开工）
- 每条带上 App 六类 `appType`（tangible / experience / skill / health / finance / event），
  App 端不再自己猜类型
- 生成后由 deploy.yml 一起发布到 GitHub Pages

    python3 tools/publish_library.py
"""
import json, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "wish-library.json")
OUT_DIR = os.path.join(ROOT, "library")
OUT = os.path.join(OUT_DIR, "v1.json")

# 网站六类 → App 六类（GoodsCategory）
KIND_MAP = {
    "习惯": "habit",
    "任务": "task",
    "项目": "project",
    "清单": "checklist",
    "陪伴": "companion",
}


# 计划灵感的「不展示但落库」默认值（v1.2.0）。
# 每条单独配：节奏、目标、阶段都给到能直接用的程度，用户只做删除或微调。
PLAN_DEFAULTS = {
    "P-ON01": dict(time="21:00", startOffsetDays=0, endOffsetDays=2, onceOffsetDays=0,
                   stages=["先列出这三年做过的事", "按岗位改一版", "找人读一遍给意见"]),
    "P-ON02": dict(time="20:00", startOffsetDays=0, endOffsetDays=2, onceOffsetDays=2,
                   stages=["按行程列清单", "把证件和充电线装好", "出门前逐项勾掉"]),
    "P-ON03": dict(time="09:30", startOffsetDays=0, endOffsetDays=7, onceOffsetDays=3,
                   stages=["查好能约的医院", "约一个上午的号", "把体检报告存起来"]),
    "P-ON04": dict(time="10:00", startOffsetDays=0, endOffsetDays=1, onceOffsetDays=1,
                   stages=["先清空桌面", "按常用 / 偶尔 / 不留分三堆", "把留下的归位"]),
    "P-ON05": dict(time="21:30", startOffsetDays=0, endOffsetDays=1, onceOffsetDays=0,
                   stages=["关掉手机十分钟", "写下三个最想要的", "给每个补一句为什么"]),
    "P-ON06": dict(time="09:00", startOffsetDays=0, endOffsetDays=30, onceOffsetDays=15,
                   stages=["挑一个周末", "查好车次和天气", "到了就走到海边"]),
    "P-ON07": dict(time="20:30", startOffsetDays=0, endOffsetDays=90, onceOffsetDays=30,
                   stages=["按年份建三个相册", "先删重复和模糊的", "每本挑一张做封面"]),
    "P-ON08": dict(time="18:30", startOffsetDays=0, endOffsetDays=7, onceOffsetDays=5,
                   stages=["挑一个都空的日子", "定一家好坐的店", "见面时把近况说完"]),

    "P-D01": dict(time="08:00", startOffsetDays=0, targetCount=21, unit="杯", unitTarget=8,
                   stages=["早上先喝一杯", "每两小时补一杯", "睡前两小时停下"]),
    "P-D02": dict(time="22:00", startOffsetDays=0, targetCount=21, unit="行", unitTarget=1,
                   stages=["把手机放到床外", "写今天最想记住的一句", "写完就关灯"]),
    "P-D03": dict(time="12:30", startOffsetDays=0, targetCount=21, unit="步", unitTarget=6000,
                   stages=["午饭后走十分钟", "下班提前一站下车", "睡前看一次步数"]),
    "P-D04": dict(time="20:30", startOffsetDays=0, targetCount=21, unit="分钟", unitTarget=10,
                   stages=["先拉肩颈两分钟", "再做腿后侧", "最后深呼吸三次"]),
    "P-D05": dict(time="21:30", startOffsetDays=0, targetCount=21, unit="页", unitTarget=10,
                   stages=["把书放在床头", "睡前读十页", "读到一句就划一下"]),
    "P-D06": dict(time="21:45", startOffsetDays=0, targetCount=21, unit="笔", unitTarget=1,
                   stages=["睡前打开记账", "只记金额和类别", "周末看一眼总数"]),
    "P-D07": dict(time="20:00", startOffsetDays=0, targetCount=30, unit="次", unitTarget=1,
                   stages=["挑一个久没联系的人", "发一句具体的问候", "聊完记一笔"]),
    "P-D08": dict(time="22:00", startOffsetDays=0, targetCount=21, unit="次", unitTarget=1,
                   stages=["二十二点把灯调暗", "二十二点半放下手机", "关灯后不再看屏幕"]),

    "P-W01": dict(time="19:30", startOffsetDays=0, weekdays=[1, 3, 5], targetCount=36,
                   unit="次", unitTarget=1,
                   stages=["先定三天固定时段", "每次至少二十分钟", "月底看一次完成次数"]),
    "P-W02": dict(time="20:30", startOffsetDays=0, weekdays=[3], targetCount=12,
                   unit="次", unitTarget=1,
                   stages=["把这一晚空出来", "关掉消息提醒", "做一件只取悦自己的事"]),
    "P-W03": dict(time="19:30", startOffsetDays=0, weekdays=[7], targetCount=12,
                   unit="次", unitTarget=1,
                   stages=["固定周日晚上", "先问这一周过得怎样", "挂之前约下一次"]),
    "P-W04": dict(time="21:00", startOffsetDays=0, weekdays=[7], targetCount=12,
                   unit="次", unitTarget=1,
                   stages=["翻一遍这周的照片", "写三行：做完 / 没做 / 下周", "只留一件下周要做的"]),
    "P-W05": dict(time="18:00", startOffsetDays=0, weekdays=[6], targetCount=12,
                   unit="道", unitTarget=1,
                   stages=["挑一道想吃的", "买齐材料", "做完拍一张"]),
    "P-W06": dict(time="10:00", startOffsetDays=0, weekdays=[6], targetCount=12,
                   unit="次", unitTarget=1,
                   stages=["先收桌面", "再处理地面", "最后倒垃圾"]),
    "P-W07": dict(time="20:00", startOffsetDays=0, weekdays=[5], targetCount=12,
                   unit="笔", unitTarget=1,
                   stages=["定一个固定金额", "发工资先转出去", "月底看累计"]),
    "P-W08": dict(time="18:30", startOffsetDays=0, weekdays=[6], targetCount=12,
                   unit="次", unitTarget=1,
                   stages=["约一个固定周末", "定低负担的地点", "见面时不聊工作"]),

    "P-M01": dict(time="20:00", startOffsetDays=0, monthDays=[10], targetCount=12,
                   unit="笔", unitTarget=1,
                   stages=["工资到账先转 20%", "把转出设成自动", "年底看总数"]),
    "P-M02": dict(time="21:00", startOffsetDays=0, monthDays=[28], targetCount=12,
                   unit="本", unitTarget=1,
                   stages=["月初选一本", "每天读十页", "月末写三行感受"]),
    "P-M03": dict(time="09:00", startOffsetDays=0, monthDays=[15], targetCount=12,
                   unit="次", unitTarget=1,
                   stages=["挑一个近的城", "定好来回车次", "只带一个小包"]),
    "P-M04": dict(time="18:00", startOffsetDays=0, monthDays=[20], targetCount=12,
                   unit="次", unitTarget=1,
                   stages=["提前买好", "写一张短句", "寄出后告诉一声"]),
    "P-M05": dict(time="20:00", startOffsetDays=0, monthDays=[1], targetCount=12,
                   unit="次", unitTarget=1, endOffsetDays=365,
                   stages=["导出这个月账单", "核对固定支出", "把异常记一笔"]),
    "P-M06": dict(time="20:30", startOffsetDays=0, monthDays=[25], targetCount=12,
                   unit="件", unitTarget=1, endOffsetDays=365,
                   stages=["月初定题", "月中做完一半", "月底收尾并发布"]),
    "P-M07": dict(time="21:00", startOffsetDays=0, monthDays=[28], targetCount=12,
                   unit="次", unitTarget=1, endOffsetDays=365,
                   stages=["记睡眠和精力", "记一次不舒服", "写下下个月要改的一件"]),
    "P-M08": dict(time="19:00", startOffsetDays=0, monthDays=[15], targetCount=12,
                   unit="顿", unitTarget=1,
                   stages=["挑一家想吃的", "不带上任何人", "点一道没吃过的"]),

    "P-Y01": dict(time="08:00", startOffsetDays=0, yearMonthDay=[10, 1], targetCount=3,
                   unit="次", unitTarget=1, endOffsetDays=365,
                   stages=["定一个想去的地方", "存够一趟的钱", "把年假请下来"]),
    "P-Y02": dict(time="08:00", startOffsetDays=0, yearMonthDay=[3, 15], targetCount=3,
                   unit="次", unitTarget=1, endOffsetDays=365,
                   stages=["年初约一次", "把旧报告带上", "看完把指标记下来"]),
    "P-Y03": dict(time="20:00", startOffsetDays=0, yearMonthDay=[1, 1], targetCount=3,
                   unit="个", unitTarget=1, endOffsetDays=365,
                   stages=["选一个能上手的", "每周固定两次", "做出一个能看的东西"]),
    "P-Y04": dict(time="20:00", startOffsetDays=0, yearMonthDay=[12, 31], targetCount=3,
                   unit="次", unitTarget=1, endOffsetDays=365,
                   stages=["按年份建相册", "删重复和模糊", "挑十二张做年度封面"]),
    "P-Y05": dict(time="21:00", startOffsetDays=0, yearMonthDay=[12, 31], targetCount=3,
                   unit="封", unitTarget=1, endOffsetDays=365,
                   stages=["写今年最要紧的三件事", "写一句给明年的自己", "封好放在固定位置"]),
    "P-Y06": dict(time="10:00", startOffsetDays=0, yearMonthDay=[1, 1], targetCount=3,
                   unit="次", unitTarget=1, endOffsetDays=365,
                   stages=["提前定下哪天", "把该请的人请上", "当天不看工作消息"]),
    "P-Y07": dict(time="18:00", startOffsetDays=0, yearMonthDay=[12, 31], targetCount=3,
                   unit="件", unitTarget=1, endOffsetDays=365,
                   stages=["年初定一个题", "每月推进一次", "年底完成并留下记录"]),
    "P-Y08": dict(time="08:00", startOffsetDays=0, yearMonthDay=[1, 20], targetCount=3,
                   unit="次", unitTarget=1, endOffsetDays=365,
                   stages=["提前订票", "留一天给旧友", "回去走一遍老路"]),
}

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
    plans = [
        {
            "id": p["id"],
            "frequency": p["frequency"],
            "kind": p["kind"],
            "appKind": KIND_MAP.get(p["kind"], "task"),
            "zh": p["zh"],
            "en": p["en"],
            **({"defaults": PLAN_DEFAULTS[p["id"]]} if p["id"] in PLAN_DEFAULTS else {}),
        }
        for p in d["plans"]
    ]
    payload = {
        "schema": 1,
        "version": "1.2.0",
        "updated": datetime.date.today().isoformat(),
        "source": "https://riverdriven.github.io/DearMe/#/library",
        "license": "文案由 DearMe / lobus 改写整理，供 DearMe App 内展示使用。",
        "counts": {"wishes": len(items), "plans": len(plans)},
        "items": items,
        "plans": plans,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.write("\n")
    dist = {}
    for it in items:
        dist[it["appType"]] = dist.get(it["appType"], 0) + 1
    print("published", len(items), "wishes,", len(plans), "plans →", OUT)
    print("appType 分布:", dist)


if __name__ == "__main__":
    main()
