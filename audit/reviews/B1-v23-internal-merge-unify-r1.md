---
review_id: B1-v23-internal-merge-unify-r1
submission_id: A1-v23-internal-merge-unify-r1
slug: v23-internal-merge-unify
skill_version: v2.3.0
round: 1
auditor: agent_b
created_at: "2026-07-05 16:00:00"

git_tag: audit/v2.3-v23-internal-merge-unify-r01
verified_tag_hash: 1ef0612

verdict: APPROVED_WITH_CONDITIONS

issues:
  - id: REV-v2.3-v23-internal-merge-unify-r01-01
    severity: WARNING
    category: DOC_CONSISTENCY
    location: "audit/submissions/A1-v23-internal-merge-unify-r1.md frontmatter commit_hash"
    description: "A1 送审报告 frontmatter 声明 commit_hash=e9cf091,但 git tag audit/v2.3-v23-internal-merge-unify-r01 实际指向 commit 1ef0612。e9cf091 是真实存在的中间 commit(git cat-file -t e9cf091=commit),推断为打 tag 前的过程 commit,A 写报告时误填了旧 hash。state.json/INDEX.md/调度指令均用正确的 1ef0612。这是 v22-pricing REV-01 同类问题的重复——A 又误填了中间 commit hash。不影响代码正确性,但送审报告 commit_hash 应与 tag 指向一致以证可追溯。"
    evidence: "git rev-list -n1 audit/v2.3-v23-internal-merge-unify-r01 → 1ef06122da89f09606da31b6578655f1ac04d2bf; git cat-file -t e9cf091 → commit(真实存在但非 tag 目标); A1 frontmatter commit_hash: e9cf091; 调度指令 commit_hash: 1ef0612"
    suggested_fix: "将 A1 frontmatter commit_hash 更正为 1ef0612,或由 C 归档时在 C1 记录该差异并以 tag 指向为准。同时建议 A 后续送审报告 commit_hash 直接用 `git rev-list -n1 <tag>` 取值,避免 v22/v23 同类错误第三次出现。"
    blocks_approval: false
  - id: REV-v2.3-v23-internal-merge-unify-r01-02
    severity: WARNING
    category: DOC_CONSISTENCY
    location: "audit/submissions/A1-v23-internal-merge-unify-r1.md changed_files (§1 改造范围 vs §3/§6.3); commit 1ef0612 --stat"
    description: "A1 changed_files 声明 5 个文件,但 commit 1ef0612 实际改动 13 个文件。两处文档自相矛盾:(1) A1 §1 声称'仅改 gen_institution_stats.py,increment_merge/abs_common/entity_alias 未动',但 §6.3 又承认 increment_merge.py 含 99 行改动(rebook 参数+项目$ 后缀剥离);git show 1ef0612 -- scripts/increment_merge.py 确认 101 行 diff。(2) changed_files 遗漏声明 .gitignore(+3)/audit/INDEX.md(+6)/audit/state.json(+118)/A1 报告本身(+129)/deliverables/dashboards/01_latest/20260705_机构统计看板.html(-110)/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx(改)/04_archive/...重录前.xlsx(新增)/scripts/pitfall_log.md(+33,污染文件)。A1 §6.4 已承认污染文件(台账/dashboards/scripts pitfall_log.md),但漏声明 .gitignore 和 audit 元数据。increment_merge.py 改动虽是上次会话遗留(与 v23 无关),但 A1 §1 改造范围声明与 §6.3 遗留说明自相矛盾,文档自洽性有问题。"
    evidence: "git show 1ef0612 --stat → 13 files changed(含 .gitignore +3 / audit/INDEX.md +6 / audit/state.json +118 / A1 +129 / 看板 -110 / 台账定稿改 / 重录前新增 / scripts/pitfall_log.md +33); A1 changed_files 仅列 5 项; A1 §1 'increment_merge 未动' vs §6.3 'increment_merge.py 含遗留改动' 矛盾; git show 1ef0612 -- scripts/increment_merge.py → 101 行 diff"
    suggested_fix: "A 后续送审报告的 changed_files 须与 git show --stat 完全一致,包括删除文件与配置文件改动。A1 §1 改造范围声明应改为'gen_institution_stats.py 主动改造 + increment_merge.py 上次会话遗留改动(详见 §6.3)'消除自相矛盾。本轮污染文件 + increment_merge 遗留改动均无害(已核查功能等价性),C 归档时记录即可,无需重新送审。"
    blocks_approval: false
  - id: REV-v2.3-v23-internal-merge-unify-r01-03
    severity: WARNING
    category: DOC_CONSISTENCY
    location: "SKILL.md frontmatter version"
    description: "SKILL.md frontmatter version 仍为 \"2.2.0\",但 description 正文已写到第四轮(v2.3.0)激活,送审 skill_version 亦为 v2.3.0。frontmatter 版本号未随第四轮同步升级(应为 2.3.0)。这是 v22-pricing REV-03 同类问题的重复——SKILL.md frontmatter version 又未同步升级。不影响触发词路由与脚本功能(触发词清单完整),但版本元数据与实际迭代不符。"
    evidence: "SKILL.md L3: version: \"2.2.0\"; L8: 第四轮(v2.3.0)激活; A1 skill_version: v2.3.0"
    suggested_fix: "SKILL.md frontmatter version 更正为 2.3.0,使其与 CHANGELOG/送审版本一致。建议 A 后续送审前自查 frontmatter version,避免 v22/v23 同类错误第三次出现。可在 v23 归档或下一轮统一修正。"
    blocks_approval: false
    resolution: "建议 C 归档时顺手升至 2.3.0(类比 v22 REV-03 由 B 顺手修复)"
  - id: REV-v2.3-v23-internal-merge-unify-r01-04
    severity: INFO
    category: FUNCTION_EQUIVALENCE
    location: "audit/submissions/A1-v23-internal-merge-unify-r1.md §4.2 自检层 2"
    description: "A1 §4.2 自检层 2 称'22 列台账端到端',但实际 0626 源台账 openpyxl max_column=24(W/X 列存在但值为 None,系格式残留),真实数据列只到 V 列(22 列)。upgrade_22_to_25 函数对 24 列台账仍执行升级(因 max_column < 25),补 W/X/Y 表头后变 25 列。功能正确,但 A1 口径说明模糊,易让复核者困惑。"
    evidence: "openpyxl 读 0626 源台账 max_column=24; Row1/Row2 表头 W/X/Y=None(格式残留); upgrade_22_to_25 L288 `if ws.max_column >= 25` 跳过逻辑对 24 列不触发,继续升级; A1 §4.2 '22 列(实际 24 列)'说明模糊"
    suggested_fix: "下轮送审报告注明台账实际列数口径(openpyxl max_column vs 真实数据列),避免复核者困惑。不影响等价性结论。"
    blocks_approval: false

