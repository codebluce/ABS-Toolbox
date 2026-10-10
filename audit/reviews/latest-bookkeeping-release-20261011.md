# 最新簿记上线独立审计与复验

最终审批：APPROVED。下列结论由独立 subagent Lagrange 给出。主 agent 仅归档原文，不替代独立审批。

## 初审（已由后续复验关闭发现）

# 独立上线前审计报告

结论：NEEDS_REVISION。

两项 P1 发布门禁缺口有独立实跑复现，尚未收到修补，不能批准主 agent commit / push / publish。完整全量候选的当前簿记及六笔源调整核对通过，不能用“当前数据正确”代替未来更新门禁正确。

## 审计对象与边界

- 项目根：`/Users/wupeizhi.nolan/Documents/LikeCodeNex/abs-toolbox`。
- 分支：main；HEAD：e3a1b146c1af3890671c6c4d3ea3c0c15161aae1。
- 审计覆盖未提交工作区：最新簿记四文件、QC/runtime/update/self-check/tests、综合/手机生成器、发布及独立双端打包、increment_merge、abs_archive 和 abs_mobile_app.js。
- 独立源码快照：`snapshot/scripts/`；42 文件 SHA-256 清单：`fingerprints.json`。首轮固定生产 HTML 已有不同面板版本混合，因此正式产物复核改用主 agent 完整生成的候选，不要求沿用旧产物结论。
- 本审计没有修改生产脚本、台账或发布产物，没有真实生产 commit / push / publish；所有反例、快照、测试输出放本审计唯一 /tmp 目录。发布回归仅在临时 Git/bare 仓库中运作。
- CodeGraph 导航技能用于查找跨文件消费者；结论以固定磁盘源和独立执行结果为准。没有调用神医扫描，没有沿用主 agent 的视觉验收。

## 阻断清单

### R1 / P1：局部更新只刷新簿记，发布门禁放行其他台账面板陈旧

定位：`scripts/update_latest_bookkeeping.py:68`（refresh）、`:76`（replace_panel）；`scripts/deploy_github_pages.py:214`（产物只校验最新簿记源指纹）。

反例基于正确的完整候选：在临时真实台账仅将 V2622 .06→.03，保持全部公式/缓存和其他 ZIP 条目，运行真实 refresh，然后真实 verify_dashboard_artifact。全部返回通过。簿记的招商证券投行 .03，投资台账的同一项目/档位/机构仍 .06。

证据：`candidate_mixed_reproduction.json`，`mixed_current_candidate.html`，`adversarial_checks.py`。

修复要求：源改变后重生成所有台账消费者，或将局部刷新产物显式标为非全量并硬拒绝发布；全量来源证明不能仅复制最新簿记 JSON 的哈希。必须通过一次真实源变更 + skip-generate 拒绝旧其他面板的回归。

### R2 / P1：非法 J/R 金额被当作缺失，上限消失

定位：`scripts/latest_bookkeeping_qc.py:207`（规模仅 float/None 对账）、`:226`（金额格式仅认购份额与申购规模）、`:273`（辅助档位数值过滤 None）、`:288`（仅 size 非 None 才查项目上限）。

反例一：规模“10亿元”、档位金额缺失、配售 100000 亿，真实 compute_data 返回 PASS、无任何 WARN、size=null。

反例二：规模 10、档位金额“0.3亿元”、配售 .4 亿，真实 compute_data 返回 PASS，仅 WARN 已披露配售不足项目规模，没有档位超配阻断。

证据：`adversarial_results.json`，`invalid_project_size/` 与 `invalid_layer_size/` 的实际合成 xlsx，`adversarial_checks.py`。

修复要求：J/R 非空非法文本、非有限数、布尔、负值必须 FAIL；真正缺失需 WARN；项目规模字段缺失要有明确处理。已明确的“辅助 R 公式无缓存仅 WARN”限制可保留，但合法 J 上限不得被非法数据静默关闭。纳入上述最小反例及有效缺失例。

## 非阻断发现与条件

### R3 / P2：已有手机版打包门禁不验证实际应用导航脚本

