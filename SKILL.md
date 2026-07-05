---
name: "ABS工具箱"
version: "2.2.0"
description: >
  ABS业务多功能工具箱。整合发行定价、机构统计、簿记录入三大业务模块,提供从台账录入到机构统计到发行定价分析的端到端工作流。
  第一轮(v2.0.0)激活:机构统计 + 产出归档。
  第二轮(v2.1.0)激活:簿记录入(原样迁入,0 改动,5 层自检通过)。
  第三轮(v2.2.0)激活:发行定价(3 个 gen 脚本,4 处路径改造,6 层自检通过)。
  全流程编排:录入→统计→定价 三步串行已激活。
  触发词包括:ABS工具箱、ABS机构统计、ABS归档、台账归档、看板归档、
  机构统计看板、管理人统计、销售机构统计、托管行统计、机构排名、
  申万宏源合并、机构合并统计、ABS发行台账、ABS产出索引。
---

# ABS工具箱 Skill

> **v2.0.0 第一轮(2026-07-05)**:激活机构统计 + 产出归档两条路径。
> **v2.1.0 第二轮(2026-07-05)**:迁入簿记录入 v2.1(原样,0 改动,5 层自检通过,已归档 APPROVED)。
> **v2.2.0 第三轮(2026-07-05)**:迁入发行定价 v1.5.0(3 个 gen 脚本,4 处路径改造,6 层自检通过)。
> **全流程编排**:录入→统计→定价 三步串行已激活。
> **回滚备份**:原 `skills/发行定价/` `skills/机构统计/` `skills/簿记录入/` 保留不动,新 skill 出问题随时回滚。

## 与原 3 skill 的关系

| 原 skill | 版本 | 状态 | 新 skill 路径 |
|---|---|---|---|
| 机构统计 | v1.1.0 | 已迁入(v2.0.0) | `scripts/gen_institution_stats.py` |
| 簿记录入 | v2.1 | 已迁入(v2.1.0) | `scripts/increment_merge.py` |
| 发行定价 | v1.5.0 | 已迁入(v2.2.0) | `scripts/gen_abs_cost_report.py` + `gen_compare_tool.py` + `gen_spread_report.py` |

**触发"ABS 全流程"时**:本 skill 串行调用 录入→统计→定价 三步。

## 触发词路由

| 触发词 | 路由 | 状态 |
|---|---|---|
| ABS 机构统计 / 机构统计看板 / 管理人统计 / 申万宏源合并 | `scripts/gen_institution_stats.py` | ✅ v2.0.0 |
| ABS 归档 / 台账归档 / 看板归档 | `scripts/abs_archive.py` | ✅ v2.0.0 |
| ABS 产出索引 / 文件索引 | `scripts/abs_archive.py index` | ✅ v2.0.0 |
| ABS 簿记录入 / 补充簿记数据 / 增量台账合并 | `scripts/increment_merge.py` | ✅ v2.1.0 |
| ABS 发行定价 / 成本分析 / 利差分析 | `scripts/gen_abs_cost_report.py` + `gen_compare_tool.py` + `gen_spread_report.py` | ✅ v2.2.0 |
| ABS 全流程 | 录入→统计→定价 串行 | ✅ v2.2.0 |

## 使用示例

### 1. 机构统计看板生成

```bash
PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_institution_stats.py \
  "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx"
```

产出: `skills/ABS工具箱/deliverables/dashboards/01_latest/YYYYMMDD_机构统计看板.html`

### 2. 产出归档

```bash
# 看板归档:旧最新版本 → 历史版本
PYTHONUTF8=1 python skills/ABS工具箱/scripts/abs_archive.py dashboards

# 台账归档:加工中 → 定稿,旧定稿 → 归档
PYTHONUTF8=1 python skills/ABS工具箱/scripts/abs_archive.py ledger

# 重建文件索引
PYTHONUTF8=1 python skills/ABS工具箱/scripts/abs_archive.py index
```

### 3. 簿记录入(补充簿记模式)

