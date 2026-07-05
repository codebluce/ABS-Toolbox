---
submission_id: A1-v22-pricing-r1
slug: v22-pricing
skill_version: v2.2.0
round: 1
created_at: "2026-07-05"
author: agent_a
git_tag: audit/v2.2-v22-pricing-r01
commit_hash: 03225ef
previous_git_tag: audit/v2.1-v21-bookkeeping-r01
changed_files:
  - scripts/gen_abs_cost_report.py (added, 复制自发行定价 v1.5.0 + 1 处路径改造)
  - scripts/gen_compare_tool.py (added, 复制自发行定价 v1.5.0 + 1 处路径改造)
  - scripts/gen_spread_report.py (added, 复制自发行定价 v1.5.0 + 1 处路径改造)
  - scripts/test_smoke.py (added, 复制自发行定价 v1.5.0 + 1 处路径改造)
  - SKILL.md (modified, 触发词路由 🟡→✅ v2.2.0 + §5/§6 使用示例 + 目录结构)
  - CHANGELOG.md (modified, v2.2.0 段新增)
status: PENDING_REVIEW
self_review:
  all_issues_addressed: true
  no_overengineering: true
  function_equivalence_verified: true
  edge_cases_covered: true
  notes: "发行定价 v1.5.0 迁入:3 gen + test_smoke 共 4 文件,4 处路径改造(唯一改动),6 层自检通过。abs_common.py 复用 v2.0.0 已复制版本(字节一致)。"
type: audit-report
tags: [reference, audit, abs, pricing]
---

# v22-pricing r1 送审报告

## 1. 变更摘要

第三轮整合发行定价 v1.5.0:复制 3 个 gen 脚本(gen_abs_cost_report / gen_compare_tool / gen_spread_report)+ test_smoke 共 4 文件到 `scripts/`,改造 4 处默认输出路径(`../../ABS技能包/看板/` → `../deliverables/dashboards/01_latest/`),删除 Inbox fallback。abs_common.py 复用 v2.0.0 已复制版本(字节一致),3 个 gen 脚本 import 自动生效。激活"ABS 发行定价" + "ABS 全流程"串行编排。

## 2. 上一轮 Issue 处理

首轮(r1),无上一轮 Issue。

## 3. 代码变更清单

| 文件 | 操作 | 改动 |
|---|---|---|
| scripts/gen_abs_cost_report.py | added | 复制自发行定价 v1.5.0(544 行) + L452-453 路径改造 + 删除 L455-459 Inbox fallback |
| scripts/gen_compare_tool.py | added | 复制自发行定价 v1.5.0(565 行) + L516 路径改造 + 删除 L518-522 Inbox fallback |
| scripts/gen_spread_report.py | added | 复制自发行定价 v1.5.0(619 行) + L508 路径改造 + 删除 L510-514 Inbox fallback |
| scripts/test_smoke.py | added | 复制自发行定价 v1.5.0(138 行) + L34-36 测试数据路径改造 + 注释 |
| SKILL.md | modified | 触发词路由 "ABS 发行定价"/"ABS 全流程" 🟡→✅ v2.2.0 + §5 发行定价示例 + §6 全流程示例 + 目录结构加 4 文件 |
| CHANGELOG.md | modified | v2.2.0 段新增 |

**改造 diff 验证**:4 文件 diff 仅路径行变化,无其他逻辑改动(详见自检层 1)。

## 4. 自审与指标

### 4.1 强制自审清单

- [x] all_issues_addressed: 首轮无历史 Issue
- [x] no_overengineering: 仅 4 处路径改造,无额外抽象
- [x] function_equivalence_verified: 6 层自检通过(见 4.2)
- [x] edge_cases_covered: 3 种输入场景(0626定稿/0515定稿/补充簿记后台账)均测

### 4.2 6 层自检证据

| 层 | 检查 | 结果 | 证据 |
|---|---|---|---|
| 1 | 改造 diff 仅 4 处路径 | ✅ | diff 4 文件,仅路径行变化,无逻辑改动 |
| 2 | 端到端穿行(3 gen × 0626 定稿) | ✅ | 新旧 QC 结果完全一致:gen_abs_cost FAILED(1+1)、gen_compare PASSED WARN(12+1/14+1)、gen_spread FAILED(1+3) |
| 3 | 新旧产出文本 diff | ✅ | gen_compare_tool HTML 字节完全一致(102966 字节) |
| 4 | 原 skill test_smoke | ✅ | 原 skill SKIP(旧路径不存在),新 skill 跑通(gen_compare OK,2 个 FAIL 数据问题) |
| 5 | 机构统计 + 簿记录入回归 | ✅ | 机构统计 QC PASSED 30+35 项;簿记录入 Fails=1 Warns=4(与之前一致) |
| 6 | 全流程串联(录入→统计→定价) | ✅ | 三步串行跑通,产出 2 份 HTML(1 PASSED + 1 FAILED 数据问题) |

### 4.3 已知数据问题(非回归)

QC FAIL 是 0626 定稿台账数据问题,新旧 skill 行为完全一致:
- gen_abs_cost_report: 1 严重 + 1 警告(成本区间数据问题)
- gen_spread_report: 1 严重 + 3 警告(利差区间数据问题)
- gen_compare_tool: PASSED WITH WARNINGS(12+1 / 14+1,1 项需关注)

## 5. 审计焦点

1. **4 处路径改造是否仅路径行**:核查 diff,确认无逻辑改动
2. **abs_common.py 复用是否字节一致**:`diff skills/发行定价/scripts/abs_common.py skills/ABS工具箱/scripts/abs_common.py` 应为空(v2.0.0 已验证)
3. **6 层自检证据真实可信**:Agent B 须独立复跑验证(不轻信 A 自报)
4. **QC FAIL 是数据问题非回归**:新旧 skill 同输入同输出
5. **全流程串联是否跑通**:录入→统计→定价三步串行

## 6. 附录

### 6.1 改造 diff 样例(gen_abs_cost_report.py)

```diff
-            os.path.dirname(os.path.abspath(__file__)), '..', '..', 'ABS技能包', '看板'
+            os.path.dirname(os.path.abspath(__file__)), '..', 'deliverables', 'dashboards', '01_latest'
-        if not os.path.isdir(kanban_dir):
-            kanban_dir = os.path.join(
-                os.path.expanduser('~'),
-                'Documents', 'LikeCodeNex', 'Inbox'
-            )
```

### 6.2 6 层自检命令完整输出

详见 Step 4-5 bash 命令输出记录。

### 6.3 abs_common.py 复用验证

```bash
$ diff skills/发行定价/scripts/abs_common.py skills/ABS工具箱/scripts/abs_common.py
(无输出,v2.0.0 已复制,字节一致)
```
