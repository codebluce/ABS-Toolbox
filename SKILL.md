---
name: "ABS工具箱"
version: "2.5.0"
description: >
  ABS业务多功能工具箱。整合发行定价、机构统计、簿记录入三大业务模块,提供从台账录入到机构统计到发行定价分析的端到端工作流。
  第一轮(v2.0.0)激活:机构统计 + 产出归档。
  第二轮(v2.1.0)激活:簿记录入(原样迁入,0 改动,5 层自检通过)。
  第三轮(v2.2.0)激活:发行定价(3 个 gen 脚本,4 处路径改造,6 层自检通过)。
  第四轮(v2.3.0)激活:internal_merge 翻译官改造(消除代码重复,自动继承 17 项 QC)。
  第五轮(v2.4.0)激活:5 层自检脚本化(self_check.py,配置驱动+降级接口,原 skill 删除后自动切 2 层)。
  第六轮(v2.5.0)激活:匹配规则调优(normalize 去连字符+Pass4 核心名+hard_map)+ rebook 设为默认模式(幂等)。
  全流程编排:录入→统计→定价 三步串行已激活。
  触发词包括:ABS工具箱、ABS机构统计、ABS归档、台账归档、看板归档、
  机构统计看板、管理人统计、销售机构统计、托管行统计、机构排名、
  申万宏源合并、机构合并统计、ABS发行台账、ABS产出索引、ABS自检、5层自检。
---

# ABS工具箱 Skill

> **v2.0.0 第一轮(2026-07-05)**:激活机构统计 + 产出归档两条路径。
> **v2.1.0 第二轮(2026-07-05)**:迁入簿记录入 v2.1(原样,0 改动,5 层自检通过,已归档 APPROVED)。
> **v2.2.0 第三轮(2026-07-05)**:迁入发行定价 v1.5.0(3 个 gen 脚本,4 处路径改造,6 层自检通过)。
> **v2.3.0 第四轮(2026-07-05)**:internal_merge 翻译官改造(消除代码重复,自动继承 17 项 QC,6 层自检通过)。
> **v2.4.0 第五轮(2026-07-05)**:5 层自检脚本化(self_check.py,配置驱动+降级接口)。
> **v2.5.0 第六轮(2026-07-05)**:匹配规则调优(normalize 去连字符+Pass4 核心名+hard_map)+ rebook 设为默认模式(幂等,推荐)。
> **全流程编排**:录入→统计→定价 三步串行已激活。
> **回滚备份**:原 `skills/发行定价/` `skills/机构统计/` `skills/簿记录入/` 保留不动,新 skill 出问题随时回滚。

## 与原 3 skill 的关系

| 原 skill | 版本 | 状态 | 新 skill 路径 |
|---|---|---|---|
| 机构统计 | v1.1.0 | 已迁入(v2.0.0) | `scripts/gen_institution_stats.py` |
| 簿记录入 | v2.1 | 已迁入(v2.1.0) | `scripts/increment_merge.py` |
| 发行定价 | v1.5.0 | 已迁入(v2.2.0) | `scripts/gen_abs_cost_report.py` + `gen_compare_tool.py` + `gen_spread_report.py` |

**触发"ABS 全流程"时**:本 skill 串行调用 录入→统计→定价 三步。

## 触发词路由

| 触发词 | 路由 | 状态 |
|---|---|---|
| ABS 机构统计 / 机构统计看板 / 管理人统计 / 申万宏源合并 | `scripts/gen_institution_stats.py` | ✅ v2.0.0 |
| ABS 归档 / 台账归档 / 看板归档 | `scripts/abs_archive.py` | ✅ v2.0.0 |
| ABS 产出索引 / 文件索引 | `scripts/abs_archive.py index` | ✅ v2.0.0 |
| ABS 簿记录入 / 补充簿记数据 / 增量台账合并 | `scripts/increment_merge.py` | ✅ v2.1.0 |
| ABS 发行定价 / 成本分析 / 利差分析 | `scripts/gen_abs_cost_report.py` + `gen_compare_tool.py` + `gen_spread_report.py` | ✅ v2.2.0 |
| ABS 全流程 | 录入→统计→定价 串行 | ✅ v2.2.0 |

