---
review_id: B1-v21-bookkeeping-r1
submission_id: A1-v21-bookkeeping-r1
slug: v21-bookkeeping
skill_version: v2.1.0
round: 1
auditor: agent_b
created_at: "2026-07-05"
status: DRAFT

git_tag: audit/v2.1-v21-bookkeeping-r01
verified_tag_hash: 27f08a8

verdict: PENDING_REVIEW
issues: []
verified_issues: []
conditions: []
---

# Agent B 审计调用建议 — v21-bookkeeping r1

> **本文件是给 Agent B 的审计任务调用建议**(非审计意见本身)。Agent B 接到本文件后,按下面指引独立审计,写正式审计意见覆盖本 draft。

## 0. 任务概述

**审计对象**:ABS工具箱 v2.1.0 第二轮 — 簿记录入 v2.1 整合
**送审报告**:`audit/submissions/A1-v21-bookkeeping-r1.md`
**commit hash**:`27f08a8`(abs-toolbox 仓库,gitee + github 双推)
**git tag**:`audit/v2.1-v21-bookkeeping-r01`
**风险等级**:★★★★★(所有 skill 中最核心,3 轮审计生产就绪)

**一句话**:Agent A 把 `increment_merge.py`(1221 行,3 轮审计)原样迁入 `skills/ABS工具箱/scripts/`,0 改动,用 5 层自检证明功能等价。请 Agent B 独立复核。

## 1. 审计范围与边界

### 在范围内(必审)

- `scripts/increment_merge.py` 是否真的 0 改动(字节对比)
- 11 个顶层函数是否全部保留(行号一致)
- 17 项 QC 7.1-7.19 是否全部保留(P0×11 + P1×8 + INFO×1)
- 5 层自检证据是否真实可信(命令 + 输出 + 结论)
- 新旧 skill 产出逐 cell diff 是否真 0 差异(50125 cell)
- 机构统计回归是否真的 QC PASSED 35 项
- SKILL.md 触发词路由是否正确(🟡 → ✅)
- CHANGELOG v2.1.0 段是否准确
- pitfall_log #ABS-002 是否记录技术债

### 在边界外(不审)

