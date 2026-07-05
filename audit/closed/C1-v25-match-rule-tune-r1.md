---
closed_id: C1-v25-match-rule-tune-r1
slug: v25-match-rule-tune
skill_version: v2.5.0
closed_at: "2026-07-05 21:30:00"
closed_by: agent_c

final_verdict: APPROVED_WITH_CONDITIONS
total_rounds: 1
final_submission: A1-v25-match-rule-tune-r1
supersedes_submissions:
  - A1-v25-match-rule-tune-r1

all_issues_resolved: true

audit_escape_risks:
  - risk_type: deferred_critical
    description: "经验值观察期:Pass 4 核心名匹配 len(inst_core)>=3 阈值与 MATCH_HARD_MAP 当前 2 条映射均为经验值,需业务台账积累 1-2 周观察。当前 0703/0626 台账未见误匹配(2字核心名如'利曦/中信/长江'一律不达阈值走 hard_map 兜底,3字以上才走核心名匹配),但长期可能出现新难匹配 case 需扩展 hard_map。建议后续发现新 case 时,在 MATCH_HARD_MAP 加双向映射 + 在 pitfall_log 记录。本轮不阻断归档,机制设计有效。"
    severity: MEDIUM
  - risk_type: deferred_critical
    description: "层 2-5 台账端到端自检未由 B 重跑(采信 A 输出)。B 仅独立复核层 1/6(读代码确认改造范围 + 默认 rebook 行为),层 2-5(0703台账QC/25列回归/发行定价回归/22列全流程)采信 A 自检输出。这是 v20-v24 一致惯例(B 不重跑业务台账),但若后续台账匹配出现回归需重新走 B 流程。本轮 A1 §4.3/6.2 输出证据完整(Pass3 hard_map 利曦 + Pass1 精确 中信建投-衍生品 + QC Fails=0),采信合理。"
    severity: LOW
  - risk_type: verification_chain_broken
    description: "无验证链断裂。2 项 Issue(REV-01 changed_files 口径 + REV-02 阈值观察)均 blocks_approval=false,在 r1 同轮内由 B 提出并留档,验证链完整。"
    severity: LOW

conditions:
  - "[已留档] A1 changed_files 声明 3 文件,git show ae1907e --stat 实际 4 文件(多送审报告 A1-*.md 自身 +184 行)。送审报告入 commit 属业界惯例,清单口径瑕疵,C1 补记完整清单"
  - "[已留档/延期观察] Pass 4 len>=3 阈值与 MATCH_HARD_MAP 当前 2 条为经验值,建议业务观察 1-2 周,发现新难匹配 case 再扩展 hard_map"
---

# v25-match-rule-tune 归档报告

## 1. 最终结论

**最终判决**: APPROVED_WITH_CONDITIONS
**总轮次**: 1
**核心收益**: 基于 0703 台账实测发现 2 个真实匹配失败 case(利曦基金 vs 利曦私募基金 / 中信建投-衍生品 vs 中信建投衍生品),通过 5 处改造解决:normalize 去 -//／ + 修复全角空格 bug + 新增 core_name() 函数(去后缀) + 新增 MATCH_HARD_MAP 显式映射 + Pass 1-4 优先级链(精确→包含→hard_map→核心名)+ rebook 设为默认模式(幂等)。6 层自检全部通过,2 个原失败 case 验证匹配成功(QC Fails=0,对比 v2.4.0 supplement 模式 Fails=2)
**是否附条件**: 是(2 项 conditions,1 项文档留档 + 1 项 INFO 延期观察)

## 2. Issue 生命周期全表

本轮 2 项 Issue 均为首轮提出,无上一轮 Issue:

| Issue ID | 提出轮次 | 严重程度 | 处理轮次 | 最终状态 |
|---|---|---|---|---|
| REV-v2.5-v25-match-rule-tune-r01-01 | r1 | WARNING | r1 同轮(B 审计后留档) | open→留档(C1 补记 changed_files 完整清单 4 文件) |
| REV-v2.5-v25-match-rule-tune-r01-02 | r1 | INFO | r1 同轮(B 审计后留档) | open→留档/延期(Pass4 阈值与 hard_map 业务观察 1-2 周) |

### Issue 详情

- **REV-01**(WARNING/留档): A1 changed_files 声明 3 文件(increment_merge.py + SKILL.md + CHANGELOG.md),git show ae1907e --stat 实际 4 文件(多送审报告 A1-v25-match-rule-tune-r1.md 自身 +184 行)。送审报告入 commit 属业界惯例,清单口径瑕疵。**不影响代码正确性**,C1 §6 补记完整清单。
- **REV-02**(INFO/延期): Pass 4 核心名匹配 len(inst_core)>=3 阈值与 MATCH_HARD_MAP 当前 2 条映射均为经验值。当前 0703/0626 台账未见误匹配(2字核心名一律走 hard_map 兜底,机制有效),但长期需业务观察 1-2 周,发现新难匹配 case 再扩展 hard_map。

