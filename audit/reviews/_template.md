---
# 审计意见 frontmatter(B 角色)
# 复制本模板填充

review_id: B{N}-{slug}-r{R}            # 与文件名一致
submission_id: A{N}-{slug}-r{R}        # 对应的 submission_id
slug: {slug}
skill_version: v{X.Y}
round: {R}
auditor: agent_b
created_at: "YYYY-MM-DD HH:MM:SS"

git_tag: audit/v{X.Y}-{slug}-r{R}      # 与 submission 一致
verified_tag_hash: a1b2c3d             # B 校验后的 commit hash

verdict: APPROVED                      # APPROVED | APPROVED_WITH_CONDITIONS | NEEDS_REVISION | NEEDS_INFO | REJECTED

issues:
  - id: REV-v{X.Y}-{slug}-r{R}-01
    severity: CRITICAL                 # CRITICAL | WARNING | INFO
    category: FUNCTION_EQUIVALENCE     # FUNCTION_EQUIVALENCE | DATA_INTEGRITY | DOC_CONSISTENCY | INTERFACE_COMPAT
    location: "scripts/xxx.py:L120"
    description: "问题描述"
    evidence: "代码片段或测试输出"
    suggested_fix: "建议修复方式"
    blocks_approval: true              # true=阻断通过

verified_issues:
  - id: REV-v{X.Y}-{slug}-r{R-1}-01
    a_claim: fixed
    b_verification: verified           # verified | not_verified | partial
    evidence: "验证证据"

conditions: []                         # APPROVED_WITH_CONDITIONS 时必填
---

<!--
正文 checklist(B 角色必守):
[x] §0 总体结论(verdict + 一句话)
[x] §1 上一轮 Issue 验证(含证据列)
[x] §2 需求合规审查
  [x] 2.1 上一轮 Issue 全覆盖
  [x] 2.2 review_focus 回应
  [x] 2.3 5 层自检证据复核
[x] §3 代码质量审查
  [x] 3.1 CRITICAL(功能等价性 / 数据完整性)
  [x] 3.2 WARNING(文档一致性 / 接口兼容性)
  [x] 3.3 INFO(改进建议)
[x] §4 下一轮指引
约束:§2 和 §3 都不能空(无 Issue 也要写"无 Issue"并说明检查范围)
-->

# {slug} r{R} 审计意见

## 0. 总体结论

**Verdict**: {APPROVED / APPROVED_WITH_CONDITIONS / NEEDS_REVISION / NEEDS_INFO / REJECTED}

{一句话总结}

## 1. 上一轮 Issue 验证

| Issue ID | A 声称 | B 验证 | 证据 | verified |
|---|---|---|---|---|
| REV-v{X.Y}-{slug}-r{R-1}-01 | fixed | verified | {证据} | ✅ |

## 2. 需求合规审查

### 2.1 上一轮 Issue 全覆盖

{检查 A 是否处理了所有上一轮 Issue}

### 2.2 review_focus 回应

{回应 A 在送审报告 §5 提出的审计焦点}

### 2.3 5 层自检证据复核

| 层 | A 声称 | B 复核 | verified |
|---|---|---|---|
| 1 | ✅ diff 为空 | 复核结论 | ✅/❌ |
| 2 | ✅ QC 一致 | 复核结论 | ✅/❌ |
| 3 | ✅ 0 差异 | 复核结论 | ✅/❌ |
| 4 | ✅ 原 skill 一致 | 复核结论 | ✅/❌ |
| 5 | ✅ 回归通过 | 复核结论 | ✅/❌ |

## 3. 代码质量审查

### 3.1 CRITICAL(功能等价性 / 数据完整性)

{CRITICAL Issue 清单,无则写"无 Issue,检查范围:..."}

### 3.2 WARNING(文档一致性 / 接口兼容性)

{WARNING Issue 清单}

### 3.3 INFO(改进建议)

{INFO 改进建议}

## 4. 下一轮指引

{如果 NEEDS_REVISION,给 A 的修复指引;如果 APPROVED,通知 Agent C 归档}