## 使用示例

### 1. 机构统计看板生成

```bash
PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_institution_stats.py \
  "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx"
```

产出: `skills/ABS工具箱/deliverables/dashboards/01_latest/YYYYMMDD_机构统计看板.html`

### 2. 产出归档

```bash
# 看板归档:旧最新版本 → 历史版本
PYTHONUTF8=1 python skills/ABS工具箱/scripts/abs_archive.py dashboards

# 台账归档:加工中 → 定稿,旧定稿 → 归档
PYTHONUTF8=1 python skills/ABS工具箱/scripts/abs_archive.py ledger

# 重建文件索引
PYTHONUTF8=1 python skills/ABS工具箱/scripts/abs_archive.py index
```

### 3. 簿记录入(补充簿记模式)

```bash
PYTHONUTF8=1 python skills/ABS工具箱/scripts/increment_merge.py \
  --processed "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx" \
  --supplement \
  --details skills/ABS工具箱/deliverables/ledger/05_bookkeeping_details/*.xlsx \
  --output "skills/ABS工具箱/deliverables/ledger/02_processing/2026年ABS发行台账-0626-补充簿记v1.xlsx"
```

产出:`deliverables/ledger/02_processing/2026年ABS发行台账-0626-补充簿记v1.xlsx`

### 4. 簿记录入(增量合并模式)

```bash
PYTHONUTF8=1 python skills/ABS工具箱/scripts/increment_merge.py \
  --processed "上周定稿.xlsx" \
  --new-raw "本周新原始台账.xlsx" \
  --details 簿记明细*.xlsx \
  --output "deliverables/ledger/02_processing/本周台账.xlsx"
```

### 5. 发行定价(三看板一次跑)

```bash
PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_abs_cost_report.py \
  "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx"

PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_compare_tool.py \
  "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx"

PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_spread_report.py \
  "skills/ABS工具箱/deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx"
```

产出 3 份 HTML 到 `deliverables/dashboards/01_latest/`:
- `YYYYMMDD_机构投标利率看板.html`(工具一:成本分布)
- `YYYYMMDD_发行定价分析工具.html`(工具二:机构比对)
- `YYYYMMDD_机构投标基准利差看板.html`(工具三:利差分析)

### 6. ABS 全流程(录入→统计→定价串行)

```bash
# Step 1: 簿记录入(补充簿记明细)
PYTHONUTF8=1 python skills/ABS工具箱/scripts/increment_merge.py \
  --processed "deliverables/ledger/03_final/2026年ABS发行台账-0626-定稿.xlsx" \
  --supplement --details deliverables/ledger/05_bookkeeping_details/*.xlsx \
  --output "deliverables/ledger/02_processing/2026年ABS发行台账-0626-补充簿记v1.xlsx"

# Step 2: 机构统计(用补充簿记后的台账)
PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_institution_stats.py \
  "deliverables/ledger/02_processing/2026年ABS发行台账-0626-补充簿记v1.xlsx"

# Step 3: 发行定价(3 看板,用补充簿记后的台账)
PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_abs_cost_report.py \
  "deliverables/ledger/02_processing/2026年ABS发行台账-0626-补充簿记v1.xlsx"
PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_compare_tool.py \
  "deliverables/ledger/02_processing/2026年ABS发行台账-0626-补充簿记v1.xlsx"
PYTHONUTF8=1 python skills/ABS工具箱/scripts/gen_spread_report.py \
  "deliverables/ledger/02_processing/2026年ABS发行台账-0626-补充簿记v1.xlsx"
```

## 目录结构

