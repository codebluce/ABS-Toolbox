# ABS工具箱 — 同事入门

> v2.0.0(2026-07-05)第一轮。本 skill 整合了原 3 个 ABS 业务 skill(发行定价 / 机构统计 / 簿记录入),提供从台账录入到机构统计到发行定价分析的端到端工作流。
> 第一轮激活:机构统计 + 产出归档。第二轮(1-2 周后)激活簿记录入 + 发行定价 + 全流程编排。

## 快速开始

### 环境要求

- Python 3.12+(推荐 3.12.4)
- 依赖:`pandas` + `openpyxl`(已预装)
- 无外部数据源依赖(纯本地 Excel 处理)
- Windows 调用前加 `PYTHONUTF8=1` 避免 GBK 编码问题

### 1. 机构统计看板生成

```bash
PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_institution_stats.py \
  "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx"
```

产出:`skills/ABS工具箱/deliverables/dashboards/01_latest/YYYYMMDD_机构统计看板.html`

### 2. 产出归档

```bash
# 看板归档(旧最新版本 → 历史版本)
PYTHONUTF8=1 python skills/ABS工具箱/scripts/abs_archive.py dashboards

# 台账归档(加工中 → 定稿,旧定稿 → 归档)
PYTHONUTF8=1 python skills/ABS工具箱/scripts/abs_archive.py ledger

# 重建文件索引
PYTHONUTF8=1 python skills/ABS工具箱/scripts/abs_archive.py index
```

## 目录结构

```
skills/ABS工具箱/
├── SKILL.md                       (触发词路由)
├── README.md                      (本文件)
├── CHANGELOG.md                   (版本历史)
├── AUDIT_REPORT.md                (审计基线)
├── pitfall_log.md                 (踩坑日志)
├── scripts/
│   ├── abs_common.py              (共享底座:预处理/QC框架/常量)
│   ├── entity_alias.py            (机构名映射:ENTITY_MERGE+BANK_NORM+HARD_MAP)
│   ├── gen_institution_stats.py   (机构统计:管理人/销售机构/托管行三表)
│   └── abs_archive.py             (归档:ledger/dashboards/index 三子命令)
└── deliverables/                  (产出,全英文目录)
    ├── ledger/                    (台账)
    │   ├── 01_source/             (源文件)
    │   ├── 02_processing/         (加工中)
    │   ├── 03_final/              (定稿)
    │   ├── 04_archive/            (归档)
    │   └── 05_bookkeeping_details/ (簿记明细)
    └── dashboards/                (看板)
        ├── 01_latest/             (最新版本)
        ├── 02_history/            (历史版本,按 YYYYMMDD 子文件夹)
        ├── 03_test/               (测试文件)
        └── 04_reference/          (参考资料)
```

## 与原 3 skill 的关系

| 原 skill | 当前状态 | 触发时路由 |
|---|---|---|
| 机构统计 v1.1.0 | 已迁入 v2.0.0 | 直接走 `ABS工具箱/scripts/gen_institution_stats.py` |
| 簿记录入 v2.1 | 第二轮迁入 | 引导回 `skills/簿记录入/` |
| 发行定价 v1.5.0 | 第二轮迁入 | 引导回 `skills/发行定价/` |

原 3 skill 完整保留(回滚备份),6 个月观察期后下线。

## 审计与追溯

- **每次重大改动**生成 `Inbox/auditReport_GLM52_YYYYMMDD_ABS工具箱.md`,按 step 分节留痕(改动文件/diff hunk/验证证据/风险)
- **长期审计基线**见 `AUDIT_REPORT.md`
- **踩坑日志**见 `pitfall_log.md`(合并自原 3 skill)
- **回滚**:`git rm -r skills/ABS工具箱/` + `git mv` 还原产出目录即可

## 命名规范

### 台账文件

`2026年ABS发行台账-MMDD[-{源|WIP|定稿|增量合并vN|簿记数据录入vN}].xlsx`

示例:`2026年ABS发行台账-0626-定稿.xlsx`

### 看板文件

`YYYYMMDD_<看板名>.html`

| 看板名 | 来源工具 | 第一轮可用 |
|---|---|---|
| 机构统计看板 | gen_institution_stats.py | ✅ |
| 发行定价分析工具 | gen_abs_cost_report.py | 🟡 第二轮 |
| 机构投标利率看板 | gen_compare_tool.py | 🟡 第二轮 |
| 机构投标基准利差看板 | gen_spread_report.py | 🟡 第二轮 |

### 簿记明细

`<项目名>簿记明细-YYYYMMDD.xlsx`

## 问题反馈

- 踩坑记录追加到 `pitfall_log.md` 第 D 节(从 #ABS-001 续编)
- 重大问题触发审计,生成 `Inbox/auditReport_GLM52_YYYYMMDD_ABS工具箱.md`
