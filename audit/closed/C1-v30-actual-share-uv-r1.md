---
closed_id: C1-v30-actual-share-uv-r1
slug: v30-actual-share-uv
skill_version: v2.5.7
closed_at: "2026-07-18 16:50:41"
closed_by: agent_c

final_verdict: APPROVED
total_rounds: 1
final_submission: A1-v30-actual-share-uv-r1
supersedes_submissions:
  - A1-v30-actual-share-uv-r1

all_issues_resolved: true

audit_escape_risks:
  - risk_type: deferred_critical
    description: "无延期 CRITICAL Issue。B1 verdict=APPROVED,唯一 Issue 为 INFO:gen_institution_stats.py 残留 RESOLVED_SHARE_COL 属 v26 UV保护遗留,不在本轮投行认购/实际份额路径上,不影响 V列中标口径。"
    severity: LOW
  - risk_type: verification_chain_broken
    description: "无验证链断裂。该 slug 为首轮,无上一轮 addressed_issues；B1 已核实 tag→commit 一致、changed_files 7 文件一致,并对 5 个业务焦点逐项独立读代码。"
    severity: LOW
  - risk_type: superseded_missing
    description: "无 superseded/rebase 风险。仅 1 轮,最终 tag audit/v2.5.7-v30-actual-share-uv-r01 指向 b1960ec。"
    severity: LOW
  - risk_type: residual_cleanup
    description: "RESOLVED_SHARE_COL 在 gen_institution_stats.py 的定义/赋值为历史兼容残留,当前不影响业务路径,但后续版本应清理以减少误读和审计噪音。"
    severity: LOW

conditions: []
---

# v30-actual-share-uv 归档报告

## 1. 最终结论

**最终判决**: APPROVED  
**总轮次**: 1  
**核心收益**: 将综合看板相关“实际中标/额度占用/投资台账”口径统一为 V列「认购份额」,明确 Y列「申购规模」仅为报价明细,避免把申购报价规模误当实际中标规模。  
**是否附条件**: 否

本轮 B1 审计 verdict=APPROVED,无 CRITICAL/WARNING,仅 1 项 INFO 残留清理建议。A1 与 B1 的 tag、commit、changed_files 均一致,无 v22/v23/v24 曾出现的 commit_hash 误填或文件清单遗漏问题。

## 2. Issue 生命周期全表

| Issue ID | 提出轮次 | 严重程度 | 处理轮次 | 最终状态 |
|---|---|---|---|---|
| REV-v2.5.7-v30-actual-share-uv-r01-01 | r1 | INFO | C1 留档 | resolved:RESOLVED_SHARE_COL 为 v26 UV保护遗留,不在本轮投行认购/实际份额路径,后续版本建议清理 |

### B1 审计结论摘要

- `verdict: APPROVED`
- `conditions: []`
- `issues: 1 INFO, blocks_approval=false`
- 5 个审计焦点全部 PASS:
  1. `gen_investment_ledger.py` 的 2026 投资台账 `share` 固定取 V列「认购份额」,不再使用 `RESOLVED_*_COL`。
  2. `itl_chat.js` 将“申购规模/报价规模/申报规模/投标规模”列为未接入口径并优先拒答,避免误答成 V列实际中标规模。
  3. `fig6_credit_panel.py` / `fig8_credit_total_panel.py` 新增认购固定按 U/V 口径扣减额度,Y列不再参与额度占用。
  4. `gen_institution_stats.py` 投行认购规模改为 U列含投行记录的 V列合计,管理/销售/托管规模继续保留项目去重 J列,说明栏已补充口径。
  5. 本轮未误改发行定价/成本/利差类 P1 脚本。

## 3. 审计逃逸风险分析

