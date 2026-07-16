# ABS工具箱 CHANGELOG

> v2.0.0 起点为整合三 skill 的新版本号。原 3 skill 的历史版本号作为指针保留,便于追溯。

## 历史版本指针(整合前)

| 原 skill | 最后版本 | 整合时状态 | 历史日志位置 |
|---|---|---|---|
| 机构统计 | v1.1.0 | 已迁入本 skill v2.0.0 | `skills/机构统计/pitfall_log.md`(保留) |
| 簿记录入 | v2.1 | 第二轮迁入(规划中) | `skills/簿记录入/v2.1/复盘踩坑日志.md`(保留) |
| 发行定价 | v1.5.0 | 第二轮迁入(规划中) | `skills/发行定价/CHANGELOG.md`(保留) |

---

## v2.5.4 — 2026-07-16 P0 防错包（QC阻断 + WXY三元组 + 额度口径 + #ABS-006）

### 修复

- **核心 QC 真阻断**:
  - `increment_merge.py` 的 QC 7.1/7.2/7.3 失败计入 `qc_fails`
  - 避免目标金额不一致、非目标 WXY 被改、目标项目缺失时只打印 FAIL 但仍落盘

- **WXY/TUV 三元组 resolved 口径**:
  - `abs_common.resolve_columns()` 不再逐列 `fillna`
  - WXY 完整则整行用 WXY；WXY 全空或部分缺失则整行回退 TUV
  - WXY 部分缺失打印 WARN，避免制造“成本来自 W、机构/份额来自 U/V”的拼接假记录

- **fig6/fig8 新增认购改 resolved 口径 + 匹配审计**:
  - 非标额度/授信总额度新增认购改为 WXY 完整优先，否则 TUV 回退
  - 增加匹配审计：多匹配不计入以防重复占用；大额未匹配打印 WARN
  - 输出 WXY/TUV/PARTIAL_WXY 来源统计

- **#ABS-006 行偏移修复**:
  - fig4/fig5/fig6/fig8 的台账读取从 `raw.iloc[2:]` 改为 `raw.iloc[1:]`
  - 补回 Row1 首条真实认购记录（东道17-3 邮储银行 4 亿）

### 验证

- `py_compile` 通过：`abs_common.py` / `increment_merge.py` / `fig6_credit_panel.py` / `fig8_credit_total_panel.py` / fig4/fig5 数据加载
- fig6 独立计算通过：matched=2, multi=0, unmatched=0
- fig8 独立计算通过：matched=16, multi=0, unmatched=7，未匹配大额记录以 WARN 输出
- 综合看板生成通过：13 个 panel + Tab JS 齐全
- #ABS-006 验证：fig4 原始认购份额合计增加 4 亿（1125.455 → 1129.455）

### 注意

- fig8 新增认购口径从表面 U/V 调整为 WXY 穿透优先，部分机构新增认购/实时剩余额度会发生预期变化
- WXY 部分缺失当前在看板读取层整行回退 TUV 并 WARN；台账写入层仍应通过 QC 防止异常落盘

---

## v2.5.3 — 2026-07-14 read_detail 层名解析修复（#ABS-005）

### 修复

- **read_detail 层名解析吃掉 A1/A2 档位标识**（#ABS-005，★★★★）:
  - L291 `re.sub(r'级.*$', '', layer)` 贪婪匹配"级"后所有内容
  - "优先**级A1**申购利率"被削成"优先"，A1/A2 档位标识丢失
  - 导致 A1/A2 两档数据混进同一"优先"层，A1 金额虚高，A2 误判缺失
  - 修复:改用 `layer.replace('级', '')` 只删"级"字本身，保留 A1/A2

### 影响

- 扫描 05 目录 12 个明细，仅"尚乘1-2"受影响（表头"优先级A1/A2"格式）
- 其余 11 个为"优先A/优先B"格式，无 bug
- 重录尚乘1-2: A1=8条/3.735亿、A2=8条/2.940亿（修复前 A1=16条/6.675亿、A2=0）

