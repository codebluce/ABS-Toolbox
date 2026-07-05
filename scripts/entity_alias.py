"""ABS 机构名映射统一模块

合并自原 3 skill 的三套机构名映射表:
  - ENTITY_MERGE_MAP (申万宏源系合并,来自机构统计 v1.1.0 L131)
  - BANK_NORM_MAP   (托管行分行归并,来自机构统计 v1.1.0 L138)
  - HARD_MAP        (杭州联合等,来自簿记录入 v2.1 SKILL.md L207-218 文档说明,
                     v2.1 代码实际用截断匹配策略,本表为文档参考用)

整合目的:申万宏源/杭州联合等机构名映射原本在两处分别维护,容易漂移。
本模块统一暴露 normalize_entity / merge_entity 接口,三 skill 共用。

来源行号对照(审计追溯用):
  - ENTITY_MERGE_MAP: skills/机构统计/gen_institution_stats.py L131-135
  - BANK_NORM_MAP:    skills/机构统计/gen_institution_stats.py L138-150
  - HARD_MAP:         skills/簿记录入/v2.1/SKILL.md L208-209 (文档,非代码)
"""

import re

# ═══════════════════════════════════════════════════════════════
# §1  实体合并映射 (申万宏源系)
# ═══════════════════════════════════════════════════════════════
# 来源: skills/机构统计/gen_institution_stats.py L131-135
# 用途: 申万宏源系 3 家子公司合并为同一主体"申万宏源"
ENTITY_MERGE_MAP = {
    '申万宏源': '申万宏源',
    '申万宏源资管': '申万宏源',
    '申万资管': '申万宏源',
}

# ═══════════════════════════════════════════════════════════════
# §2  托管行归并映射 (分行 → 总行)
# ═══════════════════════════════════════════════════════════════
# 来源: skills/机构统计/gen_institution_stats.py L138-150 + v2.0.0 补充
# 用途: 托管行统计时,分行名归并到总行(原 24 条 + v2.0.0 补 2 条 = 26 条)
# v2.0.0 补充(2026-07-05): 0626 定稿台账出现 '工银天津'/'华夏北分' 未归并,
#   原 BANK_NORM_MAP 缺失,补 '工银天津' → '工商银行' / '华夏北分' → '华夏银行'
BANK_NORM_MAP = {
    '江苏北分': '江苏银行', '民生北分': '民生银行', '南银北分': '南京银行',
    '邮储北分': '邮储银行', '邮储中关村': '邮储银行',
    '兴业北分': '兴业银行', '兴银北分': '兴业银行',
    '建行北分': '建设银行', '青岛银行总行': '青岛银行',
    '中信北分': '中信银行', '工行天津': '工商银行',
    '平安北分': '平安银行', '光大重分': '光大银行', '光大北分': '光大银行',
    '交行北分': '交通银行', '交银北分': '交通银行',
    '广发北分': '广发银行',
    '招行北分': '招商银行', '招银北分': '招商银行',
    '浦发北分': '浦发银行', '渤海银行上海自贸区分行': '渤海银行',
    '中银北分': '中国银行', '中行北分': '中国银行',
    '上银北分': '上海银行',
    # v2.0.0 补充
    '工银天津': '工商银行',
    '华夏北分': '华夏银行',
}

# ═══════════════════════════════════════════════════════════════
# §3  簿记录入 HARD_MAP (文档参考,v2.1 代码未实际使用)
# ═══════════════════════════════════════════════════════════════
# 来源: skills/簿记录入/v2.1/SKILL.md L208-209 (文档说明)
# 注: 簿记录入 v2.1 代码 increment_merge.py 实际用"截断匹配+normalize 包含匹配"
#     策略替代了硬编码映射,本表仅作文档参考。
# 第二轮迁入簿记录入时,如确认仍需硬编码映射,再激活此表。
HARD_MAP = {
    '杭州联合': '杭州联合银行',           # 明细简称 → 台账全称
    '杭州联合农村商业银行': '杭州联合银行',  # 截断后 → 台账全称
}

# ═══════════════════════════════════════════════════════════════
# §4  统一接口
# ═══════════════════════════════════════════════════════════════

def normalize_entity(name):
    """实体合并:申万系合并为同一主体。

    用途: 机构统计三表(管理人/销售机构/托管行)的机构名归一化。
    来源: 机构统计 v1.1.0 L155 normalize_entity() 函数。
    """
    return ENTITY_MERGE_MAP.get(str(name).strip(), str(name).strip())


def normalize_bank(name):
    """托管行归并:分行名 → 总行名(含正则回退)。

    用途: 机构统计托管行表统计时,把分行归并到总行。
    来源: 机构统计 v1.1.0 normalize_bank() 逻辑(含正则回退"XX银行")。
    v2.0.0 修正(2026-07-05 审计反馈): 把正则回退从 gen_institution_stats.py
        本地重定义版本迁入此处,消除函数遮蔽,统一接口。
    """
    name = str(name).strip()
    if name in BANK_NORM_MAP:
        return BANK_NORM_MAP[name]
    # 通用规则:提取"XX银行"
    m = re.search(r'([一-鿿]+银行)', name)
    if m:
        return m.group(1)
    return name


def lookup_hard_map(name):
    """簿记录入硬编码映射查询(文档参考用,第二轮激活)。

    用途: 簿记录入 v2.1 明细机构名匹配时的精确映射兜底。
    来源: 簿记录入 v2.1 SKILL.md L208-209 文档说明。
    注: v2.1 代码实际用截断匹配策略,本函数仅作文档参考,
        第二轮迁入簿记录入时确认是否激活。
    """
    return HARD_MAP.get(str(name).strip(), str(name).strip())


# ═══════════════════════════════════════════════════════════════
# §5  自检
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    print("=== entity_alias.py 自检 ===")
    print(f"ENTITY_MERGE_MAP: {len(ENTITY_MERGE_MAP)} 条")
    print(f"BANK_NORM_MAP:    {len(BANK_NORM_MAP)} 条")
    print(f"HARD_MAP:         {len(HARD_MAP)} 条 (文档参考)")

    # 测试 normalize_entity
    assert normalize_entity("申万宏源资管") == "申万宏源"
    assert normalize_entity("申万资管") == "申万宏源"
    assert normalize_entity("中信证券") == "中信证券"
    print("✅ normalize_entity 测试通过")

    # 测试 normalize_bank
    assert normalize_bank("江苏北分") == "江苏银行"
    assert normalize_bank("建行北分") == "建设银行"
    assert normalize_bank("招商银行") == "招商银行"
    print("✅ normalize_bank 测试通过")

    # 测试 lookup_hard_map
    assert lookup_hard_map("杭州联合") == "杭州联合银行"
    assert lookup_hard_map("中信证券") == "中信证券"
    print("✅ lookup_hard_map 测试通过")

    print("\n✅ entity_alias.py 自检全部通过")
