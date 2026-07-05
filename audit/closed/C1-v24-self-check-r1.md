---
closed_id: C1-v24-self-check-r1
slug: v24-self-check
skill_version: v2.4.0
closed_at: "2026-07-05 17:30:00"
closed_by: agent_c

final_verdict: APPROVED_WITH_CONDITIONS
total_rounds: 1
final_submission: A1-v24-self-check-r1
supersedes_submissions:
  - A1-v24-self-check-r1

all_issues_resolved: true

audit_escape_risks:
  - risk_type: deferred_critical
    description: "延期验证:auto 模式在原 skill 真实缺失时自动切 degraded 的分支未在真实缺失场景实测(REV-04)。原 skill 存在时无法触发该分支,只能用 --mode degraded 模拟测试(PASS=2 SKIP=3 已验)。建议原 skill 退役时(约 6 个月观察期结束后)做一次真实缺失场景实测,记为延期验证项。本轮不阻断归档,因 degraded 强制模式已验接口逻辑正确。"
    severity: MEDIUM
  - risk_type: deferred_critical
    description: "5 层自检脚本本身未经长期回归验证。v24 自检脚本作为 v25+ 后续 slug 迁入的标准回归验证工具,本身需要长期使用才能验证稳定性(基线快照对比、配置驱动扩展、降级模式真实场景)。建议在 v25+ 至少 2 个 slug 上实际使用后,再考虑将其作为强制前置自检流程。本轮 v24 仅用 v20/v21/v22/v23 四个历史 slug 跑过验证,全部 PASS,但未覆盖新 slug 场景。"
    severity: MEDIUM
  - risk_type: deferred_critical
    description: "QC 基线快照对比未实现。A1 §5 review_focus 提出'是否应该把 0626 数据的 QC 基线写入快照,后续跑出 FAIL 时对比基线',本轮未实现(留 v25+)。当前层 2/4/5 仅判 returncode=0,QC FAIL 仅记录不阻断,真正回归闸门是层 3 逐 cell diff。若后续 slug 改动导致 QC 行为变化(非数据问题),当前脚本无法自动检测。建议 v25+ 实现基线快照对比。"
    severity: LOW
  - risk_type: verification_chain_broken
    description: "无验证链断裂。4 项 Issue 中 REV-01/02/03 为文档元数据瑕疵(行数失真/多声明 .gitkeep/误报 pitfall_log.md modified),均 blocks_approval=false,功能等价性已独立复核通过;REV-04 为 INFO 级延期验证项。验证链完整。"
    severity: LOW

conditions:
  - "[已留档] A1 附录 self_check.py 行数声明 642 行应以 git 实测 919 行为准(REV-01),归档报告已记录该差异。建议 A 后续代码行数用 git show <hash>:<path> | find /c /v \"\" 实测取值"
  - "[已留档] A1 changed_files 声明 audit/self_check/.gitkeep 实际未提交(REV-02),C 归档以 git show 31f716f --stat 为准补记完整清单"
  - "[已留档] A1 changed_files 误报 scripts/pitfall_log.md modified(实际 v2.3 后未改动,REV-03),C 归档时移除该项。建议 A 形成固定自查:直接复制 git show <tag> --stat 输出作为 changed_files"
  - "[INFO/延期] auto 缺失自动降级分支建议原 skill 退役时(约 6 个月后)做真实缺失场景实测(REV-04);污染 deliverables/dashboards/01_latest/ 归档时排除 git add 即可,不阻断"
---

# v24-self-check 归档报告

## 1. 最终结论

**最终判决**: APPROVED_WITH_CONDITIONS
**总轮次**: 1
**核心收益**: 新增 5 层自检工具脚本 scripts/self_check.py(git 实测 919 行,非 skill 迁入),提供配置驱动 + 降级接口(--mode auto|full|degraded)的标准化回归验证框架。用 4 个历史 slug(v20/v21/v22/v23)跑过验证全部 PASS,核心回归闸门(层 3 逐 cell diff)经 B 独立复跑 v21 实测 total_cells_compared=13753 / diff_count=0 完全复现 A1 断言。这是 CHANGELOG 待办"5 层自检脚本化(用 6 个月)"的兑现,也是 6 个月观察期结束后删原 skill 的前置工具
**是否附条件**: 是(4 项 conditions,3 项文档留档类 + 1 项 INFO 延期验证)

