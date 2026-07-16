---
review_id: B1-v28-p123-cleanup-r1
submission_id: A1-v28-p123-cleanup-r1
slug: v28-p123-cleanup
skill_version: v2.5.5
round: 1
auditor: agent_b
created_at: "2026-07-17 02:10:00"

git_tag: audit/v2.5.5-v28-p123-cleanup-r01
verified_tag_hash: 932adb0

verdict: APPROVED

issues:
  - id: REV-v2.5.5-v28-p123-cleanup-r1-01
    severity: INFO
    category: DOC_CONSISTENCY
    location: "scripts/gen_integrated_dashboard.py:349-355"
    description: "A1 §4/§5 称'投资人分析 3 个可选面板均降级为占位块'，但本轮 commit 932adb0 diff 仅显示 fig7(理财子)/fig8(授信总额度) 新增 try/except；fig6(非标额度) 的 try/except 降级在 v27 已存在，本轮未改动。表述'均降级'成立但降级来源跨两轮，非本轮一次性完成。"
    evidence: "git show 932adb0 diff 仅含 fig7(L340-345)/fig8(L359-365) 变更；直接读 gen_integrated_dashboard.py:349-355 确认 fig6 非标额度 try/except 已存在且与 fig7/fig8 结构完全一致。"
    suggested_fix: "无需修改代码；建议后续送审报告注明可选面板降级为跨轮次(v27 fig6 + v28 fig7/fig8)累计达成一致。"
    blocks_approval: false

verified_issues: []

conditions: []
---

<!--
正文 checklist(B 角色):
[x] §0 总体结论
[x] §1 上一轮 Issue 验证(首轮无)
[x] §2 需求合规审查(2.1/2.2/2.3)
[x] §3 代码质量审查(3.1/3.2/3.3)
[x] §4 下一轮指引
-->

# v28-p123-cleanup r1 审计意见

## 0. 总体结论

**Verdict**: APPROVED

4 个审计焦点独立读代码全部核实通过，无 CRITICAL/WARNING。P1 proj_sizes 死代码在目标脚本已彻底不存在；fig6/fig7/fig8 三个可选面板降级策略完全一致；shared_tmp 异常清理路径(RuntimeError/通用 Exception/正常)三分支覆盖完整且不吞错；re/pandas 局部 import 上提干净无残留、无副作用。1 项 INFO(降级达成跨两轮)不阻断。

## 1. 上一轮 Issue 验证

本 slug 首轮，无上一轮 Issue。

## 2. 需求合规审查

### 2.1 上一轮 Issue 全覆盖

首轮无遗留 Issue，不适用。

### 2.2 review_focus 回应

A1 §5 提出 4 个审计焦点，逐一独立核实：

