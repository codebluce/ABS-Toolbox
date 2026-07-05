---
closed_id: C1-v21-bookkeeping-r1
slug: v21-bookkeeping
skill_version: v2.1.0
closed_at: "2026-07-05 12:00:00"
closed_by: agent_c

final_verdict: APPROVED
total_rounds: 1
final_submission: A1-v21-bookkeeping-r1
supersedes_submissions:
  - A1-v21-bookkeeping-r1

all_issues_resolved: true

audit_escape_risks:
  - risk_type: deferred_critical
    description: "技术债 #ABS-002:internal_merge_bookkeeping(gen_institution_stats.py:268)与 run_increment_merge(increment_merge.py:755)并存,接口不兼容(返回值/输入约束/模式/写入方式 4 项差异)。pitfall_log 已如实记录,留第三轮封装层统一处理。本轮 v2.1.0 整合范围仅原样迁入 increment_merge.py,不触碰 internal_merge,等价性已验证,不影响本轮归档。"
    severity: MEDIUM
  - risk_type: deferred_critical
    description: "数据问题逃逸:0626 定稿台账 WXY 旧值与 11 份簿记明细存在不符(QC 7.1 涉及 9 个目标项目 WXY_Y 与明细合计有差异,QC 7.5 金采7-12/耘睿24-10 跨层合并)。新旧 skill 同输入同输出(QC Fails=2 Warns=4 完全一致),系台账数据问题非迁入回归。需用户清理台账或确认明细正确性,不影响 v2.1.0 整合等价性。"
    severity: MEDIUM
  - risk_type: verification_chain_broken
    description: "无验证链断裂。3 个 Issue 中 REV-01/02 在同轮内由 B 自我更正平反(status=RESOLVED),REV-03 为 open INFO(cell 计数口径 50125 vs 64811,0 差异结论一致),不阻断归档。验证链完整。"
    severity: LOW

conditions: []
---

# v21-bookkeeping 归档报告

## 1. 最终结论

**最终判决**: APPROVED(无条件)
**总轮次**: 1
**核心收益**: 簿记录入 v2.1 `increment_merge.py`(1221 行)字节级无损迁入 ABS工具箱,11 个顶层函数 + 17 项 QC 7.1-7.19 全部保留,5 层自检经 Agent B 独立复核全部通过,功能与原 skill 100% 等价、无回归
**是否附条件**: 否

B1 首轮原提 2 项 WARNING,经 B 自身二次独立复核(findstr / git fsck 交叉验证)确认为核查环境假阳性并已平反,verdict 升级为无条件 APPROVED。

## 2. Issue 生命周期全表

| Issue ID | 提出轮次 | 严重程度 | 处理轮次 | 最终状态 |
|---|---|---|---|---|
| REV-v2.1-v21-bookkeeping-r01-01 | r1 | INFO(原 WARNING) | r1 同轮自我更正 | resolved(核查工具假阳性平反) |
| REV-v2.1-v21-bookkeeping-r01-02 | r1 | WARNING | r1 同轮自我更正 | resolved(.git 损坏假阳性平反) |
| REV-v2.1-v21-bookkeeping-r01-03 | r1 | INFO | — | open(仅提示,不阻断) |

### Issue 平反详情

- **REV-01**(原 WARNING → INFO/RESOLVED):首轮误判 `internal_merge_bookkeeping` 函数不存在(0 命中)。findstr 干净复核确认该函数真实存在于 `gen_institution_stats.py:268`(def)且被 `load_data` 在 `:370` 正常调用,pitfall_log #ABS-001/#ABS-002 描述属实。0 命中系 PowerShell Select-String 在 GBK 编码下漏匹配的假阳性。
- **REV-02**(WARNING/RESOLVED):首轮因本地 `.git` 损坏(objects/HEAD 丢失,git 误主仓库)误判 tag 从未创建。仓库恢复后 `git rev-list -n1 audit/v2.1-v21-bookkeeping-r01 → 27f08a8` 确认 tag 真实存在并已双推 gitee/github。
- **REV-03**(INFO/open):A 逐 cell diff 计数 50125(单 sheet 口径 2005×25),B 复核 64811(全 sheet 25 个累加口径),0 差异结论一致。仅提示下轮注明计数口径,不影响等价性。

## 3. 审计逃逸风险分析

- **延期风险**:**技术债 #ABS-002** — `internal_merge_bookkeeping` 与 `run_increment_merge` 并存,接口不兼容 4 项(返回值/输入约束/模式/写入方式)。pitfall_log 已如实记录,留第三轮封装层统一处理。本轮 v2.1.0 整合范围仅原样迁入 `increment_merge.py`,不触碰 `internal_merge`,等价性已 5 层自检验证,**不影响本轮归档**。严重程度 MEDIUM。
- **数据问题逃逸**:0626 定稿台账 WXY 旧值与 11 份明细不符(QC 7.1/7.5 FAIL),新旧 skill 同输入同输出,系台账数据问题非迁入回归。需用户清理台账或确认明细正确性,**不影响 v2.1.0 整合等价性**。严重程度 MEDIUM。
- **验证链断裂**:**无断裂**。3 个 Issue 中 2 个在同轮内由 B 自我更正平反(status=RESOLVED,evidence 完整),1 个 INFO 不阻断归档。验证链完整。严重程度 LOW。
- **superseded 标注**:不适用。仅 1 轮,无 rebase/重写场景。