定位：`scripts/gen_mobile_dashboard.py:668`，`scripts/build_protected_dual.py:286`。

在正常真实候选手机版，将实际导航 `if (INJ.bookkeepingHtml) items.push(['bookkeeping',...)` 改成 `if (false) items.push(...)`，入口消失；真实 verify_mobile_bookkeeping 仍通过，它只看注入数据及 iframe 组件。现生成路径会读当前应用脚本，当前真实手机版入口正常，所以本项不作为当前完整候选的数据阻断，但独立已有双端打包路径建议补校验。

证据：`candidate_mobile.html`（正常生成）、`mobile_without_bookkeeping_navigation.html`（唯一导航变动）及真实校验执行记录。

建议：校验内联应用脚本字节或有效规则哈希，防止仅有隐藏簿记 JSON 的旧手机壳打包通过；加导航缺失/旧脚本回归。

### 外部发布前置条件（不算代码审计失败）

主 agent 已确认当前实际发布 protected=false，本地规范要求 protected，但密码环境变量尚无；“三端”实际目标需用户确认；Cloudflare未配置，占位地址不可解析。请主 agent 单独取得发布模式/目标授权和所需凭据；不得从代码审计通过推断允许明文扩张发布。此报告不重复外部配置搜索。

## 独立验证通过项

- 台账 ZIP 仅 `xl/worksheets/sheet1.xml` 改变；六个 V 值还原后整棵 XML 相同，其他 ZIP 条目字节完全相同。六处变动为用户授权：V2622 .08→.06、V2623 .2→.15、V2624 .12→.09、V2627 .2→.1、V2628 .1→.05、V2629 .1→.05。
- 独立直接从原始总表读取 1065 个所选源行；11 类资产、37 项目、752 笔申购、628 笔配售与 actual HTML 最新簿记 JSON 全量一致。
- 完整候选 SHA-256：f3c86d674fa0240848a1e3a6e8b65688d8183eb35d5c4594b357f52fff7992bf，14 panel。投资台账六笔同步 .06/.15/.09/.10/.05/.05；优先B .30、中间级 .20。`candidate_reconciliation.json`。
- 42 项簿记 Python、29 项发布回归全部独立重跑通过；真实 JS 最小组件契约通过。
- 真实 JS 全项目 1380 明细、72 CSV、420 筛选核对通过；`runtime.json`。
- 自写同名跨期、09:00/15:00 同自然日、最近3不同日期、归并白取、先剔非标边界核对通过。
- 自写关键公式无缓存、布尔成本、负配售、孤儿配售、错误利率单位均真实阻断；坏 HTML 的原子写保留旧文件且清理临时文件。
- 105 WARN 对应源表：72 NO_BIDS、31 LAYER_SIZE_UNCACHED、2 ALLOCATION_SIZE_DIFF。不回退/补造。无缓存辅助 R 属用户明确限制，项目 J 硬上限应持续有效。

## 审计新鲜度与可追溯性

独立 fetch 完成记录：2026-10-11T00:59:18.022838+08:00（Asia/Shanghai）。origin / github 的 git fetch --prune 均成功；main 与 origin/main、github/main 均 ahead0 / behind0；当前上游 origin/main。审计包含工作区未提交实现。

最终复核：2026-10-11T01:07:47.947092+08:00（Asia/Shanghai）；HEAD / 分支 / 上游未变，两端仍 ahead0 / behind0；42 个固定对象与生产同字节，无指纹变动。证据 `freshness.json` / `final_recheck.json`。

定稿 SHA-256：`10bbcc84664020862a3a847718813027b7e11521666dd57687fcc8ae7069d72f`。全部被审对象哈希在 `fingerprints.json`；正确全量候选另在 `candidate_reconciliation.json`，本报告不对后续修改保证。主 agent 修补 R1/R2 后请提供补丁及重生成候选，再独立复验。没有审计 APPROVED，就不能按本报告继续上线。


## 最终复验（原文）

# 独立上线前复验报告

结论：APPROVED（同一代码／业务／发布门禁审计范围）。

