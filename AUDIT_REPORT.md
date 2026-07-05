---
title: ABS工具箱 审计基线
created: 2026-07-05
updated: 2026-07-05
version: 2.0.0
type: audit-report
tags: [reference, audit, abs]
---

# ABS工具箱 审计基线

> 本文件是 skill 长期审计基线,记录每个版本的整合结论。
> 单次执行的 step 级审计见 `Inbox/auditReport_GLM52_YYYYMMDD_ABS工具箱.md`。

## v2.0.0 第一轮(2026-07-05) — 已完成

### 整合范围

| 项 | 状态 | 说明 |
|---|---|---|
| skill 骨架 | ✅ | SKILL.md / CHANGELOG / pitfall_log / README / AUDIT_REPORT(本文件) |
| abs_common.py 共享底座 | ✅ | 从发行定价 v1.5.0 复制(364 行,字节一致) |
| entity_alias.py 机构名映射 | ✅ | 合并 ENTITY_MERGE_MAP(3) + BANK_NORM_MAP(26,含 v2.0.0 补 2) + HARD_MAP(2,文档参考) |
| gen_institution_stats.py | ✅ | 从机构统计 v1.1.0 复制 + 5 处改造(1093 行,原 1169) |
| abs_archive.py 归档工具 | ✅ | 4 子命令: ledger/final/dashboards/index |
| 产出目录迁入 | ✅ | ABS技能包/{台账,看板} → deliverables/{ledger,dashboards} |
| 9 子目录英文化 | ✅ | 01_source / 02_processing / 03_final / 04_archive / 05_bookkeeping_details / 01_latest / 02_history / 03_test / 04_reference |
| 索引重建 | ✅ | _文件索引目录.md 从 0515 同步至 2026-07-05 |
| 原 3 skill 保留 | ✅ | 发行定价/机构统计/簿记录入 文件未动(回滚备份) |

### 改造详情

#### gen_institution_stats.py 5 处改造

1. **顶部 import**:加 `sys.path.insert(0, ...)` + `from abs_common import ...` + `from entity_alias import ...`
2. **删除 ENTITY_MERGE_MAP / BANK_NORM_MAP 内联定义**(L137-158):迁入 entity_alias.py,顶部 import 加载
3. **preprocess_unmerge_fill 函数体替换**(原 65 行 → 5 行):改调 `abs_common.preprocess_xlsx_for_pandas`,保留函数名作兼容包装
4. **默认输出路径改 deliverables/dashboards/01_latest/**(原 ABS技能包/看板/ + Inbox fallback)
5. **保留 internal_merge_bookkeeping**:不删(簿记录入 v2.1 第二轮才迁,第一轮机构统计仍需内部合并能力),在 pitfall_log 标记第二轮删除

#### entity_alias.py 三套 map 合并

| Map | 条数 | 来源 |
|---|---|---|
| ENTITY_MERGE_MAP | 3 | 机构统计 v1.1.0 L131-135(申万宏源系) |
| BANK_NORM_MAP | 26 | 机构统计 v1.1.0 L138-150 原 24 条 + v2.0.0 补 2 条(工银天津/华夏北分) |
| HARD_MAP | 2 | 簿记录入 v2.1 SKILL.md L208-209 文档(代码未实际使用,截断匹配替代) |

**v2.0.0 补充**:0626 定稿台账出现 `工银天津` / `华夏北分` 未归并,原 BANK_NORM_MAP 缺失,导致 QC FAILED。
原 skill 同样失败(确认是数据问题非回归)。entity_alias.py 补 2 条映射后 QC PASSED。

#### abs_archive.py 4 子命令

| 子命令 | 行为 | 设计理由 |
|---|---|---|
| ledger | 02_processing → 03_final(仅晋升) | 保守策略,不自动归档旧定稿,避免误归当前在用定稿 |
| final | 03_final → 04_archive(人工触发) | 显式调用,不自动触发,归档动作交人工决策 |
| dashboards | 01_latest 旧日期 → 02_history/YYYYMMDD/(最新日期保留) | 滚动归档,01_latest 始终留最新 |
| index | 扫描 deliverables/ 重建 _文件索引目录.md | 修复脱节(原索引停在 0515) |

### 验证证据

| 项 | 命令 | 结果 |
|---|---|---|
| abs_common.py 复制一致 | `diff 发行定价/scripts/abs_common.py ABS工具箱/scripts/abs_common.py` | 无 diff,字节一致 |
| entity_alias.py 自检 | `python entity_alias.py` | ✅ 全部通过 |
| gen_institution_stats.py 语法 | `python -c "import ast; ast.parse(...)"` | ✅ 通过 |
| gen_institution_stats.py QC | 跑 0626 定稿台账 | ✅ 35 项全部通过,产出 12.8KB HTML |
| abs_archive.py dashboards 幂等 | 跑两次 | 第二次"仅含最新日期,无需归档" |
| abs_archive.py index 幂等 | 跑两次 | ledger 35 / dashboards 23 文件 |
| abs_archive.py ledger 保守策略 | 跑 02_processing 有 0612 文件 | 仅晋升 0612 → 03_final,不动 0626 定稿 |
| 原 3 skill 未动 | `git diff --stat skills/{发行定价,机构统计,簿记录入}/` | 仅上次会话遗留改动,本次会话零 touch |

### 已知遗留

1. **gen_institution_stats.py 仍保留 internal_merge_bookkeeping**(过渡方案,第二轮删)
2. **04_archive/ 19 份历史台账膨胀**(后续按月压缩)
3. **原 3 skill 有上次会话遗留未提交改动**(发行定价 3 脚本 + 机构统计 gen_institution_stats.py + pitfall_log.md),第二轮处理
4. **HARD_MAP 来自文档非代码**(簿记录入 v2.1 用截断匹配替代,第二轮激活时确认)
5. **BANK_NORM_MAP v2.0.0 补 2 条未同步回原 skill**(原 skill 仍会 QC FAILED,但本 skill 已修复)

### 待迁清单(第二轮)

- [ ] 簿记录入 v2.1 increment_merge.py 迁入
- [ ] 发行定价 3 个 gen_*.py 迁入(gen_abs_cost_report / gen_compare_tool / gen_spread_report)
- [ ] 删除 gen_institution_stats.py 内部 internal_merge_bookkeeping,改调 increment_merge
- [ ] 激活"ABS 全流程"串行编排(录入 → 统计 → 定价)
- [ ] 原 3 skill 标 deprecated(不删除,保留 6 个月观察期)
- [ ] HARD_MAP 是否激活(确认簿记录入 v2.1 截断匹配是否够用)
- [ ] 处理原 3 skill 上次会话遗留未提交改动

## 审计追溯

- 单次执行审计:`Inbox/auditReport_GLM52_20260705_ABS工具箱.md`(按 7 step 分节)
- 改动 commit:`git log --oneline skills/ABS工具箱/`
- 回滚:`git rm -r skills/ABS工具箱/` + `git mv` 还原产出目录(原 3 skill 完整保留)