## 4. 完整轮次时间线

| 轮次 | 送审报告 | 审计意见 | verdict | 日期 |
|---|---|---|---|---|
| r1 | A1-v21-bookkeeping-r1 | B1-v21-bookkeeping-r1 | APPROVED | 2026-07-05 |

### 关键时间点

- 2026-07-05 10:20~10:35 — A 完成 Step 1~7(复制 increment_merge.py + 5 层自检 + SKILL/CHANGELOG/pitfall 更新 + commit + 双推)
- 2026-07-05 11:20 — B 完成 r1 审计,verdict=APPROVED,3 个 Issue(2 WARNING + 1 INFO)
- 2026-07-05 11:20+ — B 自我更正:REV-01/02 经 findstr / git fsck 交叉验证平反为核查环境假阳性,verdict 升级为无条件 APPROVED
- 2026-07-05 12:00 — C 归档

## 5. 经验教训

1. **核查环境假阳性的警示**:B 首轮出现两次假阳性误判(`.git` 损坏 + PowerShell/GBK 编码搜索漏匹配),均经独立交叉验证(findstr /n /c + git fsck)平反。**教训**:核查 git 对象前先 `git fsck` 验证 `.git` 完整性;核查代码存在性用 `findstr /n /c:"..."` 或直接 `read_file` 交叉验证,**勿单一依赖 PowerShell Select-String**。
2. **5 层自检的等价性证明模式**:A 跑 5 层自检(字节对比 + 端到端穿行 + 逐 cell diff + 原 skill smoke + 机构统计回归),B 独立复核每层重跑。这种"双层验证"模式对原样迁入场景非常有效,**可直接复用到后续 slug**(如 v22-pricing / v23-发行定价全流程)。
3. **QC FAIL ≠ 回归**:0626 定稿台账 WXY 旧值与明细不符导致 QC 7.1/7.5 FAIL,但新旧 skill 同输入同输出(QC Fails=2 Warns=4 完全一致),FAIL 系数据问题非回归。**教训**:后续 slug 遇到 QC FAIL 先排查数据(新旧对比),再排查代码。
4. **技术债标记纪律**:`internal_merge` 与 `run_increment_merge` 并存作为 #ABS-002 技术债保留,pitfall_log 如实记录 4 项接口不兼容差异,**不得隐藏**。留第三轮封装层统一处理。
5. **cell 计数口径**:A 单 sheet 口径 50125,B 全 sheet 累加 64811,0 差异结论一致。**教训**:后续送审报告注明计数口径(单 sheet or 全 sheet 累加),避免复核者困惑。
6. **B 自我更正机制有效**:B 首轮误判后,在写 B1 报告过程中自身二次独立复核(findstr / git fsck),主动平反 2 项假阳性并升级 verdict。该机制证明 B 角色的"独立读代码 + 不信任 A 自述"约束有效,避免了 A 被误判 NEEDS_REVISION 的无效返工。

## 6. 代码最终状态

- **git_tag**: `audit/v2.1-v21-bookkeeping-r01`
- **commit_hash**: `27f08a8`
- **abs-toolbox 仓库**: gitee(`ppwupp/abs-toolbox`)+ github(`codebluce/ABS-Toolbox`)双推
- **原 skill 保留**: `skills/簿记录入/v2.1/increment_merge.py`(完整保留,作回滚备份)
- **迁入文件**: `skills/ABS工具箱/scripts/increment_merge.py`(1221 行,与原 skill 字节一致,SHA256 `b6bd1a11...91dd61`)
- **11 个顶层函数保留**: L28(normalize) / L36(unmerge_and_fill_raw) / L70(unmerge_and_fill_processed) / L139(get_all_projects) / L159(get_project_range) / L201(get_layers_in_project) / L219(normalize_rate) / L247(read_detail) / L302(map_detail_to_project) / L346(run_enhanced_qc) / L755(run_increment_merge)
- **17 项 QC 保留**: 7.1-7.19(P0×11 + P1×8 + INFO×1)
- **SKILL.md 触发词路由**: "ABS 簿记录入 / 补充簿记数据 / 增量台账合并" 标 ✅ v2.1.0
- **未触碰文件**: `gen_institution_stats.py`(含 `internal_merge_bookkeeping`,保留不动,#ABS-002 技术债)

### 回滚方案

```bash
# 在 abs-toolbox 仓库:
git revert 27f08a8
git push gitee main && git push github main

# 原 skill skills/簿记录入/v2.1/increment_merge.py 完整保留,可直接使用
```
