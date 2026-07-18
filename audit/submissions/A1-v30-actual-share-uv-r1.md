---
submission_id: A1-v30-actual-share-uv-r1
slug: v30-actual-share-uv
skill_version: v2.5.7
round: 1
created_at: "2026-07-18 15:26:32"
author: agent_a
git_tag: audit/v2.5.7-v30-actual-share-uv-r01
commit_hash: b1960ec
previous_git_tag: null
changed_files:
  - CHANGELOG.md
  - scripts/fig6_credit_panel.py
  - scripts/fig8_credit_total_panel.py
  - scripts/gen_institution_stats.py
  - scripts/gen_investment_ledger.py
  - scripts/itl_chat.js
  - scripts/投资台账_修改指南.md
status: PENDING_REVIEW
addressed_issues: []
self_review:
  all_issues_addressed: true
  no_overengineering: true
  function_equivalence_verified: true
  edge_cases_covered: true
  notes: "本轮按业务原则统一实际中标/额度占用规模为 V列认购份额口径；P1 发行定价类维持原申购报价/成本分析口径；管理/销售/托管项目规模保留项目去重J列并补说明。"
review_focus:
  - "核查投资台账 2026 records 的 inst/share/cost 是否固定为 U/V/T，未再使用 RESOLVED_SHARE_COL。"
  - "核查 fig6/fig8 新增认购规模是否固定为 U/V，Y列申购规模不再扣减额度。"
  - "核查 itl_chat 对“申购规模/报价规模”等未接入口径是否拒答，不再误答成 V列。"
  - "核查机构统计投行认购规模是否改为 U列投行记录的 V列合计；管理/销售/托管规模仍为项目去重J列且说明充分。"
---

# v30-actual-share-uv r1 送审报告

## 1. 变更摘要(200 字内)

本轮按业务原则修正“实际中标/持有/额度占用规模”口径：V列「认购份额」代表最终中标规模，Y列「申购规模」仅代表申购报价。投资台账、智能问答、非标额度、授信总额度、投行认购规模全部改为 U/V 实际中标口径；申购规模问答改为未接入口径拒答；机构统计管理/销售/托管规模继续保留项目去重 J列项目发行规模，并在说明栏明确。

## 2. 上一轮 Issue 处理(首轮省略)

本 slug 首轮，无上一轮 Issue。

## 3. 代码变更清单

| 文件 | 操作 | 说明 |
|---|---|---|
| `scripts/gen_investment_ledger.py` | modified | 2026 投资台账 `inst/share/cost` 固定为 U/V/T；不再用 `RESOLVED_SHARE_COL` 输出实际认购规模。 |
| `scripts/itl_chat.js` | modified | 明确规模类回答按 V列最终中标口径；“申购规模/报价规模”等未接入口径拒答。 |
| `scripts/fig6_credit_panel.py` | modified | 非标额度新增认购固定 U/V 口径，Y列不再扣减额度。 |
| `scripts/fig8_credit_total_panel.py` | modified | 授信总额度新增认购固定 U/V 口径，Y列不再扣减额度。 |
| `scripts/gen_institution_stats.py` | modified | 投行认购规模改为 U列含“投行”的记录对 V列求和；说明栏补 J/V 口径。 |
| `scripts/投资台账_修改指南.md` | modified | 数据契约改为 U/V 实际中标口径；申购报价需另增字段。 |
| `CHANGELOG.md` | modified | 新增 v2.5.7 口径修正记录与验证结果。 |

## 4. 自审与指标

### 4.1 强制自审清单

- [x] all_issues_addressed: 覆盖用户确认的 P0 全部修改；P1 4-6 经 J vs V 对账后保留 J列，并补说明。
- [x] no_overengineering: 未改 abs_common 全局 resolved，避免影响发行定价/成本/利差等已确认口径；仅在需要实际中标规模的模块局部改口径。
- [x] function_equivalence_verified: py_compile、node --check、投资台账口径验证、fig6/fig8 smoke、综合看板端到端均通过。
- [x] edge_cases_covered: 覆盖 WXY 完整时不得用 Y 扣额度、申购规模问答拒答、J列项目规模重复风险分析、多联席承销重复归属说明。

### 4.2 5 层自检证据

| 层 | 检查 | 结果 | 证据 |
|---|---|---|---|
| 1 | 文件变更边界 | ✅ | `git diff --stat` 为 7 文件：CHANGELOG、fig6、fig8、gen_institution_stats、gen_investment_ledger、itl_chat、投资台账_修改指南。 |
| 2 | 端到端穿行 | ✅ | `gen_integrated_dashboard.py ... Inbox_uv_policy_verify.html` 输出 13 panel + Tab JS 齐全。 |
| 3 | 数值口径 | ✅ | 投资台账 2026 `share_sum=1115.9175`，与 V列认购份额合计一致。 |
| 4 | 模块 smoke | ✅ | fig6 新增认购=10.0；fig8 新增认购=18.47；`node --check scripts/itl_chat.js` 无报错。 |
| 5 | 回归测试 | ✅ | 综合看板生成 6107.9KB；机构统计说明栏正常渲染；P1 发行定价类未改。 |

## 5. 审计焦点(可选·给 B 的提示)

1. **投资台账口径**：`gen_investment_ledger.py` 是否还引用 `RESOLVED_SHARE_COL`；2026 `share` 是否固定 V列。
2. **问答机器人**：`itl_chat.js` 中“申购规模/报价规模/申报规模/投标规模”是否拒答，避免把 Y列缺失的问法误答成 V列。
3. **额度占用**：fig6/fig8 新增认购是否固定 U/V；未匹配审计是否仍保留。
4. **机构统计**：投行认购规模是否改 V列；管理/销售/托管规模是否保留项目去重 J列并说明多联席承销重复归属。
5. **未改范围**：发行定价/成本/利差类 P1 1-3 已由用户确认当前口径无误，本轮不应误改。

## 6. 附录

### 6.1 编译/语法检查

```text
python -m py_compile scripts/gen_investment_ledger.py scripts/fig6_credit_panel.py scripts/fig8_credit_total_panel.py scripts/gen_institution_stats.py
node --check scripts/itl_chat.js
COMPILE_OK
```

### 6.2 投资台账 V列口径验证

```text
投资台账：1968 条投资记录，认购份额合计 1115.92 亿
records 1968
share_sum 1115.9175
```

### 6.3 fig6 / fig8 smoke

```text
fig6_new_total 10.0
fig8_new_total 18.47
```

### 6.4 综合看板端到端

```text
[4/4] 拼接 HTML...
[完成] Inbox_uv_policy_verify.html (6107.9 KB)
默认显示: 发行定价 / 定价测试
[QC] 综合看板结构检查通过：13 个 panel(7 主 + 理财子分析 + 非标额度 + 授信总额度 + 投资台账[2026+2025+2024]) + Tab 切换 JS 齐全
```

### 6.5 J列项目规模 vs V列合计对账

```text
项目数 115
J合计 1128.7600
V合计 1129.4550
总差异 V-J +0.6950
完全一致项目数 108
不一致项目数 7
```

管理/销售/托管对账明细已存：`D:\wupeizhi.nolan\Documents\LikeCodeNex\Inbox\_j_vs_v_institution_check.xlsx`。