- 原 skill `skills/簿记录入/v2.1/increment_merge.py` 的代码质量(已 3 轮审计,不在本次范围)
- 0626 定稿台账 WXY 与明细不符的数据问题(QC 7.1/7.5 FAIL 是数据问题非回归,A 已说明)
- internal_merge_bookkeeping 的保留决策(用户决策,技术债 #ABS-002 已记录)
- 第三轮发行定价迁入(未启动)

## 2. 审计步骤建议

### Step 1:文件字节对比(自检层 1 复核)

```bash
cd D:/wupeizhi.nolan/Documents/LikeCodeNex
diff skills/簿记录入/v2.1/increment_merge.py skills/ABS工具箱/scripts/increment_merge.py
# 期望:无输出
wc -l skills/ABS工具箱/scripts/increment_merge.py
# 期望:1221 行
```

**通过标准**:diff 为空,1221 行。

### Step 2:11 个顶层函数 + 17 项 QC 保留性核查

```bash
grep -n "^def " skills/ABS工具箱/scripts/increment_merge.py | head -15
# 期望:L28 normalize / L36 unmerge_and_fill_raw / L70 unmerge_and_fill_processed
#       L139 get_all_projects / L159 get_project_range / L201 get_layers_in_project
#       L219 normalize_rate / L247 read_detail / L302 map_detail_to_project
#       L346 run_enhanced_qc / L755 run_increment_merge

grep -n "7\.[0-9]\+" skills/ABS工具箱/scripts/increment_merge.py | head -20
# 期望:7.1-7.19 全部保留
```

**通过标准**:11 函数行号一致 + 17 项 QC 编号齐全。

### Step 3:端到端穿行复跑(自检层 2-3 复核)

**关键**:不要轻信 A 的输出,Agent B 必须自己跑一遍。

```bash
cd D:/wupeizhi.nolan/Documents/LikeCodeNex

# 跑新 skill
PYTHONUTF8=1 "C:/Users/wupeizhi.nolan/AppData/Local/Programs/Python/Python312/python.exe" \
  skills/ABS工具箱/scripts/increment_merge.py \
  --processed "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx" \
  --supplement \
  --details skills/ABS工具箱/deliverables/ledger/05_bookkeeping_details/*.xlsx \
  --output "Inbox/_agentB_test_新.xlsx" 2>&1 | grep -E "Fails:|RESULT:"

# 跑原 skill
PYTHONUTF8=1 "C:/Users/wupeizhi.nolan/AppData/Local/Programs/Python/Python312/python.exe" \
  skills/簿记录入/v2.1/increment_merge.py \
  --processed "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx" \
  --supplement \
  --details skills/ABS工具箱/deliverables/ledger/05_bookkeeping_details/*.xlsx \
  --output "Inbox/_agentB_test_原.xlsx" 2>&1 | grep -E "Fails:|RESULT:"

# 逐 cell diff (用 openpyxl)
PYTHONUTF8=1 "C:/Users/wupeizhi.nolan/AppData/Local/Programs/Python/Python312/python.exe" << 'PYEOF'
from openpyxl import load_workbook
wb_new = load_workbook('Inbox/_agentB_test_新.xlsx')
wb_old = load_workbook('Inbox/_agentB_test_原.xlsx')
ws_new, ws_old = wb_new.active, wb_old.active
diff = sum(1 for r in range(1, max(ws_new.max_row, ws_old.max_row)+1)
             for c in range(1, max(ws_new.max_column, ws_old.max_column)+1)
             if ws_new.cell(r,c).value != ws_old.cell(r,c).value)
print(f"差异 cell 数: {diff}")
PYEOF

# 清理
rm Inbox/_agentB_test_新.xlsx Inbox/_agentB_test_原.xlsx
```

**通过标准**:
- 新旧 QC Fails/Warns 数一致(A 声称 Fails=2 Warns=4)
- 逐 cell diff = 0

**注意**:QC FAIL 是数据问题(0626 定稿 WXY 旧值与明细不符),**不是迁入回归**。A 已在送审报告说明,Agent B 应确认"新旧一致"而非"QC PASSED"。

### Step 4:机构统计回归复跑(自检层 5 复核)

```bash
PYTHONUTF8=1 "C:/Users/wupeizhi.nolan/AppData/Local/Programs/Python/Python312/python.exe" \
  skills/ABS工具箱/scripts/gen_institution_stats.py \
  "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx" 2>&1 | grep -E "QC PASSED|QC FAILED"

# 清理产出(避免污染 01_latest)
rm -f "skills/ABS工具箱/deliverables/dashboards/01_latest/$(date +%Y%m%d)_机构统计看板.html"
```

**通过标准**:QC PASSED 30+35 项(与 v2.0.0 第一轮一致)。

### Step 5:文档合规性审查

读以下文件,核查内容与代码一致:

| 文件 | 核查点 |
|---|---|
| `SKILL.md` | "ABS 簿记录入"标 ✅ v2.1.0;使用示例命令与 argparse 接口一致 |
| `CHANGELOG.md` | v2.1.0 段内容准确;待办第三轮清单合理 |
| `pitfall_log.md` | #ABS-002 接口不兼容 4 点描述准确;彻底修复路径可行 |
| `AUDIT_REPORT.md` | v2.1.0 段 5 层自检结论与送审报告一致 |
| `audit/submissions/A1-v21-bookkeeping-r1.md` | frontmatter changed_files 与实际 commit 一致;self_review 4 bool 合理 |

### Step 6:技术债 #ABS-002 评估

`internal_merge_bookkeeping` 与 `run_increment_merge` 并存是技术债。Agent B 应评估:

1. 并存是否真的零风险?(机构统计仍用 internal_merge,不受 increment_merge 迁入影响)
2. 第三轮封装层路径是否可行?(22 列→25 列升级 + 接口转换)
3. 是否有更简单的替代方案?(如机构统计直接调 increment_merge,但需先升级 22 列)

## 3. 审计焦点(A 在送审报告 §5 提示)

A 在送审报告未显式提 review_focus,但隐含焦点:
- **increment_merge 是否真的 0 改动**(字节对比是核心证据)
- **5 层自检是否真实可信**(A 自报,Agent B 必须复跑验证)
- **QC FAIL 是数据问题非回归**(新旧一致即通过,不要求 QC PASSED)

## 4. verdict 判定建议

| 条件 | 建议 verdict |
|---|---|
| 字节对比 diff 为空 + 11 函数保留 + 17 QC 保留 + 新旧产出逐 cell 0 差异 + 机构统计 QC PASSED 35 项 | **APPROVED** |
| 上述任一不满足但有合理说明 | **APPROVED_WITH_CONDITIONS**(列条件待用户复核) |
| 字节对比有差异(非 0 改动)或函数/QC 丢失 | **NEEDS_REVISION**(A 修正后 r2) |
| 发现 A 的 self_review 不诚实(如虚报 diff 为空) | **REJECTED** + self_review_dishonest=true |

## 5. 输出要求

Agent B 完成审计后,**覆盖本文件**写正式审计意见:

1. 文件名保持 `B1-v21-bookkeeping-r1.md`(不变)
2. frontmatter 按模板填(verdict / issues / verified_issues / conditions)
3. 正文按 `audit/reviews/_template.md` 结构:
   - §0 总体结论
   - §1 上一轮 Issue 验证(本轮首轮,无上一轮,写"首轮无 Issue")
   - §2 需求合规审查(2.1 上一轮 Issue 全覆盖 / 2.2 review_focus 回应 / 2.3 5 层自检证据复核)
   - §3 代码质量审查(3.1 CRITICAL / 3.2 WARNING / 3.3 INFO)
   - §4 下一轮指引
4. push 到 abs-toolbox 仓库(gitee + github 双推)
5. 更新 `audit/INDEX.md` + `audit/state.json`(reviews 列表加 B1,slug status 改 UNDER_REVIEW 或 APPROVED)

## 6. 审计时间预估

- Step 1-2(字节+函数+QC 核查):10 分钟
- Step 3(端到端穿行 + 逐 cell diff):15 分钟(跑两次 + openpyxl diff)
- Step 4(机构统计回归):5 分钟
- Step 5(文档合规):10 分钟
- Step 6(技术债评估):5 分钟
- 写审计意见:15 分钟

**总计 ~60 分钟**

## 7. 参考资料快速链接

- 送审报告:`audit/submissions/A1-v21-bookkeeping-r1.md`
- 审计模板:`audit/reviews/_template.md`
- 审计操作手册:`audit/README.md`
- skill 长期审计基线:`AUDIT_REPORT.md`
- 原始代码:`skills/簿记录入/v2.1/increment_merge.py`(对照基准)
- 迁入代码:`skills/ABS工具箱/scripts/increment_merge.py`(审计对象)
- 5 层自检设计依据:macro-allocation-strategy 的 A→B→C 流程精简适配

---

**Agent B 接到此调用建议后,直接开始审计,无需再问 Agent A 或人类。审计完成后覆盖本文件写正式审计意见。**
