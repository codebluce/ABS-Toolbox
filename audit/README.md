# ABS工具箱 审计子系统操作手册

> **本文件是人类参考手册**。Agent A/B/C 执行时以 `audit/{submissions,reviews,closed}/_template.md` 为字段定义源。
> 由人类维护，Agent 只读。最后更新：2026-07-05（v2.1.0 第二轮落地）。

## 1. 目录结构

```
audit/
├── README.md                # 本文件(人类参考手册)
├── INDEX.md                 # 审计索引(手动维护,后续可脚本化)
├── submissions/             # 送审报告(Agent A 写)
│   ├── _template.md         # 送审报告模板
│   └── A{N}-{slug}-r{R}.md
├── reviews/                 # 审计意见(Agent B 写)
│   ├── _template.md         # 审计意见模板
│   └── B{N}-{slug}-r{R}.md
└── closed/                  # 归档报告(Agent C 写)
    ├── _template.md         # 归档报告模板
    └── C{N}-{slug}-r{R}.md
```

## 2. 送审流程(A→B→C 循环)

1. **Agent A 实现代码** + 打 git tag + 写送审报告 → push abs-toolbox 仓库
2. **人类通知 Agent B 审计**(B 是独立 Agent,不写代码,只读代码+送审报告)
3. **Agent B 写审计意见** → push
4. **根据 verdict**:
   - `APPROVED` / `APPROVED_WITH_CONDITIONS` → 通知 Agent C 归档
   - `NEEDS_REVISION` → 通知 Agent A 下一轮(round +1)
   - `NEEDS_INFO` → 通知 Agent A 答疑(不消耗轮次)
   - `REJECTED` → slug 终止
5. **Agent C 归档** → 人类复核 → COMPLETED

## 3. 文件命名规则

| 类型 | 格式 | 示例 |
|------|------|------|
| 送审报告 | `A{N}-{slug}-r{R}.md` | `A1-v20-institution-stats-r1.md` |
| 审计意见 | `B{N}-{slug}-r{R}.md` | `B1-v20-institution-stats-r1.md` |
| 归档报告 | `C{N}-{slug}-r{R}.md` | `C1-v20-institution-stats-r1.md` |
| git tag | `audit/v{X.Y}-{slug}-r{NN}` | `audit/v2.0-v20-institution-stats-r01` |
| Issue ID | `REV-v{X.Y}-{slug}-r{NN}-{seq}` | `REV-v2.0-v20-institution-stats-r01-01` |

**字段说明**:
- `N` = 该 slug 内的序号(A1/A2/A3...,B1/B2/B3...,C1),每轮递增
- `R` = 轮次号(r1/r2/r3...),每轮递增
- `slug` = 整合阶段 kebab-case(如 `v20-institution-stats`、`v21-bookkeeping`)

**slug 命名规范**:
- slug 带版本前缀,避免跨版本同名 slug 混淆
- 格式:`v{XX}-{主题}`(如 `v20-institution-stats`、`v21-bookkeeping`、`v22-pricing`)
- 跨版本升级时,新版本用新 slug
- 同版本内多次迭代用 round 号区分(r1/r2/r3...),不改 slug

## 4. ABS工具箱 vs macro-allocation-strategy 审计差异

| 维度 | macro-allocation-strategy | ABS工具箱 |
|---|---|---|
| 审计对象 | 策略代码 + 回测指标 | skill 整合代码 + 功能等价性 |
| 自检核心 | Sharpe/Drawdown/胜率 | 5 层自检(字节对比/逐 cell diff/QC 一致) |
| frontmatter 字段 | 14 字段(含 strategy_version/blocker/rebase) | 精简 8 字段 |
| 校验脚本 | validate_audit.py + refresh_audit_index.py + next_action.py | 暂手动维护 INDEX.md,第二轮稳定后再脚本化 |
| git tag 强制 | 是 | 是 |

