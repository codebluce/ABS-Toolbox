---
review_id: B1-v26-uv-protection-r1
submission_id: A1-v26-uv-protection-r1
slug: v26-uv-protection
skill_version: v2.5.1
round: 1
auditor: agent_b
created_at: "2026-07-13 12:00:00"

git_tag: audit/v2.5.1-v26-uv-protection-r01
verified_tag_hash: 1ad1a89

verdict: NEEDS_REVISION

issues:
  - id: REV-v2.5.1-v26-uv-protection-r01-01
    severity: CRITICAL
    category: DATA_INTEGRITY
    location: "scripts/increment_merge.py:L1272,L1355-1366"
    description: "QC FAIL 阻断无效——wb_a.save() 在 L1272 先执行，QC 检查在 L1355 后执行，FAIL 阻断 return 在 L1366。文件在 QC 检查前已保存到磁盘，return 只跳过后续打印，不阻止文件写入。A1 §2.2 声称'qc_fails > 0 时不保存输出文件'不成立。"
    evidence: "git show 1ad1a89:scripts/increment_merge.py L1272: 'wb_a.save(output_path)' → L1355: 'qc_fails, qc_warns = run_enhanced_qc(...)' → L1361: 'if qc_fails > 0:' → L1366: 'return'。save 在 QC 前，FAIL 阻断时文件已写入。"
    suggested_fix: "把 wb_a.save(output_path) 移到 QC 检查之后、qc_fails==0 的分支里。或者改为先写临时文件，QC PASS 后再 rename 到 output_path。"
    blocks_approval: true

  - id: REV-v2.5.1-v26-uv-protection-r01-02
    severity: WARNING
    category: DOC_CONSISTENCY
    location: "audit/submissions/A1-v26-uv-protection-r1.md §3"
    description: "A1 changed_files 声明 3 文件（increment_merge.py + pitfall_log.md + CHANGELOG.md），git show 1ad1a89 --stat 实际 4 文件（多送审报告自身 A1-v26-uv-protection-r1.md）。与 v25 REV-01 同类问题。"
    evidence: "git show 1ad1a89 --stat: 4 files changed（含 audit/submissions/A1-v26-uv-protection-r1.md +127 行）"
    suggested_fix: "送审报告入 commit 属惯例，A1 changed_files 补记送审报告自身即可。"
    blocks_approval: false

  - id: REV-v2.5.1-v26-uv-protection-r01-03
    severity: WARNING
    category: DOC_CONSISTENCY
    location: "audit/submissions/A1-v26-uv-protection-r1.md §4.3"
    description: "A1 §4.3 已知遗留第 3 条称'target_rows 的行号范围在 rebook 模式 Step 5.0 删除行后会偏移，但 QC 7.20 在 Step 6（格式优化后）执行，此时行号已稳定'。需确认 rebook 删除行后 ws_orig_protected 和 ws_out 的行号是否真的对齐——ws_orig_protected 是 processed 台账的只读副本（删除前），ws_out 是删除后的 output，两者的行号可能不对齐。"
    evidence: "QC 7.20 L782-786: 'u_orig = ws_orig_protected.cell(row=r, column=21).value' vs 'u_out = ws_out.cell(row=r, column=21).value'——同 row 号对比，但 rebook 删除行后 ws_out 的 row N 可能对应 ws_orig_protected 的 row N+K"
    suggested_fix: "确认 rebook 删除行后两个 worksheet 的行号是否对齐。如果不对齐，需要用项目名称而非行号做匹配键。"
    blocks_approval: false

verified_issues: []

conditions: []
---

# v26-uv-protection r1 审计意见

## 0. 总体结论

**Verdict**: NEEDS_REVISION

QC 7.20 UV 列值保护逻辑正确，端到端验证 PASS。但 QC FAIL 阻断机制无效——`wb_a.save()` 在 QC 检查之前执行，FAIL 时文件已保存到磁盘，`return` 只是跳过后续打印。这是 A1 声称的核心功能"qc_fails > 0 时不保存输出文件"未实现，必须修复。

## 1. 上一轮 Issue 验证

首轮审计，无上一轮 Issue。

## 2. 需求合规审查

