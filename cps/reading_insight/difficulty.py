"""R214 难度阶解析（与 R213 分级推荐共用同一实现）。

Why: 详情页要回答「难不难读」，R213 首页分级推荐按同一口径分阶——两处若各写
     一份判定，同一本书在首页和详情页会说出两个难度。解析器独立成模块，消费方
     （show_book / R213 推荐）只看返回值，不各自实现。

口径（R214 拍板⑥，扩源自 R213「按书架名解析」）四级兜底：
  ① 标签含 `阶N`（最精确，人工标注）
  ② 书架名含 `阶N`（R140 起的「英文分级·阶N（…词）」公共书架）
  ③ 系列名映射（系列名自带 `阶N` 直取；书虫·第N级 → 阶 粗映射）
  ④ 以上皆无 → 未分级（返回 None）

返回 (阶数, 来源) 而不是只返回阶数——系列映射是粗口径，UI 必须以 tooltip
标注「这一阶是系列粗映射，不是书目事实」，让用户看得出可被标签/书架覆盖。
"""
import re

# 阶位：与 R140 书架命名（英文分级·阶1（800–1500词）…阶6（9000+词））同源
_LEVEL_RE = re.compile(r"阶\s*(\d+)")
# 书虫（Oxford Bookworms 英汉改写本）系列级别：「书虫·第6级」
_BOOKWORMS_RE = re.compile(r"第\s*(\d+)\s*级")

# 书虫级别 → 本库阶位，粗映射。
# R162 实测锚点：书虫·第6级（2500 词族，CEFR B2/C1）≈ 阶2–阶3，取上界阶3；
# 1–5 级按书虫词族数（400/700/1100/1600/2200）对照 R140 阶带（阶1=800–1500词）
# 内插。页面 tooltip 必须标注 series 来源，允许人工用标签/书架覆盖。
SERIES_LEVEL_TO_BAND = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3}


def resolve_difficulty(tag_names, shelf_names, series_name=""):
    """按四级兜底解析难度阶。

    参数均为名称列表/字符串（不碰数据库，便于单测与 R213 复用）：
        tag_names    书目标签名列表，如 ["英文分级", "阶2"]
        shelf_names  书架名列表，如 ["英文分级·阶5（6500–9000词）"]
        series_name  系列名，如 "书虫·第6级"

    返回 (阶数:int | None, 来源:"tag"|"shelf"|"series"|None)。
    """
    for names, source in ((tag_names, "tag"), (shelf_names, "shelf")):
        for name in names or []:
            m = _LEVEL_RE.search(name or "")
            if m:
                return int(m.group(1)), source
    if series_name:
        m = _LEVEL_RE.search(series_name)
        if m:
            return int(m.group(1)), "series"
        m = _BOOKWORMS_RE.search(series_name)
        if m and ("书虫" in series_name or "bookworm" in series_name.lower()):
            level = int(m.group(1))
            if level in SERIES_LEVEL_TO_BAND:
                return SERIES_LEVEL_TO_BAND[level], "series"
    return None, None