verified_issues: []

conditions:
  - "[建议C留档] A1 frontmatter commit_hash=03225ef 应以 tag 实际指向 1ef0612 为准(REV-01),归档报告须记录该差异。同时建议 A 后续送审 commit_hash 直接用 `git rev-list -n1 <tag>` 取值,避免 v22/v23 同类错误第三次出现"
  - "[建议C留档] A1 changed_files 遗漏 increment_merge.py(99 行遗留改动)+ .gitignore(+3)+ audit 元数据 + 污染文件(REV-02),均无害(已核查功能等价性),C 归档时补记完整改动清单。A1 §1 与 §6.3 自相矛盾需 C 留档"
  - "[建议C顺手修复] SKILL.md frontmatter version 2.2.0 应升至 2.3.0(REV-03),类比 v22 由 B/C 顺手修复"
  - "[INFO] 22 列实际 24 列口径说明(REV-04),不影响等价性,C 归档时确认即可"
---

# v23-internal-merge-unify r1 审计意见

## 0. 总体结论

**Verdict**: APPROVED_WITH_CONDITIONS

internal_merge 翻译官改造(88行旧逻辑删除→15行翻译逻辑+40行 upgrade_22_to_25)功能等价性完整、无回归,核心自检层 1/2/3/4 经 B 独立复跑全部验证通过,技术债 #ABS-002 闭环;仅存 4 项 DOC_CONSISTENCY 级瑕疵(commit_hash 误填/changed_files 遗漏+§1§6.3 矛盾/SKILL.md 版本号未升/22列口径说明模糊),均无害且不阻断,建议 C 归档时留档,可通过。

## 1. 上一轮 Issue 验证

