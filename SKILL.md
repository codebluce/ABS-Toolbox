---
name: "ABS工具箱"
version: "2.0.0"
description: >
  ABS业务多功能工具箱。整合发行定价、机构统计、簿记录入三大业务模块,提供从台账录入到机构统计到发行定价分析的端到端工作流。
  第一轮(v2.0.0)激活:机构统计 + 产出归档。
  第二轮(规划中)激活:簿记录入 + 发行定价 + 全流程编排。
  触发词包括:ABS工具箱、ABS机构统计、ABS归档、台账归档、看板归档、
  机构统计看板、管理人统计、销售机构统计、托管行统计、机构排名、
  申万宏源合并、机构合并统计、ABS发行台账、ABS产出索引。
---

# ABS工具箱 Skill

> **v2.0.0 第一轮(2026-07-05)**:激活机构统计 + 产出归档两条路径。
> **第二轮(规划中)**:迁入簿记录入 v2.1 + 发行定价 v1.5.0,激活"ABS 全流程"串行编排。
> **回滚备份**:原 `skills/发行定价/` `skills/机构统计/` `skills/簿记录入/` 保留不动,新 skill 出问题随时回滚。

## 与原 3 skill 的关系

| 原 skill | 版本 | 状态 | 新 skill 路径 |
|---|---|---|---|
| 机构统计 | v1.1.0 | 已迁入(v2.0.0) | `scripts/gen_institution_stats.py` |
| 簿记录入 | v2.1 | 第二轮迁入(规划中) | 暂引导回原 skill |
| 发行定价 | v1.5.0 | 第二轮迁入(规划中) | 暂引导回原 skill |

**触发"ABS 簿记录入"或"ABS 发行定价"时**:本 skill 会引导你回 `skills/簿记录入/` 或 `skills/发行定价/` 执行,直至第二轮迁入完成。

## 触发词路由

| 触发词 | 路由 | 状态 |
|---|---|---|
| ABS 机构统计 / 机构统计看板 / 管理人统计 / 申万宏源合并 | `scripts/gen_institution_stats.py` | ✅ v2.0.0 |
| ABS 归档 / 台账归档 / 看板归档 | `scripts/abs_archive.py` | ✅ v2.0.0 |
| ABS 产出索引 / 文件索引 | `scripts/abs_archive.py index` | ✅ v2.0.0 |
| ABS 簿记录入 / 补充簿记数据 | 引导回 `skills/簿记录入/` | 🟡 第二轮 |
| ABS 发行定价 / 成本分析 / 利差分析 | 引导回 `skills/发行定价/` | 🟡 第二轮 |
| ABS 全流程 | 第二轮激活 | 🟡 第二轮 |

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

## 目录结构

```
skills/ABS工具箱/
├── SKILL.md                       (本文件)
├── README.md                      (同事入门)
├── CHANGELOG.md                   (版本历史)
├── AUDIT_REPORT.md                (审计基线)
├── pitfall_log.md                 (踩坑日志)
├── scripts/
│   ├── abs_common.py              (共享底座)
│   ├── entity_alias.py            (机构名映射)
│   ├── gen_institution_stats.py   (机构统计)
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

## 审计与回滚

- 每次重大改动生成 `Inbox/auditReport_GLM52_YYYYMMDD_ABS工具箱.md`,按 step 分节留痕
- skill 长期审计基线见 `AUDIT_REPORT.md`
- 回滚:`git rm -r skills/ABS工具箱/` + `git mv` 还原产出目录即可,原 3 skill 完整保留
