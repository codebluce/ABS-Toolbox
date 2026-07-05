---
review_id: B1-v25-match-rule-tune-r1
submission_id: A1-v25-match-rule-tune-r1
slug: v25-match-rule-tune
skill_version: v2.5.0
round: 1
auditor: agent_b
created_at: "2026-07-05 21:10:00"

git_tag: audit/v2.5-v25-match-rule-tune-r01
verified_tag_hash: ae1907e

verdict: APPROVED_WITH_CONDITIONS

issues:
  - id: REV-v2.5-v25-match-rule-tune-r01-01
    severity: WARNING
    category: DOC_CONSISTENCY
    location: "A1-v25-match-rule-tune-r1.md frontmatter changed_files"
    description: "A1 changed_files 声明 3 文件(increment_merge.py + SKILL.md + CHANGELOG.md),git show ae1907e --stat 实际 4 文件(多送审报告 A1-*.md 本身,+184行)。送审报告自身入 commit 属正常,但 changed_files 清单未列全。属文档一致性瑕疵,不阻断。"
    evidence: "git show ae1907e --stat: CHANGELOG.md +35 / SKILL.md +4-2 / audit/submissions/A1-v25-match-rule-tune-r1.md +184 / scripts/increment_merge.py +65-6 = 4 files"
    suggested_fix: "C 归档时留档:实际 commit 4 文件,送审报告自身可计入 changed_files(业界惯例),此项仅提示"
    blocks_approval: false
  - id: REV-v2.5-v25-match-rule-tune-r01-02
    severity: INFO
    category: FUNCTION_EQUIVALENCE
    location: "scripts/increment_merge.py Pass4 core_name L1127-1138"
    description: "Pass 4 核心名匹配 len(inst_core)>=3 阈值防误匹配设计合理,但阈值为经验值。当前 0703/0626 台账未见误匹配,长期需业务观察。core_name 去后缀后若两机构核心名恰好相同(如虚构'华夏基金'与'华夏资管'均→'华夏'2字,不达阈值;但'长江证券'→'长江'2字亦不达阈值)——2字机构一律走 hard_map 兜底,阈值机制有效。"
    evidence: "L1127 if matched_ur_idx is None → L1128 inst_core=core_name → L1129 if len(inst_core)>=3;优先级链 L1093初始化→L1100 Pass2守卫→L1111 Pass3守卫→L1127 Pass4守卫,顺序正确,Pass4 仅前三Pass全落空时触发"
    suggested_fix: "无需修复。建议 C 留档:MATCH_HARD_MAP 与 len>=3 阈值随业务台账积累持续观察1-2周,发现新难匹配 case 再扩 hard_map"
    blocks_approval: false

verified_issues: []

conditions:
  - "C 归档时留档 REV-01:实际 commit 含 4 文件(含送审报告自身),changed_files 清单口径说明"
  - "C 归档时留档 REV-02:Pass4 len>=3 阈值与 MATCH_HARD_MAP 属经验值,建议业务观察1-2周后视新 case 扩展"
---

# v25-match-rule-tune r1 审计意见

## 0. 总体结论

**Verdict**: APPROVED_WITH_CONDITIONS

v2.5.0 匹配规则调优(normalize 去连字符 + 全角空格 bug 修复 + core_name + MATCH_HARD_MAP + Pass 1-4 优先级链 + rebook 默认模式)5 处改动经 `git show ae1907e` 逐行独立核查全部真实存在且逻辑正确,优先级链守卫顺序无误,rebook 默认模式向后兼容(--supplement/--new-raw 分支保留)。功能等价性完整,无 CRITICAL。2 项瑕疵(1 WARNING changed_files 口径 + 1 INFO 阈值观察)均 blocks_approval=false,通过归档。

## 1. 上一轮 Issue 验证

v24-self-check 已归档 APPROVED_WITH_CONDITIONS,无遗留至本 slug 的 Issue(各 slug 独立)。无需验证。

## 2. 需求合规审查

### 2.1 上一轮 Issue 全覆盖

本 slug 首轮,无上一轮 Issue。v24-self-check 已独立归档闭环。

### 2.2 review_focus 回应

A 在 §5 提出 4 个审计焦点,逐一独立复核:

1. **normalize 去连字符副作用**:`n.replace("-","").replace("/","").replace("／","")` 已核实(git show 实测)。去连字符是全局归化,"中信建投-衍生品"→"中信建投衍生品"(应去,正确);"申万宏源-北京"类同理去分隔符再匹配。未发现合法机构名依赖 `-` 区分身份的 case。**回应:低风险,当前台账无误伤,可接受。**

