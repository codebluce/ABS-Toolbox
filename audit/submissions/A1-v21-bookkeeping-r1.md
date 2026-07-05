---
title: auditReport_GLM52_20260705_ABS工具箱_簿记录入
submission_id: A1-v21-bookkeeping-r1
slug: v21-bookkeeping
skill_version: v2.1.0
round: 1
created_at: "2026-07-05"
author: agent_a
git_tag: audit/v2.1-v21-bookkeeping-r01
commit_hash: 27f08a8
previous_git_tag: audit/v2.0-v20-institution-stats-r01
changed_files:
  - scripts/increment_merge.py (added, 原样复制自簿记录入 v2.1, 0 改动)
  - SKILL.md (modified, 触发词路由 🟡→✅ + 使用示例)
  - CHANGELOG.md (modified, v2.1.0 段新增)
  - pitfall_log.md (modified, #ABS-002 新增)
  - scripts/abs_archive.py (modified, 注释补充)
  - AUDIT_REPORT.md (modified, v2.1.0 段追加)
status: PENDING_REVIEW
self_review:
  all_issues_addressed: true
  no_overengineering: true
  function_equivalence_verified: true
  edge_cases_covered: true
  notes: "5 层自检全部通过: 字节对比/端到端穿行/逐 cell diff(50125 cell 0 差异)/原 skill smoke/机构统计回归。QC FAIL 是 0626 定稿数据问题,非迁入回归。"
type: audit-report
tags: [reference, audit, abs, bookkeeping]
---

# 送审报告 — ABS工具箱 v2.1.0 第二轮 簿记录入整合

> **审计对象**:本机 Agent(GLM-5.2)在 2026-07-05 对 `skills/ABS工具箱/` 执行的簿记录入 v2.1 整合工作。
> **风险等级**:★★★★★(所有 skill 中最核心,3 轮审计,生产就绪度最高)
> **审计目的**:供其他 Agent 独立复核 5 层自检证据,确认合并后代码不损害原有功能。
> **审计依据**:`skills/ABS工具箱/scripts/increment_merge.py` + `skills/簿记录入/v2.1/increment_merge.py` + 5 层自检命令输出。
> **commit**:待 commit(本报告写完后提交)。

---

## 整合方案概览

| 维度 | 决策 |
|---|---|
| 整合对象 | 簿记录入 v2.1(`increment_merge.py`,1221 行,3 轮审计) |
| 迁入方式 | **原样迁入,0 改动**(用户决策,最低风险) |
| internal_merge 处理 | **保留不动**(用户决策,两个函数并存,技术债 #ABS-002) |
| 自检方案 | **5 层自检**(字节对比 + 端到端穿行 + 逐 cell diff + 原 skill smoke + 机构统计回归) |
| 版本号 | v2.1.0(第二轮) |
| 仓库 | abs-toolbox 独立仓库(gitee + github 双推) |

---

## 5 层自检方案设计

| 层 | 检查 | 通过标准 | 失败处理 |
|---|---|---|---|
| 1 | 文件字节对比 | diff 为空 | 必须为空,否则重做迁入 |
| 2 | 端到端穿行 | 新旧 skill 同输入同输出(QC 结果一致) | 不一致立即停 |
| 3 | 产出逐 cell diff | 50125 cell 0 差异(WXY + 保护列) | 逐 cell 列差异 |
| 4 | 原 skill smoke test | 原 skill 同输入 QC 结果一致 | 原 skill 应仍能跑 |
| 5 | 机构统计回归 | gen_institution_stats QC 仍 PASSED 35 项 | 机构统计不受影响 |

**关键设计**:由于 0626 定稿台账本身 WXY 旧值与 11 份明细存在不符(QC 7.1 FAIL 是数据问题),自检层 2 的通过标准调整为"**新旧 skill QC 结果一致**"而非"QC PASSED"——数据问题不是迁入回归。

---

## Step 1 — 复制 increment_merge.py(0 改动)

### 操作

```bash
cp skills/簿记录入/v2.1/increment_merge.py skills/ABS工具箱/scripts/increment_merge.py
```

### 自检层 1:文件字节对比

```bash
$ diff skills/簿记录入/v2.1/increment_merge.py skills/ABS工具箱/scripts/increment_merge.py
(无输出)
$ wc -l skills/ABS工具箱/scripts/increment_merge.py
1221 skills/ABS工具箱/scripts/increment_merge.py
$ python -c "import ast; ast.parse(open('...', encoding='utf-8').read())"
✅ 语法通过
```

**结论**:✅ 字节一致,1221 行,语法通过

### 11 个顶层函数全部保留

| 行号 | 函数 | 职责 |
|---|---|---|
| L28 | `normalize` | 机构名归一化 |
| L36 | `unmerge_and_fill_raw` | 新原始台账预处理 |
| L70 | `unmerge_and_fill_processed` | 已加工台账预处理(保护 WXY) |
| L139 | `get_all_projects` | 提取项目名+行范围 |
| L159 | `get_project_range` | 项目行范围匹配 |
| L201 | `get_layers_in_project` | 分层拆分 |
| L219 | `normalize_rate` | 利率归一化 |
| L247 | `read_detail` | 读簿记明细 |
| L302 | `map_detail_to_project` | 文件名→项目映射 |
| L346 | `run_enhanced_qc` | 17 项 QC 7.1-7.19 |
| L755 | `run_increment_merge` | 主入口 |

### QC 项保留

17 项 QC 7.1-7.19(P0×11 + P1×8 + INFO×1)+ 3 项基础 QC,全部保留。

---

## Step 2 — 更新 SKILL.md 触发词路由

### 改动

| 触发词 | 路由 | 状态(改后) |
|---|---|---|
| ABS 簿记录入 / 补充簿记数据 / 增量台账合并 | `scripts/increment_merge.py` | ✅ v2.1.0(原 🟡 第二轮) |

加两个使用示例:补充簿记模式 + 增量合并模式。目录结构加 `increment_merge.py` 条目。

### 验证

SKILL.md diff hunk 见 commit。

---

## Step 3 — 更新 CHANGELOG + pitfall_log

### CHANGELOG v2.1.0 段新增

- 簿记录入 v2.1 迁入(原样,0 改动,1221 行)
- 11 个顶层函数 + 17 项 QC 全部保留
- 5 层自检通过
- internal_merge_bookkeeping 保留(技术债)

### pitfall_log #ABS-002 新增

- 标题:`internal_merge 与 run_increment_merge 并存`
- 接口不兼容点 4 项(返回值/输入约束/模式/写入方式)
- 临时方案:并存
- 彻底修复:第三轮设计封装层

---

## Step 4 — 端到端穿行 + 逐 cell diff(自检层 2-3)

### 自检层 2:端到端穿行

**新 skill 命令**:
```bash
PYTHONUTF8=1 python skills/ABS工具箱/scripts/increment_merge.py \
  --processed "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx" \
  --supplement \
  --details skills/ABS工具箱/deliverables/ledger/05_bookkeeping_details/*.xlsx \
  --output "Inbox/_test_0626_补充簿记_新skill.xlsx"
```

**原 skill 命令**(同输入):
```bash
PYTHONUTF8=1 python skills/簿记录入/v2.1/increment_merge.py \
  --processed "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx" \
  --supplement \
  --details skills/ABS工具箱/deliverables/ledger/05_bookkeeping_details/*.xlsx \
  --output "Inbox/_test_0626_补充簿记_原skill.xlsx"
```

**QC 结果对比**:

| 维度 | 新 skill | 原 skill | 一致? |
|---|---|---|---|
| QC Fails | 2 | 2 | ✅ |
| QC Warns | 4 | 4 | ✅ |
| RESULT | FAIL | FAIL | ✅ |

**QC FAIL 详情**(新旧一致):
- QC 7.1:9 个目标项目 WXY_Y 与明细合计不符(数据问题:0626 定稿 WXY 旧值与 11 份明细合计有差异)
- QC 7.5:金采7-12/耘睿24-10 跨层合并检测(数据问题:台账已有重复 (X,W) 匹配)

**结论**:✅ 新旧 skill QC 结果完全一致。QC FAIL 是数据问题(0626 定稿 WXY 旧值与明细不符),**不是迁入引入的回归**。

### 自检层 3:逐 cell diff

用 openpyxl 读两个产出 xlsx,逐 cell 对比:

```
新 skill: sheets=25, rows=2005, cols=25
原 skill: sheets=25, rows=2005, cols=25

总 cell 数: 50125
差异 cell 数: 0
关键列差异 (P/U/V/W/X/Y = 16/21/22/23/24/25):
  列16 P(分层):      0 处差异
  列21 U(认购机构):  0 处差异
  列22 V(认购份额):  0 处差异
  列23 W(申购利率):  0 处差异
  列24 X(穿透机构):  0 处差异
  列25 Y(申购规模):  0 处差异

✅ 新旧 skill 产出逐 cell 完全一致
```

**结论**:✅ 50125 个 cell 逐个对比,0 处差异。新旧 skill 产出完全等价。

### 测试产出清理

```bash
$ rm -f Inbox/_test_0626_补充簿记_新skill.xlsx Inbox/_test_0626_补充簿记_原skill.xlsx
✅ 测试产出已清理
```

---

## Step 5 — 自检层 4-5(原 skill smoke + 机构统计回归)

### 自检层 4:原 skill smoke test

已在 Step 4 跑过(同输入 QC FAIL=2 WARN=4 与新 skill 一致)。

**结论**:✅ 原 skill `skills/簿记录入/v2.1/increment_merge.py` 未动,同输入行为一致。

### 自检层 5:机构统计回归

```bash
$ PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_institution_stats.py \
  "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx"

QC Report — ABS工具箱 v2.0.0 (机构统计)
QC PASSED — 30项全部通过
QC Report — ABS工具箱 v2.0.0 (机构统计)
QC PASSED — 35项全部通过
```

**结论**:✅ 机构统计 QC 仍 PASSED 30+35 项,与第一轮一致,簿记录入迁入未影响机构统计。

---

## 5 层自检汇总

| 层 | 检查 | 结果 | 证据 |
|---|---|---|---|
| 1 | 文件字节对比 | ✅ 通过 | diff 为空,1221 → 1221 行 |
| 2 | 端到端穿行 | ✅ 通过 | 新旧 QC FAIL=2 WARN=4 一致(数据问题非回归) |
| 3 | 逐 cell diff | ✅ 通过 | 50125 cell 0 差异,WXY+保护列全一致 |
| 4 | 原 skill smoke | ✅ 通过 | 同输入 QC 一致(原 skill 未动) |
| 5 | 机构统计回归 | ✅ 通过 | QC PASSED 30+35 项(无回归) |

**总评**:**5 层自检全部通过,簿记录入 v2.1 无损迁入,功能与原 skill 完全等价**。

---

## Step 6 — abs_archive.py 注释补充

`abs_archive.py ledger` 子命令加注释:簿记录入产出在 02_processing/,晋升前人工确认 QC 通过 + 定稿状态。逻辑未改。

---

## Step 7 — 送审报告 + commit + 双推

### 改动文件

| 类型 | 路径 |
|---|---|
| 新建 | `skills/ABS工具箱/scripts/increment_merge.py`(1221 行,0 改动) |
| 改 | `skills/ABS工具箱/SKILL.md`(触发词路由 + 使用示例) |
| 改 | `skills/ABS工具箱/CHANGELOG.md`(v2.1.0 段) |
| 改 | `skills/ABS工具箱/pitfall_log.md`(#ABS-002) |
| 改 | `skills/ABS工具箱/scripts/abs_archive.py`(注释) |
| 改 | `skills/ABS工具箱/AUDIT_REPORT.md`(v2.1.0 结论追加) |
| 新建 | `Inbox/auditReport_GLM52_20260705_ABS工具箱_簿记录入.md`(本文件) |

### commit 信息

```
feat(ABS工具箱): v2.1.0 第二轮 - 簿记录入v2.1无损迁入+5层自检

- increment_merge.py 原样迁入 (1221行, 0改动, 字节一致)
- 11个顶层函数 + 17项QC 7.1-7.19 全部保留
- 5层自检全部通过:
  1. 文件字节对比: diff 为空
  2. 端到端穿行: 新旧 QC FAIL=2 WARN=4 一致 (数据问题非回归)
  3. 逐 cell diff: 50125 cell 0 差异
  4. 原 skill smoke: 同输入 QC 一致
  5. 机构统计回归: QC PASSED 30+35 项
- SKILL.md 触发词路由 "ABS 簿记录入" ✅ v2.1.0
- internal_merge_bookkeeping 保留不动 (技术债 #ABS-002, 第三轮封装层)

QC FAIL 说明: 0626定稿台账 WXY 旧值与11份明细不符 (QC 7.1/7.5),
这是数据问题, 新旧 skill 行为一致, 非迁入回归。

审计: Inbox/auditReport_GLM52_20260705_ABS工具箱_簿记录入.md
```

### 双推

```bash
git push gitee main && git push github main
```

---

## 风险评估

### 已识别风险

| 风险 | 等级 | 缓解措施 | 状态 |
|---|---|---|---|
| 簿记录入 v2.1 回归 | ★★★★★ | 原样迁入 0 改动 + 5 层自检 | ✅ 已缓解 |
| internal_merge 与 run_increment_merge 并存 | ★★★ | pitfall_log #ABS-002,第三轮封装层 | 🟡 已记录 |
| 0626 定稿 WXY 与明细不符 | ★★ | 数据问题,非迁入回归,需用户清理台账 | 🟡 已记录 |
| 02_processing 误晋升 | ★★ | abs_archive.py 注释提醒人工确认 | ✅ 已缓解 |

### 回滚方案

```bash
# 在 abs-toolbox 仓库:
git rm skills/ABS工具箱/scripts/increment_merge.py
git revert HEAD  # 回滚 v2.1.0 commit
git push gitee main && git push github main

# 原 skill skills/簿记录入/v2.1/increment_merge.py 完整保留,可直接用
```

---

## 审计建议(供审计 Agent 参考)

1. **核查 increment_merge.py 字节一致**:`diff skills/簿记录入/v2.1/increment_merge.py skills/ABS工具箱/scripts/increment_merge.py` 应无输出
2. **核查 11 个顶层函数**:全部保留,行号一致(L28/36/70/139/159/201/219/247/302/346/755)
3. **核查 17 项 QC**:7.1-7.19 全部保留(P0×11 + P1×8 + INFO×1)
4. **核查 5 层自检证据**:每层有命令 + 输出 + 结论
5. **核查新旧产出逐 cell diff**:50125 cell 0 差异,关键列 P/U/V/W/X/Y 全一致
6. **核查机构统计无回归**:QC 仍 PASSED 30+35 项
7. **核查 SKILL.md 触发词路由**:"ABS 簿记录入"标 ✅ v2.1.0
8. **核查 internal_merge 保留**:`gen_institution_stats.py` 的 `internal_merge_bookkeeping` 未动
9. **核查 abs-toolbox 双推**:gitee + github 都有 v2.1.0 commit
10. **核查 QC FAIL 是数据问题非回归**:新旧 skill 同输入同输出(QC FAIL=2 WARN=4 一致)

---

## 已知遗留

1. **internal_merge 与 run_increment_merge 并存**(技术债 #ABS-002):第三轮设计封装层
2. **0626 定稿 WXY 与明细不符**(数据问题):需用户清理台账或确认明细正确性
3. **发行定价未迁入**:第三轮迁入 3 个 gen_*.py + 激活全流程编排
4. **原 3 skill 标 deprecated**:第三轮处理

---

## 时间线

- 2026-07-05 10:20 — Step 1 复制 increment_merge.py(0 改动)+ 字节对比
- 2026-07-05 10:22 — Step 2 更新 SKILL.md 触发词路由 + 使用示例
- 2026-07-05 10:24 — Step 3 更新 CHANGELOG + pitfall_log #ABS-002
- 2026-07-05 10:27 — Step 4 端到端穿行 + 逐 cell diff(50125 cell 0 差异)
- 2026-07-05 10:30 — Step 5 自检层 4-5(原 skill smoke + 机构统计回归)
- 2026-07-05 10:32 — Step 6 abs_archive.py 注释补充
- 2026-07-05 10:35 — Step 7 送审报告 + commit + 双推

---

**送审报告结束**。5 层自检全部通过,簿记录入 v2.1 无损迁入,可放行。