### 2.1 上一轮 Issue 全覆盖

首轮审计，无上一轮 Issue。

### 2.2 review_focus 回应

A1 §5 审计建议 4 项：

| # | A1 建议 | B 核查 | 结论 |
|---|---|---|---|
| 1 | 核查 QC 7.20 target_rows 构建 | L770-773: 遍历 target_projects 元组，行号范围加入集合，逻辑正确 | ✅ |
| 2 | 核查 FAIL 阻断 return 后不保存 | **L1272 save 在 L1355 QC 之前，FAIL 阻断无效** | ❌ CRITICAL |
| 3 | 核查 pitfall_log #ABS-003 | pitfall_log 记录准确，根因/修复/约束齐全 | ✅ |
| 4 | 端到端验证 supplement 模式 | 跑 0703 定稿 supplement，QC 7.20 PASS | ✅ |

### 2.3 5 层自检证据复核

A1 未提供标准 5 层自检（本 slug 是 bugfix 非原样迁入，5 层自检不强制）。B 独立验证：

| 验证项 | B 复核 | verified |
|---|---|---|
| QC 7.20 逻辑正确 | 代码逐行核查，target_rows 构建 + U/V 对比 + None 检测均正确 | ✅ |
| QC 7.20 端到端 PASS | 跑 0703 定稿 supplement，"PASS: All non-target UV columns preserved" | ✅ |
| FAIL 阻断有效 | **save 在 QC 前，FAIL 阻断无效** | ❌ |
| pitfall_log 准确 | #ABS-003 记录与代码一致 | ✅ |
| CHANGELOG 准确 | v2.5.1 段描述与代码一致（但"不保存输出文件"描述不准确） | ⚠️ |

## 3. 代码质量审查

### 3.1 CRITICAL（功能等价性 / 数据完整性）

**REV-01 (CRITICAL, blocks_approval=true)**: QC FAIL 阻断无效

`scripts/increment_merge.py` L1272 `wb_a.save(output_path)` 在 L1355 `run_enhanced_qc()` 之前执行。当 QC FAIL 时（`qc_fails > 0`），文件已经保存到磁盘，L1366 的 `return` 只是跳过后续打印，不阻止文件写入。

A1 §2.2 声称"qc_fails > 0 时不保存输出文件，直接 return"——这**不成立**。

**影响**: 如果未来出现 UV 列被覆盖的情况（如 #ABS-003 重演），QC 7.20 会检测到 FAIL，但文件已经保存——用户可能直接使用已保存的错误文件，FAIL 阻断形同虚设。

**修复建议**: 把 `wb_a.save(output_path)` 移到 QC 检查之后、`qc_fails == 0` 的分支里。或者改为先写临时文件，QC PASS 后再 rename 到 output_path。

### 3.2 WARNING（文档一致性 / 接口兼容性）

**REV-02 (WARNING)**: changed_files 遗漏送审报告自身

A1 §3 声明 3 文件，git show 实际 4 文件（多 A1-v26-uv-protection-r1.md）。与 v25 REV-01 同类，送审报告入 commit 属惯例，补记即可。

**REV-03 (WARNING)**: rebook 模式行号对齐风险

A1 §4.3 已知遗留第 3 条提到 rebook 删除行后行号偏移问题，声称"QC 7.20 在 Step 6 执行，行号已稳定"。但 `ws_orig_protected` 是 processed 台账的只读副本（删除前），`ws_out` 是删除后的 output——两者的行号可能不对齐。QC 7.20 用同 row 号对比，如果不对齐会产生误判或漏判。需确认或改用项目名称做匹配键。

### 3.3 INFO（改进建议）

无 INFO 建议。QC 7.20 逻辑本身设计合理，target_rows 豁免机制正确，violation 输出有截断防刷屏。

## 4. 下一轮指引

A 修复轮需处理：

1. **REV-01 (CRITICAL)**: 把 `wb_a.save()` 移到 QC 之后。核心修复——FAIL 阻断必须真正阻止文件保存。
2. **REV-02 (WARNING)**: changed_files 补记送审报告自身。
3. **REV-03 (WARNING)**: 确认或修复 rebook 模式下行号对齐问题。
