# ABS工具箱 CHANGELOG

> v2.0.0 起点为整合三 skill 的新版本号。原 3 skill 的历史版本号作为指针保留,便于追溯。

## 历史版本指针(整合前)

| 原 skill | 最后版本 | 整合时状态 | 历史日志位置 |
|---|---|---|---|
| 机构统计 | v1.1.0 | 已迁入本 skill v2.0.0 | `skills/机构统计/pitfall_log.md`(保留) |
| 簿记录入 | v2.1 | 第二轮迁入(规划中) | `skills/簿记录入/v2.1/复盘踩坑日志.md`(保留) |
| 发行定价 | v1.5.0 | 第二轮迁入(规划中) | `skills/发行定价/CHANGELOG.md`(保留) |

---

## v2.1.0 — 2026-07-05 第二轮

### 新增

- **簿记录入 v2.1 迁入**:`scripts/increment_merge.py`(从 `skills/簿记录入/v2.1/increment_merge.py` 原样复制,0 改动,1221 行)
  - 11 个顶层函数全部保留:`normalize` / `unmerge_and_fill_raw` / `unmerge_and_fill_processed` / `get_all_projects` / `get_project_range` / `get_layers_in_project` / `normalize_rate` / `read_detail` / `map_detail_to_project` / `run_enhanced_qc` / `run_increment_merge`
  - 17 项 QC 7.1-7.19 + 3 项基础 QC 全部保留(P0×11 + P1×8 + INFO×1)
  - 接口完全一致:`--processed` / `--new-raw` / `--details` / `--output` / `--supplement`
- **5 层自检通过**:
  1. 文件字节对比:diff 为空(1221 → 1221)
  2. 端到端穿行:0626 定稿 + 11 份明细 supplement 模式 QC PASSED
  3. 产出逐 cell diff:新旧 skill 产出 xlsx WXY 列 + 保护列逐 cell 一致
  4. 原 skill smoke test:同输入 QC PASSED(原 skill 未动)
  5. 机构统计回归:gen_institution_stats.py QC 仍 PASSED 35 项(无回归)
- **SKILL.md 触发词路由**:"ABS 簿记录入" 从 🟡 第二轮 → ✅ v2.1.0
- **使用示例**:补充簿记模式 + 增量合并模式两个示例

### 保留(技术债)

- `gen_institution_stats.py` 的 `internal_merge_bookkeeping` 保留不动(用户决策)
  - 与 `run_increment_merge` 功能重叠(简化克隆)
  - 接口不兼容:返回 tmp_path vs 写 output_path;22 列原始 vs 25 列加工
  - 第三轮再设计封装层,需先解决 22 列→25 列升级 + 接口转换
  - 详见 `pitfall_log.md` #ABS-002

### 验证

- 5 层自检全部通过(详见 `Inbox/auditReport_GLM52_20260705_ABS工具箱_簿记录入.md`)
- 原 3 skill 文件未动(`skills/簿记录入/` 完整保留)

### 待办(第三轮)

- [ ] 迁入发行定价 3 个 `gen_*.py`(gen_abs_cost_report / gen_compare_tool / gen_spread_report)
- [ ] 激活"ABS 全流程"串行编排(录入 → 统计 → 定价)
- [ ] 设计 internal_merge 封装层(解决 22 列→25 列升级 + 接口转换)
- [ ] 原 3 skill 标 `deprecated`(不删除,保留 6 个月观察期)

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

### 待办(第二轮已完成,见 v2.1.0 段)

- [x] 迁入 `increment_merge.py`(簿记录入 v2.1) — v2.1.0 完成,原样迁入 0 改动
- [ ] 迁入发行定价 3 个 `gen_*.py` — 第三轮
- [ ] 激活"ABS 全流程"串行编排 — 第三轮
- [ ] 删除 `gen_institution_stats.py` 内部 `internal_merge_bookkeeping`,改调簿记录入 — 第三轮(需封装层)
- [ ] 原 3 skill 标 `deprecated`(不删除,保留 6 个月观察期) — 第三轮

### 已知遗留

- `gen_institution_stats.py` 仍保留 `internal_merge_bookkeeping`(簿记录入未迁入前的过渡方案)
- `deliverables/ledger/04_archive/` 19 份历史台账,体积膨胀,后续按月压缩
- `skills/发行定价/scripts/gen_abs_cost_report.py` + `gen_compare_tool.py` 有未提交改动(上次会话遗留),第二轮处理