| 焦点 | A 声称 | B 独立核实 | 结论 |
|---|---|---|---|
| ① P1 proj_sizes 死代码已不存在 | 确认已清理 | `grep proj_sizes scripts/` 命中 19 处，全部在 gen_pricing_insight/gen_compare_tool/lab/*，**gen_integrated_dashboard.py 零命中**；且这些命中是正常业务链(gen_compare_tool 算 proj_sizes_js → gen_pricing_insight 消费)，非死代码 | ✅ 目标脚本无残留 |
| ② fig7/fig6/fig8 可选面板降级一致性 | 3 面板均降级为占位块，占位仍计入 panel | 直接读 L340-365:fig6(L349-355)/fig7(L340-345)/fig8(L359-365) 三者结构完全一致(try→append真实body / except Exception→print WARN + append 占位 div)，占位块均 `panels.append`,不破坏 13 panel QC | ✅ 三面板降级一致 |
| ③ shared_tmp 异常清理 | except 删 tmp 后 raise 不吞错；正常路径读完删除 | 读 L309-373:RuntimeError 分支(L309-317)删 tmp+sys.exit(1);通用 Exception 分支(L318-324)删 tmp+raise(**保留原始异常不吞**);正常路径(L367-373)所有 read 完成后删 tmp 并置 None | ✅ 三分支覆盖完整 |
| ④ 局部 import 上提无副作用 | re/pandas 上提，无循环依赖/启动开销 | 读 L1-35:`import re`(L12)、`import pandas as pd`(L17) 已上提顶部;`grep import re\|pandas\|_pd` 全脚本仅此 2 处，函数内旧的 `import re`(原 build_integrated_html)与 `import pandas as _pd`(原 _assert_shared_tmp_structure)已删净;pandas 为独立第三方包,位于 sys.path.insert 前无顺序依赖 | ✅ 上提彻底无副作用 |

### 2.3 5 层自检证据复核

| 层 | A 声称 | B 复核 | verified |
|---|---|---|---|
| 1 变更边界 | ✅ 仅 2 文件 | `git show 932adb0 --stat` 确认 CHANGELOG.md + scripts/gen_integrated_dashboard.py 共 2 文件(+47/-9);tag audit/v2.5.5-v28-p123-cleanup-r01→932adb0e... 与 A1 commit_hash 一致,无遗漏文件 | ✅ |
| 2 端到端穿行 | ✅ QC 13 panel 通过 | 采信 A 输出;代码佐证:占位块均 append 进 panels，panel 计数结构不受降级影响 | ✅ |
| 3 产物结构检查 | ✅ 13 panel + Tab JS | 采信 A 输出;代码佐证同层 2 | ✅ |
| 4 py_compile | ✅ PY_COMPILE_OK | **本地实测** `python -m py_compile scripts/gen_integrated_dashboard.py` → PY_COMPILE_OK,import 上提后语法正确 | ✅ |
| 5 回归测试 | ✅ compare/cost/spread/institution/fig6/fig8 正常 | 采信 A 输出;代码佐证:panels 列表(L328-336)7 主 panel 调用未改动，P0 单次预处理 shared_tmp 路径未破坏 | ✅ |

采信说明:层 2/3/5 沿用 v20-v27 惯例(层 1/4 实测、层 2/3/5 采信 A 输出+代码佐证)。本轮改动纯属工程清理(降级容错/import 上提/异常清理/注释)，不改变任一 panel 的数据计算逻辑，代码佐证充分。

## 3. 代码质量审查

### 3.1 CRITICAL(功能等价性 / 数据完整性)

无 CRITICAL Issue。检查范围:①降级 try/except 是否吞掉真实数据错误——三面板均 `print WARN` 后 append 占位，仅在单面板 render 抛异常时降级，不影响其他 panel 与主流程;②shared_tmp 异常分支是否吞错——通用 Exception 分支 `raise` 保留原始异常;③import 上提是否改变运行时行为——re/pandas 顶层导入与原局部导入语义等价，py_compile 通过。均无功能等价性/数据完整性风险。

### 3.2 WARNING(文档一致性 / 接口兼容性)

无 WARNING Issue。检查范围:changed_files 声明(2 文件)与 `git show --stat`(2 文件)完全一致，无 v22/v23/v24 类 changed_files 遗漏问题;commit_hash(932adb0) 与 tag 指向一致，无 v22/v23 类 commit_hash 误填。文档一致性显著优于历史轮次。

### 3.3 INFO(改进建议)

- **REV-v2.5.5-v28-p123-cleanup-r1-01**(INFO/DOC_CONSISTENCY,不阻断):A1 称"3 个可选面板均降级"成立,但降级达成跨两轮——fig6 try/except 在 v27 已存在,本轮 commit 仅新增 fig7/fig8。表述准确,仅提示降级来源非本轮一次性完成。无需改代码。

## 4. 下一轮指引

verdict=APPROVED，通知 Agent C 归档。

- 无 CRITICAL/WARNING，无阻断项。
- 1 项 INFO(REV-01 降级跨两轮达成)供 C 归档留档，不影响归档。
- 建议 C 归档时确认 A1 review_focus §4 提及的"chat 模块 P1/P2 语义增强 slug"是否需另开新 slug(本轮 P3 按维护性清理处理，未涉及语义增强)。