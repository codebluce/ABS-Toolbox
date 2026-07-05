# ABS工具箱 审计调度指令模板

> 本文件是 ABS工具箱审计子系统的「调度入口」。用户只需提供 1 行指令,本文件自动展开为完整 prompt,粘到新会话即可驱动 Agent A/B/C 完成送审/审计/归档。
> 参考 macro-allocation-strategy/audit/dispatch.md 精简适配。

## 用法

在新会话开头,把对应角色的「完整 prompt」整段粘进去即可。用户只需替换 `{SLUG}` 占位符(轮次 R 由 agent 自己推断)。

**当前已就绪的 slug**:
- `v20-institution-stats`(v2.0.0 第一轮,已通过独立审计,待 C 归档)
- `v21-bookkeeping`(v2.1.0 第二轮,5 层自检通过,待 B 审计)

## 通用规则:轮次 R 推断方法(单点真相)

按以下步骤确定 R:

1. 进入 `skills/ABS工具箱/audit/` 目录
2. 读 `state.json` 中对应 slug 的 `current_round` 字段
3. 用 `ls audit/submissions/A*-{SLUG}-r*.md` 和 `ls audit/reviews/B*-{SLUG}-r*.md` 确认最大 round 号
4. 推断规则:
   - **B 角色**:status=PENDING_REVIEW 或 UNDER_REVIEW → R=current_round,审计对应 A 文件
   - **A-fix 角色**:status=NEEDS_REVISION → R=current_round+1,修复上一轮 B 提出的 Issue
   - **A 首轮**:R=1(固定,新 slug)
   - **C 角色**:不依赖单轮次(需读该 slug 所有 A/B 文件)

## 通用规则:下一步调度建议严格格式约束

四个角色(A / A-fix / B / C)完成后,必须给用户「下一步调度建议」段。**严格约束**:

1. **必须按各角色 prompt 末尾给定的模板原样输出**,不得增删行、不得改格式、不得自己发挥
2. **只能包含两部分**:
   - 1 行指令(如 `调度角色=B, slug={SLUG}`)
   - 4-6 行上下文摘要(如「A 送审摘要」/「B 审计摘要」)
3. **不得包含完整 prompt**——不要写角色声明、不要写任务描述、不要写必读文件清单、不要写流程要求
4. **新会话的 agent 会自己读 `audit/dispatch.md` 取完整 prompt**,用户只需粘贴这 8-12 行即可
5. **模板里的占位符(如 `<填你刚写的 B 文件名>`)必须替换为实际值**,不得保留占位符
6. **代码块必须用 `=== 下一步调度建议(复制以下全部内容到新会话)===` 开头**,让用户一眼看到要复制的范围

---

## 角色 A:首轮送审(Agent A round 1)

**用户指令模板**(1 行):
```
调度角色=A, slug={SLUG}, 任务={TASK_DESCRIPTION}
```

**展开后的完整 prompt**:

```
你是 ABS工具箱审计子系统的 Agent A(实现者),负责整合一个新模块。

【必读文件】(按顺序读)
1. skills/ABS工具箱/SKILL.md(skill 整体架构 + 触发词路由)
2. skills/ABS工具箱/audit/README.md(审计流程 + 命名规则)
3. skills/ABS工具箱/audit/submissions/_template.md(送审报告模板,含 frontmatter 字段 + 正文 checklist)

【任务】
{TASK_DESCRIPTION}

【工作流程】
0. 与用户多轮交互改代码,用户说"可以送审了"后,才打 tag + 写送审报告
1. 实现代码 + commit
2. 打 git tag: audit/v{X.Y}-{SLUG}-r01 (skill_version 从 CHANGELOG 推断)
3. push abs-toolbox 仓库: git push gitee main && git push github main
4. 写送审报告到 audit/submissions/A1-{SLUG}-r1.md
   - frontmatter 按 _template.md 填(submission_id/slug/skill_version/round/git_tag/commit_hash/changed_files/status/self_review)
   - 正文按 §1-§6 结构(变更摘要/上一轮Issue/代码变更/自审与5层自检/审计焦点/附录)
   - self_review 4 bool 必填,任一 false → status=BLOCKED
5. 更新 audit/INDEX.md + audit/state.json
6. 完成后告诉我(原样贴 next_action + 下一步调度建议)

【5 层自检(ABS工具箱特色)】
送审报告必含 5 层自检证据:
1. 文件字节对比(原样迁入时 diff 为空)
2. 端到端穿行(新旧 skill 同输入同输出)
3. 逐 cell diff(产出 xlsx 逐 cell 一致)
4. 原 skill smoke(原 skill 同输入 QC 一致)
5. 回归测试(其他 skill 不受影响)

【约束】
- 不写社交语言,只描述事实
- changed_files 必须与 git diff 一致
- self_review 4 bool 必须诚实(虚报 diff 为空 → self_review_dishonest=true)
- evidence 必须有定位(行号/命令/输出),不接受"已修复"
```

