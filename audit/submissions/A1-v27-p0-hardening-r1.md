---
submission_id: A1-v27-p0-hardening-r1
slug: v27-p0-hardening
skill_version: v2.5.4
round: 1
created_at: "2026-07-16 23:34:34"
author: agent_a
git_tag: audit/v2.5.4-v27-p0-hardening-r01
commit_hash: c9c2626
previous_git_tag: null
changed_files:
  - CHANGELOG.md
  - pitfall_log.md
  - scripts/abs_common.py
  - scripts/fig6_credit_panel.py
  - scripts/fig8_credit_total_panel.py
  - scripts/increment_merge.py
  - scripts/lab/fig4_new_welizhi_matrix.py
  - scripts/lab/load_data.py
status: PENDING_REVIEW
addressed_issues: []
self_review:
  all_issues_addressed: true
  no_overengineering: true
  function_equivalence_verified: true
  edge_cases_covered: true
  notes: "本轮为行为增强型防错包，不是原 skill 迁入；5 层自检按防错改造口径执行，重点验证 QC 阻断、WXY 三元组、额度 resolved 口径、#ABS-006 首行补回与综合看板回归。"
review_focus:
  - "核查 increment_merge.py 中 QC 7.1/7.2/7.3 的 qc_pre_fails 是否确实纳入最终 qc_fails，并在 FAIL 时阻断落盘。"
  - "核查 abs_common.resolve_columns 是否避免 WXY/TUV 逐列拼接；WXY 部分缺失时是否整行回退 TUV。"
  - "核查 fig6/fig8 新增认购 resolved 口径和匹配审计是否有重复计入/漏计的副作用。"
  - "核查 fig4/fig5/fig6/fig8 从 iloc[2:] 改为 iloc[1:] 是否符合当前单行表头台账结构。"
---

# v27-p0-hardening r1 送审报告

## 1. 变更摘要(200 字内)

本轮实现 P0 防错包：让 `increment_merge` 核心 QC 7.1/7.2/7.3 的 FAIL 真正计入阻断；将 `abs_common.resolve_columns()` 改为 WXY 三元组完整优先、部分缺失整行回退 TUV；fig6/fig8 新增认购改为 WXY 穿透优先口径并增加匹配审计；修复 #ABS-006 的 `iloc[2:]` 行偏移，补回台账首条认购记录。

## 2. 上一轮 Issue 处理(首轮省略)

本 slug 首轮，无上一轮 Issue。

## 3. 代码变更清单

| 文件 | 操作 | 说明 |
|---|---|---|
| `scripts/increment_merge.py` | modified | QC 7.1/7.2/7.3 失败累加到 `qc_pre_fails`，并入最终 `qc_fails`，确保 FAIL 阻断落盘。 |
| `scripts/abs_common.py` | modified | `resolve_columns()` 从逐列 fallback 改为 WXY 三元组整体判断；部分缺失整行回退 TUV 并 WARN。 |
| `scripts/fig6_credit_panel.py` | modified | 非标额度新增认购改 resolved 口径；新增唯一匹配审计；读取台账改 `iloc[1:]`。 |
| `scripts/fig8_credit_total_panel.py` | modified | 授信总额度新增认购改 resolved 口径；新增唯一匹配审计；读取台账改 `iloc[1:]`。 |
| `scripts/lab/fig4_new_welizhi_matrix.py` | modified | 修复 #ABS-006，读取台账从 `iloc[2:]` 改为 `iloc[1:]`。 |
| `scripts/lab/load_data.py` | modified | 修复 #ABS-006，读取台账从 `iloc[2:]` 改为 `iloc[1:]`。 |
| `pitfall_log.md` | modified | #ABS-006 状态更新为已修复，补充 fig6/fig8 同类修复说明。 |
| `CHANGELOG.md` | modified | 新增 v2.5.4 P0 防错包条目、验证结果与注意事项。 |

## 4. 自审与指标

### 4.1 强制自审清单

- [x] all_issues_addressed: 本 slug 首轮，无上一轮 CRITICAL/WARNING；本轮覆盖用户认可的 P0 防错包 5 项。
- [x] no_overengineering: 未引入新框架；新增 helper 限于 fig6/fig8 局部函数；未做大规模重构。
- [x] function_equivalence_verified: 已跑语法检查、fig6/fig8 独立计算、综合看板端到端生成；已验证 #ABS-006 数值补回 4 亿。
- [x] edge_cases_covered: 覆盖 WXY 部分缺失、额度未匹配/多匹配、单行表头首行数据、综合看板 13 panel 回归。