## 2. Issue 生命周期全表

本轮 4 项 Issue 均为首轮提出,无上一轮 Issue:

| Issue ID | 提出轮次 | 严重程度 | 处理轮次 | 最终状态 |
|---|---|---|---|---|
| REV-v2.4-v24-self-check-r01-01 | r1 | WARNING | r1 同轮(B 审计后留档) | open→留档(C1 补记 self_check.py 行数以 919 为准) |
| REV-v2.4-v24-self-check-r01-02 | r1 | WARNING | r1 同轮(B 审计后留档) | open→留档(C1 补记完整 changed_files 清单,移除 .gitkeep) |
| REV-v2.4-v24-self-check-r01-03 | r1 | WARNING | r1 同轮(B 审计后留档) | open→留档(C1 移除 pitfall_log.md 误报项) |
| REV-v2.4-v24-self-check-r01-04 | r1 | INFO | r1 同轮(B 审计后留档) | open→留档(C1 标记延期验证 + 污染排除) |

### Issue 详情

- **REV-01**(WARNING/留档): A1 §6 附录声称 self_check.py 642 行,git 实测 919 行(误差 277 行/43%)。疑为草稿阶段行数未随最终版本更新。**不影响脚本功能**(脚本本身正常运行),C1 §6 补记以 919 行为准。
- **REV-02**(WARNING/留档): A1 changed_files 声明 audit/self_check/.gitkeep,实际未提交(目录已含 8 个基线报告文件,未创建 .gitkeep)。C1 §6 补记完整清单以 git show 31f716f --stat 为准。
- **REV-03**(WARNING/留档): A1 changed_files 误报 scripts/pitfall_log.md modified,实际最后改动在 v2.3(1ef0612),v2.4 未改。这是 v22/v23 changed_files 不实同类问题的延续(维度不同:v22/v23 遗漏声明,本轮多列未改动文件)。C1 §6 移除该项。
- **REV-04**(INFO/延期): (1) auto 缺失自动降级分支未在真实原 skill 缺失场景实测(原 skill 存在时无法触发);(2) 污染 deliverables/dashboards/01_latest/(untracked,非本轮引入)。C1 标记延期验证项,污染归档时排除即可。

### 本轮亮点(B1 §3.3 提出)

- **commit_hash 一致**(31f716f,未重复 v22/v23 误填中间 commit 的问题)
- **SKILL.md version 已升 v2.4.0**(未重复 REV-03 类问题)

说明前三轮反馈已部分被 A 吸收,但 changed_files 自查流程仍未稳定(v22/v23/v24 连续三轮出现元数据失真)。

## 3. 审计逃逸风险分析

- **延期风险(auto 自动降级分支)**:auto 模式在原 skill 真实缺失时自动切 degraded 的分支未在真实缺失场景实测。原 skill 存在时无法触发该分支,只能用 --mode degraded 模拟测试(PASS=2 SKIP=3 已验)。建议原 skill 退役时(约 6 个月观察期结束后)做一次真实缺失场景实测。**本轮不阻断归档**,因 degraded 强制模式已验接口逻辑正确。严重程度 MEDIUM。
- **5 层自检脚本本身未经长期回归验证**:v24 自检脚本作为 v25+ 后续 slug 迁入的标准回归验证工具,本身需要长期使用才能验证稳定性(基线快照对比、配置驱动扩展、降级模式真实场景)。建议在 v25+ 至少 2 个 slug 上实际使用后,再考虑将其作为强制前置自检流程。本轮 v24 仅用 v20/v21/v22/v23 四个历史 slug 跑过验证,全部 PASS,但未覆盖新 slug 场景。严重程度 MEDIUM。
- **QC 基线快照对比未实现**:A1 §5 review_focus 提出"是否应该把 0626 数据的 QC 基线写入快照,后续跑出 FAIL 时对比基线",本轮未实现(留 v25+)。当前层 2/4/5 仅判 returncode=0,QC FAIL 仅记录不阻断,真正回归闸门是层 3 逐 cell diff。若后续 slug 改动导致 QC 行为变化(非数据问题),当前脚本无法自动检测。建议 v25+ 实现基线快照对比。严重程度 LOW。
- **验证链断裂**:**无断裂**。4 项 Issue 中 REV-01/02/03 为文档元数据瑕疵(行数失真/多声明 .gitkeep/误报 pitfall_log.md modified),均 blocks_approval=false,功能等价性已独立复核通过;REV-04 为 INFO 级延期验证项。验证链完整。严重程度 LOW。
- **superseded 标注**:不适用。仅 1 轮,无 rebase/重写场景。