```bash
PYTHONUTF8=1 python skills/ABS工具箱/scripts/increment_merge.py \
  --processed "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx" \
  --supplement \
  --details skills/ABS工具箱/deliverables/ledger/05_bookkeeping_details/*.xlsx \
  --output "skills/ABS工具箱/deliverables/ledger/02_processing/2026年ABS发行台账-0626-补充簿记v1.xlsx"
```

产出:`deliverables/ledger/02_processing/2026年ABS发行台账-0626-补充簿记v1.xlsx`

### 4. 簿记录入(增量合并模式)

```bash
PYTHONUTF8=1 python skills/ABS工具箱/scripts/increment_merge.py \
  --processed "上周定稿.xlsx" \
  --new-raw "本周新原始台账.xlsx" \
  --details 簿记明细*.xlsx \
  --output "deliverables/ledger/02_processing/本周台账.xlsx"
```

### 5. 发行定价(三看板一次跑)

```bash
PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_abs_cost_report.py \
  "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx"

PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_compare_tool.py \
  "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx"

PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_spread_report.py \
  "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx"
```

产出 3 份 HTML 到 `deliverables/dashboards/01_latest/`:
- `YYYYMMDD_机构投标利率看板.html`(工具一:成本分布)
- `YYYYMMDD_发行定价分析工具.html`(工具二:机构比对)
- `YYYYMMDD_机构投标基准利差看板.html`(工具三:利差分析)

### 6. ABS 全流程(录入→统计→定价串行)

```bash
# Step 1: 簿记录入(补充簿记明细)
PYTHONUTF8=1 python skills/ABS工具箱/scripts/increment_merge.py \
  --processed "deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx" \
  --supplement --details deliverables/ledger/05_bookkeeping_details/*.xlsx \
  --output "deliverables/ledger/02_processing/2026年ABS发行台账-0626-补充簿记v1.xlsx"

# Step 2: 机构统计(用补充簿记后的台账)
PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_institution_stats.py \
  "deliverables/ledger/02_processing/2026年ABS发行台账-0626-补充簿记v1.xlsx"

# Step 3: 发行定价(3 看板,用补充簿记后的台账)
PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_abs_cost_report.py \
  "deliverables/ledger/02_processing/2026年ABS发行台账-0626-补充簿记v1.xlsx"
PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_compare_tool.py \
  "deliverables/ledger/02_processing/2026年ABS发行台账-0626-补充簿记v1.xlsx"
PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_spread_report.py \
  "deliverables/ledger/02_processing/2026年ABS发行台账-0626-补充簿记v1.xlsx"
```

## 目录结构

```
skills/ABS工具箱/
├── SKILL.md                       (本文件)
├── README.md                      (同事入门)
├── CHANGELOG.md                   (版本历史)
├── AUDIT_REPORT.md                (审计基线)
├── pitfall_log.md                 (踩坑日志)
├── audit/                         (审计子系统,A→B→C 循环)
│   ├── README.md                  (审计操作手册)
│   ├── INDEX.md                   (审计索引)
│   ├── state.json                 (状态机)
│   ├── submissions/               (送审报告 Agent A)
│   ├── reviews/                   (审计意见 Agent B)
│   └── closed/                    (归档报告 Agent C)
├── scripts/
│   ├── abs_common.py              (共享底座)
│   ├── entity_alias.py            (机构名映射)
│   ├── gen_institution_stats.py   (机构统计)
│   ├── increment_merge.py         (簿记录入 v2.1)
│   ├── gen_abs_cost_report.py     (发行定价 工具一:成本分布)
│   ├── gen_compare_tool.py        (发行定价 工具二:机构比对)
│   ├── gen_spread_report.py       (发行定价 工具三:利差分析)
│   ├── test_smoke.py              (冒烟测试)
│   └── abs_archive.py             (归档工具)
└── deliverables/                  (产出,英文化目录)
    ├── ledger/                    (台账)
    │   ├── 01_source/             (源文件)
    │   ├── 02_processing/         (加工中)
    │   ├── 03_final/              (定稿)
    │   ├── 04_archive/            (归档)
    │   └── 05_bookkeeping_details/ (簿记明细)
    └── dashboards/                (看板)
        ├── 01_latest/             (最新版本)
        ├── 02_history/            (历史版本)
        ├── 03_test/               (测试文件)
        └── 04_reference/          (参考资料)
```