## 5. 送审报告 frontmatter 字段(精简 8 字段)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `submission_id` | str | 是 | `A{N}-{slug}-r{R}`(与文件名一致) |
| `slug` | str | 是 | 整合阶段 kebab-case |
| `skill_version` | str | 是 | 如 `v2.1.0` |
| `round` | int | 是 | 当前轮次 |
| `created_at` | datetime | 是 | ISO 8601 |
| `author` | str | 是 | `agent_a` |
| `git_tag` | str | 是 | `audit/v{X.Y}-{slug}-r{NN}` |
| `commit_hash` | str | 是 | 6 位短 hash |
| `previous_git_tag` | str | 否 | 上一轮 tag,首轮 null |
| `changed_files` | list[str] | 是 | 本轮变更文件清单 |
| `status` | enum | 是 | PENDING_REVIEW / BLOCKED |
| `addressed_issues` | list[obj] | 否 | 上一轮 Issue 处理 |
| `self_review` | obj | 是 | 4 bool + notes |

## 6. 送审报告正文结构

```
# {slug} r{R} 送审报告

## 1. 变更摘要(200 字内)
## 2. 上一轮 Issue 处理(首轮省略)
## 3. 代码变更清单(基于 changed_files 展开)
## 4. 自审与指标
  ### 4.1 强制自审清单(4 bool 必填)
  ### 4.2 5 层自检证据(ABS工具箱特色)
## 5. 审计焦点(可选·给 B 的提示)
## 6. 附录(测试输出 + 逐 cell diff 结果)
```

## 7. 审计意见 frontmatter 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `review_id` | str | 是 | `B{N}-{slug}-r{R}` |
| `submission_id` | str | 是 | 对应的 submission_id |
| `slug` / `skill_version` / `round` / `auditor` / `created_at` | - | 是 | 基础元数据 |
| `git_tag` | str | 是 | 与 submission 一致 |
| `verified_tag_hash` | str | 是 | B 校验后的 commit hash |
| `verdict` | enum | 是 | APPROVED / APPROVED_WITH_CONDITIONS / NEEDS_REVISION / NEEDS_INFO / REJECTED |
| `issues` | list[obj] | 是 | Issue 列表 |
| `verified_issues` | list[obj] | 是 | 验证上一轮 Issue |
| `conditions` | list[str] | APPROVED_WITH_CONDITIONS 时必填 | 待用户复核条件 |

## 8. 审计意见正文结构

```
# {slug} r{R} 审计意见

## 0. 总体结论(verdict + 一句话总结)
## 1. 上一轮 Issue 验证(含证据列)
## 2. 需求合规审查
  ### 2.1 上一轮 Issue 全覆盖
  ### 2.2 review_focus 回应
  ### 2.3 5 层自检证据复核
## 3. 代码质量审查
  ### 3.1 CRITICAL(功能等价性 / 数据完整性)
  ### 3.2 WARNING(文档一致性 / 接口兼容性)
  ### 3.3 INFO(改进建议)
## 4. 下一轮指引
```

## 9. 归档报告 frontmatter 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `closed_id` / `slug` / `skill_version` / `closed_at` / `closed_by` | - | 是 | 基础元数据 |
| `final_verdict` | enum | 是 | APPROVED / APPROVED_WITH_CONDITIONS |
| `total_rounds` | int | 是 | 总轮次 |
| `final_submission` | str | 是 | 最终 submission_id |
| `all_issues_resolved` | bool | 是 | 是否所有 Issue 已闭环 |
| `audit_escape_risks` | list[obj] | 是 | C 标记的逃逸风险 |
| `conditions` | list[str] | APPROVED_WITH_CONDITIONS 时必填 | 待用户复核条件 |

## 10. 已归档送审报告清单

| submission_id | slug | skill_version | round | status | git_tag | 日期 |
|---|---|---|---|---|---|---|
| A1-v20-institution-stats-r1 | v20-institution-stats | v2.0.0 | r1 | PENDING_REVIEW(已通过独立审计) | `7665fbd`(主仓库) / `524cdae`(abs-toolbox) | 2026-07-05 |
| A1-v20-institution-stats-r2 | v20-institution-stats | v2.0.0 | r2 | PENDING_REVIEW(修正轮) | `55c3ef2`(主仓库) / `524cdae`(abs-toolbox) | 2026-07-05 |
| A1-v21-bookkeeping-r1 | v21-bookkeeping | v2.1.0 | r1 | PENDING_REVIEW | `27f08a8`(abs-toolbox) | 2026-07-05 |

> 注:A1-v20-institution-stats-r1/r2 在 v2.0.0 落地时未走正式 A→B→C 流程,事后补归档。r2 的独立审计由用户委托的 Agent 已完成(4 处瑕疵+1 项遗留已修正)。
