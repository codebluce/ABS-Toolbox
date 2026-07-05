---
# 归档报告 frontmatter(C 角色)
# 复制本模板填充

closed_id: C{N}-{slug}-r{R}            # 与文件名一致
slug: {slug}
skill_version: v{X.Y}
closed_at: "YYYY-MM-DD HH:MM:SS"
closed_by: agent_c

final_verdict: APPROVED                # APPROVED | APPROVED_WITH_CONDITIONS
total_rounds: {R}                      # 总轮次
final_submission: A{N}-{slug}-r{R}     # 最终 submission_id
supersedes_submissions:                # 该 slug 所有 submission_id
  - A1-{slug}-r1
  - A2-{slug}-r2

all_issues_resolved: true              # 是否所有 Issue 已闭环

audit_escape_risks:                    # C 标记的逃逸风险
  - risk_type: deferred_critical       # deferred_critical | verification_chain_broken | superseded_missing
    description: "风险描述"
    severity: HIGH                     # HIGH | MEDIUM | LOW

conditions: []                         # APPROVED_WITH_CONDITIONS 时必填
---

<!--
正文 checklist(C 角色必守):
[x] §1 最终结论
[x] §2 Issue 生命周期全表
[x] §3 审计逃逸风险分析
[x] §4 完整轮次时间线
[x] §5 经验教训
[x] §6 代码最终状态
-->

# {slug} 归档报告

## 1. 最终结论

**最终判决**: {APPROVED / APPROVED_WITH_CONDITIONS}
**总轮次**: {R}
**核心收益**: {一句话}
**是否附条件**: {是/否}

## 2. Issue 生命周期全表

| Issue ID | 提出轮次 | 严重程度 | 处理轮次 | 最终状态 |
|---|---|---|---|---|
| REV-v{X.Y}-{slug}-r1-01 | r1 | CRITICAL | r2 | fixed & verified |

## 3. 审计逃逸风险分析

- **延期风险**:CRITICAL Issue 在 deferred_issues 但未处理 → {检查结果}
- **验证链断裂**:CRITICAL Issue 在 addressed_issues 但下一轮 verified_issues 找不到 → {检查结果}
- **superseded 标注**:rebase 场景 superseded 标注是否完整 → {检查结果}

## 4. 完整轮次时间线

| 轮次 | 送审报告 | 审计意见 | verdict | 日期 |
|---|---|---|---|---|
| r1 | A1-{slug}-r1 | B1-{slug}-r1 | NEEDS_REVISION | YYYY-MM-DD |
| r2 | A2-{slug}-r2 | B2-{slug}-r2 | APPROVED | YYYY-MM-DD |

## 5. 经验教训

{本轮整合的经验教训,供后续 slug 参考}

## 6. 代码最终状态

- **git_tag**: `audit/v{X.Y}-{slug}-r{NN}`
- **commit_hash**: {hash}
- **abs-toolbox 仓库**: gitee + github 双推
- **原 skill 保留**: {原 skill 路径,作回滚备份}
