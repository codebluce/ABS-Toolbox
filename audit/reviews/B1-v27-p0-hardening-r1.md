---
review_id: B1-v27-p0-hardening-r1
submission_id: A1-v27-p0-hardening-r1
slug: v27-p0-hardening
skill_version: v2.5.4
round: 1
auditor: agent_b
created_at: "2026-07-16 00:00:00"

git_tag: audit/v2.5.4-v27-p0-hardening-r01
verified_tag_hash: c9c2626

verdict: APPROVED_WITH_CONDITIONS

issues:
  - id: REV-v2.5.4-v27-p0-hardening-r1-01
    severity: WARNING
    category: FUNCTION_EQUIVALENCE
    location: "scripts/fig8_credit_total_panel.py:_apply_new_subscriptions / scripts/fig6_credit_panel.py 同构"
    description: "multi 匹配(命中多个授信机构)与 >=0.1亿 unmatched 均'不计入并仅 WARN'。这是保守偏差(宁少算不重复占用),但会使'新增认购规模'少算、剩余额度偏高。fig8 A 自述 unmatched=7,需确认这 7 条是否含大额基石机构导致剩余额度显著虚高。"
    evidence: "fig8 _apply_new_subscriptions: len(matches)==1 才 inst['new_subscription']+=size; multi/unmatched 仅 append+WARN,不计入。A §6 smoke: fig8 matched=16 multi=0 unmatched=7(6条未匹配未计入)。"
    suggested_fix: "确认 7 条 unmatched 的金额量级;若含大额,考虑扩展 approximate_match 规则或 MATCH_HARD_MAP,或在 panel 图例标注'未匹配新增认购合计 X 亿未计入'以便使用者知情。"
    blocks_approval: false
  - id: REV-v2.5.4-v27-p0-hardening-r1-02
    severity: INFO
    category: FUNCTION_EQUIVALENCE
    location: "scripts/fig8_credit_total_panel.py mask 筛选行"
    description: "mask 用字符串 '2026-07-01' 与 datetime 列比较,依赖 pandas 隐式解析为 Timestamp。当前可行,但健壮性弱于显式 pd.Timestamp。"
    evidence: "mask = (df_ledger['簿记时间'] >= '2026-07-01') & ..."
    suggested_fix: "改为 pd.Timestamp('2026-07-01') 显式比较(可选,非必须)。"
    blocks_approval: false

verified_issues: []

conditions:
  - "确认 fig8 7 条 unmatched 新增认购的金额量级,排除大额基石机构剩余额度虚高风险(REV-01)。"
---

<!--
本轮为 v27-p0-hardening 首轮(R=1),无上一轮 Issue,§1 空表说明。
§2/§3 均已填写,无 CRITICAL Issue,给出检查范围。
-->

# v27-p0-hardening r1 审计意见

## 0. 总体结论

**Verdict**: APPROVED_WITH_CONDITIONS

4 个审计焦点独立读代码核查全部 PASS,无 CRITICAL/无功能等价性缺陷。QC 阻断闭环采用"临时文件 rename 而非 save"架构,QC 判断先于落盘,彻底规避 v26 REV-01(save 在 QC 之前致阻断无效)同类隐患——本轮此项**优于** v26。2 项非阻断观察点(fig8 保守漏计需确认大额 + 字符串日期比较)以 condition 形式留待确认。

## 1. 上一轮 Issue 验证

首轮送审(R=1),无上一轮 Issue。

## 2. 需求合规审查

### 2.1 上一轮 Issue 全覆盖

首轮无历史 Issue,不适用。addressed_issues=[] 与 previous_git_tag=null 一致。

### 2.2 review_focus 回应

A §5 提出 4 个审计焦点,逐项独立读代码核查:

**焦点1 — QC 7.1/7.2/7.3 qc_pre_fails 纳入 qc_fails 且 FAIL 阻断落盘**:PASS。
- `increment_merge.py` L1308 `qc_pre_fails=0` 初始化;L1326(7.1)/L1373(7.2)/L1384(7.3) 累加。
- L1388 `run_enhanced_qc` 返回 7.4-7.20 的 qc_fails;L1391 `qc_fails += qc_pre_fails` 合并。
- L1394 `if qc_fails>0` → L1395 `os.remove(tmp_path)` → L1400 `return`(**根本不落盘**)。
- L1402 才 `os.rename(tmp_path, output_path)`(仅 QC PASS 分支落盘)。
- **关键**:全程无 wb.save,输出走临时文件 rename。QC 判断严格先于落盘,规避 v26 REV-01 CRITICAL(save 在 QC 前致 FAIL 阻断无效)。本轮无同类问题。

