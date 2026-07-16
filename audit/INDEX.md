# ABS工具箱 Audit Index

> 本文件手动维护(后续可脚本化,参见 macro-allocation-strategy/scripts/refresh_audit_index.py)。
> 最后刷新:2026-07-16

## 统计概览

- 送审轮次(submissions):8
- 复审轮次(reviews):7(v21-bookkeeping r1 APPROVED 已归档;v22-pricing r1 APPROVED_WITH_CONDITIONS 已归档;v20-institution-stats r1 走独立审计等效 APPROVED 已归档;v23-internal-merge-unify r1 APPROVED_WITH_CONDITIONS 已归档;v24-self-check r1 APPROVED_WITH_CONDITIONS 已归档;v25-match-rule-tune r1 APPROVED_WITH_CONDITIONS 已归档;v26-uv-protection r1 NEEDS_REVISION;v27-p0-hardening r1 APPROVED_WITH_CONDITIONS 待归档)
- 归档(closed):6(v20-institution-stats r1 + v21-bookkeeping r1 + v22-pricing r1 + v23-internal-merge-unify r1 + v24-self-check r1 + v25-match-rule-tune r1 均已归档)
- 已验证 Issue:0
- 待处理 Issue:5(v26-uv-protection r1:1 CRITICAL FAIL阻断无效 + 1 WARNING changed_files遗漏 + 1 WARNING rebook行号对齐;v27-p0-hardening r1:1 WARNING fig8保守漏计需确认unmatched=7金额 + 1 INFO 字符串日期比较)

## Submissions

| slug | round | status | self_review | created | git_tag | commit | file |
|---|---|---|---|---|---|---|---|
| v20-institution-stats | r1 | COMPLETED(已归档,独立审计等效 APPROVED) | ✅ 4/4 | 2026-07-05 | `audit/v2.0-v20-institution-stats-r01`(✅已双推) | `524cdae` | [A1-v20-institution-stats-r1.md](submissions/A1-v20-institution-stats-r1.md) |
| v21-bookkeeping | r1 | COMPLETED(已归档) | ✅ 4/4 | 2026-07-05 | `audit/v2.1-v21-bookkeeping-r01`(✅已双推) | `27f08a8` | [A1-v21-bookkeeping-r1.md](submissions/A1-v21-bookkeeping-r1.md) |
| v22-pricing | r1 | COMPLETED(已归档) | ✅ 4/4 | 2026-07-05 | `audit/v2.2-v22-pricing-r01`(✅已双推) | `1e14550` | [A1-v22-pricing-r1.md](submissions/A1-v22-pricing-r1.md) |
| v23-internal-merge-unify | r1 | COMPLETED(已归档) | ✅ 4/4 | 2026-07-05 | `audit/v2.3-v23-internal-merge-unify-r01`(✅已双推) | `1ef0612` | [A1-v23-internal-merge-unify-r1.md](submissions/A1-v23-internal-merge-unify-r1.md) |
| v24-self-check | r1 | COMPLETED(已归档) | ✅ 4/4 | 2026-07-05 | `audit/v2.4-v24-self-check-r01`(✅已双推) | `31f716f` | [A1-v24-self-check-r1.md](submissions/A1-v24-self-check-r1.md) |
| v25-match-rule-tune | r1 | COMPLETED(已归档) | ✅ 4/4 | 2026-07-05 | `audit/v2.5-v25-match-rule-tune-r01`(✅已双推) | `ae1907e` | [A1-v25-match-rule-tune-r1.md](submissions/A1-v25-match-rule-tune-r1.md) |
| v26-uv-protection | r1 | NEEDS_REVISION | ✅ 4/4 | 2026-07-13 | `audit/v2.5.1-v26-uv-protection-r01`(✅已双推) | `1ad1a89` | [A1-v26-uv-protection-r1.md](submissions/A1-v26-uv-protection-r1.md) |
| v27-p0-hardening | r1 | REVIEWED / APPROVED_WITH_CONDITIONS | ✅ 4/4 | 2026-07-16 | `audit/v2.5.4-v27-p0-hardening-r01`(✅已双推) | `c9c2626` | [A1-v27-p0-hardening-r1.md](submissions/A1-v27-p0-hardening-r1.md) |

## Reviews

