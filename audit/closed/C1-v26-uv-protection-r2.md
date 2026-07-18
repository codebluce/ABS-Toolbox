---
closed_id: C1-v26-uv-protection-r2
slug: v26-uv-protection
skill_version: v2.5.1
closed_at: "2026-07-18 18:00:00"
closed_by: agent_c

final_verdict: APPROVED
total_rounds: 2
final_submission: A2-v26-uv-protection-r2
supersedes_submissions:
  - A1-v26-uv-protection-r1
  - A2-v26-uv-protection-r2

all_issues_resolved: true

audit_escape_risks:
  - risk_type: deferred_critical
    description: "无延期 CRITICAL Issue。r1 B1 提出的 REV-01(CRITICAL: QC FAIL 阻断无效)已在 r2 经 B2 verified=fixed:save 写入 tmp,QC FAIL 删除 tmp 并 return,QC PASS 后 os.rename/os.replace 到正式输出,output_path 在 FAIL 时不落盘。"
    severity: LOW
  - risk_type: verification_chain_broken
    description: "无验证链断裂。B1 的 3 个 Issue 在 A2 addressed_issues 中逐条 fixed,B2 verified_issues 对 REV-01/02/03 全部 verified。#ABS-004 为 r2 初修引入的回归,已在 fc5ae99 闭环并由 B2 纳入验证链。"
    severity: LOW
  - risk_type: superseded_missing
    description: "存在追溯性提示但不阻断: r02 tag 指向 3d5335a(初修/中间态),完整最终修复还包括 fc5ae99(未打 tag)。A2/B2 均已如实披露,本 C1 时间线覆盖两 commit；建议后续如需审计追溯,补打说明性 tag 或在后续 tag 注释中引用 fc5ae99。"
    severity: LOW

conditions: []
---

# v26-uv-protection 归档报告

## 1. 最终结论

**最终判决**: APPROVED  
**总轮次**: 2  
**核心收益**: #ABS-003 UV 列原始数据丢失事件的核心防线闭环:新增 QC 7.20 保护非目标项目 U/V 列,并修复 r1 中“QC FAIL 后文件已先保存”的阻断无效缺陷；最终实现 QC FAIL 不落正式输出、rebook 模式不再依赖行号对齐、同机构多笔认购不再被 dict 覆盖误判。  
**是否附条件**: 否

本 slug 经 r1 NEEDS_REVISION、r2 APPROVED 两轮闭环。B1 提出的 1 个 CRITICAL + 2 个 WARNING 全部由 B2 验证为 fixed。r2 修复链实际跨两个 commit: `3d5335a` 是 r02 tag 指向的初修 commit,`fc5ae99` 是 #ABS-004 回归修复与 Counter 多重集最终修复 commit。该双 commit 修复链已由 A2 如实披露、B2 采信并验证,归档时留痕。

## 2. Issue 生命周期全表

| Issue ID | 提出轮次 | 严重程度 | 处理轮次 | 最终状态 |
|---|---|---|---|---|
| REV-v2.5.1-v26-uv-protection-r01-01 | r1 | CRITICAL | r2 | fixed & verified:save 从 QC 前移至 tmp,QC FAIL 删除 tmp + return,QC PASS 后替换正式输出 |
| REV-v2.5.1-v26-uv-protection-r01-02 | r1 | WARNING | r2 | fixed & verified:changed_files 补记送审报告自身,3d5335a stat 与 A2 声明一致 |
| REV-v2.5.1-v26-uv-protection-r01-03 | r1 | WARNING | r2 | fixed & verified:QC 7.20 改为项目名豁免 + Counter 多重集 (项目名,分层,机构,V),规避 rebook 行号不对齐 |
| INFO-01(fc5ae99 未打 tag) | r2 | INFO | r2/C1 留档 | non-blocking:fc5ae99 未打 tag,但 A2/B2 已披露,当前 HEAD 已含最终修复 |

### Issue 详情

- **REV-01(CRITICAL)**:B1 发现 r1 的 `wb_a.save(output_path)` 在 QC 之前执行,导致 QC FAIL 时文件已经落盘,`return` 不能阻止错误文件生成。r2 修复为先保存到同目录 tmp,QC FAIL 时 `os.remove(tmp_path)+return`,QC PASS 后再 `os.rename/os.replace` 到 `output_path`。B2 对 3d5335a 与当前 HEAD 均验证通过。
- **REV-02(WARNING)**:A1 changed_files 漏掉送审报告自身。A2 补记,3d5335a stat=3 文件,与 A2 声明一致。
- **REV-03(WARNING)**:r1 QC 7.20 用同 row 号比较 `ws_orig_protected` 与 `ws_out`,rebook 删除行后存在行号不对齐风险。r2 初修改用项目名/分层/机构 dict key,随后 #ABS-004 暴露 dict key 冲突和遍历崩溃,fc5ae99 最终改为 Counter 多重集 `(项目名,分层,机构,V)`。
- **INFO-01**:r02 tag 指向 3d5335a,而最终 Counter 修复在 fc5ae99 且未打 tag。A2/B2 已如实披露,不阻断,但归档留痕。

## 3. 审计逃逸风险分析