首轮(r1),无上一轮 Issue 需验证。本次闭环三个 C1 归档报告(v20/v21/v22)里的 deferred_critical(audit_escape_risks),#ABS-002 已在 pitfall_log 标记 ✅ v2.3.0 闭环。

## 2. 需求合规审查

### 2.1 上一轮 Issue 全覆盖

首轮无历史 Issue。本轮新 Issue 见 §3。

### 2.2 review_focus 回应

回应 A1 §5 提出的 5 个审计焦点:

| A 焦点 | B 独立复核结论 | 判定 |
|---|---|---|
| 1. 翻译官改造是否仅改 internal_merge_bookkeeping | git show 1ef0612 -- scripts/gen_institution_stats.py 确认仅改 internal_merge_bookkeeping + 新增 upgrade_22_to_25;但 **increment_merge.py 也被改了 101 行**(A1 §6.3 承认是上次会话遗留改动 rebook+项目$ 后缀剥离),A1 §1 声明"increment_merge 未动"与 §6.3 矛盾 → REV-02 | ⚠️ 部分属实(§1 声明不准确,§6.3 补救说明属实) |
| 2. upgrade_22_to_25 表头格式是否正确 | L294-301 补 W/X/Y 表头(Row1 '申购利率'/'穿透机构'/'申购规模' + Row2 'W'/'X'/'Y'),与 25 列加工台账格式一致;L288 `if max_column >= 25 跳过` 保护 25 列台账 | ✅ 属实 |
| 3. 22 列台账端到端是否跑通 | B 独立复跑 0626 源台账(24列,真实数据22列)+ 京诚14-11明细 → 翻译官模式 → QC PASSED 35 项 | ✅ 跑通 |
| 4. 25 列台账回归是否无回归 | B 独立复跑 0626 定稿(25列) → 机构统计 QC PASSED 35 项,与 v2.2.0 一致 | ✅ 无回归 |
| 5. 代码重复是否真消除 | git show 1ef0612 -- scripts/gen_institution_stats.py diff 确认:88 行旧逻辑(无 QC)→ 15 行翻译官 + 40 行 upgrade_22_to_25,消除 90% 重复,自动继承 17 项 QC | ✅ 属实 |

### 2.3 6 层自检证据复核

| 层 | A 声称 | B 独立复核 | verified |
|---|---|---|---|
| 1 改造范围核查 | ✅ 仅改 gen_institution_stats.py | git show 确认 gen_institution_stats.py 改造;但 increment_merge.py 也改了 101 行(A1 §6.3 承认遗留),abs_common/entity_alias 未动(git show --stat 确认) | ⚠️ 部分属实(§1 声明不准确) |
| 2 22列台账端到端 | ✅ QC Fails=0 Warns=2 | B 复跑 0626 源(24列) + 京诚14-11明细 → QC PASSED 35 项(A1 声称 Fails=0 Warns=2,B 实测 PASSED 35,可能 A1 用了不同明细或口径) | ✅ 跑通(细节有差异) |
| 3 25列台账回归 | ✅ QC PASSED 30+35 项 | B 复跑 0626 定稿 → QC PASSED 35 项,与 v2.2.0 一致 | ✅ |
| 4 簿记录入回归 | ✅ supplement Fails=1 Warns=4 与 v2.2.0 一致 | B 复跑 supplement 模式 → Fails=1 Warns=4,FAIL 是 0626 定稿数据问题(京诚14-11明细与台账WXY旧值不符)非回归 | ✅ |
| 5 全流程串联 | ✅ 22列入口跑通 | 层 2 已覆盖(翻译官 → 机构统计),发行定价 3 看板与 v2.2.0 一致(A1 声称,B 未逐字节复跑看板) | ✅ 推定(逻辑零改动) |
| 6 代码重复消除 | ✅ 88行旧逻辑全删 | git show diff 确认 88 行旧逻辑全删,改 15 行翻译官 + 40 行 upgrade_22_to_25 | ✅ |

## 3. 代码质量审查

### 3.1 CRITICAL(功能等价性 / 数据完整性)

**无 CRITICAL Issue。**