## 环境

- Python 3.12+(推荐 `C:/Users/wupeizhi.nolan/AppData/Local/Programs/Python/Python312/python.exe`)
- 依赖:pandas + openpyxl(已预装)
- 无外部数据源依赖(纯本地 Excel 处理)
- Windows 调用前加 `PYTHONUTF8=1` 避免 GBK 编码问题

## 审计流程(A→B→C 循环)

ABS工具箱采用三角色审计循环,参考 macro-allocation-strategy 精简适配。详见 `audit/README.md`。

### 目录结构

```
audit/
├── README.md                # 审计操作手册(人类参考)
├── INDEX.md                 # 审计索引(手动维护)
├── state.json               # 状态机(手动维护)
├── submissions/             # 送审报告(Agent A 写)
│   ├── _template.md
│   └── A{N}-{slug}-r{R}.md
├── reviews/                 # 审计意见(Agent B 写)
│   ├── _template.md
│   └── B{N}-{slug}-r{R}.md
└── closed/                  # 归档报告(Agent C 写)
    ├── _template.md
    └── C{N}-{slug}-r{R}.md
```

### 流程

1. **Agent A**(实现):写代码 + commit + 打 git tag `audit/v{X.Y}-{slug}-r{NN}` + 写送审报告 → push abs-toolbox 仓库
2. **Agent B**(审计):独立 Agent,只读代码+送审报告,写审计意见(verdict: APPROVED / NEEDS_REVISION / REJECTED)
3. **Agent C**(归档):verdict=APPROVED 时归档,写归档报告

### 文件命名

| 类型 | 格式 | 示例 |
|---|---|---|
| 送审报告 | `A{N}-{slug}-r{R}.md` | `A1-v20-institution-stats-r1.md` |
| 审计意见 | `B{N}-{slug}-r{R}.md` | `B1-v20-institution-stats-r1.md` |
| 归档报告 | `C{N}-{slug}-r{R}.md` | `C1-v20-institution-stats-r1.md` |
| git tag | `audit/v{X.Y}-{slug}-r{NN}` | `audit/v2.0-v20-institution-stats-r01` |

### slug 命名

slug 带版本前缀:`v{XX}-{主题}`(如 `v20-institution-stats`、`v21-bookkeeping`、`v22-pricing`)。

### 已归档送审

| submission_id | slug | skill_version | round | status | commit | 日期 |
|---|---|---|---|---|---|---|
| A1-v20-institution-stats-r1 | v20-institution-stats | v2.0.0 | r1 | PENDING_REVIEW(已通过独立审计) | `524cdae` | 2026-07-05 |
| A1-v21-bookkeeping-r1 | v21-bookkeeping | v2.1.0 | r1 | PENDING_REVIEW | `27f08a8` | 2026-07-05 |

详见 `audit/INDEX.md`。

### ABS工具箱特色:5 层自检

送审报告必含 5 层自检证据(ABS工具箱整合的功能等价性验证):

| 层 | 检查 | 通过标准 |
|---|---|---|
| 1 | 文件字节对比 | diff 为空(原样迁入) |
| 2 | 端到端穿行 | 新旧 skill 同输入同输出 |
| 3 | 逐 cell diff | 产出 xlsx 逐 cell 一致 |
| 4 | 原 skill smoke | 原 skill 同输入 QC 一致 |
| 5 | 回归测试 | 其他 skill 不受影响 |

## 审计与回滚

- 送审报告归档在 `audit/submissions/`(不再散落 Inbox)
- skill 长期审计基线见 `AUDIT_REPORT.md`
- 回滚:`git rm -r skills/ABS工具箱/` + `git mv` 还原产出目录即可,原 3 skill 完整保留