```
skills/ABS工具箱/
├── SKILL.md                       (本文件)
├── README.md                      (同事入门)
├── CHANGELOG.md                   (版本历史)
├── AUDIT_REPORT.md                (审计基线)
├── pitfall_log.md                 (踩坑日志)
├── audit/                         (审计子系统,A→B→C 循环)
│   ├── README.md                  (审计操作手册)
│   ├── INDEX.md                   (审计索引)
│   ├── state.json                 (状态机)
│   ├── submissions/               (送审报告 Agent A)
│   ├── reviews/                   (审计意见 Agent B)
│   └── closed/                    (归档报告 Agent C)
├── scripts/
│   ├── abs_common.py              (共享底座)
│   ├── entity_alias.py            (机构名映射)
│   ├── gen_institution_stats.py   (机构统计)
│   ├── increment_merge.py         (簿记录入 v2.1)
│   ├── gen_abs_cost_report.py     (发行定价 工具一:成本分布)
│   ├── gen_compare_tool.py        (发行定价 工具二:机构比对)
│   ├── gen_spread_report.py       (发行定价 工具三:利差分析)
│   ├── test_smoke.py              (冒烟测试)
│   └── abs_archive.py             (归档工具)
└── deliverables/                  (产出,英文化目录)
    ├── ledger/                    (台账)
    │   ├── 01_source/             (源文件)
    │   ├── 02_processing/         (加工中)
    │   ├── 03_final/              (定稿)
    │   ├── 04_archive/            (归档)
    │   └── 05_bookkeeping_details/ (簿记明细)
    └── dashboards/                (看板)
        ├── 01_latest/             (最新版本)
        ├── 02_history/            (历史版本)
        ├── 03_test/               (测试文件)
        └── 04_reference/          (参考资料)
```

## 环境

- Python 3.12+(推荐 `C:/Users/wupeizhi.nolan/AppData/Local/Programs/Python/Python312/python.exe`)
- 依赖:pandas + openpyxl(已预装)
- 无外部数据源依赖(纯本地 Excel 处理)
- Windows 调用前加 `PYTHONUTF8=1` 避免 GBK 编码问题

## 审计流程(A→B→C 循环)

ABS工具箱采用三角色审计循环,参考 macro-allocation-strategy 精简适配。详见 `audit/README.md`。

### 目录结构

```
audit/
├── README.md                # 审计操作手册(人类参考)
├── INDEX.md                 # 审计索引(手动维护)
├── state.json               # 状态机(手动维护)
├── submissions/             # 送审报告(Agent A 写)
│   ├── _template.md
│   └── A{N}-{slug}-r{R}.md
├── reviews/                 # 审计意见(Agent B 写)
│   ├── _template.md
│   └── B{N}-{slug}-r{R}.md
└── closed/                  # 归档报告(Agent C 写)
    ├── _template.md
    └── C{N}-{slug}-r{R}.md
```

### 流程

1. **Agent A**(实现):写代码 + commit + 打 git tag `audit/v{X.Y}-{slug}-r{NN}` + 写送审报告 → push abs-toolbox 仓库
2. **Agent B**(审计):独立 Agent,只读代码+送审报告,写审计意见(verdict: APPROVED / NEEDS_REVISION / REJECTED)
3. **Agent C**(归档):verdict=APPROVED 时归档,写归档报告

### 文件命名

| 类型 | 格式 | 示例 |
|---|---|---|
| 送审报告 | `A{N}-{slug}-r{R}.md` | `A1-v20-institution-stats-r1.md` |
| 审计意见 | `B{N}-{slug}-r{R}.md` | `B1-v20-institution-stats-r1.md` |
| 归档报告 | `C{N}-{slug}-r{R}.md` | `C1-v20-institution-stats-r1.md` |
| git tag | `audit/v{X.Y}-{slug}-r{NN}` | `audit/v2.0-v20-institution-stats-r01` |

### slug 命名

slug 带版本前缀:`v{XX}-{主题}`(如 `v20-institution-stats`、`v21-bookkeeping`、`v22-pricing`)。

### 已归档送审