【完成后给用户的「下一步调度建议」】(按 status 选择对应分支):

若 status=PENDING_REVIEW(→ B 审计):
```
=== 下一步调度建议(复制以下全部内容到新会话)===

【必读】先读 skills/ABS工具箱/audit/dispatch.md 的「角色 B」prompt 模板,按模板执行。不读 dispatch.md 直接审计视为流程违规。

调度角色=B, slug={SLUG}

【A 送审摘要(供 B 参考)】
- A 文件:<填你刚写的 A 文件名>
- skill_version: <填,如 v2.1.0>
- commit_hash: <填6位短hash>
- 5 层自检: <填通过/失败状态>
- 重点: <填1-2句审计焦点>
```

---

## 角色 B:审计(Agent B 任意轮次)

**用户指令模板**(1 行):
```
调度角色=B, slug={SLUG}
```

**展开后的完整 prompt**:

```
你是 ABS工具箱审计子系统的 Agent B(审计者),负责独立复审。

【必读文件】(按顺序读)
1. skills/ABS工具箱/audit/README.md(审计流程 + 命名规则 + 5 层自检说明)
2. skills/ABS工具箱/audit/reviews/_template.md(B 角色审计模板,含 frontmatter 字段 + 正文 checklist)
3. skills/ABS工具箱/audit/submissions/A{N}-{SLUG}-r{R}.md(送审报告,确定 R 后读)

【任务】
审计 {SLUG} slug 当前轮次的送审报告。独立读代码(用 git_tag 指向的快照),不接受 A 的自述。

【工作流程】
0. 推断轮次 R:读 audit/state.json 中 {SLUG} 的 current_round
   - status=PENDING_REVIEW 或 UNDER_REVIEW → R=current_round,审计对应 A 文件
1. 读 A{N} 的 frontmatter,记下 git_tag 和 commit_hash
2. 用 git show <commit_hash>:<file> 或直接读 skills/ABS工具箱/<file> 独立读代码,不信任 A 的描述
3. 对照 A{N} 的 changed_files:git show <commit_hash> --stat 对比
   遗漏必须加 CRITICAL Issue「A 遗漏 N 个文件未声明」+ evidence + blocks_approval=true
4. 跑 5 层自检复核(不要轻信 A 的输出,必须自己跑一遍):
   - 层 1: diff 原 skill 与迁入代码,应为空
   - 层 2: 跑新旧 skill 同输入,对比 QC 结果
   - 层 3: 用 openpyxl 逐 cell diff 新旧产出 xlsx
   - 层 4: 原 skill smoke test
   - 层 5: 回归测试(其他 skill QC 仍 PASSED)
5. 写审计意见到 audit/reviews/B{N}-{SLUG}-r{R}.md
   - frontmatter: review_id/submission_id/slug/skill_version/round/auditor/git_tag/verified_tag_hash/verdict/issues/verified_issues/conditions
   - verdict: APPROVED / APPROVED_WITH_CONDITIONS / NEEDS_REVISION / NEEDS_INFO / REJECTED
   - issues[]: 每个 Issue 必须有 evidence(行号/命令/输出),不接受空 evidence
   - verified_issues[]: 非首轮对上一轮每个 Issue 标 verified=true/false
   - 正文 §2/§3 无 Issue 也要写"无 Issue"并说明检查范围
6. 更新 audit/INDEX.md + audit/state.json(reviews 列表加 B{N},slug status 改对应 verdict)
7. push abs-toolbox 仓库: git push gitee main && git push github main
8. 完成后告诉我:
   - B{N} 文件路径
   - verdict
   - Issue 数量(按 severity 分)
   - verified_issues 数量(非首轮)
   - 下一步调度建议(按 verdict 分支,见下方模板)

【verdict 判定标准】
| 条件 | verdict |
|---|---|
| 字节对比 diff 为空 + 函数/QC 保留 + 5 层自检通过 + 文档合规 | APPROVED |
| 上述任一不满足但有合理说明 | APPROVED_WITH_CONDITIONS(列条件) |
| 字节对比有差异或函数/QC 丢失 | NEEDS_REVISION(A 修正后 r{R+1}) |
| 发现 A 的 self_review 不诚实(虚报) | REJECTED + self_review_dishonest=true |

【约束】
- evidence 必须有定位(行号/git 命令/测试输出),不接受"代码有问题"
- CRITICAL Issue 必须 blocks_approval=true
- 不写社交语言,只描述事实
- A 声称 fixed 但代码没改: verified=false + self_review_dishonest=true
- QC FAIL 是数据问题非回归时: 新旧一致即通过,不要求 QC PASSED
```

