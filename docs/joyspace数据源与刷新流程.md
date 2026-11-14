# JoySpace 数据源与刷新流程

四个面板的数据来自 JoySpace，页面、页签、取数方式统一登记在 `data/joyspace_sources.json`。
改页签或换表时先改登记表，不要在代码里另写一份。

## 数据源一览

| 面板 | JoySpace 表 | 页签 | 取数方式 | 写入文件 |
|---|---|---|---|---|
| 机构速查 | 2026年ABS管理人与投资人进展表 | 吴沛智、李亦非、姜守园、邓殷洁、高雅 | 整本导出 Excel | data/机构画像数据.json |
| 次级速查 | 终版-26年次级分配 | 1月…11月 | 单页签读取 Markdown | data/secondary_allocation_snapshot.json |
| 消金资产 | 资产和风险表 | 资产余额 | 导出 Excel 后按区域还原 | data/asset_distribution_snapshot.json |
| 风险表现 | 资产和风险表 | 动态池数据、静态池逾期率&不良率 | 取 rangeData 后重建 HTML | data/risk_performance_snapshot.json |

页面地址：

- 机构进展表 `https://joyspace.jd.com/sheets/5QmWOOFQl19SdQUM1l3y`
- 次级分配 `https://joyspace.jd.com/sheets/89PMGlBmUHUueYQ6Cl7L`
- 资产和风险 `https://joyspace.jd.com/sheets/6DsPlXNgFeEBf7G2ghLx`

## 每次更新台账后的固定动作

1. 跑 `python scripts/joyspace_sources.py check`，它会对比四个快照与台账最新簿记日，列出落后的面板和对应页签链接。
2. 按提示取数（见下节），把结果写回快照。
3. 重新生成看板并发布。

`check` 只读、不联网，可以在任何时点跑；`--strict` 时有落后会返回非零，适合放进流水线。

## 三种取数方式

### 一、整本导出 Excel（机构速查、消金资产）

1. 打开表，点右上角“…”→“导出为”→“Excel”，文件落到下载目录。
2. 机构速查：
   `python scripts/import_institution_profile_xlsx.py --xlsx <文件> --out-dir data/joyspace_profile_sync/<YYYYMMDD>`
   再跑 `python scripts/sync_institution_profile.py --input-dir data/joyspace_profile_sync/<YYYYMMDD>`。
3. 消金资产：
   `python scripts/joyspace_sources.py apply --dataset asset_distribution --xlsx <文件> --date <YYYY-MM-DD>`

### 二、单页签读取（次级速查）

用 JoySpace 读取工具读 `页面地址?sheetId=<当月页签>`，得到 Markdown 表格，转成 TSV 后：

`python scripts/lab/secondary_allocation_quick.py --update-month <N月> --month-tsv <TSV> --snapshot-date <YYYY-MM-DD>`

只更新当月，1–10 月历史快照不动。

### 三、区域 rangeData（风险表现）

两个页签分别取 rangeData，重建 `pages.dynamic` / `pages.static` 的完整 HTML（含样式）。
这一步目前没有自动化，`apply` 会明确拒绝而不是写坏快照。

## 容易踩的坑

- **逐格接口不要整表拉**：一个页签几百个单元格，每个单元格十几行 JSON，很容易把会话撑爆。整表用读取工具拿 Markdown，或直接导出 Excel。
- **页签编号会变**：`sheetId` 是页签创建顺序，插入新页签后会变。登记表里存编号，`check` 输出的链接可直接点开验证；对不上就更新登记表。
- **日期必须保留 Excel 序列号**：消金资产表头用 `originalCellValue` 反算日期，只给文本会让表头全部失效。
- **浏览器只能作为兜底**：JoySpace 表格是画布渲染，页面结构里读不到单元格；导出菜单在页面右上角“…”里，可以用脚本点击，但优先用读取工具。
- **快照日期取导入时间**：机构速查的“数据截至”是导入时间，不是数据本身的截止日；导入后务必核对最新一周列是否有内容。
