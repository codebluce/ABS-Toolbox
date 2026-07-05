---
review_id: B1-v21-bookkeeping-r1
submission_id: A1-v21-bookkeeping-r1
slug: v21-bookkeeping
skill_version: v2.1.0
round: 1
auditor: agent_b
created_at: "2026-07-05 11:20:00"

git_tag: audit/v2.1-v21-bookkeeping-r01
verified_tag_hash: 27f08a8

verdict: APPROVED

issues:
  - id: REV-v2.1-v21-bookkeeping-r01-01
    severity: INFO
    category: DOC_CONSISTENCY
    status: RESOLVED
    location: "scripts/gen_institution_stats.py:268 (def) + :370 (调用); pitfall_log.md #ABS-001/#ABS-002"
    description: "【原判失实,已更正】首轮曾误判 internal_merge_bookkeeping 函数在代码中不存在(0 命中),据此拟要求修正 pitfall_log。经 findstr 干净复核确认:该函数真实存在于 gen_institution_stats.py:268(def internal_merge_bookkeeping),并在 :370 由 load_data 正常调用。此前 0 命中系 PowerShell Select-String 在 GBK 编码/搜索范围下的假阳性(与 REV-...-02 同源环境问题)。pitfall_log #ABS-001/#ABS-002 关于'保留在 gen_institution_stats.py'的描述属实,技术债 #ABS-002 的并存状态在代码中成立,文档与代码一致,无需修正。"
    evidence: "findstr /n /c:\"def internal_merge_bookkeeping\" scripts/*.py → gen_institution_stats.py:268 命中; findstr /n /c:\"internal_merge_bookkeeping\" → :14(docstring)/:268(def)/:370(load_data 调用)命中; read_file L268-370 确认完整函数体(openpyxl 预处理+明细合并+WXY 写入)+ load_data L370 调用"
    suggested_fix: "无需处理,函数存在且文档描述属实。此 Issue 系核查工具假阳性,现已关闭。"
    blocks_approval: false
  - id: REV-v2.1-v21-bookkeeping-r01-02
    severity: WARNING
    category: DOC_CONSISTENCY
    location: "submissions/A1-v21-bookkeeping-r1.md frontmatter git_tag; abs-toolbox 仓库 tag 列表"
    status: RESOLVED
    description: "【原判失实,已更正】首轮审计时因本地 .git 损坏(objects/HEAD 丢失,git 误�主仓库)导致 tag/commit 无法解析,曾误判 tag 从未创建。经 Agent A 从 abs-toolbox 远端 fetch 恢复独立仓库后复核:commit 27f08a8 真实存在,tag audit/v2.1-v21-bookkeeping-r01 已指向 27f08a8 且已推送 gitee/github。此 Issue 系环境损坏造成的假阳性,现已解决。"
    evidence: "恢复后 git rev-list -n1 audit/v2.1-v21-bookkeeping-r01 → 27f08a8...; git ls-remote --tags gitee → 27f08a8 refs/tags/audit/v2.1-v21-bookkeeping-r01; git log 显示 27f08a8 (tag: audit/v2.1-v21-bookkeeping-r01)"
    suggested_fix: "无需处理,tag 已存在并双推。归档条件已满足。"
    blocks_approval: false
  - id: REV-v2.1-v21-bookkeeping-r01-03
    severity: INFO
    category: FUNCTION_EQUIVALENCE
    location: "submissions/A1-v21-bookkeeping-r1.md §4 自检层3 (逐 cell diff)"
    description: "A 声称逐 cell diff 总数 50125(单 sheet 口径 2005×25)。B 独立复核按 25 个 sheet 各自 max_row×max_col 全量累加得 total=64811。cell 计数口径不同,但核心结论'0 差异'双方完全一致,B 复核口径更全面。"
    evidence: "B openpyxl 逐 cell 脚本输出: new sheets:25 orig sheets:25 / total cells:64811 / diff cells:0 / RESULT:0_DIFF_PASS"
    suggested_fix: "下轮送审报告注明 cell 计数口径(单 sheet or 全 sheet 累加),避免复核者困惑。不影响等价性结论。"
    blocks_approval: false

verified_issues: []

conditions:
  - "[已满足] git tag audit/v2.1-v21-bookkeeping-r01 已指向 27f08a8 并双推 gitee/github(REV-...-02 系本地仓库损坏假阳性,恢复后确认 tag 真实存在)"
  - "[已解除] internal_merge_bookkeeping 函数真实存在于 gen_institution_stats.py:268,pitfall #ABS-001/#ABS-002 描述属实(REV-...-01 系核查工具假阳性,已平反)"
---

# v21-bookkeeping r1 审计意见

## 0. 总体结论

**Verdict**: APPROVED

簿记录入 v2.1(increment_merge.py,1221 行)以**字节级完全一致**迁入 ABS工具箱,5 层自检经 B 独立复核全部通过,**功能与原 skill 100% 等价、无回归**;放行。首轮原提 2 项 WARNING,复核后**均确认为核查环境的假阳性**:REV-...-02(git tag 缺失)系本地 .git 损坏导致,仓库恢复后确认 tag/commit 真实存在并已双推;REV-...-01(internal_merge_bookkeeping 不存在)系 PowerShell/编码搜索假阳性,findstr 干净复核确认该函数真实存在于 gen_institution_stats.py:268 并被 load_data(:370) 正常调用,pitfall #ABS-001/#ABS-002 描述属实。两项假阳性均已平反,**无遗留条件,升级为无条件 APPROVED**。

## 1. 上一轮 Issue 验证

首轮(r1),无上一轮 Issue。

## 2. 需求合规审查

### 2.1 上一轮 Issue 全覆盖