| submission_id | slug | skill_version | round | status | commit | 日期 |
|---|---|---|---|---|---|---|
| A1-v20-institution-stats-r1 | v20-institution-stats | v2.0.0 | r1 | PENDING_REVIEW(已通过独立审计) | `524cdae` | 2026-07-05 |
| A1-v21-bookkeeping-r1 | v21-bookkeeping | v2.1.0 | r1 | PENDING_REVIEW | `27f08a8` | 2026-07-05 |

详见 `audit/INDEX.md`。

### ABS工具箱特色:5 层自检

送审报告必含 5 层自检证据(ABS工具箱整合的功能等价性验证):

| 层 | 检查 | 通过标准 |
|---|---|---|
| 1 | 文件字节对比 | diff 为空(原样迁入) |
| 2 | 端到端穿行 | 新旧 skill 同输入同输出 |
| 3 | 逐 cell diff | 产出 xlsx 逐 cell 一致 |
| 4 | 原 skill smoke | 原 skill 同输入 QC 一致 |
| 5 | 回归测试 | 其他 skill 不受影响 |

## 5 层自检脚本 (v2.4.0 新增)

`scripts/self_check.py` 是 ABS工具箱 的自动化回归验证工具, 每次 skill 改动后跑一遍验证无回归。

### 5 层内容

| 层 | 名称 | 检查内容 | 依赖原 skill |
|---|---|---|---|
| 1 | 字节对比 | 新 skill 脚本 vs 原 skill 脚本 md5 一致 | 是 |
| 2 | 端到端穿行 | 跑新 skill 核心入口, returncode=0 + 产出存在 | 否 |
| 3 | 逐 cell diff | 新旧 skill 产出 xlsx 逐 cell 一致 (仅 increment_merge 类) | 是 |
| 4 | 原 skill smoke | 跑原 skill 同输入, returncode=0 + 产出存在 | 是 |
| 5 | 回归测试 | 跑下游脚本 (机构统计 + 3 看板), returncode=0 | 否 |

**判定逻辑**: 层 2/4/5 仅判 `returncode=0`, QC FAIL 仅记录不阻断 (0626 数据本身存在已知 QC FAIL, 真正的回归闸门是层 3 逐 cell diff)。

### 降级模式

`--mode auto|full|degraded`:

- **auto** (默认): 自动检测原 skill 是否存在, 任一缺失切 degraded
- **full**: 强制 5 层, 缺原 skill 报错 (6 个月观察期内用)
- **degraded**: 强制 2 层 (层 2 + 层 5), 跳过 1/3/4 (原 skill 删除后用)

### 使用示例

```bash
# 全部 slug, auto 模式 (推荐)
python scripts/self_check.py

# 指定单 slug
python scripts/self_check.py --slug v21-bookkeeping

# 强制 full 模式 (原 skill 删除前)
python scripts/self_check.py --mode full

# 强制 degraded 模式 (原 skill 删除后)
python scripts/self_check.py --mode degraded

# 列出所有 slug 配置
python scripts/self_check.py --list
```

### 输出

- JSON: `audit/self_check/{slug}_r{R}_{timestamp}.json`
- Markdown: `audit/self_check/{slug}_r{R}_{timestamp}.md`

### cell 计数口径

为避免 v21 那种 A/B 分歧 (单 sheet vs 全 sheet), 本脚本默认走**全 sheet**对比 (所有 sheet × 6 列 P/U/V/W/X/Y × max_row 行), 在层 3 details.cell_count_caliber 字段写明实际口径。

## 版本管理规范(多 Agent 协作)

本仓库常有多个 Agent(不同会话/不同任务)先后甚至并发修改。单分支直推 main + 双远程(Gitee+GitHub),已实际出现过"生成产出物撞名阻塞 pull""交接材料污染 git status"两类问题,故定下以下铁律,任何 Agent 操作本仓库前必须遵守:

### 1. 改动前必须先同步基线

```bash
git fetch origin && git fetch github
git log HEAD..origin/main --oneline   # 看 Gitee 是否领先
git log HEAD..github/main --oneline   # 看 GitHub 是否领先
```