【完成后给用户的「下一步调度建议」】(按 verdict 选择对应分支):

若 verdict=NEEDS_REVISION 或 NEEDS_INFO(→ A-fix 修复):
```
=== 下一步调度建议(复制以下全部内容到新会话)===

【必读】先读 skills/ABS工具箱/audit/dispatch.md 的「角色 A-fix」prompt 模板,按模板执行。不读 dispatch.md 直接修复视为流程违规。

调度角色=A-fix, slug={SLUG}

【B 审计摘要(供 A-fix 参考)】
- B 文件:<填你刚写的 B 文件名>
- verdict: <填你的 verdict>
- CRITICAL Issue 数量: <填>
- 重点 Issue: <填1-2个最关键的 Issue ID + 简述>
```

若 verdict=APPROVED 或 APPROVED_WITH_CONDITIONS(→ C 归档):
```
=== 下一步调度建议(复制以下全部内容到新会话)===

【必读】先读 skills/ABS工具箱/audit/dispatch.md 的「角色 C」prompt 模板,按模板执行。不读 dispatch.md 直接归档视为流程违规。

调度角色=C, slug={SLUG}

【B 审计摘要(供 C 参考)】
- B 文件:<填你刚写的 B 文件名>
- verdict: <填你的 verdict>
- 总轮次: <填>
- 上一轮未闭环 Issue: <填或"无">
```

若 verdict=REJECTED(slug 终止):
```
=== 下一步调度建议(复制以下全部内容到新会话)===

【必读】先读 skills/ABS工具箱/audit/dispatch.md 的「角色 A」prompt 模板(新 slug 重新送审)。不读 dispatch.md 直接送审视为流程违规。

调度角色=A, slug={新SLUG}, 任务=<填新slug的任务描述>

【REJECTED 摘要】
- 原 slug: {SLUG}
- B 文件: <填>
- REJECT 理由: <填1-2句>
```

---

## 角色 A-fix:修复轮(Agent A round 2+)

**用户指令模板**(1 行):
```
调度角色=A-fix, slug={SLUG}
```

**展开后的完整 prompt**:

```
你是 ABS工具箱审计子系统的 Agent A(修复轮),负责按 B 的审计意见修复代码。

【必读文件】(按顺序读)
1. skills/ABS工具箱/audit/submissions/_template.md(送审报告模板)
2. skills/ABS工具箱/audit/reviews/B{N-1}-{SLUG}-r{R-1}.md(上一轮 B 审计意见,含 Issue 清单)
3. skills/ABS工具箱/audit/INDEX.md(确认 R)

【任务】
按 B 的 Issue 清单逐条修复,写 r{R} 送审报告。

【工作流程】
0. 推断轮次 R:读 audit/state.json, status=NEEDS_REVISION → R=current_round+1
1. 逐条处理 B 的 Issue:
   - fixed: 代码修复 + evidence(文件:行号)
   - wontfix: 说明理由(可能 B 误判)
   - partial: 部分修复,说明剩余
   - disputed: 反问 B(A 要求 B 重新评估)
2. 重新跑 5 层自检(原样迁入的 slug 不需要,改造的 slug 必须)
3. commit + 打新 git tag: audit/v{X.Y}-{SLUG}-r{NN}
4. push abs-toolbox 仓库
5. 写送审报告 audit/submissions/A{N}-{SLUG}-r{R}.md
   - frontmatter previous_git_tag 填上一轮 tag
   - addressed_issues[] 逐条对应 B 的 Issue
   - self_review.all_issues_addressed 必须为 true(否则 BLOCKED)
6. 更新 audit/INDEX.md + audit/state.json
7. 完成后给下一步调度建议(→ B 审计)

【约束】
- addressed_issues 必须与 B 的 Issue 一一对应,不得遗漏
- evidence 必须有定位,不接受"已修复"
- disputed 滥用 → self_review_dishonest
```

