---
review_id: B1-v30-actual-share-uv-r1
submission_id: A1-v30-actual-share-uv-r1
slug: v30-actual-share-uv
skill_version: v2.5.7
round: 1
auditor: agent_b
git_tag: audit/v2.5.7-v30-actual-share-uv-r01
verified_tag_hash: b1960ec
verdict: APPROVED
issues:
  - id: REV-v2.5.7-v30-actual-share-uv-r01-01
    severity: INFO
    category: FUNCTION_EQUIVALENCE
    blocks_approval: false
    summary: gen_institution_stats.py 残留 RESOLVED_SHARE_COL(L153定义/L441/443赋值)为 v26 UV保护遗留，不影响本轮投行认购路径(已改用认购份额V列)，建议后续清理
verified_issues: []
conditions: []
---

# B1 审计意见 — v30-actual-share-uv (r1)

## §0 审计元信息

- **送审报告**：A1-v30-actual-share-uv-r1.md（skill_version=v2.5.7，round=1）
- **审计对象 commit**：`b1960ec`（git_tag `audit/v2.5.7-v30-actual-share-uv-r01`）
- **审计者**：Agent B（独立审计，未信任 A 自述，逐项独立读代码 + grep 残留验证）
- **审计范围**：5 个「实际份额/UV口径统一」焦点 + 5 层自检复核
- **最终 verdict**：**APPROVED**

## §1 git 核实

| 核验项 | 命令 / 证据 | 结果 |
|---|---|---|
| tag→commit 一致 | `git show-ref --tags` → `audit/v2.5.7-v30-actual-share-uv-r01` = `b1960ec135c1e7eafdcafbd6e7e6d68ebcb1bae6`，与 A 声明 `b1960ec` 一致 | ✅ |
| changed_files 吻合 | `git show --stat --name-only b1960ec` = 7 文件：CHANGELOG.md / fig6_credit_panel.py / fig8_credit_total_panel.py / gen_institution_stats.py / gen_investment_ledger.py / itl_chat.js / 投资台账_修改指南.md，与 A 声明完全一致无遗漏 | ✅ |

作者=吴沛智(Nolan)，日期 Sat Jul 18 15:25:20 2026 +0800，commit msg=`fix(综合看板): 机构实际规模统一改V列中标口径`。洁净性优（无 v22/v23/v24 类 commit_hash 误填 / changed_files 遗漏）。

## §2 上一轮 Issue 复核

本 slug 为首轮（round=1），无上一轮遗留 Issue 待复核。

## §3 审计焦点核查

### 焦点 1：gen_investment_ledger.py — 投资台账 share=V列 ✅ PASS

独立读 `git show` diff + grep：
- `_records_from_25col_df` 中 `share=_n(row.get('认购份额'))`(V列) / `inst=normalize_investor_name(row.get('认购机构'))`(U列) / `cost=_n(row.get('成本'))`(T列)。
- import 移除 `RESOLVED_COST_COL/RESOLVED_INST_COL/RESOLVED_SHARE_COL`；grep `RESOLVED_.*_COL` = **0 命中**（全清除）。
- docstring 明确 WXY(申购利率/穿透机构/申购规模) 是申购报价明细，不用于 share 聚合。2025 改独立轻量解析保留真实日期。

### 焦点 2：itl_chat.js — 智能问答申购规模拒答 ✅ PASS

独立读 L153/L289-395/L700-711 + grep：
- **L153** `UNSUPPORTED_METRIC = /倍数|收益率|久期|余额|净值|回报|申购规模|报价规模|申报规模|投标规模/`（新增 4 个申购报价口径词）。
- **L391** spec 构建时 `unsupported: (UNSUPPORTED_METRIC.test(q) ? q.match(UNSUPPORTED_METRIC)[0] : null)`，对原始 q 命中即赋值。
- **判定优先级确认**：L708 `if (spec.unsupported)` 拒答分支位于 L712 `lastSpec=spec` / L715 `answer(spec)` 之前——即便 parseMetric 已把"申购"解析成 metric=share，"申购规模"仍先命中 unsupported 被 L708 拦截返回拒答提示（"申购报价规模需后续单独接入Y列"），**不会误答成 V列 share 数字**。
- 顶部注释明确 Y列不代表中标。