### 4.2 5 层自检证据

| 层 | 检查 | 结果 | 证据 |
|---|---|---|---|
| 1 | 文件变更边界 | ✅ | `git show --stat --name-only c9c2626` 仅 8 文件：CHANGELOG、pitfall_log、6 个脚本。 |
| 2 | 端到端穿行 | ✅ | `python scripts/gen_integrated_dashboard.py deliverables/ledger/03_final/2026年ABS发行台账-0706-定稿.xlsx Inbox_should_not_exist.html` 输出 `[QC] 综合看板结构检查通过：13 个 panel...`。 |
| 3 | 数值 spot check | ✅ | #ABS-006 验证：`iloc[1:]` 原始认购份额合计 1129.455，`iloc[2:]` 为 1125.455，delta=4.0，补回东道17-3 邮储银行 4 亿。 |
| 4 | 模块 smoke | ✅ | `py_compile` 通过；fig6 独立计算 matched=2,multi=0,unmatched=0；fig8 独立计算 matched=16,multi=0,unmatched=7。 |
| 5 | 回归测试 | ✅ | 综合看板 13 panel 全齐；compare/cost/spread/institution QC 均正常输出，其中机构统计 QC PASSED 30 项全部通过。 |

## 5. 审计焦点(可选·给 B 的提示)

1. **QC 阻断闭环**：重点看 `scripts/increment_merge.py` 中 `qc_pre_fails` 的作用域、累加点和 `qc_fails += qc_pre_fails` 是否覆盖 QC 7.1/7.2/7.3。
2. **WXY 三元组**：重点看 `scripts/abs_common.py` 中 `wxy_complete` 与 `wxy_partial` 判断，确认部分缺失不会混用 W 与 U/V。
3. **额度口径变更**：fig8 从表面 U/V 改为 WXY 穿透优先后，新增认购/实时剩余额度会发生预期变化；请审查是否符合业务口径。
4. **匹配审计**：fig6/fig8 多匹配当前策略为“不计入并 WARN”，避免重复占用；请审查这是否应升级为阻断或在 HTML 中展示。
5. **#ABS-006**：确认当前 0703/0706 定稿均为单行表头，`iloc[1:]` 不会把子表头当数据。

## 6. 附录

### 6.1 git 快照

```text
c9c2626 fix(ABS工具箱): P0防错包-QC阻断+WXY三元组+额度口径审计
CHANGELOG.md
pitfall_log.md
scripts/abs_common.py
scripts/fig6_credit_panel.py
scripts/fig8_credit_total_panel.py
scripts/increment_merge.py
scripts/lab/fig4_new_welizhi_matrix.py
scripts/lab/load_data.py
```

### 6.2 py_compile

```text
python -m py_compile scripts/abs_common.py scripts/increment_merge.py scripts/fig6_credit_panel.py scripts/fig8_credit_total_panel.py scripts/lab/fig4_new_welizhi_matrix.py scripts/lab/load_data.py
PY_COMPILE_OK
```

### 6.3 fig6 smoke

```text
7月起非标/保登新增认购记录数: 2
[口径] 新增认购 resolved 来源: WXY=1193 TUV=834 PARTIAL_WXY回退=6
[MATCH] 非标额度新增认购: matched=2, multi=0, unmatched=0
fig6 institutions 46 new_total 10.0
```

### 6.4 fig8 smoke

```text
7月起全口径新增认购记录数: 23
[口径] 新增认购 resolved 来源: WXY=1193 TUV=834 PARTIAL_WXY回退=6
[WARN] 授信总额度新增认购: 6 条>=0.1亿新增认购未匹配授信机构，未计入。
[MATCH] 授信总额度新增认购: matched=16, multi=0, unmatched=7
fig8 institutions 36 new_total 26.42
```

### 6.5 综合看板端到端

```text
[4/4] 拼接 HTML...
[完成] Inbox_should_not_exist.html (6122.5 KB)
默认显示: 发行定价 / 定价测试
[QC] 综合看板结构检查通过：13 个 panel(7 主 + 理财子分析 + 非标额度 + 授信总额度 + 投资台账[2026+2025+2024]) + Tab 切换 JS 齐全
```

### 6.6 #ABS-006 spot check

```text
fig4 size iloc1 1129.455
fig4 size iloc2 1125.455
delta 4.0
```