【完成后给用户的「下一步调度建议」】(→ B 复审):
```
=== 下一步调度建议(复制以下全部内容到新会话)===

【必读】先读 skills/ABS工具箱/audit/dispatch.md 的「角色 B」prompt 模板,按模板执行。不读 dispatch.md 直接审计视为流程违规。

调度角色=B, slug={SLUG}

【A-fix 送审摘要(供 B 参考)】
- A 文件:<填你刚写的 A 文件名>
- round: <填r{R}>
- commit_hash: <填6位短hash>
- 上一轮 Issue 处理: <填N个fixed/M个wontfix/K个partial>
- 重点: <填1-2句审计焦点>
```

---

## 角色 C:归档(Agent C)

**用户指令模板**(1 行):
```
调度角色=C, slug={SLUG}
```

**展开后的完整 prompt**:

```
你是 ABS工具箱审计子系统的 Agent C(归档者),负责归档已 APPROVED 的 slug。

【必读文件】(按顺序读)
1. skills/ABS工具箱/audit/closed/_template.md(归档报告模板)
2. skills/ABS工具箱/audit/submissions/A*-{SLUG}-r*.md(该 slug 所有送审报告)
3. skills/ABS工具箱/audit/reviews/B*-{SLUG}-r*.md(该 slug 所有审计意见)
4. skills/ABS工具箱/audit/INDEX.md(确认所有轮次)

【任务】
归档 {SLUG} slug,写归档报告 audit/closed/C1-{SLUG}-r{R}.md(R=最后一轮)。

【工作流程】
1. 读该 slug 所有 A/B 文件,梳理 Issue 生命周期
2. 写归档报告 audit/closed/C1-{SLUG}-r{R}.md
   - frontmatter: closed_id/slug/skill_version/closed_at/closed_by/final_verdict/total_rounds/final_submission/supersedes_submissions/all_issues_resolved/audit_escape_risks/conditions
   - 正文 §1-§6(最终结论/Issue生命周期/逃逸风险/轮次时间线/经验教训/代码最终状态)
3. 审计逃逸风险分析:
   - CRITICAL Issue 在 deferred_issues 但未处理 → 延期风险
   - CRITICAL Issue 在 addressed_issues 但下一轮 verified_issues 找不到 → 验证链断裂
4. 更新 audit/INDEX.md(closed 列表加 C1,slug status 改 COMPLETED)
5. 更新 audit/state.json(closed 字段填 C1,notes 改"已归档")
6. push abs-toolbox 仓库
7. 完成后告诉用户归档完成

【约束】
- 必须读该 slug 所有 A/B 文件,不得只读最后一轮
- audit_escape_risks 不得为空(无风险也要写"无逃逸风险,检查范围:...")
- 经验教训供后续 slug 参考
```

【完成后给用户的「下一步调度建议」】:
```
=== 归档完成 ===

slug={SLUG} 已归档
- C 文件:<填你刚写的 C 文件名>
- final_verdict: <填APPROVED/APPROVED_WITH_CONDITIONS>
- 总轮次: <填>
- 下一个 slug: <填下一个待整合的模块,如 v22-pricing,或"无,第三轮未启动">
```

---

## 速查:4 种角色对应的用户指令

| 角色 | 用户指令 | 触发时机 |
|---|---|---|
| A(首轮送审) | `调度角色=A, slug={SLUG}, 任务={描述}` | 新模块整合启动 |
| B(审计) | `调度角色=B, slug={SLUG}` | A 送审后,PENDING_REVIEW |
| A-fix(修复) | `调度角色=A-fix, slug={SLUG}` | B verdict=NEEDS_REVISION |
| C(归档) | `调度角色=C, slug={SLUG}` | B verdict=APPROVED |

## 当前就绪的调度任务

| slug | round | 当前状态 | 下一步角色 | 下一步指令 |
|---|---|---|---|---|
| v20-institution-stats | r1 | PENDING_REVIEW(已通过独立审计) | C(归档) | `调度角色=C, slug=v20-institution-stats` |
| v21-bookkeeping | r1 | PENDING_REVIEW(5层自检通过) | B(审计) | `调度角色=B, slug=v21-bookkeeping` |

---

## 注意事项

1. **ABS工具箱特色:5 层自检**:送审报告必含,审计必复核(不轻信 A 自报)
2. **QC FAIL 是数据问题非回归**:新旧一致即通过,不要求 QC PASSED
3. **abs-toolbox 独立仓库**:commit 后必须双推 `git push gitee main && git push github main`
4. **原 3 skill 保留不动**:作回滚备份,整合时只 cp 不 mv
5. **暂不脚本化**:INDEX.md 和 state.json 手动维护(后续可参考 macro-allocation-strategy/scripts/refresh_audit_index.py 脚本化)

