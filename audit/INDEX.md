# ABS工具箱 Audit Index

> 本文件手动维护(后续可脚本化,参见 macro-allocation-strategy/scripts/refresh_audit_index.py)。
> 最后刷新:2026-07-17

## 统计概览

- 送审轮次(submissions):11
- 复审轮次(reviews):9(v21-bookkeeping r1 APPROVED 已归档;v22-pricing r1 APPROVED_WITH_CONDITIONS 已归档;v20-institution-stats r1 走独立审计等效 APPROVED 已归档;v23-internal-merge-unify r1 APPROVED_WITH_CONDITIONS 已归档;v24-self-check r1 APPROVED_WITH_CONDITIONS 已归档;v25-match-rule-tune r1 APPROVED_WITH_CONDITIONS 已归档;v26-uv-protection r1 NEEDS_REVISION;v27-p0-hardening r1 APPROVED_WITH_CONDITIONS 已归档;v28-p123-cleanup r1 APPROVED 待归档;v29-runtime-hardening r1 APPROVED 已归档)
- 归档(closed):8(v20-institution-stats r1 + v21-bookkeeping r1 + v22-pricing r1 + v23-internal-merge-unify r1 + v24-self-check r1 + v25-match-rule-tune r1 + v27-p0-hardening r1 + v29-runtime-hardening r1 均已归档)
- 已验证 Issue:0
- 待处理 Issue:3(v26-uv-protection r1:1 CRITICAL FAIL阻断无效 + 1 WARNING changed_files遗漏 + 1 WARNING rebook行号对齐);1 个待归档 slug(v28-p123-cleanup r1 APPROVED 待 Agent C 归档);1 个待审 slug(v30-actual-share-uv r1)

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
| v28-p123-cleanup | r1 | REVIEWED / APPROVED | ✅ 4/4 | 2026-07-17 | `audit/v2.5.5-v28-p123-cleanup-r01`(✅已双推) | `932adb0` | [A1-v28-p123-cleanup-r1.md](submissions/A1-v28-p123-cleanup-r1.md) |
| v29-runtime-hardening | r1 | COMPLETED(已归档) | ✅ 4/4 | 2026-07-17 | `audit/v2.5.6-v29-runtime-hardening-r01`(✅已双推) | `1ed4874` | [A1-v29-runtime-hardening-r1.md](submissions/A1-v29-runtime-hardening-r1.md) |
| v30-actual-share-uv | r1 | PENDING_REVIEW | ✅ 4/4 | 2026-07-18 | `audit/v2.5.7-v30-actual-share-uv-r01`(✅已双推) | `b1960ec` | [A1-v30-actual-share-uv-r1.md](submissions/A1-v30-actual-share-uv-r1.md) |

## Reviews

