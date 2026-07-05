# ABS工具箱 Audit Index

> 本文件手动维护(后续可脚本化,参见 macro-allocation-strategy/scripts/refresh_audit_index.py)。
> 最后刷新:2026-07-05

## 统计概览

- 送审轮次(submissions):2
- 复审轮次(reviews):1(DRAFT,待 Agent B 接手)
- 归档(closed):0
- 已验证 Issue:0
- 待处理 Issue:0

## Submissions

| slug | round | status | self_review | created | git_tag | commit | file |
|---|---|---|---|---|---|---|---|
| v20-institution-stats | r1 | PENDING_REVIEW(已通过独立审计,4 瑕疵已修正) | ✅ 4/4 | 2026-07-05 | `audit/v2.0-v20-institution-stats-r01` | `524cdae` | [A1-v20-institution-stats-r1.md](submissions/A1-v20-institution-stats-r1.md) |
| v21-bookkeeping | r1 | PENDING_REVIEW | ✅ 4/4 | 2026-07-05 | `audit/v2.1-v21-bookkeeping-r01` | `27f08a8` | [A1-v21-bookkeeping-r1.md](submissions/A1-v21-bookkeeping-r1.md) |

## Reviews

| slug | round | status | issues | created | file |
|---|---|---|---|---|---|
| v21-bookkeeping | r1 | DRAFT(待 Agent B 接手) | 0 | 2026-07-05 | [B1-v21-bookkeeping-r1.md](reviews/B1-v21-bookkeeping-r1.md) |

> 注:v20 r1 已通过用户委托的独立审计(4 瑕疵已修正),审计意见未走正式 B 流程,直接待 Agent C 归档。

## Closed

| slug | round | final_verdict | total_rounds | closed_at | file |
|---|---|---|---|---|---|
| _暂无_ | | | | | |

## Open Issues

| Issue ID | slug | round | severity | status | review_file |
|---|---|---|---|---|---|
| _暂无_(v20 r1 修正轮已处理独立审计 4 瑕疵+1 遗留,但未发正式 Issue ID) | | | | | |

## slug 流转状态

| slug | 当前轮次 | 下一动作 | 备注 |
|---|---|---|---|
| v20-institution-stats | r1 已通过独立审计 | 待 Agent C 归档 | 4 瑕疵已在修正轮处理,可直接归档 |
| v21-bookkeeping | r1 PENDING_REVIEW | 待 Agent B 审计 | 5 层自检通过,送审中 |

## 命名规则

| 类型 | 格式 | 示例 |
|---|---|---|
| 送审报告 | `A{N}-{slug}-r{R}.md` | `A1-v20-institution-stats-r1.md` |
| 审计意见 | `B{N}-{slug}-r{R}.md` | `B1-v20-institution-stats-r1.md` |
| 归档报告 | `C{N}-{slug}-r{R}.md` | `C1-v20-institution-stats-r1.md` |
| git tag | `audit/v{X.Y}-{slug}-r{NN}` | `audit/v2.0-v20-institution-stats-r01` |
| Issue ID | `REV-v{X.Y}-{slug}-r{NN}-{seq}` | `REV-v2.0-v20-institution-stats-r01-01` |

详见 `audit/README.md`。