### 本轮亮点(B1 §3.2 提出)

- **commit 洁净性显著改善**:本轮 commit 仅含 4 文件(3 代码 + 送审报告),**未混入 abs_common.py/entity_alias.py/gen 脚本/业务台账**。较 v22/v23/v24 连续三轮元数据失真(遗漏声明/多列/误报),本轮 §5 污染文件声明与 git show 实际一致,**予以认可**。
- **5 处改动全部真实**:git show ae1907e 逐行核查,normalize 去连字符+全角空格 bug 修复+core_name 有防削空保护(len(n)>len(suffix))+ MATCH_HARD_MAP 双向映射+Pass 1-4 优先级链守卫顺序正确(L1093/1100/1111/1127)+ rebook 默认互斥校验向后兼容。

## 3. 审计逃逸风险分析

- **经验值观察期**:Pass 4 len>=3 阈值与 MATCH_HARD_MAP 当前 2 条映射均为经验值,需业务台账积累 1-2 周观察。当前 0703/0626 台账未见误匹配(2字核心名如"利曦/中信/长江"一律不达阈值走 hard_map 兜底,3字以上才走核心名匹配),但长期可能出现新难匹配 case 需扩展 hard_map。建议后续发现新 case 时,在 MATCH_HARD_MAP 加双向映射 + 在 pitfall_log 记录。**本轮不阻断归档**,机制设计有效。严重程度 MEDIUM。
- **层 2-5 自检采信 A 输出**:B 仅独立复核层 1/6(读代码确认改造范围 + 默认 rebook 行为),层 2-5(0703台账QC/25列回归/发行定价回归/22列全流程)采信 A 自检输出。这是 v20-v24 一致惯例(B 不重跑业务台账),但若后续台账匹配出现回归需重新走 B 流程。本轮 A1 §4.3/6.2 输出证据完整(Pass3 hard_map 利曦 + Pass1 精确 中信建投-衍生品 + QC Fails=0),采信合理。严重程度 LOW。
- **验证链断裂**:**无断裂**。2 项 Issue(REV-01 changed_files 口径 + REV-02 阈值观察)均 blocks_approval=false,在 r1 同轮内由 B 提出并留档,验证链完整。严重程度 LOW。
- **superseded 标注**:不适用。仅 1 轮,无 rebase/重写场景。

## 4. 完整轮次时间线

| 轮次 | 送审报告 | 审计意见 | verdict | 日期 |
|---|---|---|---|---|
| r1 | A1-v25-match-rule-tune-r1 | B1-v25-match-rule-tune-r1 | APPROVED_WITH_CONDITIONS | 2026-07-05 |

### 关键时间点

- 2026-07-05 20:30 — A 完成代码改造 + 6 层自检 + commit + 打 tag
- 2026-07-05 21:10 — B 完成 r1 审计,verdict=APPROVED_WITH_CONDITIONS,2 项 Issue(1 WARNING + 1 INFO,均不阻断)
- 2026-07-05 21:30 — C 归档

### B 独立复核关键证据

- **5 处改动经 git show ae1907e 逐行核查全部真实**:
  - normalize 去 -//／(L? replace 链)
  - 全角空格 bug 修复(重复 replace "　")
  - core_name() 函数(有 len(n)>len(suffix) 防削空保护)
  - MATCH_HARD_MAP 双向映射({"利曦基金": "利曦私募基金", ...})
  - Pass 1-4 优先级链守卫(L1093 初始化→L1100 Pass2 守卫→L1111 Pass3 守卫→L1127 Pass4 守卫,顺序正确)
  - rebook 默认互斥校验向后兼容(--supplement/--new-raw 分支保留)
- **0703 台账 rebook 测试**:QC Fails=0 Warns=3(对比 v2.4.0 supplement 模式 Fails=2),2 个原失败 case 全部解决
  - `[Pass3 hard_map] 利曦私募基金 -> 利曦基金 (Row1838)`
  - `MATCH: 中信建投-衍生品 -> Row1847`(normalize 去连字符后 Pass 1 精确匹配)

## 5. 经验教训