2. **Pass 4 len>=3 阈值**:核实 core_name L1127-1138。2 字核心名(利曦/中信/长江)一律不达阈值走 hard_map 兜底,3 字以上才走核心名匹配,且 Pass 4 位于优先级链末位(前三 Pass 全落空才触发)。**回应:阈值机制有效,记为 INFO 观察项(REV-02),非阻断。**

3. **MATCH_HARD_MAP 扩展性**:当前 2 条双向映射(利曦基金↔利曦私募基金)。**回应:同意 A 建议,业务观察1-2周后视新 case 扩展,记入 conditions。**

4. **默认 rebook 兼容性**:核实 `__main__` 分支,原 `parser.error(...)` 改为 `args.rebook=True` + INFO 提示,`--supplement`/`--new-raw`/`--rebook` 三分支互斥校验保留。已传 mode 的用户不受影响。**回应:向后兼容,无破坏性。**

### 2.3 6 层自检证据复核

| 层 | A 声称 | B 复核 | verified |
|---|---|---|---|
| 1 | 改造 diff 仅 increment_merge.py +60/-5 | git show ae1907e 实测 +65/-6,5处改动全真实 | ✅ |
| 2 | 0703 台账 QC Fails=0,2 case 匹配成功 | A1 §4.3/6.2 输出证据完整(Pass3 hard_map 利曦 + Pass1 精确 中信建投-衍生品) | ✅(信 A 自检输出,B 未复跑台账) |
| 3 | 25 列台账回归 QC PASSED 30项 | A1 附录证据 | ✅(采信) |
| 4 | 发行定价回归 PASSED WITH WARNINGS | 已知数据问题非回归 | ✅(采信) |
| 5 | 22 列台账全流程 35项通过 | A1 附录证据 | ✅(采信) |
| 6 | 默认 rebook 行为 | git show 实测 __main__ 分支代码确认 | ✅ |

> B 复核方式:层 1/6 通过 git show 逐行读代码独立确认;层 2-5 为台账端到端运行结果,采信 A 自检输出(与 v20-v24 一致惯例,B 不重跑业务台账)。

## 3. 代码质量审查

### 3.1 CRITICAL(功能等价性 / 数据完整性)

无 Issue。检查范围:normalize 归一化逻辑、core_name 去后缀(有 `len(n)>len(suffix)` 防削空保护)、MATCH_HARD_MAP 双向映射、Pass 1-4 优先级链守卫(L1093/1100/1111/1127 逐 Pass `if None` 守卫,顺序正确)、rebook 默认模式互斥校验。均无功能等价性或数据完整性缺陷。

### 3.2 WARNING(文档一致性 / 接口兼容性)

- **REV-v2.5-v25-match-rule-tune-r01-01**(DOC_CONSISTENCY):A1 changed_files 声明 3 文件,git show ae1907e --stat 实际 4 文件(多送审报告自身 +184)。送审报告入 commit 属正常,清单口径瑕疵,不阻断,C 留档。
- **§5 污染文件说明核查**:A1 §5 声明"仅 v25 相关文件进 commit,其他 modified 脚本留单独 commit"。git show ae1907e --stat 实测 commit 确实仅含 4 文件(3 代码文件 + 送审报告),**未混入 abs_common.py/entity_alias.py/gen 脚本/业务台账**。**较 v22/v23/v24 连续三轮元数据失真,本轮 commit 洁净性显著改善,§5 声明与实际一致,予以认可。**

### 3.3 INFO(改进建议)

- **REV-v2.5-v25-match-rule-tune-r01-02**(FUNCTION_EQUIVALENCE):Pass 4 len>=3 阈值与 MATCH_HARD_MAP 为经验值,建议业务观察 1-2 周,发现新难匹配 case 再扩 hard_map。当前无误匹配,机制有效。

## 4. 下一轮指引

verdict=APPROVED_WITH_CONDITIONS → 通知 Agent C 归档。2 项瑕疵均 blocks_approval=false,由 C1 留档关闭:REV-01(changed_files 口径)、REV-02(阈值/hard_map 业务观察)C 归档时 audit_escape_risks 不得为空:建议标记"层 2-5 台账端到端自检未由 B 重跑(采信 A 输出),若后续台账匹配出现回归需重新走 B 流程"为 LOW 逃逸风险。