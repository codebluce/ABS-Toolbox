# ABS工具箱 Audit Index

> 本文件手动维护(后续可脚本化,参见 macro-allocation-strategy/scripts/refresh_audit_index.py)。
> 最后刷新:2026-07-05

## 统计概览

- 送审轮次(submissions):2
- 复审轮次(reviews):1(v21-bookkeeping r1 已完成,APPROVED 无条件通过)
- 归档(closed):1(v21-bookkeeping r1 已归档)
- 已验证 Issue:0
- 待处理 Issue:0(首轮 2 项 WARNING 经复核均为核查环境假阳性并已平反 resolved;1 项 INFO 提示无需处理;1 项 MEDIUM 技术债 #ABS-002 留第三轮封装层处理)

## Submissions

| slug | round | status | self_review | created | git_tag | commit | file |
|---|---|---|---|---|---|---|---|
| v20-institution-stats | r1 | PENDING_REVIEW(已通过独立审计,4 瑕疵已修正) | ✅ 4/4 | 2026-07-05 | `audit/v2.0-v20-institution-stats-r01` | `524cdae` | [A1-v20-institution-stats-r1.md](submissions/A1-v20-institution-stats-r1.md) |
| v21-bookkeeping | r1 | COMPLETED(已归档) | ✅ 4/4 | 2026-07-05 | `audit/v2.1-v21-bookkeeping-r01`(✅已双推) | `27f08a8` | [A1-v21-bookkeeping-r1.md](submissions/A1-v21-bookkeeping-r1.md) |

## Reviews

| slug | round | status | issues | created | file |
|---|---|---|---|---|---|
| v21-bookkeeping | r1 | REVIEWED / APPROVED | 3(全部关闭:2 WARNING 平反 resolved + 1 INFO) | 2026-07-05 | [B1-v21-bookkeeping-r1.md](reviews/B1-v21-bookkeeping-r1.md) |

> 注:v20 r1 已通过用户委托的独立审计(4 瑕疵已修正),审计意见未走正式 B 流程,直接待 Agent C 归档。

## Closed

| slug | round | final_verdict | total_rounds | closed_at | file |
|---|---|---|---|---|---|
| v21-bookkeeping | r1 | APPROVED | 1 | 2026-07-05 | [C1-v21-bookkeeping-r1.md](closed/C1-v21-bookkeeping-r1.md) |

## Open Issues

| Issue ID | slug | round | severity | status | review_file |
|---|---|---|---|---|---|
| REV-v2.1-v21-bookkeeping-r01-01 | v21-bookkeeping | r1 | INFO | resolved(函数真实存在,假阳性平反) | [B1](reviews/B1-v21-bookkeeping-r1.md) |
| REV-v2.1-v21-bookkeeping-r01-02 | v21-bookkeeping | r1 | WARNING | resolved(tag已双推,假阳性平反) | [B1](reviews/B1-v21-bookkeeping-r1.md) |
| REV-v2.1-v21-bookkeeping-r01-03 | v21-bookkeeping | r1 | INFO | open(仅提示,无需处理) | [B1](reviews/B1-v21-bookkeeping-r1.md) |

> 注:首轮 2 项 WARNING(REV-01/REV-02)经二次独立复核确认均为本地核查环境假阳性(.git 损坏 + 编码搜索漏匹配),已全部平反 resolved,无阻断归档的遗留 Issue。
> 技术债 #ABS-002(internal_merge 与 run_increment_merge 并存)留第三轮封装层处理,详见 [C1 归档报告](closed/C1-v21-bookkeeping-r1.md) §3 audit_escape_risks。

## slug 流转状态

| slug | 当前轮次 | 下一动作 | 备注 |
|---|---|---|---|
| v20-institution-stats | r1 已通过独立审计 | 待 Agent C 归档 | 4 瑕疵已在修正轮处理,可直接归档 |
| v21-bookkeeping | r1 已归档(COMPLETED) | — | 功能字节级等价无回归;首轮 2 项 WARNING 均系核查环境假阳性已平反;技术债 #ABS-002 留第三轮封装层处理 |

## 命名规则

| 类型 | 格式 | 示例 |
|---|---|---|
| 送审报告 | `A{N}-{slug}-r{R}.md` | `A1-v20-institution-stats-r1.md` |
| 审计意见 | `B{N}-{slug}-r{R}.md` | `B1-v20-institution-stats-r1.md` |
| 归档报告 | `C{N}-{slug}-r{R}.md` | `C1-v20-institution-stats-r1.md` |
| git tag | `audit/v{X.Y}-{slug}-r{NN}` | `audit/v2.0-v20-institution-stats-r01` |
| Issue ID | `REV-v{X.Y}-{slug}-r{NN}-{seq}` | `REV-v2.0-v20-institution-stats-r01-01` |

详见 `audit/README.md`。