| slug | round | status | issues | created | file |
|---|---|---|---|---|---|
| v21-bookkeeping | r1 | REVIEWED / APPROVED | 3(全部关闭:2 WARNING 平反 resolved + 1 INFO) | 2026-07-05 | [B1-v21-bookkeeping-r1.md](reviews/B1-v21-bookkeeping-r1.md) |
| v22-pricing | r1 | REVIEWED / APPROVED_WITH_CONDITIONS | 3(全部 DOC_CONSISTENCY WARNING,均无害不阻断,待 C 留档) | 2026-07-05 | [B1-v22-pricing-r1.md](reviews/B1-v22-pricing-r1.md) |
| v23-internal-merge-unify | r1 | REVIEWED / APPROVED_WITH_CONDITIONS | 4(3 WARNING + 1 INFO,全部 DOC_CONSISTENCY/FUNCTION_EQUIVALENCE,均无害不阻断,待 C 留档) | 2026-07-05 | [B1-v23-internal-merge-unify-r1.md](reviews/B1-v23-internal-merge-unify-r1.md) |
| v24-self-check | r1 | REVIEWED / APPROVED_WITH_CONDITIONS | 4(3 WARNING + 1 INFO,全部 DOC_CONSISTENCY/MAINTAINABILITY,均无害不阻断,待 C 留档) | 2026-07-05 | [B1-v24-self-check-r1.md](reviews/B1-v24-self-check-r1.md) |
| v25-match-rule-tune | r1 | REVIEWED / APPROVED_WITH_CONDITIONS | 2(1 WARNING DOC_CONSISTENCY + 1 INFO FUNCTION_EQUIVALENCE,均无害不阻断,待 C 留档) | 2026-07-05 | [B1-v25-match-rule-tune-r1.md](reviews/B1-v25-match-rule-tune-r1.md) |
| v26-uv-protection | r1 | REVIEWED / NEEDS_REVISION | 3(1 CRITICAL FAIL阻断无效 blocks_approval + 1 WARNING changed_files遗漏 + 1 WARNING rebook行号对齐) | 2026-07-13 | [B1-v26-uv-protection-r1.md](reviews/B1-v26-uv-protection-r1.md) |
| v27-p0-hardening | r1 | REVIEWED / APPROVED_WITH_CONDITIONS | 2(1 WARNING FUNCTION_EQUIVALENCE fig8保守漏计需确认unmatched=7金额 + 1 INFO 字符串日期比较,均不阻断,待 C 留档+确认) | 2026-07-16 | [B1-v27-p0-hardening-r1.md](reviews/B1-v27-p0-hardening-r1.md) |

> 注:v20 r1 已通过用户委托的独立审计(4 瑕疵已修正),审计意见未走正式 B 流程,直接待 Agent C 归档。

## Closed

| slug | round | final_verdict | total_rounds | closed_at | file |
|---|---|---|---|---|---|
| v20-institution-stats | r1 | APPROVED(独立审计等效) | 1(含修正轮) | 2026-07-05 | [C1-v20-institution-stats-r1.md](closed/C1-v20-institution-stats-r1.md) |
| v21-bookkeeping | r1 | APPROVED | 1 | 2026-07-05 | [C1-v21-bookkeeping-r1.md](closed/C1-v21-bookkeeping-r1.md) |
| v22-pricing | r1 | APPROVED_WITH_CONDITIONS | 1 | 2026-07-05 | [C1-v22-pricing-r1.md](closed/C1-v22-pricing-r1.md) |
| v23-internal-merge-unify | r1 | APPROVED_WITH_CONDITIONS | 1 | 2026-07-05 | [C1-v23-internal-merge-unify-r1.md](closed/C1-v23-internal-merge-unify-r1.md) |
| v24-self-check | r1 | APPROVED_WITH_CONDITIONS | 1 | 2026-07-05 | [C1-v24-self-check-r1.md](closed/C1-v24-self-check-r1.md) |
| v25-match-rule-tune | r1 | APPROVED_WITH_CONDITIONS | 1 | 2026-07-05 | [C1-v25-match-rule-tune-r1.md](closed/C1-v25-match-rule-tune-r1.md) |

## Open Issues