1. **基于真实失败 case 驱动改造**:本轮基于 0703 台账实测发现的 2 个真实匹配失败 case(利曦基金/中信建投-衍生品)驱动改造,而非空想。**教训**:匹配规则调优应有真实失败 case 支撑,避免过度工程化。
2. **优先级链设计模式**:Pass 1-4(精确→包含→hard_map→核心名)优先级链清晰,每个 Pass 有 `if matched_ur_idx is None` 守卫,前三 Pass 全落空才触发下一 Pass。**教训**:匹配逻辑应分层优先级,精确匹配优先,模糊匹配兜底,显式 hard_map 兜底难匹配 case。
3. **核心名 len>=3 阈值防误匹配**:2 字核心名(利曦/中信/长江)一律不达阈值走 hard_map 兜底,3 字以上才走核心名匹配。**教训**:模糊匹配应有最小长度阈值,避免短名误匹配(如"中信"匹配"中信证券"和"中信建投")。
4. **core_name 防削空保护**:core_name 函数有 `len(n)>len(suffix)` 保护,避免去后缀后削空(如"基金"→"")。**教训**:字符串处理应有边界保护,避免异常输入导致空值。
5. **MATCH_HARD_MAP 双向映射**:利曦基金↔利曦私募基金 双向映射,任一方向都能匹配。**教训**:难匹配 case 的 hard_map 应双向,避免方向性遗漏。
6. **rebook 设为默认模式**:rebook 幂等(清空+重录),避免 supplement 多次跑累积脏行。**教训**:幂等模式应作为默认,降低用户使用门槛,避免重复跑产生脏数据。
7. **commit 洁净性改善**:本轮 commit 仅含 v25 相关 4 文件,未混入其他 modified 脚本和业务台账。**教训**:A 送审 commit 应严格隔离 v25 相关文件,其他遗留改动单独 commit 标"上次会话遗留",避免污染。
8. **B 采信 A 自检输出的惯例**:层 2-5 台账端到端自检采信 A 输出(B 不重跑业务台账),这是 v20-v24 一致惯例。**教训**:B 复核方式应明确声明(读代码 vs 重跑台账),避免模糊。若后续台账匹配出现回归,需重新走 B 流程重跑台账。

## 6. 代码最终状态

- **git_tag**: `audit/v2.5-v25-match-rule-tune-r01`
- **commit_hash**: `ae1907e`(tag 实际指向,A1 frontmatter 一致,未重复 v22/v23 误填)
- **abs-toolbox 仓库**: gitee(`ppwupp/abs-toolbox`)+ github(`codebluce/ABS-Toolbox`)双推
- **原 skill 保留**: 本轮改造基于 ABS工具箱 `scripts/increment_merge.py`(v2.1 迁入版),原 skill `skills/簿记录入/v2.1/increment_merge.py` 保留不动
- **修改文件**(commit ae1907e 实际 4 文件,A1 changed_files 声明 3 文件,C1 补记):
  - `skills/ABS工具箱/scripts/increment_merge.py`(+65/-6,5 处改动)
    - normalize 去 -//／ + 修复全角空格 bug
    - 新增 INST_SUFFIXES + core_name() 函数(有 len(n)>len(suffix) 防削空保护)
    - 新增 MATCH_HARD_MAP 双向映射({"利曦基金": "利曦私募基金", ...})
    - Pass 1-4 优先级链守卫(L1093/1100/1111/1127)
    - CLI 默认 rebook 模式(向后兼容 --supplement/--new-raw)
  - `skills/ABS工具箱/SKILL.md`(版本升 v2.5.0,加第六轮激活说明,+4/-2)
  - `skills/ABS工具箱/CHANGELOG.md`(加 v2.5.0 段,+35)
  - `skills/ABS工具箱/audit/submissions/A1-v25-match-rule-tune-r1.md`(送审报告自身,+184,A1 changed_files 遗漏声明,C1 补记)
- **未纳入 v25 commit 的遗留改动**(A1 §5 声明留单独 commit 标"上次会话遗留"):
  - `scripts/abs_common.py`(v24 综合看板相关)
  - `scripts/entity_alias.py`(v24 上银浦东分行补充)
  - `scripts/gen_abs_cost_report.py` / `gen_compare_tool.py` / `gen_spread_report.py`(v22 迁入后路径调整)
  - 业务台账文件(0703 定稿等)

### 5 处改造的 Pass 1-4 优先级链

```
Pass 1: 精确匹配(normalize 后 ==)
Pass 2: 包含匹配(len>=4,xn in un or un in xn)
Pass 3: hard_map 显式映射(MATCH_HARD_MAP 双向)
Pass 4: 核心名匹配(core_name len>=3,去后缀后 ==)
```

### 回滚方案

```bash
# 在 abs-toolbox 仓库:
git revert ae1907e
git push gitee main && git push github main

# 原 v2.4.0 行为完全保留,rebook 默认模式回退为 parser.error
```
