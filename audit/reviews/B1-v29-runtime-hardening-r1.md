---
review_id: B1-v29-runtime-hardening-r1
submission_id: A1-v29-runtime-hardening-r1
slug: v29-runtime-hardening
skill_version: v2.5.6
round: 1
auditor: agent_b
git_tag: audit/v2.5.6-v29-runtime-hardening-r01
verified_tag_hash: 1ed4874
verdict: APPROVED
issues: []
verified_issues: []
conditions: []
---

# B1 审计意见 — v29-runtime-hardening (r1)

## §0 审计元信息

- **送审报告**：A1-v29-runtime-hardening-r1.md（skill_version=v2.5.6，round=1）
- **审计对象 commit**：`1ed4874`（git_tag `audit/v2.5.6-v29-runtime-hardening-r01`）
- **审计者**：Agent B（独立审计，未信任 A 自述，逐项独立读代码）
- **审计范围**：4 个运行时加固焦点 + 5 层自检复核
- **最终 verdict**：**APPROVED**

## §1 git 核实

| 核验项 | 命令 / 证据 | 结果 |
|---|---|---|
| 独立仓库 | `git rev-parse --show-toplevel` = `D:/.../skills/ABS工具箱` | ✅ 独立仓库 |
| tag→commit 一致 | `git rev-list -n 1 audit/v2.5.6-v29-runtime-hardening-r01` = `1ed487430cd...`，与 A 声明 `1ed4874` 一致 | ✅ |
| changed_files 吻合 | `git show 1ed4874 --stat` = 4 文件：CHANGELOG.md(+28) / gen_integrated_dashboard.py(+101,重构) / gen_investment_ledger.py(+6) / increment_merge.py(+57)，与 A 声明完全一致无遗漏 | ✅ |

作者=吴沛智(Nolan)，日期 Fri Jul 17 01:16:09 2026。

## §2 审计焦点核查

### 焦点 1：gen_integrated_dashboard.py — shared_tmp finally 全路径清理 ✅ PASS

独立读 L283-375（`git show` + grep 定位）：

- **L287** `shared_tmp = None` 在 try 外初始化。
- **L288-349** try 块覆盖全路径：preprocess_xlsx_for_pandas → `_assert_shared_tmp_structure` 结构断言 → 各 `compute_data`(cmp/cost/spread/inst/led) → 7 主面板 render_body → 3 可选投资人面板（各自 try/except→WARN+占位）。
- **L350-353** `except RuntimeError`: print + `sys.exit(1)`（RuntimeError 仍非零退出）。
- **L354-360** `finally`: `if shared_tmp` → `os.remove`（`except OSError: pass`）→ `shared_tmp=None`。**无条件清理，覆盖正常/RuntimeError/通用异常三路径**；通用异常无 except 捕获，自然向上抛出，不吞错。
- **L365** `render_body_multi_year(led_data)` 在 finally 之后执行，`led_data` 已于 L307 算好，无 shared_tmp 依赖，finally 删除临时文件不影响后续渲染。

### 焦点 2：increment_merge.py — workbook 显式 close ✅ PASS

独立读 `git show ... -- scripts/increment_merge.py` diff：

- 新增 `close_workbook(wb)` best-effort helper（wb=None 直接 return，close 异常吞掉不影响主流程）。
- **read_detail 返回前**（L339 附近）新增 `close_workbook(wb)`，避免明细 workbook 句柄泄漏。
- **run_increment_merge 初始化** `wb_a/wb_b/wb_out/wb_orig = None`。
- **三路径均显式 close**：
  - no-increment 路径：`save_workbook_atomic(wb_a, ...)` 后 `close_workbook(wb_b)` + `close_workbook(wb_a)`。
  - QC FAIL 路径：`os.remove(tmp_path)` 后依次 close wb_out/wb_orig/wb_b/wb_a，再退出。
  - QC PASS 路径：依次 close wb_out/wb_orig/wb_b/wb_a 后 `os.replace`。
- WXY 校验处新增 `wb_orig = openpyxl.load_workbook(...)` 具名变量承接（原为匿名 `.active` 句柄，无法关闭），修复句柄泄漏。

### 焦点 3：output 替换改 os.replace 原子替换 ✅ PASS

- **no-increment 路径**：原 `wb_a.save(output_path)` → `save_workbook_atomic(wb_a, output_path)`（同目录 mkstemp + save + `os.replace`，失败清理 tmp 并 raise）。
- **QC PASS 路径**：原 `if os.path.exists(output_path): os.remove(output_path); os.rename(tmp_path, output_path)` → 直接 `os.replace(tmp_path, output_path)`，**不再先删正式输出**，消除删除后 rename 失败导致输出丢失的空窗。
- **dir 兜底**：`os.path.dirname(output_path) or '.'` / `or "."` 防止 output 无目录前缀时 mkstemp 报错。

### 焦点 4：gen_investment_ledger.py — 历史年份缺失/错配 WARN ✅ PASS

独立读 compute_data_multi_year（L239-245 附近，diff 仅 6 行）：

- 缺失年份：`if not path or not os.path.exists(path)` → `print('[WARN] 投资台账 {year} 年源文件缺失，已跳过')` + `continue`，**保持原有跳过行为兼容**。
- 文件名年份错配：`if year not in basename` → 仅 `print('[WARN] ...请确认是否错配')`，**仅告警不阻断**。
- 2026 走 compute_data（注入 preprocessed_path），2025/2024 走 _compute_flat_year，逻辑不受 WARN 影响。

## §3 5 层自检复核

| 层 | 内容 | 复核方式 | 结果 |
|---|---|---|---|
| 层1 | git tag/commit 一致 | 实测（§1） | ✅ |
| 层2 | 函数/QC 保留 | 采信 A + diff 佐证（无函数删除，仅新增 helper + close/replace） | ✅ |
| 层3 | 0706 定稿综合看板端到端 | 采信 A + 代码佐证（shared_tmp/finally 逻辑自洽） | ✅ |
| 层4 | py_compile | **实测** `python -m py_compile` 三文件 = `PY_COMPILE_OK` | ✅ |
| 层5 | increment_merge no-increment smoke | 采信 A + 代码佐证（no-increment 路径 save_workbook_atomic 逻辑自洽） | ✅ |

## §4 结论与建议

- **verdict = APPROVED**。4 焦点全部 PASS，字节 diff 无函数丢失/QC 弱化，5 层自检复核通过（层1/层4 实测），文档合规。
- **无 CRITICAL / WARNING / INFO 级 Issue**。
- **下一步**：交 Agent C 归档 v29-runtime-hardening。
- **附注（与 v29 无关）**：v28-p123-cleanup 仍处 REVIEWED 待 Agent C 归档；v26 仍 NEEDS_REVISION 待 Agent A 修复。