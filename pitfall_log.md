# ABS工具箱 踩坑日志

> 合并自原 3 skill 的踩坑日志(机构统计 v1.1.0 / 簿记录入 v2.1 / 发行定价 v1.5.0),按 skill 分节保留。
> 新 skill 的踩坑从 #ABS-001 开始编号(避免与原编号冲突)。

## 来源追溯

- 机构统计原日志:`skills/机构统计/pitfall_log.md`(保留不动)
- 簿记录入原日志:`skills/簿记录入/v2.1/复盘踩坑日志.md`(保留不动)
- 发行定价原日志:`skills/发行定价/pitfall_log.md`(保留不动)

---

## A. 机构统计 v1.1.0 踩坑(已迁入,共 ~10 条)

| # | 严重度 | 内容 | 状态 |
|---|---|---|---|
| 1 | ★★★★★ | 申万宏源系合并(申万宏源+申万宏源承销保荐+申万宏源证券) | ✅ 已修 |
| 2 | ★★★★ | 托管行分行归并(22 条 BANK_NORM_MAP) | ✅ 已修 |
| 3 | ★★★ | 字体全黑(CSS 未应用) | ✅ 已修 |
| 4 | ★★★★ | 联席承销商"/"拆分逻辑 | ✅ 已修 |
| 5 | ★★★★ | QC 项目数不一致(NaN 行未过滤) | ✅ 已修 |
| 6 | ★★★ | 22 列原始台账兼容(无 WXY 列时回退 TUV) | ✅ 已修 |
| 7 | ★★★★ | v1.1.0 新增内部簿记合并能力(与簿记录入 skill 解耦) | ✅ 已修(过渡方案,第二轮删) |
| 8 | ★★★ | 上游台账质量预警(WXY 覆盖率) | ✅ 已修 |

---

## B. 簿记录入 v2.1 踩坑(第二轮迁入时参考,#1-#43 摘要)

| # | 严重度 | 内容 | 状态 |
|---|---|---|---|
| #27 | P1 | 利率归一化 normalize_rate 边界 | ✅ v2.1 已修 |
| #41 | P1 | 项目名映射 map_detail_to_project | ✅ v2.1 已修 |
| #42 | P1 | QC 7.4 文档-代码不一致(文档 [0.001,0.05],代码 [0.005,0.05]) | 🟡 v2.1 残留(第三轮审计 P1) |
| #43 | P2 | 文档瑕疵 2 项 | 🟡 v2.1 残留 |
| - | - | HARD_MAP 杭州联合→杭州农商行资管等 | ✅ 已合并到 entity_alias.py |

