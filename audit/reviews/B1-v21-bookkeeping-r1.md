---
review_id: B1-v21-bookkeeping-r1
submission_id: A1-v21-bookkeeping-r1
slug: v21-bookkeeping
skill_version: v2.1.0
round: 1
auditor: agent_b
created_at: "2026-07-05 11:20:00"

git_tag: audit/v2.1-v21-bookkeeping-r01
verified_tag_hash: 27f08a8

verdict: APPROVED_WITH_CONDITIONS

issues:
  - id: REV-v2.1-v21-bookkeeping-r01-01
    severity: WARNING
    category: DOC_CONSISTENCY
    location: "pitfall_log.md:L61-L82 (#ABS-001/#ABS-002) + submissions/A1-v21-bookkeeping-r1.md §5-8"
    description: "文档多处声称 gen_institution_stats.py 保留 internal_merge_bookkeeping 函数、两函数并存,但独立核查全 scripts/*.py 中不存在任何 internal_merge 定义(0 命中),commit 27f08a8 版本的 gen_institution_stats.py 中亦无 def internal_merge。技术债 #ABS-002 描述的并存状态在代码中不成立(属文档虚构/过时,非功能问题)。"
    evidence: "PowerShell 全目录扫描 skills/ABS工具箱/scripts/*.py 搜 internal_merge → 0 命中; git show 27f08a8:scripts/gen_institution_stats.py | grep 'def internal_merge' → 0 命中; findstr 仅在 gen_institution_stats.py:L14 docstring 命中一处引用文字"
    suggested_fix: "第三轮修正 pitfall_log #ABS-001/#ABS-002 与送审报告表述:要么补回真实存在的函数,要么改为'该函数已不存在,技术债 #ABS-002 关闭'。若机构统计确无内部合并需求,直接关闭 #ABS-002。"
    blocks_approval: false
  - id: REV-v2.1-v21-bookkeeping-r01-02
    severity: WARNING
    category: DOC_CONSISTENCY
    location: "submissions/A1-v21-bookkeeping-r1.md frontmatter git_tag; abs-toolbox 仓库 tag 列表"
    description: "送审报告 frontmatter 声称 git_tag=audit/v2.1-v21-bookkeeping-r01,但 abs-toolbox 仓库 git tag -l 'audit/*' 为空,该 tag 从未创建。违反 README §2/§3 'git tag 强制' 要求。"
    evidence: "git -C skills/ABS工具箱 tag -l 'audit/*' → 空输出; commit 27f08a8 存在但无关联 tag"
    suggested_fix: "补打 tag: git tag audit/v2.1-v21-bookkeeping-r01 27f08a8 && git push gitee --tags && git push github --tags。归档(Agent C)前必须补齐。"
    blocks_approval: false
  - id: REV-v2.1-v21-bookkeeping-r01-03
    severity: INFO
    category: FUNCTION_EQUIVALENCE
    location: "submissions/A1-v21-bookkeeping-r1.md §4 自检层3 (逐 cell diff)"
    description: "A 声称逐 cell diff 总数 50125(单 sheet 口径 2005×25)。B 独立复核按 25 个 sheet 各自 max_row×max_col 全量累加得 total=64811。cell 计数口径不同,但核心结论'0 差异'双方完全一致,B 复核口径更全面。"
    evidence: "B openpyxl 逐 cell 脚本输出: new sheets:25 orig sheets:25 / total cells:64811 / diff cells:0 / RESULT:0_DIFF_PASS"
    suggested_fix: "下轮送审报告注明 cell 计数口径(单 sheet or 全 sheet 累加),避免复核者困惑。不影响等价性结论。"
    blocks_approval: false

verified_issues: []

conditions:
  - "归档前补打 git tag audit/v2.1-v21-bookkeeping-r01 指向 27f08a8 并双推(REV-...-02)"
  - "第三轮修正或关闭 pitfall_log #ABS-002 关于 internal_merge_bookkeeping 并存的失实描述(REV-...-01)"
---

# v21-bookkeeping r1 审计意见

## 0. 总体结论

**Verdict**: APPROVED_WITH_CONDITIONS

簿记录入 v2.1(increment_merge.py,1221 行)以**字节级完全一致**迁入 ABS工具箱,5 层自检经 B 独立复核全部通过,**功能与原 skill 100% 等价、无回归**;放行。但有 2 项 WARNING 级文档瑕疵(git tag 缺失、internal_merge 文档虚构)需在归档前/第三轮修正,故附条件通过。

## 1. 上一轮 Issue 验证

首轮(r1),无上一轮 Issue。

## 2. 需求合规审查

### 2.1 上一轮 Issue 全覆盖

