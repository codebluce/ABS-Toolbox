---
closed_id: C1-v20-institution-stats-r1
slug: v20-institution-stats
skill_version: v2.0.0
closed_at: "2026-07-05 15:30:00"
closed_by: agent_c

final_verdict: APPROVED
total_rounds: 1
final_submission: A1-v20-institution-stats-r1
supersedes_submissions:
  - A1-v20-institution-stats-r1

all_issues_resolved: true

audit_escape_risks:
  - risk_type: deferred_critical
    description: "B 流程缺失:本轮未走正式 Agent B 审计流程,采用用户委托的独立审计(等效 APPROVED)。独立审计已确认架构强健、功能无损,4 处瑕疵(docstring/normalize_bank 遮蔽/QC 版本号/数字口径)+ 1 项遗留(工行天津/工银天津)均已在修正轮处理并验证。但缺乏正式 B1 文件记录,审计证据链较 v21/v22 弱。后续若发现本轮引入的回归,需重新走 B 流程复审。"
    severity: MEDIUM
  - risk_type: deferred_critical
    description: "技术债 #ABS-001:internal_merge_bookkeeping 函数(gen_institution_stats.py:268)保留不动,作第二轮簿记录入迁入后的封装层处理基础。已在 v21 C1 §3 audit_escape_risks 升级为 #ABS-002(internal_merge 与 run_increment_merge 并存),留第三轮封装层处理。本轮 v2.0.0 整合范围仅机构统计模块,不触碰簿记录入,等价性已验证。"
    severity: MEDIUM
  - risk_type: deferred_critical
    description: "数据问题逃逸:0626 定稿台账出现 `工银天津`/`华夏北分` 未归并,原 BANK_NORM_MAP 缺失。修正轮已补 2 条到 entity_alias.py + 回写原 skill(gen_institution_stats.py BANK_NORM_MAP),原 skill QC 从 FAILED 修复为 PASSED 30+35 项。数据脏源头仍存在(同实体两写法并存反映源数据脏),后续需在台账源头统一。"
    severity: LOW
  - risk_type: verification_chain_broken
    description: "无验证链断裂。本轮无正式 B Issue,4 处瑕疵 + 1 项遗留均在修正轮内由 A 自行处理并验证,验证证据完整(语法检查 + entity_alias 自检 + 新旧 skill QC 对比 + 副作用清理)。验证链完整。"
    severity: LOW

conditions: []
---

# v20-institution-stats 归档报告

## 1. 最终结论

**最终判决**: APPROVED(等效,基于用户委托的独立审计)
**总轮次**: 1(第一轮 + 修正轮合并报告)
**核心收益**: ABS工具箱 v2.0.0 第一轮整合——机构统计 v1.1.0 迁入 + abs_common.py 共享底座(364行字节一致)+ entity_alias.py 合并三套机构名映射(ENTITY_MERGE+BANK_NORM+HARD_MAP)+ gen_institution_stats.py 5 处改造(1093→1083行)+ abs_archive.py 4 子命令归档工具 + 64 文件 git mv 产出目录英文化;QC 从原 skill FAILED 修复为 PASSED 35 项
**是否附条件**: 否(独立审计等效 APPROVED,4 瑕疵+1 遗留均已修正)

## 2. Issue 生命周期全表

本轮未走正式 B 流程,无 B1 Issue 记录。独立审计提出的 4 处瑕疵 + 1 项遗留,均在修正轮内由 A 处理:

| 瑕疵/遗留 | 提出方 | 严重程度 | 处理轮次 | 最终状态 |
|---|---|---|---|---|
| 瑕疵 1: docstring 位置参数与 --output 不符 | 独立审计 | WARNING | r1 修正轮 | fixed(gen_institution_stats.py L17-19 docstring 改为 [--output]) |
| 瑕疵 2: normalize_bank 函数遮蔽 | 独立审计 | WARNING | r1 修正轮 | fixed(正则回退迁入 entity_alias,删本地重定义 10 行) |
| 瑕疵 3: QC 版本号未更 | 独立审计 | INFO | r1 修正轮 | fixed(L708 HTML 模板 + L739 QC Report 改为 ABS工具箱 v2.0.0) |
| 瑕疵 4: 数字口径小误(12/11, 18/19) | 独立审计 | INFO | r1 修正轮 | fixed(报告+AUDIT_REPORT+CHANGELOG+pitfall_log 全部修正) |
| 遗留: 工行天津/工银天津 并存回写原 skill | 独立审计 | WARNING | r1 修正轮 | fixed(BANK_NORM_MAP 补 2 条同步回原 skill,原 skill QC 从 FAILED 修复为 PASSED 30+35) |