| Issue ID | slug | round | severity | status | review_file |
|---|---|---|---|---|---|
| REV-v2.1-v21-bookkeeping-r01-01 | v21-bookkeeping | r1 | INFO | resolved(函数真实存在,假阳性平反) | [B1](reviews/B1-v21-bookkeeping-r1.md) |
| REV-v2.1-v21-bookkeeping-r01-02 | v21-bookkeeping | r1 | WARNING | resolved(tag已双推,假阳性平反) | [B1](reviews/B1-v21-bookkeeping-r1.md) |
| REV-v2.1-v21-bookkeeping-r01-03 | v21-bookkeeping | r1 | INFO | open(仅提示,无需处理) | [B1](reviews/B1-v21-bookkeeping-r1.md) |
| REV-v2.2-v22-pricing-r01-01 | v22-pricing | r1 | WARNING | resolved(C1 留档:commit_hash 以 tag→1e14550 为准,A1 frontmatter 误填 03225ef) | [B1](reviews/B1-v22-pricing-r1.md) |
| REV-v2.2-v22-pricing-r01-02 | v22-pricing | r1 | WARNING | resolved(C1 留档:补记完整 changed_files 清单 11 文件,pitfall_log 删除+.gitignore 无害) | [B1](reviews/B1-v22-pricing-r1.md) |
| REV-v2.2-v22-pricing-r01-03 | v22-pricing | r1 | WARNING | resolved(SKILL.md version 已由 B 顺手升至 2.2.0) | [B1](reviews/B1-v22-pricing-r1.md) |
| REV-v2.3-v23-internal-merge-unify-r01-01 | v23-internal-merge-unify | r1 | WARNING | resolved(C1 留档:commit_hash 以 tag→1ef0612 为准,A1 frontmatter 误填 e9cf091) | [B1](reviews/B1-v23-internal-merge-unify-r1.md) |
| REV-v2.3-v23-internal-merge-unify-r01-02 | v23-internal-merge-unify | r1 | WARNING | resolved(C1 留档:补记完整 13 文件 changed_files 清单;§1§6.3 矛盾留档) | [B1](reviews/B1-v23-internal-merge-unify-r1.md) |
| REV-v2.3-v23-internal-merge-unify-r01-03 | v23-internal-merge-unify | r1 | WARNING | resolved(SKILL.md version 已由 C 顺手升至 2.3.0) | [B1](reviews/B1-v23-internal-merge-unify-r1.md) |
| REV-v2.3-v23-internal-merge-unify-r01-04 | v23-internal-merge-unify | r1 | INFO | resolved(C1 留档:22列实际24列口径确认,不影响等价性) | [B1](reviews/B1-v23-internal-merge-unify-r1.md) |
| REV-v2.4-v24-self-check-r01-01 | v24-self-check | r1 | WARNING | resolved(C1 留档:self_check.py 行数以 git 实测 919 为准,A1 §6 误填 642) | [B1](reviews/B1-v24-self-check-r1.md) |
| REV-v2.4-v24-self-check-r01-02 | v24-self-check | r1 | WARNING | resolved(C1 留档:补记完整 changed_files 清单,移除 .gitkeep 误声明) | [B1](reviews/B1-v24-self-check-r1.md) |
| REV-v2.4-v24-self-check-r01-03 | v24-self-check | r1 | WARNING | resolved(C1 留档:移除 pitfall_log.md 误报 modified 项,实际 v2.3 后未改) | [B1](reviews/B1-v24-self-check-r1.md) |
| REV-v2.4-v24-self-check-r01-04 | v24-self-check | r1 | INFO | resolved(C1 留档:auto 自动降级分支延期至原 skill 退役时实测;污染 deliverables/dashboards/01_latest/ 归档时排除) | [B1](reviews/B1-v24-self-check-r1.md) |
| REV-v2.5-v25-match-rule-tune-r01-01 | v25-match-rule-tune | r1 | WARNING | resolved(C1 留档:changed_files 实际 4 文件含送审报告自身,送审报告入 commit 属业界惯例,补记完整清单) | [B1](reviews/B1-v25-match-rule-tune-r1.md) |
| REV-v2.5-v25-match-rule-tune-r01-02 | v25-match-rule-tune | r1 | INFO | resolved(C1 留档/延期:Pass4 len>=3 阈值+MATCH_HARD_MAP 业务观察 1-2 周,发现新难匹配 case 再扩展) | [B1](reviews/B1-v25-match-rule-tune-r1.md) |
| REV-v2.5.4-v27-p0-hardening-r1-01 | v27-p0-hardening | r1 | WARNING | open(fig6/fig8 保守匹配 multi/大额unmatched 不计入,方向正确但存漏计风险;待 Agent C 归档确认 fig8 unmatched=7 金额量级,含大额则记 audit_escape_risk 或 v28 扩展匹配规则) | [B1](reviews/B1-v27-p0-hardening-r1.md) |
| REV-v2.5.4-v27-p0-hardening-r1-02 | v27-p0-hardening | r1 | INFO | open(fig8 mask 字符串日期比较依赖隐式转换,当前格式统一正确,建议后续统一 to_datetime;C1 留档) | [B1](reviews/B1-v27-p0-hardening-r1.md) |