- **延期风险**:无延期 CRITICAL。B1 的 CRITICAL REV-01 已在 r2 verified=fixed,不存在 deferred critical。
- **验证链断裂**:无验证链断裂。A2 addressed_issues 对 B1 3 个 Issue 一一回应,B2 verified_issues 全部 verified。#ABS-004 虽为 r2 初修引入的回归,但已由 fc5ae99 修复并被 B2 纳入验证链。
- **superseded 标注 / 双 commit 风险**:存在 LOW 级追溯风险。r02 tag `audit/v2.5.1-v26-uv-protection-r02` 指向 `3d5335a`,但真正可运行的最终修复态还需要 `fc5ae99`。A2/B2 都已说明“代码逻辑核查看 3d5335a,端到端运行基线看 fc5ae99/HEAD”,因此不构成未披露逃逸；建议后续如做审计自动化,允许 closed 报告记录“tag commit + untagged follow-up fix”的修复链。
- **回归风险**:#ABS-004 说明“修一处 QC 保护”可能引入新的键冲突/遍历形态问题。Counter 多重集已修复同机构多笔认购场景,但未来若 U/V 保护扩展到更多列,仍应优先设计集合/多重集而非 dict 单值覆盖。

## 4. 完整轮次时间线

| 时间/轮次 | 文件 / commit | verdict / 结果 | 说明 |
|---|---|---|---|
| r1 / 2026-07-13 | A1-v26-uv-protection-r1 / `1ad1a89` | PENDING_REVIEW | 新增 QC 7.20 + 声称 QC FAIL 不保存 |
| r1 B 审计 | B1-v26-uv-protection-r1 | NEEDS_REVISION | 发现 REV-01 CRITICAL:save 在 QC 前,FAIL 阻断无效;另有 changed_files 与 rebook 行号风险 |
| r2 初修 / 2026-07-18 | A2-v26-uv-protection-r2 / `3d5335a` / tag `audit/v2.5.1-v26-uv-protection-r02` | PENDING_REVIEW | save 改 tmp+QC PASS 后替换;changed_files 补记;QC7.20 改项目名匹配键(dict 中间态) |
| r2 回归修复 | `fc5ae99` | #ABS-004 闭环 | 修复 3d5335a 引入的 dict 遍历崩溃与同机构多笔认购 key 冲突,改 Counter 多重集;0706台账 QC 7.1/7.2/7.3/7.20 全 PASS |
| r2 B 复审 | B2-v26-uv-protection-r2 | APPROVED | B1 3 Issue 全 verified=fixed;INFO-01 留档提示 fc5ae99 未打 tag,不阻断 |
| C 归档 | C1-v26-uv-protection-r2 | APPROVED | 本报告归档双 commit 修复链和 #ABS-004 验证链 |

### B2 独立复核关键证据

- REV-01:3d5335a 快照中 `save(tmp_path)`、`qc_fails>0 → os.remove(tmp_path)+return`、QC PASS 后 `os.rename`;当前 HEAD 升级为 `os.replace`。
- REV-02:`git show 3d5335a --stat` 为 3 文件,与 A2 changed_files 一致。
- REV-03:当前 HEAD `target_project_names` 项目名豁免 + `collect_uv_multiset` Counter 多重集 `(项目名,分层,机构,V)` + `orig_ms/out_ms` 差集。
- #ABS-004:fc5ae99 CHANGELOG v2.5.2 记录 0706 台账+东裕4号续发簿记录入 QC 7.1/7.2/7.3/7.20 全 PASS,Fails=0。

## 5. 经验教训

1. **QC 阻断必须先于正式落盘**:只在 QC 后 `return` 不够,如果正式文件已保存,阻断就是假的。稳妥模式是 tmp 文件 + QC PASS 后原子替换。
2. **防篡改 QC 不应用行号当身份**:rebook 会删行/重排,行号不是稳定身份。应使用业务键,如项目名、分层、机构、金额等。
3. **业务键如果不唯一,不能用 dict 覆盖**:同一项目/分层/机构可存在多笔认购,dict 会覆盖旧值。Counter 多重集更适合做“记录集合一致性”检查。
4. **修复轮要如实披露回归修复链**:A2 明确说明 r02 tag 的 3d5335a 是中间态、fc5ae99 是最终态,这是正确做法。审计归档要覆盖完整链条,不能只看 tag commit。
5. **tag 不可变时,后续无 tag 修复必须留档**:fc5ae99 未打 tag 不阻断,但要在 C1 记录,否则未来追溯只看 r02 tag 会误以为 dict 中间态是最终代码。
6. **后续 slug 的加固也能补强早期修复**:v27/v29 对同一区域增加 close_workbook/save_workbook_atomic/os.replace 等资源与原子性加固,虽不属于 v26 审计范围,但说明该风险区域持续被强化。

## 6. 代码最终状态

- **git_tag**: `audit/v2.5.1-v26-uv-protection-r02`
- **tag commit_hash**: `3d5335a`
- **follow-up fix commit**: `fc5ae99`(#ABS-004 回归修复 + Counter 多重集最终修复,无 tag)
- **final_verdict**: APPROVED
- **abs-toolbox 仓库**: gitee(`ppwupp/abs-toolbox`) + github(`codebluce/ABS-Toolbox`)已双推
- **原 skill 保留**: 本轮修改 ABS工具箱 `scripts/increment_merge.py`,不删除原 skill
- **核心文件**:
  - `scripts/increment_merge.py`
  - `CHANGELOG.md`
  - `audit/submissions/A1-v26-uv-protection-r1.md`
  - `audit/submissions/A2-v26-uv-protection-r2.md`
  - `audit/reviews/B1-v26-uv-protection-r1.md`
  - `audit/reviews/B2-v26-uv-protection-r2.md`

### 回滚方案

若仅回滚 v26 r2 修复链:

```bash
cd skills/ABS工具箱
git revert fc5ae99
git revert 3d5335a
git push gitee main && git push github main
```

注意:后续 v27/v29/v30 已在同一区域叠加加固或口径修复,真实回滚前需先评估冲突和依赖关系。
