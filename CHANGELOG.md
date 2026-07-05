# ABS工具箱 CHANGELOG

> v2.0.0 起点为整合三 skill 的新版本号。原 3 skill 的历史版本号作为指针保留,便于追溯。

## 历史版本指针(整合前)

| 原 skill | 最后版本 | 整合时状态 | 历史日志位置 |
|---|---|---|---|
| 机构统计 | v1.1.0 | 已迁入本 skill v2.0.0 | `skills/机构统计/pitfall_log.md`(保留) |
| 簿记录入 | v2.1 | 第二轮迁入(规划中) | `skills/簿记录入/v2.1/复盘踩坑日志.md`(保留) |
| 发行定价 | v1.5.0 | 第二轮迁入(规划中) | `skills/发行定价/CHANGELOG.md`(保留) |

---

## v2.0.0 — 2026-07-05 第一轮

### 新增

- **skill 骨架**:SKILL.md / CHANGELOG.md / pitfall_log.md / README.md / AUDIT_REPORT.md
- **共享底座**:`scripts/abs_common.py`(从发行定价 v1.5.0 复制,364 行)
- **机构名映射**:`scripts/entity_alias.py` 合并三套 map
  - `ENTITY_MERGE_MAP`(申万宏源系 3 条,来自机构统计 v1.1.0 L131)
  - `BANK_NORM_MAP`(分行归并 22 条,来自机构统计 v1.1.0 L138)
  - `HARD_MAP`(杭州联合等,来自簿记录入 v2.1 SKILL.md L207-218)
- **机构统计**:`scripts/gen_institution_stats.py`(从机构统计 v1.1.0 复制 + 5 处改造)
  - 接入 abs_common(删 `preprocess_unmerge_fill`)
  - 接入 entity_alias(删 `ENTITY_MERGE_MAP` + `BANK_NORM_MAP` 内联)
  - 保留 `internal_merge_bookkeeping`(第二轮删,簿记录入 v2.1 迁入后改调原 skill)
  - 输出路径改 `deliverables/dashboards/01_latest/`
- **归档工具**:`scripts/abs_archive.py`(新写)
  - `ledger` 子命令:加工中 → 定稿,旧定稿 → 归档
  - `dashboards` 子命令:最新版本 → 历史版本/YYYYMMDD/
  - `index` 子命令:重建 `_文件索引目录.md`(修复脱节,从 0515 同步至 07-05)
- **产出目录迁入**:`ABS技能包/{台账,看板}` → `skills/ABS工具箱/deliverables/{ledger,dashboards}`
- **目录英文化**:9 个子目录中文 → 英文(`01-源文件` → `01_source` 等)

### 验证

- 0626 定稿台账跑通,产出机构统计看板
- 新旧 skill 产出 HTML 内容一致(除路径外)
- abs_archive.py 三子命令幂等
- 原 3 skill 文件未动(`git diff` 为空)

### 待办(第二轮,1-2 周后)

- [ ] 迁入 `increment_merge.py`(簿记录入 v2.1)
- [ ] 迁入发行定价 3 个 `gen_*.py`
- [ ] 激活"ABS 全流程"串行编排
- [ ] 删除 `gen_institution_stats.py` 内部 `internal_merge_bookkeeping`,改调簿记录入
- [ ] 原 3 skill 标 `deprecated`(不删除,保留 6 个月观察期)

### 已知遗留

- `gen_institution_stats.py` 仍保留 `internal_merge_bookkeeping`(簿记录入未迁入前的过渡方案)
- `deliverables/ledger/04_archive/` 19 份历史台账,体积膨胀,后续按月压缩
- `skills/发行定价/scripts/gen_abs_cost_report.py` + `gen_compare_tool.py` 有未提交改动(上次会话遗留),第二轮处理