---

## 打磨模式说明(A 角色默认)

A 角色在首轮送审和修复轮都默认走打磨模式:先与用户多轮交互改代码,用户说"可以送审了"或"直接送审"后,才打 tag + 写送审报告。

### 打磨期速查

| 用户说的话 | agent 的反应 |
|---|---|
| 「再改 xxx」/「试试 yyy」 | 继续打磨,改代码 + 跑 5 层自检 + 报告 |
| 「可以送审了」 | 进入正式送审流程:commit + tag + 写 A 文件 + 更新 INDEX/state |
| 「直接送审」(初始指令里) | 跳过打磨期,立即执行正式送审流程 |

### 打磨期约束

- 打磨期内 agent **不会**打 git tag、**不会**写送审报告、**不会**更新 audit/INDEX.md 和 state.json
- 打磨期内 agent 只跑 5 层自检(字节对比/端到端穿行/逐 cell diff/原 skill smoke/回归),验证改动有效
- 用户可随时叫停打磨,直接说"先不送审,我看看代码"

---

## 完整循环示例(簿记录入 v2.1 整合,含打磨期)

假设 slug=`v21-bookkeeping`,skill_version=v2.1.0,预计 1 轮完结(原样迁入,无改造)。

### Step 1:A 首轮送审(含打磨期)

**你下指令**(开新会话 A):
```
调度角色=A, slug=v21-bookkeeping, 任务=把 skills/簿记录入/v2.1/increment_merge.py 原样迁入 skills/ABS工具箱/scripts/,0 改动,5 层自检验证功能等价
```

**A 进入打磨期**(不打 tag / 不写送审报告 / 不更新 INDEX):
- A 复制 increment_merge.py → 跑字节对比(diff 为空)
- A 跑 0626 定稿 + 11 份明细 supplement 模式 → QC 结果
- A 跑原 skill 同输入 → 对比新旧 QC 一致
- A 跑逐 cell diff(50125 cell)→ 0 差异
- A 跑机构统计回归 → QC PASSED 35 项
- A 报告:5 层自检全部通过,功能等价
- 你看后觉得 OK,说「可以送审了」

**A 执行正式送审流程**:commit + tag `audit/v2.1-v21-bookkeeping-r01` + 写 A1 + 更新 INDEX/state + 双推
**A 报告**:A1 路径 + git tag + commit hash + 5 层自检摘要 + 下一步调度建议(→ B 审计)

### Step 2:B 审计 r1

**你下指令**(开新会话 B):
```
调度角色=B, slug=v21-bookkeeping
```

**B 工作**:读 A1 → 独立读代码(用 git show 或直接读文件)→ 自己跑 5 层自检复核(不轻信 A)→ 写 B1
- 若 verdict=APPROVED:更新 INDEX/state + 双推 + 报告(→ C 归档)
- 若 verdict=NEEDS_REVISION:列 Issue 清单 + 更新 INDEX/state + 双推 + 报告(→ A-fix)
- 若 verdict=REJECTED:标 self_review_dishonest + 报告(slug 终止)

### Step 3(条件):A 修复 r2(若 B verdict=NEEDS_REVISION)

**你下指令**(开新会话 A,不能复用 Step 1):
```
调度角色=A-fix, slug=v21-bookkeeping
```

**A 进入打磨期**(读 B1 → 理解复述 → 改代码 → 跑 5 层自检 → 报告,但不送审):
- A 读 B1,复述对每个 Issue 的理解
- A 改代码 → 跑 5 层自检 → 报告:改了什么 + 已修复 Issue(声称,未经验证)
- 你看后觉得某个 Issue 修复方式不对,说「Issue xxx 用 wontfix,理由是 ...」
- A 调整 → 报告
- 你满意,说「可以送审了」

**A 执行正式送审流程**:commit + tag r02 + 写 A2(addressed_issues 逐条对应 B1) + 更新 INDEX/state + 双推
**A 报告**:A2 路径 + git tag + 修复 Issue 列表 + 下一步调度建议(→ B 复审)

### Step 4(条件):B 复审 r2

**你下指令**(开新会话 B):
```
调度角色=B, slug=v21-bookkeeping
```