**焦点2 — resolve_columns 避免 WXY 逐列拼接,部分缺失整行回退 TUV**:PASS。
- `abs_common.py` L235 `wxy_count = w.notna + x_present + y.notna`(0-3);L236 `wxy_complete==3`、L237 `wxy_partial 0<count<3`。
- L244-246 三列**统一** `.where(~wxy_complete, W/X/Y)`:仅三元组齐全整体取 WXY,否则整行回退 TUV。消除旧版 `w.fillna(t)` 逐列拼接("W 来自穿透、X/Y 来自表面")。
- L239-242 partial 整行回退 TUV 并 WARN(与 A smoke PARTIAL_WXY回退=6 一致)。
- 亮点:X 用 `x_present`(notna & !='' & !='nan')判断,比旧版单纯 notna 更严格,规避空串误判。

**焦点3 — fig6/fig8 新增认购 resolved 口径 + 匹配审计无重复/漏计**:PASS(附 REV-01 观察)。
- `fig8` `_apply_new_subscriptions`:`len(matches)==1` 才计入;multi(>1)不计入+WARN("避免重复占用");unmatched 中 >=0.1亿 WARN。无重复计。
- `_add_resolved_subscription_columns` 与 abs_common 同源 WXY 三元组口径(wxy_complete 取穿透,否则回退 U/V)。
- fig6 与 fig8 逻辑同构,py_compile 通过,A smoke fig6 matched=2/multi=0/unmatched=0。
- 观察:multi/大额 unmatched 保守不计入,可能少算新增认购、剩余额度偏高 → REV-01(WARNING,需确认大额)。

**焦点4 — iloc[2:]→iloc[1:] 符合单行表头台账结构**:PASS。
- `lab/load_data.py` L26-27 `headers=raw.iloc[0]` + `df=raw.iloc[1:]`,L25 注释明确"定稿台账为单行表头,Row1 起即真实数据;不能跳过 Row1 首条认购记录(#ABS-006)"。
- fig8 L172-176 同口径 iloc[0] 表头 + iloc[1:] 数据。
- 0703 定稿为单行表头,旧 iloc[2:] 会把首条数据(东道17-3邮储银行4亿)当子表头跳过导致漏计;iloc[1:] 补回。与 A §4.2 层3 delta=4.0 吻合。

### 2.3 5 层自检证据复核

| 层 | A 声称 | B 复核 | verified |
|---|---|---|---|
| 1 | git show 8 文件 | git show c9c2626 --stat 实际 8 文件,与 A 声明完全一致(CHANGELOG/pitfall_log/abs_common/fig6/fig8/increment_merge/fig4/load_data),无遗漏 | ✅ |
| 2 | 综合看板 13 panel 通过 | 采信 A 输出(v25 惯例层2-5采信);py_compile 全绿佐证脚本无语法错 | ✅ |
| 3 | #ABS-006 delta=4.0 补回邮储4亿 | 读 load_data L25-27 逻辑确认 iloc[1:] 单行表头正确,delta=4.0 与首行数据补回一致 | ✅ |
| 4 | py_compile OK + fig6 matched=2 + fig8 matched=16 unmatched=7 | B 重跑 py_compile 6 文件全部 PY_COMPILE_OK;fig6/fig8 匹配逻辑读代码确认;unmatched=7 转 REV-01 condition | ✅ |
| 5 | 机构统计 QC PASSED 30 项 | 采信 A 输出 | ✅ |

## 3. 代码质量审查

### 3.1 CRITICAL(功能等价性 / 数据完整性)

**无 CRITICAL Issue。** 检查范围:QC 阻断落盘时序(重点比对 v26 REV-01 save 时序隐患)、WXY 三元组整行取舍防拼接、fig6/fig8 匹配审计防重复占用、iloc 行偏移防首行漏计。4 项焦点均无功能等价性/数据完整性缺陷。

### 3.2 WARNING(文档一致性 / 接口兼容性)

- **REV-v2.5.4-v27-p0-hardening-r1-01**(FUNCTION_EQUIVALENCE, WARNING, blocks_approval=false):fig8/fig6 multi 与大额 unmatched 保守不计入,需确认 7 条 unmatched 金额量级排除剩余额度虚高。详见 frontmatter。

### 3.3 INFO(改进建议)

- **REV-v2.5.4-v27-p0-hardening-r1-02**(INFO):fig8 mask 用字符串日期比较依赖隐式转换,建议显式 pd.Timestamp(可选)。

## 4. 下一轮指引

verdict = APPROVED_WITH_CONDITIONS,通知 **Agent C 归档**。归档时:
1. 确认 condition REV-01:fig8 7 条 unmatched 新增认购金额量级(排除大额基石机构剩余额度虚高)。若含大额,记为 audit_escape_risk 或建议 v28 扩展匹配规则。
2. REV-02(字符串日期比较)留档为 INFO 改进建议,非必须修复。
3. 补记完整 8 文件 changed_files 清单(本轮 A 声明与 git show 一致,无 v22/v23 类遗漏问题)。
4. 亮点留档:QC 阻断采用 rename 架构,已修复 v26 REV-01 同类隐患。