### 瑕疵处理详情

- **瑕疵 1**(docstring): `gen_institution_stats.py` docstring 标称 `[output_path]` 位置参数,实际 argparse 用 `--output` 选项,Step6 用法示例误导。修正:L17-19 docstring 改为 `[--output <输出路径>]`,默认路径改 `deliverables/dashboards/01_latest/`。
- **瑕疵 2**(normalize_bank 遮蔽): 脚本本地重定义 `normalize_bank`(含正则回退)遮蔽 entity_alias 导入版本。修正:把正则回退逻辑迁入 `entity_alias.normalize_bank`,删除本地重定义 10 行,行数 1093→1083。验证:QC PASSED 35 项,申万系合并+托管行归并功能等价。
- **瑕疵 3**(QC 版本号): 输出仍打印"机构统计 Skill v1.0.0"。修正:L708 HTML 模板 + L739 QC Report print,统一改为 `ABS工具箱 v2.0.0 (机构统计)`。
- **瑕疵 4**(数字口径): 报告称簿记明细 12 份实为 11,归档 18/19 份口径混用。修正:Inbox 审计报告 + skill AUDIT_REPORT.md + CHANGELOG.md + pitfall_log.md 全部改为 11 份/19 份。
- **遗留**(工行天津/工银天津): 同实体两写法并存反映源数据脏,补充合理但未回写原 skill。修正:entity_alias.py 的 v2.0.0 补 2 条(`工银天津`/`华夏北分`)同步回 `skills/机构统计/gen_institution_stats.py` 的 BANK_NORM_MAP。验证:原 skill 跑 0626 台账 QC PASSED 30+35 项(此前 QC FAILED)。

## 3. 审计逃逸风险分析

- **B 流程缺失**:**本轮未走正式 Agent B 审计流程**,采用用户委托的独立审计(等效 APPROVED)。独立审计已确认架构强健、功能无损,4 处瑕疵 + 1 项遗留均已在修正轮处理并验证。但**缺乏正式 B1 文件记录**,审计证据链较 v21/v22 弱。后续若发现本轮引入的回归,需重新走 B 流程复审。严重程度 MEDIUM。
- **技术债 #ABS-001**:`internal_merge_bookkeeping` 函数(gen_institution_stats.py:268)保留不动,作第二轮簿记录入迁入后的封装层处理基础。已在 v21 C1 §3 升级为 #ABS-002(internal_merge 与 run_increment_merge 并存),留第三轮封装层处理。本轮 v2.0.0 整合范围仅机构统计模块,不触碰簿记录入,等价性已验证。严重程度 MEDIUM。
- **数据问题逃逸**:0626 定稿台账出现 `工银天津`/`华夏北分` 未归并,原 BANK_NORM_MAP 缺失。修正轮已补 2 条到 entity_alias.py + 回写原 skill,原 skill QC 从 FAILED 修复为 PASSED 30+35 项。**数据脏源头仍存在**(同实体两写法并存反映源数据脏),后续需在台账源头统一。严重程度 LOW。
- **验证链断裂**:**无断裂**。本轮无正式 B Issue,4 处瑕疵 + 1 项遗留均在修正轮内由 A 自行处理并验证,验证证据完整(语法检查 + entity_alias 自检 + 新旧 skill QC 对比 + 副作用清理)。验证链完整。严重程度 LOW。
- **superseded 标注**:不适用。仅 1 轮(含修正轮合并),无 rebase/重写场景。

## 4. 完整轮次时间线

| 轮次 | 送审报告 | 审计意见 | verdict | 日期 |
|---|---|---|---|---|
| r1(含修正轮) | A1-v20-institution-stats-r1 | 无正式 B1(用户委托独立审计,4 瑕疵+1 遗留已修正) | APPROVED(等效) | 2026-07-05 |

### 关键时间点

- 2026-07-05 09:13~09:30 — A 完成 Step 1~7(骨架创建 + abs_common 复制 + entity_alias 创建 + gen 改造 + 64 文件 git mv + abs_archive 4 子命令 + 端到端验证 + commit + 推送)
- 2026-07-05 09:30+ — 用户委托独立审计,提出 4 处瑕疵 + 1 项遗留
- 2026-07-05 修正轮 — A 处理全部瑕疵+遗留,验证 QC PASSED 35 项 + 原 skill QC 修复
- 2026-07-05 15:30 — C 归档

## 5. 经验教训