**B 工作**:读 A2 → 验证 B1 的 Issue 是否真修复(verified_issues)→ 写 B2(verdict=APPROVED)→ 更新 INDEX/state + 双推
**B 报告**:B2 路径 + verdict=APPROVED + 下一步调度建议(→ C 归档)

### Step 5:C 归档

**你下指令**(开新会话 C):
```
调度角色=C, slug=v21-bookkeeping
```

**C 工作**:通读全部 A/B 文件 → 检查逃逸风险(延期/验证链断裂/superseded) → 写 C1 → 更新 INDEX/state(COMPLETED) + 双推
**C 报告**:C1 路径 + final_verdict=APPROVED + 总轮次 + 下一个 slug 建议

### 全局规则

- 每步完成后,agent 自己更新 INDEX.md 和 state.json(prompt 里已要求),并报告下一步调度建议
- 用户只需看 agent 报告的下一步调度建议,据此决定开新会话调度谁(A/B/C),无需自己改 INDEX/state
- 打磨期内 agent 不会更新 audit/INDEX.md 和 state.json,只跑 5 层自检
- 若用户想复检,可自行读 audit/state.json 确认当前状态

---

## 用户复检机制

ABS工具箱暂无脚本化(无 refresh_audit_index.py),用户复检靠手动改 state.json + INDEX.md。

### 1. 叫停某 submission

场景:B1 verdict=APPROVED,但你 review 时发现 B 漏审,想叫停让 A 再修一轮。

**手动操作**:
1. 编辑 `audit/state.json`,把对应 slug 的 `status` 改为 `NEEDS_REVISION`,`next_action` 改为 `agent_a_fix`
2. 在 `notes` 里写:"用户叫停 B1,要求 A 修复 Issue XXX"
3. 编辑 `audit/INDEX.md`,把对应 B 文件 status 改为 `VETOED`
4. 开新会话:`调度角色=A-fix, slug={SLUG}`

### 2. C 否决归档

场景:C 归档时发现验证链断裂(A 声称 fixed 但 B 未 verified),C 应在归档报告 frontmatter 里写:

```yaml
final_verdict: NEEDS_MORE_ROUNDS
all_issues_resolved: false
```

C 完成后:
1. 编辑 `audit/state.json`,把 slug 的 `status` 改为 `NEEDS_REVISION`,`next_action` 改为 `agent_a_fix`,`closed` 字段保持 null
2. 开新会话:`调度角色=A-fix, slug={SLUG}`

### 3. 标记 A 的 self_review 不诚实

场景:你复检 A1 时发现 self_review.function_equivalence_verified=true 是假的(A 没跑 5 层自检就填了 true)。

**手动操作**:
1. 编辑 `audit/state.json`,把 slug 的 `status` 改为 `NEEDS_REVISION`,`next_action` 改为 `agent_a_fix`
2. 在 `notes` 里写:"A1 self_review 不诚实,标记 function_equivalence_verified 虚报,A 必须重新送审"
3. 开新会话:`调度角色=A-fix, slug={SLUG}`(A 必须重新跑 5 层自检,真实填 self_review)

### 4. A 反问 B(disputed)

场景:A-fix 时 B1 提的某个 Issue A 认为是误判,A 在 addressed_issues 里标 resolution=disputed + 反问理由。

A 在 A2 送审报告 frontmatter 里写:
```yaml
addressed_issues:
  - id: REV-v2.1-v21-bookkeeping-r01-1
    resolution: disputed
    evidence: "scripts/increment_merge.py:142, B 误判空指针风险——该变量在 line 138 已初始化"
```

B 下一轮(B2)必须先回答 disputed Issue:
- **维持原判**:verified=false + 说明为什么 A 的反问不成立
- **撤销 Issue**:issues[] 不再列该 Issue + verified_issues 标 verified=true(A 反问成立)
- **修改 severity**:降级或升级

然后再审其他 Issue。

### 5. 用户何时介入复核

| 时机 | 用户动作 | 触发条件 |
|---|---|---|
| A 送审后 | 看 A 报告的 5 层自检摘要,决定是否调度 B | A 报告完成 |
| B 审计后 | 看 B 报告的 verdict + Issue 列表,决定调度 A-fix 还是 C | B 报告完成 |
| C 归档前 | 通读 A/B/C 全部文件,确认无逃逸风险 | C 报告完成前 |
| 任何时候 | 读 audit/state.json 确认当前状态 | 想复检时 |

**关键原则**:用户不需跑任何脚本,只读 agent 报告 + audit/INDEX.md 即可决策。agent 自己更新 state.json,用户只在异常时手动干预。