上轮 R1 / P1、R2 / P1、R3 / P2 均已独立实跑原反例，确认关闭。本结论只适用于下述最终源、45 个文件指纹和最终候选；不是外部发布模式或目标授权，也不替代主 agent 的最终视觉及线上验收。

## 1. 审计范围和对象

- 根：`/Users/wupeizhi.nolan/Documents/LikeCodeNex/abs-toolbox`；分支 main；HEAD `e3a1b146c1af3890671c6c4d3ea3c0c15161aae1`。
- 覆盖工作区未提交实现，包括簿记四文件、QC/runtime/update/self-check/tests、综合/手机生成、abs_mobile_app、发布/已有双端打包、increment_merge、abs_archive，以及修复新增 dashboard_provenance。
- 最终源定稿：`deliverables/ledger/03_final/2026年ABS发行台账-0924-定稿.xlsx`；SHA-256 `10bbcc84664020862a3a847718813027b7e11521666dd57687fcc8ae7069d72f`。
- 最终候选：`/tmp/abs-release-candidate-final-20261011.html`；独立副本 `final_run/release-candidate-final.html`；SHA-256 `43791d592387874796ce72e5070d143572f280a8b4ec869268895fc747c48f4d`；5 模块、14 panel。
- 实际生成并验收的手机版：`final_run/candidate_mobile.html`；SHA-256 `1eb6ae0f7b912aaf619ec272555263677d2ae70ee2df47589d8d10197cf6fd56`。
- 45 个被审代码／源文件逐文件 SHA-256：`fingerprints_final.json`；最终独立源码副本 `final_run/snapshot/scripts/`。
- 最终受控生产规则指纹：`482fce564b3c07bd503f377d79a792da4f43442caaaecebd480ec3203a84671e`。
- 只读操作，无生产代码、台账或正式产物改动；没有生产 commit、push 或 publish。反例和审计证据均在本独立 /tmp 目录。真实发布回归仅对临时 Git/bare 仓库执行。
- 使用代码导航技能确认跨文件门禁消费者，但判断基于固定源码及独立实际执行。

## 2. 原发现复验闭环

### R1 / P1：局部刷新导致其他台账消费者陈旧 —— CLOSED

关键修补：`scripts/dashboard_provenance.py:35` 只在完整生成入口调用添加全量来源证明；`:64` 独立核对定稿 source SHA、业务文件名、生产实现指纹。`scripts/gen_integrated_dashboard.py:442` 全量生成签发，`scripts/deploy_github_pages.py:214` 发布同时核对独立全量来源证明，不借用簿记证明充当全部面板证明。

原反例重新执行：从最终真实候选复制，将临时真实台账 V2622 .06→.03，保留所有公式缓存及其他 ZIP 条目，运行真实 refresh。簿记 .03、投资台账 .06，局部刷新不重签全量证明。随后真实 verify_dashboard_artifact 拒绝“其他台账面板来源陈旧”。

额外同范围验证：真实 build_site（skip-generate 用的包装入口）拒绝该混合产物，拒绝发生在清理站点包前，预置旧 index 字节保留；同源 partial refresh 仍可通过；改变临时生产实现、删证明、重复证明均拒绝。

证据：`final_run/reverify_findings.py`、`final_run/reverification_results.json`、`final_run/changed/mixed.html`、`final_run/stage_previous/index.html`。

### R2 / P1：非法 J/R 金额静默关闭上限 —— CLOSED

关键修补：`scripts/latest_bookkeeping_qc.py:207` 对项目规模、辅助档位金额非空值检查非负有限数值；`:21` 规模纳入必需字段；真实缺失有显式 WARN；辅助 R 无缓存保留约定 WARN。

原反例“规模10亿元、配售100000亿”返回 FAIL / PROJECT_AMOUNT_FORMAT；“档位0.3亿元、配售.4亿”返回 FAIL / LAYER_AMOUNT_FORMAT。

两字段的 NaN、Inf、-Infinity、True、False、负值及非法单位文本均真实阻断；None / '-' 真缺失返回 PASS_WITH_WARN。无缓存辅助 R 时，合法已知 J=10、配售11 的项目上限仍硬 FAIL；R 无缓存且项目未超配仍 WARN，不改变原约定。

