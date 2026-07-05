---
# 送审报告 frontmatter(A 角色)
# 复制本模板填充,替换 {占位符}

# --- 基础元数据 ---
submission_id: A{N}-{slug}-r{R}        # 与文件名一致
slug: {slug}                           # v{XX}-{主题},整个循环不变
skill_version: v{X.Y}                  # 如 v2.1.0
round: {R}                             # 首轮=1,修复轮由上一轮 +1
created_at: "YYYY-MM-DD HH:MM:SS"      # 必须加引号
author: agent_a

# --- 代码快照 ---
git_tag: audit/v{X.Y}-{slug}-r{R}      # commit 后打,push 前完成
commit_hash: a1b2c3d                   # git rev-parse --short <tag>,6 位
previous_git_tag: null                 # 首轮 null,修复轮填上一轮 tag

# --- 变更文件 ---
changed_files:
  - path/relative/to/skill/root.py     # modified / added / deleted

# --- 状态机 ---
status: PENDING_REVIEW                 # PENDING_REVIEW | BLOCKED

# --- 上一轮 Issue 处理(首轮省略)---
addressed_issues:
  - id: REV-v{X.Y}-{slug}-r{R-1}-01
    resolution: fixed                  # fixed | wontfix | partial | disputed | superseded
    evidence: "文件:行号,说明修复方式"

# --- 强制自审(4 bool 必填)---
self_review:
  all_issues_addressed: true           # 上一轮 CRITICAL/WARNING 全部处理了?
  no_overengineering: true             # 没引入不必要的抽象?
  function_equivalence_verified: true  # 功能等价性验证了?(ABS工具箱特色:5 层自检)
  edge_cases_covered: true             # 边界情况测了?
  notes: ""

# --- 审计焦点(可选)---
review_focus: []
---

<!--
正文 checklist(A 角色必守):
[x] §1 变更摘要(200 字内)
[x] §2 上一轮 Issue 处理表(首轮省略)
[x] §3 代码变更清单(与 changed_files 一致)
[x] §4.1 强制自审清单(4 checkbox,与 frontmatter self_review 一致)
[x] §4.2 5 层自检证据(ABS工具箱特色:字节对比/端到端穿行/逐 cell diff/原 skill smoke/回归)
[x] §5 审计焦点(可选)
[x] §6 附录(测试输出 + 逐 cell diff 结果)
禁止:社交性语言 / "已修复"等无定位声称 / 未提交代码就填 git_tag
-->

# {slug} r{R} 送审报告

## 1. 变更摘要(200 字内)

{一句话说明本轮做了什么}

## 2. 上一轮 Issue 处理(首轮省略)

| Issue ID | 严重程度 | 处理方式 | 证据 |
|---|---|---|---|
| REV-v{X.Y}-{slug}-r{R-1}-01 | CRITICAL | fixed | 文件:行号 |

## 3. 代码变更清单

| 文件 | 操作 | 说明 |
|---|---|---|
| scripts/xxx.py | added/modified/deleted | 一句话 |

## 4. 自审与指标

### 4.1 强制自审清单

- [ ] all_issues_addressed: 上一轮 CRITICAL/WARNING 全部处理
- [ ] no_overengineering: 没引入不必要的抽象
- [ ] function_equivalence_verified: 5 层自检通过,功能与原 skill 等价
- [ ] edge_cases_covered: 边界情况测试

### 4.2 5 层自检证据

| 层 | 检查 | 结果 | 证据 |
|---|---|---|---|
| 1 | 文件字节对比 | ✅/❌ | diff 输出 |
| 2 | 端到端穿行 | ✅/❌ | QC 结果对比 |
| 3 | 逐 cell diff | ✅/❌ | cell 数 + 差异数 |
| 4 | 原 skill smoke | ✅/❌ | 原 skill QC 输出 |
| 5 | 回归测试 | ✅/❌ | 机构统计 QC 输出 |

## 5. 审计焦点(可选·给 B 的提示)

{给 B 的审查提示,如"重点核查某函数"}

## 6. 附录

{测试输出 + 逐 cell diff 完整结果}
