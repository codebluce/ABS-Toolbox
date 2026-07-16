---
closed_id: C1-v27-p0-hardening-r1
slug: v27-p0-hardening
skill_version: v2.5.4
closed_at: "2026-07-17 00:01:07"
closed_by: agent_c

final_verdict: APPROVED_WITH_CONDITIONS
total_rounds: 1
final_submission: A1-v27-p0-hardening-r1
supersedes_submissions:
  - A1-v27-p0-hardening-r1

all_issues_resolved: true

audit_escape_risks:
  - risk_type: deferred_critical
    description: "fig8 授信总额度新增认购采用保守匹配策略：唯一匹配才计入，multi/unmatched 不计入以避免重复占用。C 归档核查 0706 定稿发现 fig8 unmatched=7，合计 5.93 亿，其中 6 条 >=0.1 亿；机构包括杭州银行(0.8+0.55)、建信信托(0.9)、国泰海通(1.3)、招商证券(1.0)、中信证券(1.3)、中信建投投顾(0.08)。该策略方向正确但可能使相关机构新增认购少计、剩余额度偏高。建议 v28 扩展匹配规则或在 panel 显示未匹配新增认购合计/明细，让使用者知情。"
    severity: MEDIUM
  - risk_type: deferred_critical
    description: "fig8 日期筛选 mask 当前使用字符串 '2026-07-01' 与已 to_datetime 的簿记时间列比较，当前格式下 pandas 可正确比较，但健壮性弱于显式 pd.Timestamp('2026-07-01')。建议后续统一改为 Timestamp 常量。"
    severity: LOW
  - risk_type: verification_chain_broken
    description: "无验证链断裂。首轮无上一轮 CRITICAL；B1 提出的 2 项 Issue 均 blocks_approval=false，已由 C1 留档关闭。"
    severity: LOW

conditions:
  - "[已核查并留档] fig8 unmatched=7，合计 5.93 亿，含多条 >=0.1 亿记录；作为 MEDIUM audit_escape_risk 留档，建议 v28 扩展匹配规则或展示未计入金额。"
  - "[已留档] 字符串日期比较建议后续统一改为 pd.Timestamp，不阻断归档。"
---

# v27-p0-hardening 归档报告

## 1. 最终结论

**最终判决**: APPROVED_WITH_CONDITIONS  
**总轮次**: 1  
**核心收益**: v2.5.4 P0 防错包完成 4 个高优先级硬化点：QC 7.1/7.2/7.3 真阻断落盘、WXY 三元组整行取舍、fig6/fig8 新增认购唯一匹配审计、#ABS-006 单行表头首行认购补回。B1 独立审计 4 个焦点全 PASS，无 CRITICAL。  
**是否附条件**: 是。2 项非阻断条件已由 C1 留档，其中 fig8 unmatched=7 合计 5.93 亿作为 MEDIUM 逃逸风险记录并建议 v28 扩展。

## 2. Issue 生命周期全表

本轮 2 项 Issue 均为首轮 B1 提出，无上一轮 Issue。

| Issue ID | 提出轮次 | 严重程度 | 处理轮次 | 最终状态 |
|---|---|---|---|---|
| REV-v2.5.4-v27-p0-hardening-r1-01 | r1 | WARNING | r1 同轮(B 审计后 C 归档核查) | open → C1 已核查并留档；unmatched=7 合计 5.93 亿，记 MEDIUM audit_escape_risk，建议 v28 扩展匹配/展示未计入金额 |
| REV-v2.5.4-v27-p0-hardening-r1-02 | r1 | INFO | r1 同轮(B 审计后留档) | open → C1 留档；建议后续字符串日期比较改 pd.Timestamp |

### Issue 详情

- **REV-01**(WARNING/留档): fig6/fig8 `_apply_new_subscriptions()` 仅唯一匹配计入；multi 和 unmatched 不计入并 WARN。该策略避免重复占用，方向保守，但会少计新增认购、使剩余额度偏高。C 归档使用 0706 定稿复核 fig8：总新增记录 23 条，matched=16，unmatched=7，unmatched 合计 5.93 亿。明细为：杭州银行 0.800 亿、杭州银行 0.550 亿、建信信托 0.900 亿、国泰海通 1.300 亿、招商证券 1.000 亿、中信证券 1.300 亿、中信建投投顾 0.080 亿。该风险不推翻本轮硬化逻辑，但建议 v28 增强匹配规则或在 HTML 中披露未计入合计。
- **REV-02**(INFO/留档): fig8 日期筛选在 `df_ledger['簿记时间'] = pd.to_datetime(...)` 后仍用字符串 `'2026-07-01'` 比较。当前 pandas 可隐式比较且现有台账格式通过，但后续建议改为 `pd.Timestamp('2026-07-01')`，减少格式漂移隐患。

## 3. 审计逃逸风险分析

