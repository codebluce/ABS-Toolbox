# ABS工具箱 Audit Index

> 本文件手动维护(后续可脚本化,参见 macro-allocation-strategy/scripts/refresh_audit_index.py)。
> 最后刷新:2026-07-05

## 统计概览

- 送审轮次(submissions):2
- 复审轮次(reviews):1(v21-bookkeeping r1 已完成,APPROVED_WITH_CONDITIONS)
- 归档(closed):0
- 已验证 Issue:0
- 待处理 Issue:3(2 WARNING + 1 INFO,均 blocks_approval=false)

## Submissions

| slug | round | status | self_review | created | git_tag | commit | file |
|---|---|---|---|---|---|---|---|
| v20-institution-stats | r1 | PENDING_REVIEW(已通过独立审计,4 瑕疵已修正) | ✅ 4/4 | 2026-07-05 | `audit/v2.0-v20-institution-stats-r01` | `524cdae` | [A1-v20-institution-stats-r1.md](submissions/A1-v20-institution-stats-r1.md) |
| v21-bookkeeping | r1 | REVIEWED(APPROVED_WITH_CONDITIONS) | ✅ 4/4 | 2026-07-05 | `audit/v2.1-v21-bookkeeping-r01`(⚠️未创建) | `27f08a8` | [A1-v21-bookkeeping-r1.md](submissions/A1-v21-bookkeeping-r1.md) |

## Reviews

| slug | round | status | issues | created | file |
|---|---|---|---|---|---|
| v21-bookkeeping | r1 | REVIEWED / APPROVED_WITH_CONDITIONS | 3(2 WARNING+1 INFO) | 2026-07-05 | [B1-v21-bookkeeping-r1.md](reviews/B1-v21-bookkeeping-r1.md) |

> 注:v20 r1 已通过用户委托的独立审计(4 瑕疵已修正),审计意见未走正式 B 流程,直接待 Agent C 归档。

## Closed

| slug | round | final_verdict | total_rounds | closed_at | file |
|---|---|---|---|---|---|
| _暂无_ | | | | | |

## Open Issues

| Issue ID | slug | round | severity | status | review_file |
|---|---|---|---|---|---|
| REV-v2.1-v21-bookkeeping-r01-01 | v21-bookkeeping | r1 | WARNING | open | [B1](reviews/B1-v21-bookkeeping-r1.md) |
| REV-v2.1-v21-bookkeeping-r01-02 | v21-bookkeeping | r1 | WARNING | open | [B1](reviews/B1-v21-bookkeeping-r1.md) |
| REV-v2.1-v21-bookkeeping-r01-03 | v21-bookkeeping | r1 | INFO | open | [B1](reviews/B1-v21-bookkeeping-r1.md) |

## slug 流转状态

| slug | 当前轮次 | 下一动作 | 备注 |
|---|---|---|---|
| v20-institution-stats | r1 已通过独立审计 | 待 Agent C 归档 | 4 瑕疵已在修正轮处理,可直接归档 |
| v21-bookkeeping | r1 REVIEWED(APPROVED_WITH_CONDITIONS) | 待 Agent C 归档 | 功能字节级等价无回归;归档前须补打 git tag + 修正 pitfall #ABS-002 |

## 命名规则

| 类型 | 格式 | 示例 |
|---|---|---|
| 送审报告 | `A{N}-{slug}-r{R}.md` | `A1-v20-institution-stats-r1.md` |
| 审计意见 | `B{N}-{slug}-r{R}.md` | `B1-v20-institution-stats-r1.md` |
| 归档报告 | `C{N}-{slug}-r{R}.md` | `C1-v20-institution-stats-r1.md` |
| git tag | `audit/v{X.Y}-{slug}-r{NN}` | `audit/v2.0-v20-institution-stats-r01` |
| Issue ID | `REV-v{X.Y}-{slug}-r{NN}-{seq}` | `REV-v2.0-v20-institution-stats-r01-01` |

详见 `audit/README.md`。