## 4. 完整轮次时间线

| 轮次 | 送审报告 | 审计意见 | verdict | 日期 |
|---|---|---|---|---|
| r1 | A1-v24-self-check-r1 | B1-v24-self-check-r1 | APPROVED_WITH_CONDITIONS | 2026-07-05 |

### 关键时间点

- 2026-07-05 16:40~16:50 — A 完成 self_check.py 编写 + 4 slug 基线报告生成 + SKILL/CHANGELOG 更新 + commit + 打 tag
- 2026-07-05 17:10 — B 完成 r1 审计,verdict=APPROVED_WITH_CONDITIONS,4 项 Issue(3 WARNING + 1 INFO,均不阻断)
- 2026-07-05 17:30 — C 归档

### B 独立复跑关键证据

- **层 1 字节对比**: PASS,new_md5=orig_md5=c5e41afdb9932d036def68050e29ed59,byte_equal=true
- **层 2 端到端穿行**: PASS,returncode=0,output_exists=true(QC Fails=1 Warns=4 仅记录,0626 数据已知)
- **层 3 逐 cell diff**: PASS,**total_cells_compared=13753,diff_count=0**,口径=25 sheet×6 列(P/U/V/W/X/Y)×max_row(完全复现 A1 断言)
- **层 4 原 skill smoke**: PASS,原 skill(簿记录入/v2.1)returncode=0
- **层 5 回归测试**: PASS,机构统计 QC PASSED 35 项 + 成本/利差报告 QC FAIL(0626 数据)+ 比对工具 PASSED,均 returncode=0
- **降级模式 --mode degraded**: 总评 PASS(PASS=2 SKIP=3,层1/3/4 正确跳过)

## 5. 经验教训

1. **A changed_files 自查流程仍未稳定**:v22/v23/v24 已连续三轮出现 changed_files/元数据失真(v22/v23 遗漏声明,v24 行数失真+多列/误报)。**强烈建议 A 形成固定自查流程**:送审前直接复制 `git show <tag> --stat` 输出作为 changed_files 清单,代码行数用 `git show <hash>:<path> | find /c /v ""` 实测取值。**教训**:changed_files 自查应脚本化,避免人工抄写误差。
2. **A 元数据自查有改进**:本轮 commit_hash 一致(未重复 v22/v23 误填中间 commit)、SKILL.md version 已升 v2.4.0(未重复 REV-03 类问题),说明前几轮反馈已部分被 A 吸收。**教训**:反馈循环有效,但 changed_files 自查仍需强化。
3. **5 层自检脚本化的价值**:v24 将 v21-bookkeeping 整合时手工跑的 5 层自检(字节对比/端到端/逐 cell diff/原 skill smoke/回归)脚本化,配置驱动 + 降级接口,可复用到 v25+ 后续 slug。**教训**:手工验证流程应及时脚本化,避免每次重复劳动 + 降低人为误差。
4. **QC FAIL 不阻断的设计**:层 2/4/5 仅判 returncode=0,QC FAIL(0626 数据已知问题)仅记录不阻断,真正回归闸门是层 3 逐 cell diff。**教训**:数据问题不应污染代码等价性判定,回归闸门应聚焦产出等价性(逐 cell diff)而非 QC PASS(可能含数据问题)。
5. **降级模式的设计**:--mode auto|full|degraded 三态清晰,原 skill 删除后切 degraded(只跑层 2/5)。**教训**:工具脚本应预留降级接口,适应未来原 skill 退役场景。
6. **基线快照对比的延期**:A1 §5 提出基线快照对比但本轮未实现(留 v25+)。**教训**:首轮可只跑出基线,后续轮次再实现对比,避免一次性过度工程化。
7. **cell 计数口径声明**:A1 §6.2 明确声明"全 sheet 对比,在层 3 details.cell_count_caliber 字段写明实际口径",避免 v21 那种 A/B 分歧(A=50125 单 sheet,B=64811 全 sheet)。**教训**:口径声明应在脚本输出中固化,避免人工报告歧义。
8. **配置驱动的可维护性**:SLUG_CONFIG 字典硬编码 4 个 slug 配置,新增 slug 只需扩配置。**教训**:配置驱动优于硬编码分支,降低维护成本。但 A1 §5 提出是否改成自动扫描 state.json 的 slugs,本轮未实现(合理,避免过度工程化)。