- **延期风险**: 无未处理 CRITICAL。B1 无 CRITICAL Issue；2 项 Issue 均 blocks_approval=false。REV-01 已由 C 核查金额量级并作为 MEDIUM 风险留档，建议 v28 扩展；REV-02 作为 LOW 技术改进留档。
- **验证链断裂**: 无断裂。本 slug 仅 r1，A1 无 addressed_issues；B1 提出 2 项非阻断 Issue，C1 均已逐项留档闭环。
- **superseded 标注**: 不适用。仅 1 轮，无 rebase/重写/替代 submission。
- **fig8 unmatched 审计逃逸风险**: 存在 MEDIUM 风险。保守不计入策略会避免重复扣减额度，但 0706 定稿中未匹配金额 5.93 亿，若这些机构应归入既有授信机构，将导致新增认购少计、剩余额度虚高。后续应优先补充机构别名/硬映射，或在面板中将 unmatched 合计与明细列为提示。

## 4. 完整轮次时间线

| 轮次 | 送审报告 | 审计意见 | verdict | 日期 |
|---|---|---|---|---|
| r1 | A1-v27-p0-hardening-r1 | B1-v27-p0-hardening-r1 | APPROVED_WITH_CONDITIONS | 2026-07-16 |

### 关键时间点

- 2026-07-16 23:34 — A 完成 P0 防错包送审，tag `audit/v2.5.4-v27-p0-hardening-r01` 指向 `c9c2626`。
- 2026-07-16 — B 完成 r1 审计，verdict=APPROVED_WITH_CONDITIONS，4 个审计焦点全 PASS，无 CRITICAL，提出 2 项非阻断 Issue + 1 condition。
- 2026-07-17 00:01 — C 完成归档核查，确认 fig8 unmatched=7 合计 5.93 亿，写入 C1 风险留档。

### B 独立复核关键证据

- **QC 真阻断架构**: `increment_merge.py` 中 `qc_fails>0 → os.remove(tmp_path) → return`，仅 PASS 分支 `os.rename(tmp_path, output_path)`，全程无 `wb.save`，从架构上规避 v26 REV-01「save 在 QC 前」导致阻断无效的同类风险。
- **WXY 三元组整行取舍**: `abs_common.py` 使用 `wxy_complete==3` 统一 `.where`，三元组完整才使用 W/X/Y，部分缺失整行回退 T/U/V，消除逐列 `fillna` 拼接。
- **fig6/fig8 保守匹配**: 唯一匹配才计入；multi 不计入并 WARN，避免重复占用；unmatched 大额 WARN，暴露漏计风险。
- **#ABS-006 修复**: `iloc[2:]` 改 `iloc[1:]`，符合当前单行表头定稿台账结构，补回首行真实认购记录。

## 5. 经验教训

1. **QC 阻断最好用临时文件 + 原子 rename**: v26 的问题根源是先 `save` 后 QC，本轮改为临时文件通过 QC 后再 `rename`，从架构上避免「FAIL 时文件已落盘」。后续涉及写文件的脚本应优先采用该模式。
2. **多列业务三元组不能逐列 fallback**: WXY 穿透字段代表一个整体事实，逐列 `fillna` 会产生「机构来自穿透、规模来自表面」的拼接假数据。凡是语义绑定字段，都应整体完整才采用，否则整行回退。
3. **保守不重复与漏计风险要同时披露**: fig6/fig8 对 multi/unmatched 不计入能防止重复扣减额度，但也会造成剩余额度偏高。后续面板既要避免自动误匹配，也要把未计入金额透明展示给使用者。
4. **单行/多行表头假设必须写清楚**: #ABS-006 说明 `iloc[2:]` 这种历史假设会在表头结构变化后悄悄漏掉首行数据。后续读取 Excel 应显式识别表头结构或在代码注释中标明输入版本假设。
5. **非阻断 Issue 也要量化核查**: B1 的 condition 要求确认 unmatched 金额量级。C 归档不能只复述，应实际跑脚本量化，本轮核查得出 5.93 亿并据此标 MEDIUM 风险。

## 6. 代码最终状态

- **git_tag**: `audit/v2.5.4-v27-p0-hardening-r01`
- **tag commit_hash**: `c9c2626`
- **B 审计提交**: `d44faf2`(B1 审计意见 + INDEX/state 更新，gitee + github 已双推)
- **abs-toolbox 仓库**: gitee(`ppwupp/abs-toolbox`) + github(`codebluce/ABS-Toolbox`)双推
- **原 skill 保留**: 本轮为 ABS工具箱主代码 P0 防错增强，不替换原 3 个 skill；原 skill 仍作回滚备份。
- **修改文件**(A1 声明与 git show c9c2626 一致，共 8 文件):
  - `CHANGELOG.md`
  - `pitfall_log.md`
  - `scripts/abs_common.py`
  - `scripts/fig6_credit_panel.py`
  - `scripts/fig8_credit_total_panel.py`
  - `scripts/increment_merge.py`
  - `scripts/lab/fig4_new_welizhi_matrix.py`
  - `scripts/lab/load_data.py`

### 回滚方案

```bash
# 在 abs-toolbox 仓库:
git revert c9c2626
git push gitee main && git push github main
```