> 注:首轮 2 项 WARNING(REV-01/REV-02)经二次独立复核确认均为本地核查环境假阳性(.git 损坏 + 编码搜索漏匹配),已全部平反 resolved,无阻断归档的遗留 Issue。
> 技术债 #ABS-002(internal_merge 与 run_increment_merge 并存)留第三轮封装层处理,详见 [C1 归档报告](closed/C1-v21-bookkeeping-r1.md) §3 audit_escape_risks。
> 注:v22-pricing r1 三项 WARNING 均为 DOC_CONSISTENCY 文档一致性瑕疵,REV-03 已修复,REV-01/02 由 C1 留档关闭(详见 [C1-v22-pricing-r1.md](closed/C1-v22-pricing-r1.md) §2 Issue 生命周期)。
> 注:v23-internal-merge-unify r1 四项瑕疵(3 WARNING + 1 INFO),REV-03(SKILL.md version)由 C 顺手修复,REV-01/02/04 由 C1 留档关闭(详见 [C1-v23-internal-merge-unify-r1.md](closed/C1-v23-internal-merge-unify-r1.md) §2)。技术债 #ABS-002 于 v2.3.0 主动闭环,v20/v21/v22 三个 C1 的 deferred_critical 全部解除。

## slug 流转状态

| slug | 当前轮次 | 下一动作 | 备注 |
|---|---|---|---|
| v20-institution-stats | r1 已归档(COMPLETED,独立审计等效 APPROVED) | — | 4 瑕疵+1 遗留已在修正轮处理;B 流程缺失留档为逃逸风险(MEDIUM) |
| v21-bookkeeping | r1 已归档(COMPLETED) | — | 功能字节级等价无回归;首轮 2 项 WARNING 均系核查环境假阳性已平反;技术债 #ABS-002 留第三轮封装层处理 |
| v22-pricing | r1 已归档(COMPLETED) | — | v2.2.0 第三轮发行定价迁入,APPROVED_WITH_CONDITIONS;3 项 DOC_CONSISTENCY 瑕疵 REV-03 已修复,REV-01/02 由 C1 留档关闭 |
| v23-internal-merge-unify | r1 已归档(COMPLETED,APPROVED_WITH_CONDITIONS) | — | v2.3.0 第四轮 internal_merge 翻译官改造,闭环 #ABS-002(解除 v20/v21/v22 三个 C1 的 deferred_critical);6 层自检通过;4 项瑕疵 REV-03 已修复,REV-01/02/04 由 C1 留档关闭 |
| v24-self-check | r1 已归档(COMPLETED) | — | v2.4.0 新增 5 层自检工具脚本;核心层 3 逐 cell diff 回归闸门通过(13753 cell 0 差异);降级模式 --mode degraded 已验;3 项 WARNING + 1 INFO 由 C1 留档关闭;延期验证项:auto 自动降级分支留原 skill 退役时实测 |
| v25-match-rule-tune | r1 已归档(COMPLETED) | — | v2.5.0 匹配规则调优:normalize 去连字符+全角空格 bug 修复+core_name+MATCH_HARD_MAP+Pass 1-4 优先级链+rebook 默认模式;5 处改动 git show ae1907e 逐行独立核查全真实、优先级链守卫顺序正确、rebook 向后兼容;6 层自检层1/6 读代码确认+层2-5采信 A 输出;§5 污染文件声明与实际一致(commit 仅 4 文件,较 v22/v23/v24 洁净性显著改善);2 项瑕疵(1 WARNING changed_files 口径+1 INFO 阈值观察)由 C1 留档关闭;延期观察:Pass4 阈值/hard_map 业务观察 1-2 周 |
| v26-uv-protection | r1 NEEDS_REVISION | A-fix | B1 已指出 QC FAIL 阻断无效等 3 项 Issue，待修复轮 |
| v27-p0-hardening | r1 REVIEWED(APPROVED_WITH_CONDITIONS) | C-close | v2.5.4 P0 防错包：4 焦点独立读代码全 PASS 无 CRITICAL。焦点1 QC 真阻断——rename 架构(qc_fails>0→os.remove tmp→return 不落盘,仅 PASS 分支 os.rename),全程无 wb.save,从架构规避 v26 REV-01 同类隐患；焦点2 WXY三元组 wxy_complete==3 统一 where 整行取舍消除拼接；焦点3 fig6/fig8 唯一匹配+multi不计入WARN+大额unmatched告警(保守防重复)；焦点4 #ABS-006 iloc[1:] 单行表头修复。2 项 Issue 均不阻断；1 condition 待 C 归档确认 fig8 unmatched=7 金额量级 |

## 命名规则

| 类型 | 格式 | 示例 |
|---|---|---|
| 送审报告 | `A{N}-{slug}-r{R}.md` | `A1-v20-institution-stats-r1.md` |
| 审计意见 | `B{N}-{slug}-r{R}.md` | `B1-v20-institution-stats-r1.md` |
| 归档报告 | `C{N}-{slug}-r{R}.md` | `C1-v20-institution-stats-r1.md` |
| git tag | `audit/v{X.Y}-{slug}-r{NN}` | `audit/v2.0-v20-institution-stats-r01` |
| Issue ID | `REV-v{X.Y}-{slug}-r{NN}-{seq}` | `REV-v2.0-v20-institution-stats-r01-01` |

详见 `audit/README.md`。