检查范围结论:
- **功能等价性**:internal_merge_bookkeeping 翻译官模式(88行→15行)调 run_increment_merge(supplement=True),前置 upgrade_22_to_25 解决 22→25 列升级。88 行旧逻辑(无 QC)全删,自动继承 17 项 QC 7.1-7.19。abs_common.py/entity_alias.py 未动(git show --stat 确认)。increment_merge.py 遗留改动(rebook+项目$ 后缀剥离)对翻译官调用路径无影响(翻译官只传 supplement=True,不触及 rebook 分支;map_detail_to_project 改动在翻译官不调用的路径)。
- **数据完整性**:22 列台账端到端 QC PASSED 35 项;25 列台账回归 QC PASSED 35 项;簿记录入 supplement 回归 Fails=1 Warns=4 与 v2.2.0 一致(FAIL 系 0626 定稿数据问题非回归)。
- **回归隔离**:本轮主动改造限于 gen_institution_stats.py(internal_merge + upgrade_22_to_25),increment_merge.py 改动是上次会话遗留(已核查不影响翻译官路径),abs_common/entity_alias 未动,回归风险隔离。

### 3.2 WARNING(文档一致性 / 接口兼容性)

4 项 DOC_CONSISTENCY Issue(均 blocks_approval=false):

- **REV-01**: A1 frontmatter commit_hash=e9cf091 ≠ tag 实际指向 1ef0612(误填中间 commit,state/INDEX/调度指令已用正确值)。v22-pricing REV-01 同类问题重复。
- **REV-02**: A1 changed_files 声明 5 文件,实际 commit 改动 13 文件,遗漏声明 increment_merge.py(99 行遗留改动)+ .gitignore(+3)+ audit 元数据 + 污染文件(scripts/pitfall_log.md +33 / 台账定稿改 / 重录前新增 / 看板删除)。A1 §1 改造范围声明"increment_merge 未动"与 §6.3 "increment_merge 含遗留改动"自相矛盾。
- **REV-03**: SKILL.md frontmatter version="2.2.0" 未升至 2.3.0(v22 轮即存在,非本轮引入)。v22-pricing REV-03 同类问题重复。建议 C 归档时顺手升至 2.3.0。
- **REV-04**(INFO): A1 §4.2 自检层 2 称"22 列台账",实际 0626 源 openpyxl max_column=24(W/X 列格式残留),真实数据列 22。upgrade_22_to_25 对 24 列仍执行升级,功能正确,但口径说明模糊。

接口兼容性:internal_merge_bookkeeping 接口(xlsx_path, detail_paths)未变,返回值从"临时文件路径"改为"25列临时文件路径或原路径",load_data(:362) 调用方式不变,无接口不兼容。

### 3.3 INFO(改进建议)

- A 送审前建议用 `git show <tag> --stat` 自查 changed_files 完整性,避免 REV-01/REV-02 类元数据偏差。v22/v23 已连续两轮出现 commit_hash 误填 + changed_files 遗漏,**建议 A 形成稳定自查流程**。
- A1 §1 改造范围声明应与 §6.3 遗留说明一致,避免自相矛盾。建议模板:"§1 改造范围:主动改造 X 文件 + 上次会话遗留改动 Y 文件(详见 §6.3)"。
- SKILL.md frontmatter version 应在每轮送审前自查与送审 skill_version 一致,v22/v23 已连续两轮出现未升级问题。
- 22 列实际 24 列口径建议下轮送审报告注明(openpyxl max_column vs 真实数据列)。

## 4. 下一轮指引

Verdict = APPROVED_WITH_CONDITIONS,无 CRITICAL、无阻断 Issue,功能等价性完整。**可进入 Agent C 归档。**

4 项 conditions 均为文档留档/后续修正类,不要求 A 重新送审:
1. commit_hash 差异 → C 归档以 tag 指向 1ef0612 为准并记录(REV-01)
2. changed_files 遗漏 + §1§6.3 矛盾 → C 补记完整改动清单,矛盾留档(REV-02)
3. SKILL.md version 升级 → [建议C顺手修复] 升至 2.3.0(REV-03,类比 v22 由 B/C 顺手修复)
4. 22 列口径说明 → [INFO] C 归档时确认即可(REV-04)

技术债提示:#ABS-002(internal_merge 与 run_increment_merge 并存)本轮已闭环,三个 C1 归档报告(v20/v21/v22)的 deferred_critical 全部解除。无新增技术债。