证据：`final_run/reverification_results.json` 中 R2 的 22 条独立案例及对应实际合成 xlsx。

### R3 / P2：手机壳只有数据但导航不可用仍通过 —— CLOSED

关键修补：`scripts/gen_mobile_dashboard.py:674` 校验实际 `abs-mobile-app` 内联脚本字节等于当前生产脚本；已有双端打包同样复用此校验。

从最终完整候选现场生成正常手机版通过；将其唯一实际簿记导航判断改成 `if (false)`，真实 verify_mobile_bookkeeping 拒绝“实际导航应用脚本陈旧或被篡改”。

证据：`final_run/candidate_mobile.html`、`final_run/mobile_bad_nav.html`、`final_run/reverification_results.json` 中 R3。

### 来源名称 HTML 逃逸补丁 —— PASS

`dashboard_provenance.py` 转义改为字面 `\u` 序列，新增来源名称测试独立通过。补丁使生产指纹改变，旧 fixed 候选实际被门禁拒绝；final 候选在最终生产代码下真实通过。以 final 为唯一批准产物，不沿用旧 fixed 哈希。

## 3. 最终真实数据与回归

- 直接读取原始总表 1065 行，与最终候选簿记 JSON 全量一致：11 类资产、37 项目、752 申购、628 配售，共1380明细。
- 原始台账与调整前备份的 ZIP 比较：仅 sheet1.xml 改动；将六格值还原后 XML 完全相同，其他 ZIP 条目字节相同。六格仅用户授权比例调整：V2622 .08→.06，V2623 .2→.15，V2624 .12→.09，V2627 .2→.1，V2628 .1→.05，V2629 .1→.05。
- 最终完整候选的投资台账这六笔值 .06/.15/.09/.10/.05/.05 与簿记一致；优先B .30 亿，中间级 .20 亿。
- 46 项簿记 Python 回归（含新增转义测试）、29 项发布回归独立重跑全通过。
- 真实 JS 组件契约通过，全部37项目的1380条明细、72份CSV、420次筛选校验通过。
- 105 源 WARN 保留且一致：72 NO_BIDS、31 LAYER_SIZE_UNCACHED、2 ALLOCATION_SIZE_DIFF；没有补造、回退或降低源表约束。

证据：`final_run/independent_source_reconciliation.json`、`final_run/candidate_reconciliation.json`、`final_run/regression.log`、`final_run/publish_regression.log`、`final_run/runtime.json`。

## 4. 发布条件（外部前置事项，非代码审计FAIL）

- 主 agent 仍需用户明确“三端”真实目标和发布模式；不能默认把机构明细明文扩张到更多外部渠道。
- 若按本地规范 protected 发布，必须具备经用户授权的密码／环境配置；Cloudflare 未配置不能声称已同步成功。
- 可继续主代码合并／提交流程，仅提交经主 agent确认的任务范围文件，不把 .venv、无关历史实验和临时审计资料自动纳入。
- 只发布本报告批准的最终候选字节或重新完整生成且再次通过当前门禁的产物；源／生产规则改变必须重生成，不能拿 partial refresh 当全量同步。来源证明用于受控流程追溯，不是抗恶意修改的加密签名。
- 主 agent 按原任务完成双端视觉及实际发布结果验证；本独立复验不声称做过新的浏览器截图或外部访问验收。

## 5. 审计新鲜度

审计前独立 git fetch --prune origin / github 均成功，记录时间 `2026-10-11T01:12:10.061085+08:00`（Asia/Shanghai）；main 对 origin/main、github/main 均 ahead0 / behind0，上游 origin/main，审计包含未提交工作区。

最终复验时间 `2026-10-11T01:19:05.062891+08:00`（Asia/Shanghai）；根、main、HEAD及上游未变，两端仍 ahead0 / behind0；最终45文件均与生产同字节，候选与固定副本同字节；最终门禁还在生产脚本环境中实际运行通过。

证据：`freshness.json`、`revision.json`、`fingerprints_final.json`、`final_recheck.json`。本次修复后的 APPROVED 取代上轮 NEEDS_REVISION，仅对记录的固定最终对象作保证。