| slug | round | status | issues | created | file |
|---|---|---|---|---|---|
| v21-bookkeeping | r1 | REVIEWED / APPROVED | 3(全部关闭:2 WARNING 平反 resolved + 1 INFO) | 2026-07-05 | [B1-v21-bookkeeping-r1.md](reviews/B1-v21-bookkeeping-r1.md) |
| v22-pricing | r1 | REVIEWED / APPROVED_WITH_CONDITIONS | 3(全部 DOC_CONSISTENCY WARNING,均无害不阻断,待 C 留档) | 2026-07-05 | [B1-v22-pricing-r1.md](reviews/B1-v22-pricing-r1.md) |
| v23-internal-merge-unify | r1 | REVIEWED / APPROVED_WITH_CONDITIONS | 4(3 WARNING + 1 INFO,全部 DOC_CONSISTENCY/FUNCTION_EQUIVALENCE,均无害不阻断,待 C 留档) | 2026-07-05 | [B1-v23-internal-merge-unify-r1.md](reviews/B1-v23-internal-merge-unify-r1.md) |
| v24-self-check | r1 | REVIEWED / APPROVED_WITH_CONDITIONS | 4(3 WARNING + 1 INFO,全部 DOC_CONSISTENCY/MAINTAINABILITY,均无害不阻断,待 C 留档) | 2026-07-05 | [B1-v24-self-check-r1.md](reviews/B1-v24-self-check-r1.md) |
| v25-match-rule-tune | r1 | REVIEWED / APPROVED_WITH_CONDITIONS | 2(1 WARNING DOC_CONSISTENCY + 1 INFO FUNCTION_EQUIVALENCE,均无害不阻断,待 C 留档) | 2026-07-05 | [B1-v25-match-rule-tune-r1.md](reviews/B1-v25-match-rule-tune-r1.md) |
| v26-uv-protection | r1 | REVIEWED / NEEDS_REVISION | 3(1 CRITICAL FAIL阻断无效 blocks_approval + 1 WARNING changed_files遗漏 + 1 WARNING rebook行号对齐) | 2026-07-13 | [B1-v26-uv-protection-r1.md](reviews/B1-v26-uv-protection-r1.md) |
| v27-p0-hardening | r1 | REVIEWED / APPROVED_WITH_CONDITIONS | 2(1 WARNING FUNCTION_EQUIVALENCE fig8保守漏计已由 C 核查 unmatched=7 合计5.93亿并留档 + 1 INFO 字符串日期比较,均不阻断) | 2026-07-16 | [B1-v27-p0-hardening-r1.md](reviews/B1-v27-p0-hardening-r1.md) |
| v28-p123-cleanup | r1 | REVIEWED / APPROVED | 1(1 INFO DOC_CONSISTENCY 降级达成跨两轮,不阻断) | 2026-07-17 | [B1-v28-p123-cleanup-r1.md](reviews/B1-v28-p123-cleanup-r1.md) |
| v29-runtime-hardening | r1 | REVIEWED / APPROVED | 0(4 焦点全 PASS,无 CRITICAL/WARNING/INFO) | 2026-07-17 | [B1-v29-runtime-hardening-r1.md](reviews/B1-v29-runtime-hardening-r1.md) |

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
| v27-p0-hardening | r1 | APPROVED_WITH_CONDITIONS | 1 | 2026-07-17 | [C1-v27-p0-hardening-r1.md](closed/C1-v27-p0-hardening-r1.md) |
| v29-runtime-hardening | r1 | APPROVED | 1 | 2026-07-17 | [C1-v29-runtime-hardening-r1.md](closed/C1-v29-runtime-hardening-r1.md) |

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
| REV-v2.5.4-v27-p0-hardening-r1-01 | v27-p0-hardening | r1 | WARNING | resolved(C1 核查 fig8 unmatched=7 合计5.93亿,含6条>=0.1亿;作为 MEDIUM audit_escape_risk 留档,建议 v28 扩展匹配规则或展示未计入金额) | [B1](reviews/B1-v27-p0-hardening-r1.md) |
| REV-v2.5.4-v27-p0-hardening-r1-02 | v27-p0-hardening | r1 | INFO | resolved(C1 留档:fig8 mask 字符串日期比较当前可行,建议后续统一 pd.Timestamp 显式比较) | [B1](reviews/B1-v27-p0-hardening-r1.md) |
| REV-v2.5.5-v28-p123-cleanup-r1-01 | v28-p123-cleanup | r1 | INFO | open(降级达成跨两轮:v27 fig6+v28 fig7/fig8,表述准确,待 C 留档,不阻断) | [B1](reviews/B1-v28-p123-cleanup-r1.md) |

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
| v27-p0-hardening | r1 已归档(COMPLETED,APPROVED_WITH_CONDITIONS) | — | v2.5.4 P0 防错包：4 焦点独立读代码全 PASS 无 CRITICAL。QC rename 架构规避 v26 REV-01 同类隐患；WXY三元组整行取舍；fig6/fig8 唯一匹配+multi不计入WARN+大额unmatched告警；#ABS-006 iloc[1:] 单行表头修复。C1 已核查 fig8 unmatched=7 合计5.93亿并作为 MEDIUM audit_escape_risk 留档，建议 v28 扩展匹配规则或展示未计入金额 |
| v28-p123-cleanup | r1 REVIEWED / APPROVED | C-close | v2.5.5 P1/P2/P3 工程清理：B 审计 verdict=APPROVED 无 CRITICAL/WARNING。4 焦点独立读代码全 PASS(proj_sizes 死代码零残留 + fig6/fig7/fig8 三面板降级一致 + shared_tmp 三分支异常清理完整不吞错 + re/pandas import 上提彻底);git show 932adb0 --stat 仅 2 文件 changed_files 声明一致(洁净性优于 v22/v23/v24);5 层自检层1 git+层4 py_compile 实测通过。1 项 INFO(降级跨两轮达成)不阻断，待 Agent C 归档 |
| v29-runtime-hardening | r1 已归档(COMPLETED,APPROVED) | — | v2.5.6 第二批运行稳定性修复：B 审计 verdict=APPROVED 无 CRITICAL/WARNING/INFO。4 焦点独立读代码全 PASS(shared_tmp finally 全路径清理不吞错 + increment_merge close_workbook/wb_a/wb_b/wb_out/wb_orig 三路径显式 close + save_workbook_atomic/os.replace 原子替换不先删正式输出 + 投资台账缺失年份 WARN+continue 兼容/错配仅 WARN 不阻断);git show 1ed4874 --stat 4 文件与 changed_files 声明一致;5 层自检层1 git tag→1ed4874+层4 py_compile 实测 PY_COMPILE_OK 通过。C1 已归档，运行时资源加固不改变业务口径，逃逸风险 LOW |
| v30-actual-share-uv | r1 PENDING_REVIEW | B 审计 | v2.5.7 机构实际规模统一改 V列中标口径：投资台账 share=V;智能问答规模类=V且申购规模拒答;fig6/fig8 新增认购=U/V;机构统计投行认购=V;管理/销售/托管项目规模保留项目去重J列并补说明 |

## 命名规则

| 类型 | 格式 | 示例 |
|---|---|---|
| 送审报告 | `A{N}-{slug}-r{R}.md` | `A1-v20-institution-stats-r1.md` |
| 审计意见 | `B{N}-{slug}-r{R}.md` | `B1-v20-institution-stats-r1.md` |
| 归档报告 | `C{N}-{slug}-r{R}.md` | `C1-v20-institution-stats-r1.md` |
| git tag | `audit/v{X.Y}-{slug}-r{NN}` | `audit/v2.0-v20-institution-stats-r01` |
| Issue ID | `REV-v{X.Y}-{slug}-r{NN}-{seq}` | `REV-v2.0-v20-institution-stats-r01-01` |

详见 `audit/README.md`。