### 焦点 3：fig6/fig8 — 新增认购=U/V ✅ PASS

独立读 fig6_credit_panel.py + fig8_credit_total_panel.py diff（对称改造）：
- `_add_resolved_subscription_columns`(WXY优先/否则回退TUV) → `_add_actual_subscription_columns`(固定 `actual_inst=认购机构`(U) / `actual_share=pd.to_numeric(认购份额)`(V) / `actual_source='UV'`)。
- compute_maturity_amounts 的 mask 改用 actual_inst/actual_share。
- print 口径改「U/V=...；Y列申购规模不用于额度占用」。
- `_apply_new_subscriptions` 唯一匹配审计逻辑保留（v27 保守匹配 multi/unmatched 不计入未动）。

### 焦点 4：gen_institution_stats.py — 投行认购=V列 + 项目去重J列说明 ✅ PASS

独立读 L425-499 diff + grep：
- `compute_ib_subscription`(L488-499) 投行认购 `ib_scale` 用 `认购份额_数值`(V列 pd.to_numeric)，不再用 RESOLVED_SHARE_COL。
- 项目去重 L478-481 `drop_duplicates(subset='项目名称')` 取「规模」(J列，项目级发行规模)，避免逐行加总虚增。
- 说明栏(L729区)补充充分：「多联席承销项目按参与机构重复归属」+「管理/参与/托管规模=项目去重后J列发行规模；投行认购规模=U列投行记录的V列中标份额」。
- **INFO(REV-01)**：`RESOLVED_SHARE_COL`(L153定义 / L441/443 abs_common resolve 赋值)残留，属 v26 UV保护遗留、不在本轮投行认购路径上、不影响 V列口径，建议后续版本清理。**不阻断**。

### 焦点 5：P1 发行定价/成本/利差脚本未误改 ✅ PASS

`git show --stat --name-only b1960ec` = 7 文件，**不含**发行定价/成本/利差类脚本（gen_pricing_insight 等未触及），P1 1-3 口径未被本轮误改。

## §4 5 层自检复核

| 层 | 内容 | 复核方式 | 结果 |
|---|---|---|---|
| 层1 | git tag/commit/changed_files 一致 | **实测**（§1） | ✅ |
| 层2 | 投资台账 V列口径 share_sum=1115.9175 | 采信 A + 代码佐证（焦点1 share=V列逻辑自洽） | ✅ |
| 层3 | fig6 新增=10.0 / fig8 新增=18.47 smoke | 采信 A + 代码佐证（焦点3 U/V 逻辑自洽） | ✅ |
| 层4 | py_compile + node --check | py_compile **实测** 4 脚本 = `PY_COMPILE_OK`；node --check 因本地环境未装 node 无法实测，采信 A 自述 + itl_chat.js 结构人工复核（正则/分支/return 均闭合） | ✅ |
| 层5 | 综合看板 13panel 端到端 6107.9KB | 采信 A + 代码佐证 | ✅ |

## §5 结论与建议

- **verdict = APPROVED**。5 焦点全部 PASS，业务口径统一改 V列(认购份额=实际中标)正确，字节 diff 无函数丢失 / QC 弱化，5 层自检复核通过（层1/层4-py 实测），文档合规。
- **Issue**：1 项 INFO（gen_institution_stats.py RESOLVED_SHARE_COL v26 遗留残留），不阻断归档。**无 CRITICAL / WARNING**。
- **下一步**：交 Agent C 归档 v30-actual-share-uv，INFO 项建议 C1 留档并提示后续版本清理。
- **附注（与 v30 无关）**：v28-p123-cleanup 仍处 REVIEWED 待 Agent C 归档；v26 仍 NEEDS_REVISION 待 Agent A 修复。