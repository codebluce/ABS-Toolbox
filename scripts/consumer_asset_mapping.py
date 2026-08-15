"""消金资产实验面板的来源映射与展示配置。"""

from __future__ import annotations

WHITE_FUNDING_SHEET = "白条消费余额by资金类型"
GOLD_BALANCE_SHEET = "金条大盘余额"

WHITE_SECTIONS = ("白条消费", "分分卡", "取现")
WHITE_SECTION_LABELS = {
    "白条消费": "白条消费",
    "分分卡": "分分卡",
    "取现": "白取",
}
WHITE_FUNDING_ORDER = ("赊销", "信托", "小贷", "助贷100%", "助贷联合贷")
GOLD_FUNDING_ORDER = ("信托", "小贷", "助贷")

CONSUMER_LOAN_ASSETS = ("白条消费", "分分卡")
CASH_LOAN_ASSETS = ("金条", "白取")
CONSUMER_LOAN_FUNDING_ORDER = ("赊销", "信托", "小贷", "助贷合计")
CASH_LOAN_FUNDING_ORDER = ("信托", "小贷", "助贷合计")

# 面板的固定类别色。颜色由实体决定，不随金额排名变化。
CATEGORY_COLORS = {
    # 所有结构条统一使用同一蓝色系，以位置、标签、占比和数值区分实体。
    "白条消费": "#2a78d6",
    "分分卡": "#2a78d6",
    "白取": "#2a78d6",
    "消费贷": "#2a78d6",
    "现金贷": "#2a78d6",
    "消金资产合计": "#2a78d6",
    "赊销": "#2a78d6",
    "信托": "#2a78d6",
    "小贷": "#2a78d6",
    "助贷": "#2a78d6",
    "助贷合计": "#2a78d6",
    "助贷100%": "#2a78d6",
    "助贷联合贷": "#2a78d6",
}

PANEL_SUMMARY_RULE = "面板汇总以展示明细加总为准；来源表汇总仅用于容差校验（允许 1 元尾差）。"
CONSUMER_LOAN_RULE = "消费贷 = 白条消费 + 分分卡。"
CASH_LOAN_RULE = "现金贷 = 金条 + 白取。"
CASH_FUNDING_RULE = "现金贷助贷合计 = 金条助贷 + 白取助贷100% + 白取助贷联合贷。"
TOTAL_ASSET_RULE = "消金资产合计 = 消费贷 + 现金贷。"