任一方领先,先 `git pull origin main`(fast-forward)同步到最新,再开始改动。**禁止在落后的基线上生成产出物或整文件覆盖脚本**——本地旧版本 diff 出来的"补丁"可能已经不是真实增量。

### 2. 生成产出物(dashboards HTML / 台账 xlsx)不允许跨会话遗留为 untracked

`deliverables/dashboards/01_latest/*.html` 和 `deliverables/ledger/03_final/*.xlsx` 属于要提交入库的产出物(供同事直接在 Gitee/GitHub 上查看,不是 build cache)。文件名按日期命名(`ABS综合看板_YYYYMMDD.html`),同一天两个 Agent 各跑一次会撞名。规则:

- 生成后**当场**决定:要么立刻 `git add` + commit + 双推,要么用完即删,不允许放着不管、留到下个会话。
- 跑生成脚本前先按第 1 条同步基线,若远程已有同名产出,pull 下来后本地重新生成会**直接覆盖**(确定性输出,内容应一致或本地更新即为最新),而不是拿本地 untracked 副本去和 pull 撞车。
- 若 `git pull` 报 "untracked working tree files would be overwritten",说明第 1 条没做到位——先把本地文件移到临时目录(不要用 `git checkout --`/`rm` 直接丢弃,除非确认是本会话刚生成、可重新跑出来的产出物),pull 完再对比要不要保留。

### 3. 一次性交接材料不进主仓库

Agent 之间常通过"设计 zip 包 + 落地指令 prompt"移交任务(如 `ABS综合看板设计.zip`、`落地指令_*.md`、`集成说明.md`、`*_审计报告.md`)。这类文件是**给执行 Agent 看的一次性说明书**,不是给同事/未来 Agent 用的长期文档,落地完成后不提交:

| 类型 | 示例 | 是否提交 |
|---|---|---|
| 源代码 | `*.py` `*.js` `*.css` | ✅ 提交 |
| 长期参考文档 | `SKILL.md` `README.md` `CHANGELOG.md` `*_修改指南.md`(供后续 Agent 按配方改代码) | ✅ 提交 |
| 产出物 | `deliverables/**/*.html` `deliverables/**/*.xlsx` | ✅ 提交(见第 2 条) |
| 一次性交接材料 | `落地指令_*.md` `集成说明.md` `*_审计报告.md` `*.zip` | ❌ 不提交,落地后可删除或留在本地不 add |

commit 时用 `git add <具体文件>` 精确加(**禁止 `git add -A` / `git add .`**),避免把交接材料和临时产出一起带进去。

### 4. 覆盖式改动(整文件替换)前必须 diff 确认

当交接材料要求"用 merge/ 里的某文件整体覆盖本地同名文件"时(常见于 `gen_integrated_dashboard.py` 这类多方共改的核心文件):

```bash
diff <merge包里的新文件> <本地当前文件>
```

- diff 出来的每一处差异都必须能对应上"落地指令里描述的补丁点"。
- 如果出现**认不出来源**的差异(既不是待落地的补丁,也不是自己刚才的改动),说明基线之间有别的 Agent 插入的改动未被感知——停下来,不要盲目覆盖,向用户汇报差异内容。
- 确认无误才整文件覆盖;否则退回手动打補丁,只改 diff 里明确的那几处。

### 5. 双远程铁律

- 本仓库固定双远程:`origin`(Gitee)+ `github`(GitHub),两边必须保持内容一致。
- 仓库内已配置 `git pushall` alias(`git push origin main && git push github main`),**任何 commit 后一律用它推送,不允许只推一边**——历史上 obsidian-vault 仓库就因为单推导致过分叉。
- 推送后逐仓库列出 `✅`/`❌` 状态确认,不要假设推送成功。

## 审计与回滚

- 送审报告归档在 `audit/submissions/`(不再散落 Inbox)
- skill 长期审计基线见 `AUDIT_REPORT.md`
- 回滚:`git rm -r skills/ABS工具箱/` + `git mv` 还原产出目录即可,原 3 skill 完整保留
