# 项目数据更新发布规则

用户已授权：台账、簿记、同业发行、JoySpace 快照或看板数据更新完成后，在现有测试和产物校验通过的前提下，默认继续完成提交、GitHub/Gitee 双端同步和 GitHub Pages 发布，无需逐次询问。

- 发布前必须完成与改动相匹配的测试、看板产物校验和手机版验证；失败时停止并报告。
- 只提交本次数据更新及必要的代码、测试和说明，不提交虚拟环境、备份、临时分析目录或未确认的本地材料。
- 发布后核对桌面、手机版密文和公网文件与本地发布包一致。
- 涉及凭据时只使用现有本机配置，不把密码写入仓库或日志。

# 簿记明细补充口径（2026-11-07 用户确认）

统计“哪些项目还缺簿记明细”时，以下两类一律不计入待补清单：

1. **簿记时间早于 2026-06-01 的项目**：历史缺口不再回溯补录。
2. **非标项目**：发行场所为“平层非标”“结构化非标”“非标”的项目，不补录簿记明细。

只有 2026-06-01 及以后、且发行场所不是非标的项目，缺明细时才需要补录。
口径判断统一走 `scripts/list_missing_bookkeeping.py`，不要手工重新定义。

# 机构画像数据随台账同步（2026-11-14 用户确认）

每次更新发行台账时，默认一并刷新机构画像面板的四类数据，不再等用户单独提出：

1. **机构速查**：`data/joyspace_profile_sync/*.json` → `sync_institution_profile.py`
2. **次级速查**：JoySpace 月份 TSV → `scripts/lab/secondary_allocation_quick.py --import-dir`
3. **消金资产**：`data/asset_distribution_snapshot.json`
4. **风险表现**：`data/risk_performance_snapshot.json`

四类数据都来自 JoySpace 导出，仓库内没有抓取接口，只能导入导出文件。因此台账更新时按以下顺序处理：

- 先在本机查找比现有快照更新的导出文件（默认目录 `data/joyspace_profile_sync/`、次级分配的月份 TSV 目录），有则直接导入并重建快照。
- 没有新导出时，不得假装已更新：生成日志会打印“机构画像 JoySpace 数据落后台账超过 7 天”的清单，汇报时须明确写出哪几类数据停在哪天、需要导出哪张表。
- 台账、明细照常更新发布；机构画像数据缺失不阻断台账发布，但必须在交付说明里点名，不能静默略过。

## JoySpace 取数方式（2026-11-14 教训）

JoySpace 的 Sheets 表格**可以直接用 JoySpace 专用读取工具取数，不要用浏览器去点页面**。

- 已有链接直接读取；指定工作表在链接后加 `?sheetId=<sheetId>`，先用工作表清单接口拿到每个页签的 sheetId。
- 单次读取上限 25 行，整表读取用读取工具（返回 Markdown 表格）而不是逐格接口；逐格接口返回的 JSON 每个单元格十几行，几百格就会把上下文撑爆。
- 浏览器只用于 JoySpace 工具确实不支持的场景；画布式渲染读不到单元格，不代表 JoySpace 没有数据。
- 次级速查的月份 TSV 落在 `deliverables/dashboards/03_source/joyspace/<日期>/allocation/`，导入用 `scripts/lab/secondary_allocation_quick.py --update-month <N月> --month-tsv <文件>`。

## JoySpace 数据源登记表（2026-11-14 固化）

四个面板的页面、页签编号、取数方式和写回文件统一登记在 `data/joyspace_sources.json`，
代码里不再另存一份。换表、加页签、页签编号变化时先改登记表。

- 每次更新台账后先跑 `python scripts/joyspace_sources.py check`，按输出刷新落后的面板；
  `--strict` 时有落后返回非零。
- 看板生成时会自动调用同一套检查，落后超过 7 天在日志里点名。
- 详细步骤见 `docs/joyspace数据源与刷新流程.md`。
- 风险表现需要重建 HTML，`apply` 会拒绝自动写回，必须人工重建后再发布。