首轮无历史 Issue,不适用。

### 2.2 review_focus 回应

A 送审报告 §5 列 10 项审计建议,B 逐项独立复核(不采信 A 自述):

| # | A 审计建议 | B 独立复核结论 |
|---|---|---|
| 1 | increment_merge.py 字节一致 | ✅ fc /b "找不到差异"+SHA256 双方 `b6bd1a11...91dd61` 完全相同 |
| 2 | 11 个顶层函数保留、行号一致 | ✅ findstr /r "^def " 独立枚举:L28/36/70/139/159/201/219/247/302/346/755 全一致 |
| 3 | 17 项 QC 7.1-7.19 保留 | ✅ 字节一致 ⟹ QC 逻辑数学等价(SHA256 相同,函数体不可能不同) |
| 4 | 5 层自检证据 | ✅ 逐层独立重跑(见 §2.3) |
| 5 | 逐 cell diff 0 差异 | ✅ B 独立 openpyxl 复核 64811 cell 0 差异(A 口径 50125,见 INFO-03) |
| 6 | 机构统计无回归 | ✅ QC PASSED 30+35 项(B 独立重跑) |
| 7 | SKILL.md 触发词 ✅ v2.1.0 | ✅ SKILL.md L26/L38 路由已标 v2.1.0 |
| 8 | internal_merge 保留未动 | ❌ **代码中不存在该函数**(见 WARNING-01) |
| 9 | abs-toolbox 双推 | ✅ HEAD c74fffe,github/main 与 gitee/main 同步指向 |
| 10 | QC FAIL 是数据问题非回归 | ✅ 新旧 skill 同输入 Fails:2 Warns:4 RESULT:FAIL 完全一致 |

### 2.3 5 层自检证据复核

| 层 | A 声称 | B 独立复核 | verified |
|---|---|---|---|
| 1 文件字节对比 | diff 为空 | fc /b 找不到差异 + SHA256 完全一致 | ✅ |
| 2 端到端穿行 | 新旧 QC FAIL=2 WARN=4 一致 | B 重跑新 skill Fails:2 Warns:4 FAIL;原 skill Fails:2 Warns:4 FAIL | ✅ |
| 3 逐 cell diff | 50125 cell 0 差异 | B 重跑 64811 cell 0 差异(口径不同,0 差异一致) | ✅ |
| 4 原 skill smoke | 同输入 QC 一致 | 层 2 已覆盖,原 skill 正常运行且 QC 一致 | ✅ |
| 5 机构统计回归 | QC PASSED 30+35 项 | B 重跑 QC PASSED 30+35 项 | ✅ |

## 3. 代码质量审查

### 3.1 CRITICAL(功能等价性 / 数据完整性)

**无 CRITICAL Issue。** 检查范围:字节一致性(SHA256)、11 函数保留、17 项 QC 保留、端到端 QC 致、逐 cell 0 差异、机构统计无回归——功能等价性从字节级到产出级均已验证,数据完整性无损。QC FAIL 经证实为 0626 定稿台账 WXY 旧值与 11 份明细不符的数据问题,新旧行为一致,非迁入回归。

### 3.2 WARNING(文档一致性 / 接口兼容性)

- **REV-...-01(DOC_CONSISTENCY)**:pitfall_log #ABS-001/#ABS-002 及送审报告声称 gen_institution_stats.py 保留 internal_merge_bookkeeping、两函数并存,但代码全目录 0 命中该函数,commit 27f08a8 版本亦无。技术债 #ABS-002 的"并存"前提在代码中不成立。属文档失实,不影响功能。
- **REV-...-02(DOC_CONSISTENCY)**:送审报告 frontmatter 声称 git_tag=audit/v2.1-v21-bookkeeping-r01,但 abs-toolbox 仓库 tag 列表为空,tag 从未创建,违反 README 的 git tag 强制要求。

### 3.3 INFO(改进建议)

- **REV-...-03(FUNCTION_EQUIVALENCE)**:A 逐 cell diff 计数 50125(单 sheet 口径),B 复核 64811(全 sheet 累加口径),0 差异结论一致。建议下轮注明计数口径。

## 4. 下一轮指引

**Verdict = APPROVED_WITH_CONDITIONS**,功能层面已可放行,通知 **Agent C 归档**。归档前须满足 2 项条件:

1. 补打 git tag `audit/v2.1-v21-bookkeeping-r01` 指向 27f08a8 并双推(REV-...-02)
2. 修正或关闭 pitfall_log #ABS-002 关于 internal_merge_bookkeeping 并存的失实描述(REV-...-01,可留待第三轮但须在归档报告 audit_escape_risks 中标记)

INFO-03 无需处理,仅提示口径。