1. **B 流程缺失的逃逸风险**:本轮采用用户委托独立审计替代正式 B 流程,虽然独立审计质量高(发现 4 处瑕疵+1 遗留),但缺乏 B1 文件记录,审计证据链较弱。**教训**:后续 slug 应严格走 A→B→C 完整流程,独立审计只能作为补充而非替代,避免审计证据链断裂。
2. **abs_common.py 共享底座模式有效**:从发行定价 v1.5.0 复制 abs_common.py(364行字节一致),作为机构统计/发行定价/簿记录入三模块的共享底座,消除重复代码。**教训**:后续整合多 skill 时,优先抽取共享模块,降低维护成本。
3. **entity_alias.py 统一机构名映射**:合并三套机构名映射(ENTITY_MERGE_MAP + BANK_NORM_MAP + HARD_MAP)到独立文件,import 替代内联定义。**教训**:机构名映射应作为独立数据资产维护,避免散落在各脚本内联。
4. **normalize_bank 遮蔽问题**:脚本本地重定义遮蔽 import 版本,功能更强但违背"统一接口"初衷。**教训**:import 后不得本地重定义,如需增强功能应修改源模块而非遮蔽。
5. **数据脏源头治理**:工行天津/工银天津并存反映台账源头数据脏,补充合理但未根治。**教训**:发现数据脏应在源头治理(台账录入时统一),而非在下游 skill 补 map。
6. **64 文件 git mv 产出目录英文化**:整体迁入 + 子目录英文化(01_source/02_processing/03_final/04_archive/05_bookkeeping_details/01_latest/02_history/03_test/04_reference),为后续多 skill 整合奠定目录规范。**教训**:目录命名统一英文+数字前缀,避免中文目录在 git/脚本中的编码问题。
7. **abs_archive.py 保守策略**:初版 `ledger` 子命令自动归档旧定稿,测试时误把 0626-定稿归档。修正为保守策略,只做晋升,归档交独立 `final` 子命令人工触发。**教训**:归档类工具默认保守,destructive 操作必须人工显式触发。
8. **修正轮合并报告模式**:首轮 + 修正轮合并为单个 A1 报告,适用于瑕疵数量少且已在首轮内处理完毕的场景。**教训**:若修正轮改动较大或涉及多轮迭代,应拆分为 A1/A2 独立报告,避免单报告过长。

## 6. 代码最终状态

- **git_tag**: `audit/v2.0-v20-institution-stats-r01`
- **commit_hash**: `524cdae`
- **abs-toolbox 仓库**: gitee(`ppwupp/abs-toolbox`)+ github(`codebluce/ABS-Toolbox`)双推
- **原 skill 保留**: `skills/机构统计/gen_institution_stats.py`(完整保留,仅 BANK_NORM_MAP 补 2 条同步回写)
- **新建文件**:
  - `skills/ABS工具箱/SKILL.md`(触发词路由 + 使用示例)
  - `skills/ABS工具箱/README.md`(同事入门)
  - `skills/ABS工具箱/CHANGELOG.md`(v2.0.0 起点 + 历史指针)
  - `skills/ABS工具箱/pitfall_log.md`(合并三 skill 踩坑 + #ABS-001)
  - `skills/ABS工具箱/AUDIT_REPORT.md`(skill 长期审计基线)
  - `skills/ABS工具箱/scripts/abs_common.py`(364 行,复制自发行定价 v1.5.0,字节一致)
  - `skills/ABS工具箱/scripts/entity_alias.py`(~115 行,合并三套机构名映射 + normalize_bank 正则回退)
  - `skills/ABS工具箱/scripts/gen_institution_stats.py`(1083 行,改造自机构统计 v1.1.0,5 处改造 + 修正轮删 10 行)
  - `skills/ABS工具箱/scripts/abs_archive.py`(~210 行,4 子命令归档工具)
  - `skills/ABS工具箱/历史复盘踩坑日志.md`(从 ABS技能包根目录迁入)
- **迁入文件**(64 文件 git mv):
  - ledger:35 文件(3 源 + 1 加工 + 1 定稿 + 19 归档 + 11 簿记明细)
  - dashboards:23 文件(4 最新 + 12 历史 + 4 测试 + 2 参考 + 1 README)
  - 9 子目录英文化
- **删除文件**:
  - `ABS技能包/_文件索引目录.md`(旧版脱节,由 abs_archive.py 重建)
  - `ABS技能包/`(根目录空壳)
- **回写原 skill**(修正轮):
  - `skills/机构统计/gen_institution_stats.py` BANK_NORM_MAP 补 2 条(`工银天津`/`华夏北分`)

### 回滚方案

```bash
# 在 abs-toolbox 仓库:
git revert 524cdae
git push gitee main && git push github main

# 原 skill skills/机构统计/gen_institution_stats.py 完整保留(仅 BANK_NORM_MAP 补 2 条),可直接使用
# ABS技能包/ 已删除,如需恢复从 git history 恢复
```