完整日志见 `skills/簿记录入/v2.1/复盘踩坑日志.md`(40KB,#1-#43 含旧日志→新编号映射表)。

---

## C. 发行定价 v1.5.0 踩坑(第二轮迁入时参考,共 7 条)

| # | 严重度 | 内容 | 状态 |
|---|---|---|---|
| 1 | ★★★★★ | 合并单元格预处理缺失(导致 pandas 读 NaN) | ✅ v1.5.0 已修(abs_common.preprocess_xlsx_for_pandas) |
| 2 | ★★★★★ | "优先A"/"优先级"双写法 | ✅ v1.5.0 已修(PRIORITY_LAYERS 常量) |
| 3 | ★★★★ | QC 过滤条件不同步 | ✅ v1.4.0 已修 |
| 4 | ★★★ | 配色不足(13 种资产) | ✅ v1.5.0 已扩(ASSET_COLORS) |
| 5 | ★★★★ | QC 未定义变量 diff | ✅ v1.4.1 已修 |
| 6 | ★★★★ | gen_spread_report QC 遗漏 | ✅ v1.4.0 已修 |
| 7 | ★★★ | 三脚本重复代码 | ✅ v1.5.0 已修(abs_common 抽取) |

---

## D. ABS工具箱 v2.0.0 新增踩坑

(第一轮执行过程中新增的踩坑记录于此,从 #ABS-001 开始编号)

### #ABS-001 — internal_merge_bookkeeping 临时保留

- **日期**:2026-07-05
- **严重度**:★★★(技术债)
- **现象**:第一轮迁入机构统计时,`internal_merge_bookkeeping` 未删除(簿记录入 v2.1 第二轮才迁,第一轮机构统计仍需内部合并能力)
- **临时方案**:保留 `internal_merge_bookkeeping` 在 `gen_institution_stats.py` 内
- **状态**:v2.1.0 第二轮后仍保留(见 #ABS-002)
- **追踪**:CHANGELOG v2.0.0 待办第 4 项

### #ABS-002 — internal_merge 与 run_increment_merge 并存(v2.1.0 第二轮)

- **日期**:2026-07-05
- **严重度**:★★★(技术债)
- **现象**:第二轮迁入 `run_increment_merge` 后,`gen_institution_stats.py` 的 `internal_merge_bookkeeping` 仍保留(用户决策:保留不动)。两个函数功能重叠(internal_merge 是 increment_merge 的简化克隆)
- **接口不兼容点**:
  1. 返回值:`internal_merge` 返回 tmp_path;`run_increment_merge` 写 output_path
  2. 输入约束:`internal_merge` 处理 22→25 列升级;`run_increment_merge` 要求 processed 已是 25 列
  3. 模式:`internal_merge` 仅补充;`run_increment_merge` 支持增量合并 + 补充(--supplement)
  4. 写入方式:`internal_merge` openpyxl 原位写;`run_increment_merge` Plan C 插行
- **临时方案**:并存,机构统计用 `internal_merge`,簿记录入用 `run_increment_merge`
- **彻底修复**:**✅ v2.3.0 第四轮已闭环**。翻译官模式:internal_merge_bookkeeping 改为 thin wrapper,内部调 `run_increment_merge(supplement=True)`,前置 `upgrade_22_to_25()` 解决 22→25 列升级。88 行旧逻辑删除,自动继承 17 项 QC 7.1-7.19
- **追踪**:CHANGELOG v2.3.0 段

---

### #ABS-003 — 自定义脚本绕过 QC 体系导致 UV 列丢失

- **日期**:2026-07-12
- **严重度**:★★★★★（数据丢失）
- **现象**:用自定义 `_append_new_project.py` 追加新项目"东裕4号仲裕（续发）"到 0703 定稿，列映射错误导致已有行的 U/V 列（认购机构/认购份额）原始数据被覆盖。用户发现后回滚。
- **根因**:
  1. 绕过 `increment_merge.py` 的 QC 体系，自定义脚本没有 UV 值保护
  2. QC 7.14 只检查 V 列**格式**（number_format），不检查 V 列**值**是否被覆盖
  3. QC FAIL 后不阻断执行（`run_enhanced_qc` 返回 `qc_fails` 但 `run_increment_merge` 未检查就保存文件）
  4. supplement 模式被误用于"追加新项目"（设计用途是"对已有项目补充簿记明细"）
- **修复**:
  1. ✅ 新增 QC 7.20: UV column value preservation — 对比 processed 和 output 的 U/V 列值，非目标项目的 U/V 值变化为 FAIL
  2. ✅ QC FAIL 阻断 — `qc_fails > 0` 时不保存输出文件，直接 return
  3. ✅ pitfall_log 记录 #ABS-003
- **约束**:录入新台账时，必须走 `--new-raw` 模式（增量合并），不能自己写脚本追加。如果原始台账是 21 列（无 WXY），由 increment_merge 自动处理列升级。
- **追踪**:CHANGELOG v2.5.1 段

---

### #ABS-004 — r1 修复引入回归（QC 7.20 崩溃 + 误报）

- **日期**:2026-07-14
- **严重度**:★★★（回归 bug，阻断正常录入）
- **现象**:用 0706 台账走正规 `--new-raw` 模式录入东裕4号仲裕（续发）时，QC 7.20 崩溃 `ValueError: too many values to unpack (expected 3)`；修复崩溃后又误报 `东裕3-10/优先A/交银理财 V '0.25' -> '2.7'` FAIL，阻断 output 生成。
- **根因**（v2.5.1 r1 修复 REV-03 引入两个 bug）:
  1. **dict 遍历错误**:`get_all_projects()` 返回 dict `{name:{'start','end'}}`，但 r1 代码写成 `for proj_name, pstart, pend in orig_projects`（误以为是三元组列表）。遍历 dict 按字符拆解项目名 → unpack 错误。
  2. **匹配键不唯一**:`(项目名,分层,机构)` 作为 dict key 时，同机构多笔认购（合法，如东裕3-10/优先A 交银理财有 V=2.7 和 V=0.25 两行）会 key 冲突，dict 只留最后一个 V。out 遍历时每行都和"最后 V"对比，非最后一行必然不等 → 误报 FAIL。
- **修复**（v2.5.2 r2）:
  1. ✅ dict 遍历改用 `.items()`，`pstart, pend = info['start'], info['end']`
  2. ✅ 改用 `Counter` 多重集对比 `(项目名,分层,机构,V)`：同机构多笔认购在 multiset 里是不同元素各自计数，orig/out 一致即 PASS；真正的篡改/丢失才 FAIL
- **验证**:0706 台账增量合并 + 东裕4号续发簿记录入，QC 7.1/7.2/7.3/7.20 全 PASS，Fails=0
- **教训**:r1 修复必须用真实台账端到端跑通，不能只看代码逻辑。REV-03 改匹配键方案时未测试同机构多笔认购场景。
- **追踪**:CHANGELOG v2.5.2 段

---

### #ABS-005 — read_detail 层名解析吃掉 A1/A2 档位标识

- **日期**:2026-07-14
- **严重度**:★★★★（分层数据错位，金额虚高）
- **发现者**:用户（复核尚乘1-2 时发现 A2 档被误判缺失）
- **现象**:尚乘1-2 簿记明细含 A1/A2 两档 section（"优先级A1申购利率"/"优先级A2申购利率"），`read_detail` 读到全部 16 条数据，但层名都解析成"优先"。录入时台账"优先A1"层把 16 条全收（`"优先" in "优先A1"` True），A2 层空 → 误判缺失。A1 层金额虚高 6.675 亿（实际应 3.735），A2 层本该 2.940 亿却为 0。
- **根因**:`read_detail` L291 `re.sub(r'级.*$', '', layer)` 正则匹配"级"及**之后所有内容**，"优先**级A1**"被削成"优先"，A1/A2 档位标识丢失。
  - 该正则原意处理"优先A1**级**"（级在数字后），却误伤"优先**级**A1"（级在前）。
- **修复**(v2.5.3):改用 `layer.replace('级', '')`——只删"级"字本身，保留 A1/A2。
  | 表头 | 修复前 | 修复后 |
  |---|---|---|
  | 优先级A1申购利率 | 优先 ❌ | 优先A1 ✓ |
  | 优先级A2申购利率 | 优先 ❌ | 优先A2 ✓ |
  | 优先A1级申购利率 | 优先A1 ✓ | 优先A1 ✓ |
  | 优先级申购利率 | 优先 ✓ | 优先 ✓ |
- **影响范围**:扫描 05 目录 12 个明细，仅"尚乘1-2"受影响（表头"优先级A1/A2"格式）。其余 11 个为"优先A/优先B"格式，无 bug。
- **验证**:重录尚乘1-2 后 A1=8条/3.735亿、A2=8条/2.940亿，分档正确。
- **教训**:正则 `级.*$` 贪婪匹配"级"后所有内容，对"级在前"格式有破坏性。改用精确字符替换更安全。用户复核分层数据是发现此类 bug 的关键，QC 7.1 金额对账无法发现（总金额不变，仅分档错位）。
- **追踪**:CHANGELOG v2.5.3 段

---

## E. v2.0.0 第一轮已知风险

1. **22 列原始台账兼容性**:删 `preprocess_unmerge_fill` 改用 abs_common 后,22 列台账(无 WXY 列)兼容性需端到端验证(Step 6)
2. **跨 skill import**:第一轮不引入跨 skill 依赖,`internal_merge_bookkeeping` 保留即为此
3. **产出目录体积**:04_archive/ 19 份历史台账 6.3M,git mv 后历史保留,同事 clone 体积大(后续按月压缩)
4. **重名冲突**:根目录 `ABS技能包/` 与新 `skills/ABS工具箱/` 不同名,无冲突;子目录中英文重命名分两次 commit(Step 4 Commit A/B)避免路径混淆