### 教训

- QC 7.1 金额对账无法发现此类 bug（总金额不变，仅分档错位）
- 用户复核分层数据是发现关键
- 正则贪婪匹配对"级在前"格式有破坏性，精确字符替换更安全

### 追踪

- 用户发现 A2 档被误判缺失 → 排查 read_detail 层名解析 → 修复

---

## v2.5.2 — 2026-07-14 QC 7.20 r2 修复（r1 回归）

### 修复

- **QC 7.20 dict 遍历崩溃**（r1 回归 #ABS-004）:
  - r1 修复 REV-03 改用 (项目名,分层,机构) 匹配键时,误写 `for proj_name, pstart, pend in orig_projects`
  - 但 `get_all_projects()` 返回 dict `{name:{'start','end'}}`,不是三元组列表
  - 遍历 dict 按字符拆解项目名 → `ValueError: too many values to unpack (expected 3)`
  - 修复:改用 `.items()` 遍历,`pstart, pend = info['start'], info['end']`

- **QC 7.20 匹配键不唯一导致误报**（r1 回归 #ABS-004）:
  - (项目名,分层,机构) 作为 dict key 时,同机构多笔认购(合法)会 key 冲突
  - 实测:东裕3-10/优先A 交银理财有 V=2.7 和 V=0.25 两行,dict 只留最后一个(0.25)
  - out 遍历时每行都和"最后 V"对比,Row 的 V=2.7 ≠ 0.25 → 误报 FAIL,阻断正常录入
  - 修复:改用 `Counter` 多重集对比 (项目名,分层,机构,V)
  - 同机构多笔认购在 multiset 里是不同元素各自计数,orig/out 一致即 PASS
  - 真正的篡改/丢失(如 #ABS-003 场景)才 FAIL

### 验证（0706 台账增量合并 + 东裕4号仲裕续发簿记录入）

| QC | 结果 |
|---|---|
| 7.1 目标金额 | WXY_Y=21.9 = detail 21.9, diff=0.000 PASS |
| 7.2 非目标 WXY 保留 | 114 项目全保留 PASS |
| 7.3 目标项目存在 | 东裕4号续发 rows 1900-1920 OK |
| 7.20 非目标 UV 保留 | PASS（不再误报）|
| Summary | Fails=0, Warns=3（已知数据问题）|

### 踩坑

- **#ABS-004: r1 修复引入回归**（★★★）
  - v2.5.1 r1 修复 REV-03 未用真实台账端到端测试,rebook 行号对齐改匹配键方案有两个 bug
  - 教训:r1 修复必须用真实台账跑通,不能只看代码逻辑

### 追踪

- slug: v26-uv-protection,本轮为 r2 修复（待 Agent B 复审）

---

## v2.5.1 — 2026-07-13 UV 列值保护修复

### 新增

- **QC 7.20: UV column value preservation**（#ABS-003 修复）:
  - 对比 processed 和 output 的 U/V 列（认购机构/认购份额）值
  - 非目标项目的 U/V 值变化为 **FAIL**（不只是 WARN）
  - 目标项目（supplement/rebook 的目标）的 U/V 允许变化

### 修复

- **QC FAIL 阻断执行**（#ABS-003 修复 + REV-01 r1 修复）:
  - `run_enhanced_qc` 返回 `(qc_fails, qc_warns)` 后，`run_increment_merge` 检查 `qc_fails > 0`
  - FAIL 时删除临时文件，不生成 output，直接 return，打印 `[BLOCKED]` 提示
  - r1 修复: save 从 QC 前移到临时文件，QC PASS 后 rename 到 output_path，FAIL 时删除临时文件
  - 之前：QC FAIL 后仍保存文件（save 在 QC 前，return 只跳过打印）

- **QC 7.20 行号对齐**（REV-03 r1 修复）:
  - rebook 模式删除行后 ws_orig_protected 和 ws_out 行号不对齐
  - 改用 (项目名, 分层, 机构) 做匹配键，不再用行号直接对比

### 踩坑

- **#ABS-003: 自定义脚本绕过 QC 体系导致 UV 列丢失**（★★★★★）
  - 2026-07-12 用自定义 `_append_new_project.py` 追加新项目，列映射错误导致已有行 UV 数据被覆盖
  - 根因：绕过 increment_merge.py 的 QC 体系 + QC 7.14 只检查格式不检查值 + QC FAIL 不阻断
  - 已回滚至 0703 定稿，新增 QC 7.20 + FAIL 阻断

---

## v2.5.0 — 2026-07-05 第六轮

### 新增

- **匹配规则调优 + rebook 默认模式**(基于 0703 台账实测发现的问题):
  - `normalize()` 增加去除连字符 `-` / 斜杠 `/` / 全角斜杠 `／`,解决"中信建投-衍生品"vs"中信建投衍生品"类问题
  - 修复 `　` 字面字符串 bug(原代码未生效,全角空格没真正去除)
  - 新增 `core_name()` 函数:去后缀(私募基金/基金/资管/理财/自营/投行/投顾/证券/衍生品/信托/保险),用于 Pass 4 兜底匹配
  - 新增 `MATCH_HARD_MAP` 显式映射表:解决已知难匹配机构(如"利曦基金"↔"利曦私募基金")
  - 匹配 Pass 1→4 优先级链:Pass1 精确 → Pass2 包含(len>=4) → Pass3 hard_map 显式 → Pass4 核心名(len>=3)
  - `--rebook` 设为默认模式:不传 `--supplement/--rebook/--new-raw` 时默认 rebook(幂等,推荐)
  - `--supplement` 文档加警告:"多次跑会累积脏行,推荐用 --rebook"

### 修复

- 0703 台账实测发现 supplement 模式 bug:跨分层重复追加同一明细 + 不写 U/V → 产生脏行(U=None + WXY 有数据)
- rebook 模式 Step 5.0 已有清理机制(`U=None + WXY 有数据` 物理删除),v2.5.0 设为默认避免用户误用 supplement

### 6 层自检

| 层 | 检查 | 结果 |
|---|---|---|
| 1 | 改造范围核查 | ✅ 仅改 `increment_merge.py`(+60/-5 行,4 处改动) |
| 2 | 0703 台账端到端 | ✅ QC Fails=0,利曦私募基金/中信建投-衍生品 全部匹配成功 |
| 3 | 25 列台账回归 | ✅ 机构统计 QC PASSED 30 项 |
| 4 | 发行定价回归 | ✅ gen_abs_cost / gen_compare QC 一致(WARN 是已知数据问题) |
| 5 | 22 列台账全流程 | ✅ 翻译官模式 + 机构统计 QC PASSED 35 项 |
| 6 | 默认 rebook 行为 | ✅ 不传 mode 时默认 rebook + 打印 INFO |

### 已知遗留

- 无

---

## v2.4.0 — 2026-07-05 第五轮

### 新增

- **5 层自检脚本化**(CHANGELOG 待办"5 层自检脚本化 (用 6 个月)"兑现):
  - `scripts/self_check.py` (642 行): 配置驱动 + 降级接口的 5 层自检工具
  - 5 层 = 字节对比 / 端到端穿行 / 逐 cell diff / 原 skill smoke / 回归测试
  - `--mode auto|full|degraded` 自动检测原 skill 是否存在, 删除后切 degraded (只跑层 2+5)
  - JSON + MD 双输出到 `audit/self_check/{slug}_r{R}_{timestamp}.{json,md}`
  - cell 计数口径声明 (避免 v21 那种 A/B 分歧)

### 验证 (4 slug 全部 PASS)

| slug | 层 1 | 层 2 | 层 3 | 层 4 | 层 5 | 总评 |
|---|---|---|---|---|---|---|
| v20-institution-stats | INFO | PASS | SKIP | PASS | PASS | PASS |
| v21-bookkeeping | PASS | PASS | PASS (13753 cell 0 差异) | PASS | PASS | PASS |
| v22-pricing | INFO | PASS | SKIP | PASS | PASS | PASS |
| v23-internal-merge-unify | INFO | PASS | PASS (13753 cell 0 差异) | PASS | PASS | PASS |

降级模式 (v21 --mode degraded): 层 1/3/4 SKIP, 层 2/5 PASS。

### 关键设计决策

- **QC FAIL 不阻断**: 层 2/4/5 仅判 `returncode=0`, QC FAIL 仅记录 (0626 数据本身存在已知 QC FAIL, 真正的回归闸门是层 3 逐 cell diff)
- **降级接口**: 原 skill 删除后, auto 模式自动切 degraded, 保留层 2+5 (不依赖原 skill)
- **配置驱动**: SLUG_CONFIG dict 抽 4 个 slug 差异 (是否需 details, downstream, 原 skill 路径)
- **cell 计数口径**: 默认走全 sheet × 6 列 (P/U/V/W/X/Y) × max_row, 在 details.cell_count_caliber 字段写明

### 关闭的待办

- [x] 5 层自检脚本化 (用 6 个月) — v2.4.0 完成
- [x] 设计时预留"删除原 skill 后降级为 2 层"的接口 — v2.4.0 完成 (`--mode degraded`)

### 待办(后续)

- [ ] 04_archive/ 19 份历史台账按月压缩
- [ ] 2026-12-31 评估删除原 3 skill (6 个月观察期结束) → 实测 degraded 模式
- [ ] 后续 v25+ 写基线快照对比 (当前 v24 仅跑出基线, 不对比)

### 已知遗留

- 降级模式仅模拟测试 (--mode degraded), 未实际删除原 skill 验证; 留 2026-12-31 删除原 skill 后实测
- SLUG_CONFIG 硬编码 4 个 slug 配置, 后续新增 slug 需手动加 (未自动扫描 state.json)

---

## v2.3.0 — 2026-07-05 第四轮

### 新增

- **internal_merge 翻译官改造**(技术债 #ABS-002 闭环):
  - `scripts/gen_institution_stats.py` 新增 `upgrade_22_to_25()` 函数:22 列原始台账 → 25 列临时文件(补 WXY 空表头)
  - 改造 `internal_merge_bookkeeping()` 为翻译官模式:调 `run_increment_merge(supplement=True)`,不再自己实现簿记合并
  - 删除原 88 行内部合并逻辑(与 run_increment_merge 90% 重复,无 QC)
  - 自动继承 increment_merge 的 17 项 QC 7.1-7.19
- **代码量变化**:internal_merge_bookkeeping 88 行 → 55 行翻译官 + 40 行 upgrade_22_to_25 = 95 行(净增 7 行,但消除 90% 重复逻辑 + QC 覆盖)

### 改造详情

#### 翻译官 3 步流程

1. **22 列 → 25 列**:`upgrade_22_to_25()` 复制台账到临时文件,补 W/X/Y 三列表头(Row1 + Row2),数据行留空
2. **调 run_increment_merge(supplement=True)**:把明细金额填到 WXY,17 项 QC 全检
3. **返回 25 列临时文件路径**:保持原接口,load_data 透明使用

#### 接口兼容性

| 不兼容点(改造前) | 翻译官解决方式 |
|---|---|
| 22 列 vs 25 列输入 | upgrade_22_to_25 升级 |
| 返回 tmp_path vs 写 output_path | 翻译官包装,返回 output_path |
| 模式开关需显式指定 | 翻译官自动传 supplement=True |

### 验证(6 层自检)

| 层 | 检查 | 结果 |
|---|---|---|
| 1 | 改造范围核查 | ✅ 仅改 gen_institution_stats.py,increment_merge 未动 |
| 2 | 22 列台账端到端 | ✅ 22 列 + 明细 → 翻译官 → 机构统计 QC Fails=0 Warns=2 |
| 3 | 25 列台账回归 | ✅ 机构统计 QC PASSED 30+35 项;发行定价 3 看板与 v2.2.0 一致 |
| 4 | 簿记录入回归 | ✅ supplement 模式 Fails=1 Warns=4(与 v2.2.0 一致) |
| 5 | 全流程串联 | ✅ 22 列台账入口跑通(翻译官 → 机构统计 → 发行定价) |
| 6 | 代码重复消除 | ✅ 88 行旧逻辑删除,改调 run_increment_merge |

### 关闭的技术债

- **#ABS-002**(internal_merge 与 run_increment_merge 并存):✅ 闭环。翻译官模式消除代码重复,自动继承 17 项 QC

### 已知遗留

- `gen_institution_stats.py` 仍保留 `internal_merge_bookkeeping` 函数名(作翻译官包装,接口不变)
- `skills/发行定价/scripts/gen_*.py` 上次会话遗留未提交改动(原 skill 保留不动)

---

## v2.2.0 — 2026-07-05 第三轮

### 新增

- **发行定价 v1.5.0 迁入**:3 个 gen 脚本 + test_smoke,共 4 文件
  - `scripts/gen_abs_cost_report.py`(544 行,工具一:成本分布)
  - `scripts/gen_compare_tool.py`(565 行,工具二:机构比对)
  - `scripts/gen_spread_report.py`(619 行,工具三:利差分析)
  - `scripts/test_smoke.py`(138 行,冒烟测试)
- **abs_common.py 复用**:v2.0.0 已复制(字节一致),3 个 gen 脚本 import 自动生效
- **4 处路径改造**(唯一改动):
  - 3 个 gen 脚本默认输出路径 `../../ABS技能包/看板/` → `../deliverables/dashboards/01_latest/`
  - test_smoke 测试数据路径 `../../ABS技能包/台账/03-定稿/` → `../deliverables/ledger/03_final/`
  - 删除 Inbox fallback 逻辑(统一走 deliverables)
- **6 层自检通过**:
  1. 改造 diff 仅 4 处路径(无逻辑改动)
  2. 3 个 gen 跑 0626 定稿产 HTML,QC PASSED
  3. 新旧产出文本 diff(剔除日期/路径后一致)
  4. 原 skill test_smoke.py 跑通
  5. 机构统计 + 簿记录入 QC 不受影响(回归)
  6. 全流程串联:录入→统计→定价三步跑通
- **SKILL.md 触发词路由**:"ABS 发行定价" + "ABS 全流程" 从 🟡 第三轮 → ✅ v2.2.0
- **使用示例**:加 §5 发行定价 + §6 全流程串行

### 验证

- 6 层自检全部通过(详见 `audit/submissions/A1-v22-pricing-r1.md`)
- 原 3 skill 文件未动(`skills/发行定价/` 完整保留)

### 待办(后续)

- [x] 原 3 skill(发行定价/机构统计/簿记录入)标 `deprecated`(保留 6 个月观察期) — 2026-07-05 完成
- [x] 设计 internal_merge 封装层(技术债 #ABS-002) — v2.3.0 已闭环
- [x] 5 层自检脚本化(用 6 个月) — v2.4.0 完成 (`scripts/self_check.py`)
- [x] 设计时预留"删除原 skill 后降级为 2 层"的接口 — v2.4.0 完成 (`--mode degraded`)
- [ ] 04_archive/ 19 份历史台账按月压缩
- [ ] 2026-12-31 评估删除原 3 skill(6 个月观察期结束) → 实测 degraded 模式
- [ ] 后续 v25+ 写基线快照对比(当前 v24 仅跑出基线,不对比)

### 已知遗留

- `gen_institution_stats.py` 仍保留 `internal_merge_bookkeeping` 函数名(v2.3.0 改为翻译官 thin wrapper,不再有内部合并逻辑,函数名保留作接口兼容)
- `skills/发行定价/scripts/gen_*.py` 有上次会话遗留未提交改动(本次迁入复制当前磁盘版本,原 skill 保留不动)

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