首轮无历史 Issue,不适用。

### 2.2 review_focus 回应

A 送审报告 §5 列 10 项审计建议,B 逐项独立复核(不采信 A 自述):

| # | A 审计建议 | B 独立复核结论 |
|---|---|---|
| 1 | increment_merge.py 字节一致 | ✅ fc /b "找不到差异"+SHA256 双方 `b6bd1a11...91dd61` 完全相同 |
| 2 | 11 个顶层函数保留、行号一致 | ✅ findstr /r "^def " 独立枚举:L28/36/70/139/159/201/219/247/302/346/755 全一致 |
| 3 | 17 项 QC 7.1-7.19 保留 | ✅ 字节一致 ⟹ QC 逻辑数学等价(SHA256 相同,函数体不可能不同) |
| 4 | 5 层自检证据 | ✅ 逐层独立重跑(见 §2.3) |
| 5 | 逐 cell diff 0 差异 | ✅ B 独立 openpyxl 复核 64811 cell 0 差异(A 口径 50125,见 INFO-03) |
| 6 | 机构统计无回归 | ✅ QC PASSED 30+35 项(B 独立重跑) |
| 7 | SKILL.md 触发词 ✅ v2.1.0 | ✅ SKILL.md L26/L38 路由已标 v2.1.0 |
| 8 | internal_merge 保留未动 | ✅ **函数真实存在** gen_institution_stats.py:268(def)+:370(load_data 调用),pitfall 描述属实(首轮 0 命中系搜索假阳性,已平反) |
| 9 | abs-toolbox 双推 | ✅ HEAD c74fffe,github/main 与 gitee/main 同步指向 |
| 10 | QC FAIL 是数据问题非回归 | ✅ 新旧 skill 同输入 Fails:2 Warns:4 RESULT:FAIL 完全一致 |

### 2.3 5 层自检证据复核

| 层 | A 声称 | B 独立复核 | verified |
|---|---|---|---|
| 1 文件字节对比 | diff 为空 | fc /b 找不到差异 + SHA256 完全一致 | ✅ |
| 2 端到端穿行 | 新旧 QC FAIL=2 WARN=4 一致 | B 重跑新 skill Fails:2 Warns:4 FAIL;原 skill Fails:2 Warns:4 FAIL | ✅ |
| 3 逐 cell diff | 50125 cell 0 差异 | B 重跑 64811 cell 0 差异(口径不同,0 差异一致) | ✅ |
| 4 原 skill smoke | 同输入 QC 一致 | 层 2 已覆盖,原 skill 正常运行且 QC 一致 | ✅ |
| 5 机构统计回归 | QC PASSED 30+35 项 | B 重跑 QC PASSED 30+35 项 | ✅ |

## 3. 代码质量审查

### 3.1 CRITICAL(功能等价性 / 数据完整性)

**无 CRITICAL Issue。** 检查范围:字节一致性(SHA256)、11 函数保留、17 项 QC 保留、端到端 QC 致、逐 cell 0 差异、机构统计无回归——功能等价性从字节级到产出级均已验证,数据完整性无损。QC FAIL 经证实为 0626 定稿台账 WXY 旧值与 11 份明细不符的数据问题,新旧行为一致,非迁入回归。

### 3.2 WARNING(文档一致性 / 接口兼容性)

**无遗留 WARNING。** 首轮原提 2 项 WARNING 经复核均为核查环境假阳性,已平反关闭:

- **REV-...-01(已平反,INFO/RESOLVED)**:首轮误判 internal_merge_bookkeeping 不存在(0 命中)。findstr 干净复核确认函数真实存在于 gen_institution_stats.py:268,并在 :370 由 load_data 调用;pitfall_log #ABS-001/#ABS-002 描述属实。0 命中系 PowerShell/GBK 编码搜索假阳性(与 REV-...-02 同源)。文档与代码一致,无需修正。
- **REV-...-02(已平反,RESOLVED)**:首轮因本地 .git 损坏误判 tag 从未创建。仓库恢复后确认 commit 27f08a8 与 tag audit/v2.1-v21-bookkeeping-r01 真实存在并已双推 gitee/github。

### 3.3 INFO(改进建议)

- **REV-...-03(FUNCTION_EQUIVALENCE)**:A 逐 cell diff 计数 50125(单 sheet 口径),B 复核 64811(全 sheet 累加口径),0 差异结论一致。建议下轮注明计数口径。

## 4. 下一轮指引

**Verdict = APPROVED**,功能层面已可放行,首轮 2 项 WARNING 均经复核平反为核查环境假阳性,**无遗留归档条件**,通知 **Agent C 归档**。

1. [已满足] git tag `audit/v2.1-v21-bookkeeping-r01` 已指向 27f08a8 并双推(REV-...-02 假阳性平反)
2. [已解除] pitfall_log #ABS-001/#ABS-002 描述属实,internal_merge_bookkeeping 真实存在于 gen_institution_stats.py:268(REV-...-01 假阳性平反)

INFO-03 无需处理,仅提示口径。

## 5. 审计教训(audit_escape_risks)

本次审计首轮出现**两次假阳性误判**,均源于本地核查环境问题(而非 A 送审造假),Agent B 已自我更正,提请归档时留档警示:
- **REV-...-02**:本地 .git 损坏(objects/HEAD 丢失)导致 commit/tag 无法解析,误判为"tag 从未创建"。教训:核查 git 对象前须先验证 `.git` 完整性(git fsck / rev-parse --git-dir)。
- **REV-...-01**:PowerShell Select-String 在 GBK 编码与搜索范围下漏匹配,误判函数不存在。教训:代码存在性核查应以 findstr /n /c 或直接 read_file 交叉验证,勿单一依赖 Select-String。