## 6. 代码最终状态

- **git_tag**: `audit/v2.4-v24-self-check-r01`
- **commit_hash**: `31f716f`(tag 实际指向,A1 frontmatter 一致,未重复 v22/v23 误填)
- **abs-toolbox 仓库**: gitee(`ppwupp/abs-toolbox`)+ github(`codebluce/ABS-Toolbox`)双推
- **原 skill 保留**: 本轮无原 skill 迁入(v24 是新增工具脚本,非 skill 整合)
- **新增文件**:
  - `skills/ABS工具箱/scripts/self_check.py`(git 实测 919 行,A1 §6 附录误填 642 行,以 919 为准)
  - `skills/ABS工具箱/audit/self_check/v20-institution-stats_r1_20260705_164043.json` + `.md`(基线报告)
  - `skills/ABS工具箱/audit/self_check/v21-bookkeeping_r1_20260705_164809.json` + `.md`(基线报告)
  - `skills/ABS工具箱/audit/self_check/v22-pricing_r1_20260705_164522.json` + `.md`(基线报告)
  - `skills/ABS工具箱/audit/self_check/v23-internal-merge-unify_r1_20260705_164401.json` + `.md`(基线报告)
- **修改文件**:
  - `skills/ABS工具箱/SKILL.md`(frontmatter 升 v2.4.0 + 加"5 层自检脚本"章节)
  - `skills/ABS工具箱/CHANGELOG.md`(加 v2.4.0 段)
- **A1 changed_files 误报移除**(C1 补记):
  - `audit/self_check/.gitkeep`(A1 声明但实际未提交,目录已含 8 个基线报告文件)
  - `scripts/pitfall_log.md`(A1 误报 modified,实际最后改动在 v2.3 1ef0612,v2.4 未改)
- **完整 commit 改动清单**(以 `git show 31f716f --stat` 为准):
  - 1 新增脚本:scripts/self_check.py(919 行)
  - 8 新增基线报告:audit/self_check/*.json + *.md(4 slug × 2 文件)
  - 2 修改:SKILL.md + CHANGELOG.md
  - audit 元数据:audit/INDEX.md / audit/state.json / audit/submissions/A1-v24-self-check-r1.md
- **未纳入 commit 的污染文件**(REV-04,git status untracked):
  - `deliverables/dashboards/01_latest/`(与 v23 归档时同类,非本轮引入,C 归档时排除 git add)

### 5 层自检脚本架构

```
scripts/self_check.py (git 实测 919 行,A1 §6 误填 642 行)
├── SLUG_CONFIG dict (4 slug 配置: v20/v21/v22/v23)
├── detect_mode()         # auto/full/degraded 切换
├── layer1_byte_diff()    # 字节对比 (md5)
├── layer2_e2e_run()      # 端到端穿行 (returncode + 产出存在)
├── layer3_cell_diff()    # 逐 cell diff (openpyxl, 6 列 × 全 sheet)
├── layer4_orig_smoke()   # 原 skill smoke
├── layer5_regression()   # 回归测试 (机构统计 + 3 看板)
└── run_self_check()      # 主流程, 输出 JSON + MD 到 audit/self_check/
```

### 回滚方案

```bash
# 在 abs-toolbox 仓库:
git revert 31f716f
git push gitee main && git push github main

# self_check.py 是独立新增工具脚本,删除后不影响其他 skill 功能
# audit/self_check/ 基线报告可保留(历史快照)或一并删除
```
