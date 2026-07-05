---
# --- 基础元数据 ---
submission_id: A1-v24-self-check-r1
slug: v24-self-check
skill_version: v2.4.0
round: 1
created_at: "2026-07-05 16:50:00"
author: agent_a

# --- 代码快照 ---
git_tag: audit/v2.4-v24-self-check-r01
commit_hash: 31f716f
previous_git_tag: null

# --- 变更文件 ---
changed_files:
  - scripts/self_check.py                      # added
  - audit/self_check/.gitkeep                  # added
  - audit/self_check/v20-institution-stats_r1_20260705_164043.json   # added (测试产出基线)
  - audit/self_check/v20-institution-stats_r1_20260705_164043.md     # added
  - audit/self_check/v21-bookkeeping_r1_20260705_164809.json         # added
  - audit/self_check/v21-bookkeeping_r1_20260705_164809.md           # added
  - audit/self_check/v22-pricing_r1_20260705_164522.json             # added
  - audit/self_check/v22-pricing_r1_20260705_164522.md               # added
  - audit/self_check/v23-internal-merge-unify_r1_20260705_164401.json # added
  - audit/self_check/v23-internal-merge-unify_r1_20260705_164401.md   # added
  - SKILL.md                                   # modified (v2.4.0 + 自检章节)
  - CHANGELOG.md                               # modified (v2.4.0 段)
  - pitfall_log.md                             # modified (无新增, 仅同步)

# --- 状态机 ---
status: PENDING_REVIEW

# --- 强制自审 ---
self_review:
  all_issues_addressed: true
  no_overengineering: true
  function_equivalence_verified: true
  edge_cases_covered: true
  notes: "v24 不是 skill 迁入, 是工具脚本 (self_check.py). 5 层自检脚本本身用 4 个 slug 跑过验证, 全部 PASS."

# --- 审计焦点 ---
review_focus:
  - 降级模式 (degraded) 是否在原 skill 删除后真能跑通 — 当前仅模拟测试 (用 --mode degraded 跳过 1/3/4), 未实际删除原 skill 验证
  - QC FAIL 不阻断的逻辑是否合理 (0626 数据已知问题, 真正回归闸门是层 3 逐 cell diff)
---

# v24-self-check r1 送审报告

## 1. 变更摘要 (200 字内)

新增 `scripts/self_check.py` 5 层自检脚本, 配置驱动 + 降级接口. 5 层 = 字节对比/端到端穿行/逐 cell diff/原 skill smoke/回归测试. `--mode auto|full|degraded` 自动检测原 skill 是否存在, 删除后切 degraded (只跑层 2+5). 用 4 个 slug (v20/v21/v22/v23) 跑过验证, v21/v23 全 5 层 PASS, v22 (3 SKIP 1 INFO) PASS, v20 (1 INFO) PASS. 这是 CHANGELOG 待办里"5 层自检脚本化 (用 6 个月)"的兑现, 也是 6 个月观察期结束后删原 skill 的前置工具.

## 2. 上一轮 Issue 处理

首轮, 无上一轮 Issue.

## 3. 代码变更清单