- **延期风险**:无延期 CRITICAL Issue。唯一 Issue 为 INFO,且 B1 明确不阻断。C1 将其关闭为“后续清理建议”。
- **验证链断裂**:无验证链断裂。本轮首轮无历史 Issue；B1 已独立核实 tag、changed_files、关键业务路径,并实测 py_compile 通过。
- **superseded 标注**:不适用。仅 1 轮,无 rebase / superseded submission。
- **残留清理风险**:低风险。`gen_institution_stats.py` 中 `RESOLVED_SHARE_COL` 的定义/赋值仍存在,但当前投行认购路径已直接使用 `认购份额_数值`(V列)。残留变量未来可能造成维护者误读,建议后续版本清理并补 grep 断言。
- **node --check 未实测风险**:低风险。B1 因本地无 node 未实测 `itl_chat.js`,但已人工复核正则、unsupported 分支优先级和返回路径；A1 曾声明 node check 通过。后续若 JS 继续改动,建议在 CI/self_check 中加入可选 node 环境检测。

## 4. 完整轮次时间线

| 轮次 | 送审报告 | 审计意见 | verdict | 日期 |
|---|---|---|---|---|
| r1 | A1-v30-actual-share-uv-r1 | B1-v30-actual-share-uv-r1 | APPROVED | 2026-07-18 |

### 关键时间点

- 2026-07-18 15:25 — A 完成 v2.5.7 机构实际规模统一改 V列中标口径,commit `b1960ec`,tag `audit/v2.5.7-v30-actual-share-uv-r01`。
- 2026-07-18 — B 完成 r1 审计,verdict=APPROVED,1 INFO。
- 2026-07-18 — C 归档,将 INFO 残留清理建议留档并关闭。

### B 独立复核关键证据

- tag→commit 一致:`audit/v2.5.7-v30-actual-share-uv-r01` → `b1960ec`。
- changed_files 一致:7 文件,与 A1 声明完全吻合。
- 层 4 `py_compile` 实测 4 个 Python 脚本通过。
- 5 个业务焦点逐项独立读代码 PASS。

## 5. 经验教训

1. **“申购规模”和“认购份额”必须严格分层**:Y列是申购报价明细,代表投资人报价意愿；V列是最终中标/认购份额,代表实际持有和额度占用。综合看板、投资台账、额度监控等实际规模场景必须优先使用 V列。
2. **问答入口要拒答未接入口径**:当用户问“申购规模/报价规模/投标规模”时,如果系统尚未接入 Y列报价明细问答,应明确拒答,不能用 V列实际中标规模替代回答。
3. **局部口径修正优于全局改 resolved 列**:本轮未改 `abs_common` 全局 resolved 逻辑,避免波及发行定价/成本/利差等仍需 WXY 报价分析的模块,审计边界清晰。
4. **项目规模 J列与机构份额 V列并存合理**:管理/销售/托管规模是项目级发行规模,使用项目去重 J列；投行认购和额度占用是机构实际份额,使用 U/V。文档说明必须同步,避免后续再把两类规模混用。
5. **历史兼容残留要及时清理**:`RESOLVED_SHARE_COL` 当前不影响路径,但残留会增加审计噪音。后续小版本可单独清理并加入 grep/py_compile smoke。

## 6. 代码最终状态

- **git_tag**: `audit/v2.5.7-v30-actual-share-uv-r01`
- **commit_hash**: `b1960ec`
- **abs-toolbox 仓库**: gitee(`ppwupp/abs-toolbox`) + github(`codebluce/ABS-Toolbox`)按 B1 §1 已确认 tag/commit 信息一致；C 归档后需再次双推本归档 commit。
- **原 skill 保留**: 本轮在 ABS工具箱主脚本内做口径统一,不涉及原 3 skill 删除。
- **最终修改文件**:
  - `CHANGELOG.md`
  - `scripts/fig6_credit_panel.py`
  - `scripts/fig8_credit_total_panel.py`
  - `scripts/gen_institution_stats.py`
  - `scripts/gen_investment_ledger.py`
  - `scripts/itl_chat.js`
  - `scripts/投资台账_修改指南.md`

### 后续建议

1. 在后续版本清理 `gen_institution_stats.py` 中未使用的 `RESOLVED_SHARE_COL` 定义/赋值。
2. 若后续接入 Y列申购报价问答,应新增独立 metric,并在文档中明确“申购报价规模”和“实际中标规模”的差异。
3. self_check 可增加“V列口径”断言:投资台账 share_sum 等于 V列合计,fig6/fig8 新增认购不读取 Y列。

### 回滚方案

```bash
cd skills/ABS工具箱
git revert b1960ec
git push gitee main && git push github main
```
