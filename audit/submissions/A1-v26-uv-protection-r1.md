# A1-v26-uv-protection-r1.md — UV 列值保护修复送审报告

## 基本信息

- **slug**: v26-uv-protection
- **skill_version**: v2.5.1
- **日期**: 2026-07-13
- **触发原因**: #ABS-003 UV 列原始数据丢失事件
- **next_action**: review_by_agent_b

## 1. 改造背景

### 1.1 事件经过

2026-07-12，用户上传 0706 新台账 + 东裕4号仲裕（续发）簿记明细，要求录入。

0706 台账是 21 列（无 WXY），0703 定稿是 25 列（有 WXY）。我写了一个自定义脚本 `_append_new_project.py` 把 0706 的新项目追加到 0703 定稿末尾，然后跑 supplement 模式录入簿记明细。

用户发现 UV 列（认购机构/认购份额）原始数据丢失，要求回滚。已回滚至 0703 定稿。

### 1.2 根因

| 层面 | 问题 |
|---|---|
| 操作层面 | 自定义脚本绕过 increment_merge.py 的 QC 体系 |
| 代码层面 | QC 7.14 只检查 V 列**格式**（number_format），不检查 V 列**值** |
| 代码层面 | QC FAIL 后不阻断执行（run_enhanced_qc 返回值未被检查） |
| 流程层面 | supplement 模式被误用于"追加新项目"（设计用途是"对已有项目补充簿记"） |

## 2. 改造范围

### 2.1 新增 QC 7.20: UV column value preservation

**文件**: `scripts/increment_merge.py` L763-797（新增）

**逻辑**:
- 对比 `ws_orig_protected`（processed 台账）和 `ws_out`（output 台账）的 U/V 列值
- 非目标项目的 U/V 值变化 → FAIL
- 目标项目（supplement/rebook 的目标项目行号范围）的 U/V 允许变化

**关键代码**:
```python
# QC 7.20: UV column value preservation (#ABS-003)
target_rows = set()
for key, pstart, pend in target_projects:
    for r in range(pstart, pend + 1):
        target_rows.add(r)

for r in range(2, max_r + 1):
    if r in target_rows:
        continue  # 目标项目允许变化
    u_orig = ws_orig_protected.cell(row=r, column=21).value
    v_orig = ws_orig_protected.cell(row=r, column=22).value
    u_out = ws_out.cell(row=r, column=21).value
    v_out = ws_out.cell(row=r, column=22).value
    if u_orig != u_out or v_orig != v_out:
        uv_violations.append((r, u_orig, v_orig, u_out, v_out))
```

### 2.2 QC FAIL 阻断执行

**文件**: `scripts/increment_merge.py` L1356-1368（修改）

**逻辑**:
- `run_enhanced_qc` 返回 `(qc_fails, qc_warns)`
- `qc_fails > 0` 时不保存输出文件，直接 return
- 打印 `[BLOCKED]` 提示

**关键代码**:
```python
qc_fails, qc_warns = run_enhanced_qc(...)
if qc_fails > 0:
    print(f"[BLOCKED] {mode_label} aborted due to {qc_fails} QC FAIL(s).")
    print(f"[BLOCKED] Output file NOT saved. Fix the issues above and re-run.")
    return  # 不保存
```

### 2.3 pitfall_log #ABS-003

**文件**: `pitfall_log.md`（新增章节）

记录事件经过、根因、修复方案、约束。

### 2.4 CHANGELOG v2.5.1

**文件**: `CHANGELOG.md`（新增段）

## 3. 改造 diff 范围

| 文件 | 改动 |
|---|---|
| `scripts/increment_merge.py` | +35 行（QC 7.20 + FAIL 阻断） |
| `pitfall_log.md` | +18 行（#ABS-003） |
| `CHANGELOG.md` | +25 行（v2.5.1 段） |

## 4. 自检

### 4.1 QC 7.20 覆盖范围

- ✅ U 列（认购机构）值变化检测
- ✅ V 列（认购份额）值变化检测
- ✅ None vs 值 的变化检测
- ✅ 目标项目豁免（supplement/rebook 目标行号范围）
- ✅ 非目标项目严格保护

### 4.2 FAIL 阻断覆盖范围

- ✅ `qc_fails > 0` 时不保存文件
- ✅ 打印 `[BLOCKED]` 提示
- ✅ `return` 退出 `run_increment_merge`

### 4.3 已知遗留

- QC 7.20 只检查 U/V 列，不检查 T 列（成本）或其他列。如果未来出现其他列丢失，需要扩展。
- QC 7.20 依赖 `ws_orig_protected`（processed 台账的只读副本），如果 processed 台账本身有问题，QC 无法检测。
- `target_rows` 的行号范围在 `rebook` 模式 Step 5.0 删除行后会偏移，但 QC 7.20 在 Step 6（格式优化后）执行，此时行号已稳定。

## 5. 审计建议

1. **核查 QC 7.20 逻辑**: 确认 `target_rows` 集合构建正确，不会误判目标项目
2. **核查 FAIL 阻断**: 确认 `return` 后确实不保存文件（`wb.save()` 在 return 之后）
3. **核查 pitfall_log**: 确认 #ABS-003 记录准确
4. **端到端验证**: 用 0703 定稿跑一次 supplement 模式，确认 QC 7.20 PASS

## 6. commit_hash

1ad1a89
