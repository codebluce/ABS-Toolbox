---
submission_id: A1-v29-runtime-hardening-r1
slug: v29-runtime-hardening
skill_version: v2.5.6
round: 1
created_at: "2026-07-17 01:16:47"
author: agent_a
git_tag: audit/v2.5.6-v29-runtime-hardening-r01
commit_hash: 1ed4874
previous_git_tag: null
changed_files:
  - CHANGELOG.md
  - scripts/gen_integrated_dashboard.py
  - scripts/gen_investment_ledger.py
  - scripts/increment_merge.py
status: PENDING_REVIEW
addressed_issues: []
self_review:
  all_issues_addressed: true
  no_overengineering: true
  function_equivalence_verified: true
  edge_cases_covered: true
  notes: "本轮执行用户指定第二批运行稳定性事项：shared_tmp finally 管理、workbook 显式 close、output os.replace 原子替换、投资台账历史年份缺失/错配提示。第三批/第四批未纳入本 slug。"
review_focus:
  - "核查 gen_integrated_dashboard.py 中 shared_tmp 是否由 finally 全路径清理，且 RuntimeError 仍 exit(1)。"
  - "核查 increment_merge.py 中主要 openpyxl workbooks 是否显式 close，尤其 no-increment/QC FAIL/QC PASS 三路径。"
  - "核查 output 替换是否由 os.remove+rename 改为 os.replace 或 save_workbook_atomic。"
  - "核查 gen_investment_ledger.py 历史年份缺失/年份错配 WARN 是否明确且不破坏缺失年份跳过行为。"
---

# v29-runtime-hardening r1 送审报告

## 1. 变更摘要(200 字内)

本轮按第二批“运行稳定，半天-1天”事项修复：`shared_tmp` 改为 `finally` 全路径清理；`increment_merge` 增加 workbook 显式 close，并将 no-increment / QC PASS 输出替换改为同目录临时文件 + `os.replace` 原子替换；投资台账多年份加载在历史年份缺失或文件名年份错配时输出 WARN，避免静默跳过。

## 2. 上一轮 Issue 处理(首轮省略)

本 slug 首轮，无上一轮 Issue。

## 3. 代码变更清单

| 文件 | 操作 | 说明 |
|---|---|---|
| `scripts/gen_integrated_dashboard.py` | modified | `shared_tmp` 生命周期改为 `try/finally`，覆盖预处理/compute/render 异常路径。 |
| `scripts/increment_merge.py` | modified | 新增 `close_workbook()` / `save_workbook_atomic()`；主要 workbook 显式 close；输出替换改 `os.replace`。 |
| `scripts/gen_investment_ledger.py` | modified | 多年份源文件缺失与文件名年份错配输出 WARN，仍保持缺失年份跳过的兼容行为。 |
| `CHANGELOG.md` | modified | 新增 v2.5.6 第二批运行稳定性修复记录与验证证据。 |

## 4. 自审与指标

### 4.1 强制自审清单

- [x] all_issues_addressed: 覆盖用户指定第二批 4 项；第三批/第四批未夹带。
- [x] no_overengineering: 未引入新框架，仅增加两个小型资源管理 helper 与 WARN 提示。
- [x] function_equivalence_verified: 综合看板端到端生成通过；`increment_merge` no-increment 分支 smoke 通过。
- [x] edge_cases_covered: 覆盖 shared_tmp 异常清理、workbook close、原子替换、历史年份缺失/错配提示。

### 4.2 5 层自检证据

| 层 | 检查 | 结果 | 证据 |
|---|---|---|---|
| 1 | 文件变更边界 | ✅ | `git diff --stat` 为 4 文件：`CHANGELOG.md`、`gen_integrated_dashboard.py`、`gen_investment_ledger.py`、`increment_merge.py`。 |
| 2 | 端到端穿行 | ✅ | `python scripts/gen_integrated_dashboard.py ... Inbox_batch2_verify.html` 输出 13 panel + Tab JS 齐全。 |
| 3 | 产物结构检查 | ✅ | `Inbox_batch2_verify.html` 约 6.0MB，验证后已删除临时 HTML。 |
| 4 | smoke | ✅ | `py_compile` 三文件通过；`increment_merge` no-increment smoke 输出 `Saved (unchanged): Inbox_batch2_no_increment.xlsx`。 |
| 5 | 回归测试 | ✅ | compare/cost/spread/institution/fig6/fig8/ledger 多年份仍正常执行；历史年份存在时无额外误报。 |

## 5. 审计焦点(可选·给 B 的提示)

1. **shared_tmp finally**：确认 `finally` 覆盖 compute 和三类投资人可选面板渲染路径；异常不吞错。
2. **workbook close**：确认 `wb_a`/`wb_b`/`wb_out`/`wb_orig` 在 no-increment、QC FAIL、QC PASS 路径关闭；`read_detail` 正常返回前关闭 detail workbook。
3. **原子替换**：确认 no-increment 使用 `save_workbook_atomic()`，QC PASS 使用 `os.replace(tmp_path, output_path)`，不再先删正式输出。
4. **历史年份提示**：确认 `compute_data_multi_year` 对缺失年份 WARN 后继续跳过；文件名年份错配仅 WARN，不阻断现有流程。

## 6. 附录

### 6.1 git 快照

```text
1ed4874 fix(综合看板): 第二批运行稳定性修复
CHANGELOG.md
scripts/gen_integrated_dashboard.py
scripts/gen_investment_ledger.py
scripts/increment_merge.py
```

### 6.2 py_compile

```text
python -m py_compile scripts/gen_integrated_dashboard.py scripts/increment_merge.py scripts/gen_investment_ledger.py
PY_COMPILE_OK
```

### 6.3 综合看板端到端验证

```text
[4/4] 拼接 HTML...
[完成] Inbox_batch2_verify.html (6122.5 KB)
默认显示: 发行定价 / 定价测试
[QC] 综合看板结构检查通过：13 个 panel(7 主 + 理财子分析 + 非标额度 + 授信总额度 + 投资台账[2026+2025+2024]) + Tab 切换 JS 齐全
```

### 6.4 increment_merge no-increment smoke

```text
=== Step 2: Project diff ===
  Increment projects (new): 0
  No increment projects found. Nothing to merge.
Saved (unchanged): Inbox_batch2_no_increment.xlsx
```