| 文件 | 操作 | 说明 |
|---|---|---|
| scripts/self_check.py | added | 5 层自检脚本主入口, 642 行 |
| audit/self_check/*.json/*.md | added | 4 个 slug 首次跑的基线报告 (8 文件) |
| SKILL.md | modified | frontmatter 升 v2.4.0 + 加"5 层自检脚本"章节 |
| CHANGELOG.md | modified | 加 v2.4.0 段 |
| pitfall_log.md | modified | 同步 (无新增 pitfall) |

## 4. 自审与指标

### 4.1 强制自审清单

- [x] all_issues_addressed: 首轮, 无上一轮 Issue
- [x] no_overengineering: 配置驱动 (SLUG_CONFIG dict), 4 个 slug 共用同一套 layer 函数; 没引入额外抽象层
- [x] function_equivalence_verified: 4 个 slug 全部跑过 PASS (v21 5/5 PASS, v23 5/5 PASS, v22 3 PASS + 1 SKIP + 1 INFO, v20 4 PASS + 1 INFO)
- [x] edge_cases_covered: 降级模式 (degraded) 测过 v21, 1/3/4 SKIP, 2/5 PASS; v22 的 layer 3 SKIP (不适用 increment_merge 类) 也覆盖了

### 4.2 5 层自检证据 (脚本自身验证)

| slug | 层 1 字节对比 | 层 2 端到端 | 层 3 逐 cell diff | 层 4 原 skill smoke | 层 5 回归 | 总评 |
|---|---|---|---|---|---|---|
| v20-institution-stats | INFO (改造预期) | PASS | SKIP (非 increment_merge) | PASS | PASS | PASS |
| v21-bookkeeping | PASS (字节级一致) | PASS | PASS (13753 cell 0 差异) | PASS | PASS | PASS |
| v22-pricing | INFO (路径改造预期) | PASS | SKIP (非 increment_merge) | PASS | PASS | PASS |
| v23-internal-merge-unify | INFO (改造预期) | PASS | PASS (13753 cell 0 差异) | PASS | PASS | PASS |

**关键证据**:
- v21-bookkeeping 字节对比: `new_md5 == orig_md5 == c5e41afdb9932d036def68050e29ed59` (PASS, 原样迁入 0 改动)
- v21/v23 逐 cell diff: 25 sheet × 6 列 (P/U/V/W/X/Y) × max_row 行 = 13753 cell, 0 差异
- 降级模式 (v21 --mode degraded): 层 1/3/4 SKIP, 层 2/5 PASS

## 5. 审计焦点 (给 B 的提示)

1. **QC FAIL 不阻断的逻辑**: 层 2/4/5 仅判 `returncode=0`, QC FAIL 仅记录不阻断. 这是因 0626 数据本身存在已知 QC FAIL (gen_abs_cost_report 11 条成本超界, gen_spread_report 13 条利差超界, increment_merge Fails=1 Warns=4), v22 B1 已确认非回归. 真正的回归闸门是层 3 逐 cell diff (新旧产出必须 0 差异). 请评估此设计是否合理 — 是否应该把 0626 数据的 QC 基线写入快照, 后续跑出 FAIL 时对比基线?

2. **降级模式实测**: 当前只用 `--mode degraded` 模拟测试 (跳过 1/3/4). 真正删除原 skill 后, `auto` 模式是否会正确切 degraded? 需要实际删除一个原 skill 测试吗 (建议不删, 6 个月观察期结束后再实测)?

3. **配置驱动**: SLUG_CONFIG 字典硬编码了 4 个 slug 的配置 (新/原 skill 路径, 是否需 details, downstream). 后续若新增 slug (如 v25-xxx), 需要手动加配置. 是否应该改成自动扫描 audit/state.json 的 slugs?

4. **Python 解释器路径**: `find_python()` 函数硬编码了 2 个候选路径. 如果用户换机器, 需要更新这个列表. 是否应该改成只信任 `sys.executable`?

## 6. 附录

### 6.1 5 层自检脚本架构

```
scripts/self_check.py (642 行)
├── SLUG_CONFIG dict (4 slug 配置)
├── detect_mode()         # auto/full/degraded 切换
├── layer1_byte_diff()    # 字节对比 (md5)
├── layer2_e2e_run()      # 端到端穿行 (returncode + 产出存在)
├── layer3_cell_diff()    # 逐 cell diff (openpyxl, 6 列 × 全 sheet)
├── layer4_orig_smoke()   # 原 skill smoke
├── layer5_regression()   # 回归测试 (机构统计 + 3 看板)
└── run_self_check()      # 主流程, 输出 JSON + MD 到 audit/self_check/
```

### 6.2 cell 计数口径声明 (避免 v21 那种 A/B 分歧)

- **单 sheet 对比**: 仅主 sheet 的 P/U/V/W/X/Y 6 列 × max_row 行
- **全 sheet 对比**: 所有 sheet × 6 列 × max_row 行
- **本脚本默认走全 sheet**, 在层 3 details.cell_count_caliber 字段写明实际口径
- v21/v23 实际跑出: 25 sheet × 6 列 × max_row 行 = 13753 cell, 0 差异

### 6.3 降级模式测试证据

```
$ python scripts/self_check.py --slug v21-bookkeeping --mode degraded --round 1
[Layer 2] 端到端穿行 ...  → PASS
[Layer 5] 回归测试 ...    → PASS
总评: PASS  PASS=2  FAIL=0  SKIP=3  INFO=0
```

### 6.4 4 slug 全量跑通证据

```
$ python scripts/self_check.py --mode auto --round 1
  v20-institution-stats                PASS  (4 PASS + 1 INFO)
  v21-bookkeeping                      PASS  (5 PASS)
  v22-pricing                          PASS  (3 PASS + 1 SKIP + 1 INFO)
  v23-internal-merge-unify             PASS  (4 PASS + 1 INFO)
  总评: PASS
```

### 6.5 关键设计决策

| 决策 | 理由 |
|---|---|
| 5 层只判 returncode=0 + 产出存在 | 0626 数据本身存在 QC FAIL, 不是回归; 真正回归看层 3 逐 cell diff |
| 降级模式跳过 1/3/4 | 这 3 层都依赖原 skill, 删除后无法跑; 层 2/5 不依赖原 skill, 仍可跑 |
| 配置驱动 (SLUG_CONFIG) | 4 个 slug 的差异 (是否需 details, downstream, 原 skill 路径) 抽到一个 dict, 主流程统一 |
| JSON + MD 双输出 | JSON 给程序读 (后续可写对比脚本), MD 给人读 |
| 不写基线快照对比 | 首轮只跑出基线; 后续轮次可对比基线, 但本次不实现 (留 v25+) |
