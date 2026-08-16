---
submission_id: A1-v33-audit-cleanup-r1
slug: v33-audit-cleanup
skill_version: v2.5.10
round: 1
created_at: "2026-08-16 14:47:37"
author: agent_a

git_tag: audit/v2.5.10-v33-audit-cleanup-r01
commit_hash: 3281ae7
previous_git_tag: audit/v2.5.9-v32-audit-tooling-fix-r01

changed_files:
  - CHANGELOG.md
  - scripts/audit_validate.py
  - scripts/test_publish_chain.py

status: PENDING_REVIEW

addressed_issues:
  - id: REV-v2.5.9-v32-audit-tooling-fix-r01-01
    resolution: fixed
    evidence: "scripts/audit_validate.py L108-115: git() 内 subprocess.run 命令前统一加 '-c','core.quotepath=off'(L113),全部 git 调用含 V6 的 git('show',tag,'--stat') (L209)均经此出口;实测 A1-v30 单文件校验由修复前 遗漏1/多报1 → PASS(附录 6.2),全量 WARNING 12→10,余 10 条均为历史注记格式真问题(附录 6.4)"
  - id: REV-v2.5.9-v32-audit-tooling-fix-r01-02
    resolution: fixed
    evidence: "CHANGELOG.md L15-19 新增 v2.5.10 条目(3 条 bullet,与本轮三项改动一一对应)、L21-26 补记 v2.5.9 条目(4 条 bullet,与 0a507e8 实际四项修复一一对应),版本号追溯不再仅依赖 commit message 与 frontmatter"
  - id: REV-v2.5.9-v32-audit-tooling-fix-r01-03
    resolution: fixed
    evidence: "scripts/test_publish_chain.py L294: _run_no_change_publish 签名 (local_sha, remote_sha, merge_base),删除未消费的 has_local;L318-321 merge-base mock 改为直接 return merge_base,删除 sha 长度启发式;3 个测试(L337/343/349)断言未变,61/61 通过(附录 6.1)"

self_review:
  all_issues_addressed: true
  no_overengineering: true
  function_equivalence_verified: true
  edge_cases_covered: true
  notes: "3 个 Issue(REV-01 WARNING + REV-02/03 INFO)全部 fixed。四点如实披露: (1) v2.5.9 CHANGELOG 条目为本轮补记(0a507e8 当时未写),内容按该 commit 实际四项改动 retrospective 撰写,与 B1-v32 verified_issues 记录逐项相符,REV-02 suggested_fix 即授权此做法; (2) REV-03 清理后场景 2 的 merge_base='behind2'(=remote 端)与旧启发式实际返回值('ahead11'=local 端)方向相反——新值才是 git 真实语义(本地领先 ⇒ merge-base=remote),且 B1-v32 已论证两端点均在生产 L545 放行条件内,断言不变仍通过; (3) 删除 has_local 参数不改变 mock 行为:生产 has_local 仍由被 mock 的 show-ref returncode=0 恒为 True,场景 3 依旧是结果等价路径(local_sha_now='' 经 rev-parse 空串),该事实已由 docstring 'local_sha 传空串即模拟无本地分支' 显式化,不再是隐性瑕疵; (4) git() 加 -c core.quotepath=off 影响该函数全部调用(含 V5 tag 校验的 rev-parse),rev-parse 输出为纯 hex hash 与 quotepath 无关,已确认无副作用,且 -c 仅作用于单次 subprocess 不改用户 git 配置。"

review_focus:
  - "quotepath 修复有效性: audit_validate.py L108-115 的 -c core.quotepath=off 是否彻底消除中文路径假阳性——A1-v30 单文件应 0 遗漏 0 多报(其 changed_files 声明 scripts/投资台账_修改指南.md,修复前 stat 输出该文件为八进制转义串,见附录 6.3 前后对照);全量 --all WARNING 应 12→10,余 10 条(v21/v22/v23/v24/v25 各 2)是否确为历史括号注记格式真问题而非残留假阳性。"
  - "CHANGELOG 准确性: L15-19 v2.5.10 三条 bullet 与 3281ae7 实际改动、L21-26 v2.5.9 四条 bullet 与 0a507e8 实际改动(及 B1-v32 verified_issues 记录)是否逐项一致无夸大;'修复 B1-v32 REV-xx' 的指认是否准确。"
  - "夹具清理后测试仍有效: test_publish_chain.py L294-353 三个测试断言(pushes==[]/len==1/len==1)与生产 deploy_github_pages.py L572-576 三分支对应关系是否未变;merge_base 显式化后场景 1(same111)/2(behind2)/3('')的取值语义是否正确(尤其场景 2 base=remote 与旧启发式 base=local 翻转,见 self_review notes 第 2 点);删除 has_local 后 mock 路径(show-ref returncode=0 → 生产 has_local=True)是否与清理前完全一致。"

---

# v33-audit-cleanup r1 送审报告

## 1. 变更摘要(200 字内)

C1-v32 建议的收尾轮,修复 B1-v32 的 3 个 Issue: REV-01(WARNING) audit_validate.py 的 git() 加 `-c core.quotepath=off`,消除 V6 中文路径成对假阳性,实测 A1-v30 由 遗漏1/多报1 → PASS,全量 WARNING 12→10;REV-02(INFO) 补记 v2.5.9/v2.5.10 CHANGELOG 条目;REV-03(INFO) 测试夹具清理(显式 merge_base 参数,删未消费的 has_local)。测试 61/61,skip-historical 校验 0 CRITICAL 0 WARNING。commit 3281ae7,版本 v2.5.10。

## 2. 上一轮 Issue 处理

上一轮: B1-v32-audit-tooling-fix-r1(verdict APPROVED_WITH_CONDITIONS,3 Issue 均 blocks_approval=false,其中 REV-01 为 WARNING)。

| Issue ID | 严重程度 | 处理方式 | 证据 |
|---|---|---|---|
| REV-v2.5.9-v32-audit-tooling-fix-r01-01 | WARNING | fixed | `scripts/audit_validate.py:108-115`: `git()` 的 subprocess.run 命令列表前统一插入 `"-c", "core.quotepath=off"`(L113),带注释指明 Issue 编号。V6 的 `git("show", str(tag), "--stat", "--format=")`(L209)及 V5 的 rev-parse 均经此出口。**有效性实测(附录 6.2/6.3/6.4)**: (a) 同一 stat 命令前后对照——默认配置输出 `...277\256\346\224\271\346\214\207\345\215\227.md"`(八进制转义),加 -c 后输出明文 `scripts/投资台账_修改指南.md`,与 A1-v30 declared 条目精确匹配;(b) A1-v30 单文件校验 `[PASS]` 0 CRITICAL 0 WARNING(修复前 遗漏1/多报1,B1-v32 Issue 原文实录);(c) 全量 `--all` WARNING 12→10,消除的 2 条恰为 A1-v30 的成对假阳性,余 10 条(v21×2/v22×2/v23×2/v24×2/v25×2)全部为历史括号注记格式真问题,v23 的中文文件名在遗漏清单中已显示为明文可读。采用 B suggested_fix 的方案一(加 -c 参数)而非方案二(反转义) |
| REV-v2.5.9-v32-audit-tooling-fix-r01-02 | INFO | fixed | `CHANGELOG.md:15-19` 新增 v2.5.10 条目(审计工具收尾,3 bullet 对应本轮 REV-01/02/03);`CHANGELOG.md:21-26` 补记 v2.5.9 条目(4 bullet 对应 0a507e8 的 REV-01/02/03/04,含"链路测试 17→20,总测试 58→61"与 B1-v32 verified 记录一致)。条目位置在 `---` 分隔线后、v2.5.8 之前,倒序惯例保持。git diff 该文件 +13/-0,无其他行触碰 |
| REV-v2.5.9-v32-audit-tooling-fix-r01-03 | INFO | fixed | `scripts/test_publish_chain.py:294` 签名改为 `_run_no_change_publish(self, local_sha, remote_sha, merge_base)`,has_local 参数删除;L318-321 merge-base 分支改为 `return merge_base`,删除 `len(local_sha) <= len(remote_sha)` 长度启发式及两行注释;docstring(L296-299)显式说明"merge_base 显式传入,由调用方定义 fast-forward 语义""local_sha 传空串即模拟无本地分支",将原隐性约定文字化。3 个测试调用点同步改造: L339 `merge_base="same111"`(场景1)、L345 `merge_base="behind2"`(场景2,=remote,git 真实语义:本地领先 ⇒ base=remote)、L352 `merge_base=""`(场景3)。**断言三行未动**(L340-341/346-347/353-354 与 0a507e8 版本逐字一致),61/61 通过证明行为等价(附录 6.1) |

B 的 2 条 conditions 处置: 条件 1(REV-01 quotepath 并入下一 slug 修复)即本轮完成,修复后 A1-v30 回到 0 遗漏 0 多报,suggested_fix 验收口径达成;条件 2(REV-02/03 顺带完成)即本轮完成。v25 §10 第 6 条(浏览器性能预算)仍属阶段 C 遗留,本轮未触碰,与 C1-v32 归档口径一致。

## 3. 代码变更清单

`git show 3281ae7 --stat`: 3 files changed, 33 insertions(+), 11 deletions(-)。与 frontmatter changed_files 一致(逐条核对)。

| 文件 | 操作 | 说明 |
|---|---|---|
| `CHANGELOG.md` | modified (+13/-0) | REV-02: 新增 v2.5.10 条目(L15-19)+ 补记 v2.5.9 条目(L21-26) |
| `scripts/audit_validate.py` | modified (+7/-1) | REV-01: `git()` L108-115 统一加 `-c core.quotepath=off`(+2 行注释指明 Issue 编号),单点修复覆盖全部 git 调用 |
| `scripts/test_publish_chain.py` | modified (+24/-10) | REV-03: `_run_no_change_publish` 删 has_local 参数、merge-base mock 改显式 merge_base(L294/318-321),docstring 扩展;3 个测试调用点改关键字传参,断言未变;注释中 REV-04 编号改写为场景描述(该编号属 v32 轮,本轮语境下自然失效) |

## 4. 自审与指标

### 4.1 强制自审清单

- [x] all_issues_addressed: 上一轮 3 个 Issue(REV-01 WARNING + REV-02/03 INFO)全部 fixed,证据见 §2,无 wontfix/partial;2 条 conditions 全部落地。
- [x] no_overengineering: REV-01 为单点 2 行修改(命令列表插 2 元素)+2 行注释;REV-02 纯文档;REV-03 为参数替换无新增抽象;未引入新函数/新依赖(仍纯标准库)。
- [x] function_equivalence_verified: 校验器除 quotepath 行为按 Issue 预期改变外无回归——`--all --skip-historical` 8 文件全 PASS 0 CRITICAL 0 WARNING(较 v32 时 5 文件新增 A1-v32/B1-v32/C1-v32 三个 v32 轮产物,均 PASS);全量 `--all` CRITICAL 5(同一批历史既存问题,数量与 v32 一致)/ WARNING 12→10,净变化与 Issue 预期完全一致(附录 6.4)。发布链路功能未动(deploy_github_pages.py 零改动);测试夹具清理后断言逐字未变,61/61。
- [x] edge_cases_covered: 中文文件名(A1-v30 实测 0/0);quotepath 修复对纯 hex 输出的 V5 rev-parse 无影响(hash 与路径转义无关,已确认);历史带注记文件仍按整串匹配计数偏大(v21-v25 共 10 条,方向检出正确,该边界 v32 轮已披露且本轮无恶化);夹具 merge_base 三场景取值含两端点重合(场景1)/base=remote(场景2)/空串(场景3)组合,生产 L545 分叉守卫与 L572-576 引用比对分支覆盖关系不变。

### 4.2 5 层自检证据

| 层 | 检查 | 结果 | 证据 |
|---|---|---|---|
| 1 | 文件变更边界 | ✅ | `git show 3281ae7 --stat` 3 文件与 changed_files 逐条一致(附录 6.5);HEAD 即 3281ae7;工作区对 scripts/audit/CHANGELOG.md 干净(仅本报告待写) |
| 2 | 端到端穿行 | ✅ | run_tests.py 61/61 OK(7+30+20+4),冒烟输出含三种无变化分支真实打印(跳过推送×1/执行 git push×2),与 v32 轮输出一致(附录 6.1) |
| 3 | 门禁有效性 | ✅ | quotepath 修复实证: A1-v30 由 遗漏1/多报1 → PASS;全量 WARNING 12→10,消除量与 B1-v32 Issue 记录的假阳性数量(2 条)精确吻合;余 10 条与 v32 轮已知历史检出完全相同(v21-v25 注记格式,无新增无恶化)(附录 6.2/6.4) |
| 4 | 修复前后对照 | ✅ | 同一 git show 命令带/不带 `-c core.quotepath=off` 输出对照: 转义八进制串 vs 明文中文路径(附录 6.3);夹具: 旧启发式返回值 vs 新显式 merge_base,断言不变 61/61 |
| 5 | 回归 | ✅ | 61/61(链路 20 不变);`--all --skip-historical` 8 文件全 PASS 0/0;`--all` 全量 CRITICAL 5 不变(均为本轮前既存历史问题: tag 不存在×1/commit_hash 不符×3/frontmatter 不可解析×1) |

## 5. 审计焦点(给 B 的提示)

1. **quotepath 修复有效性**(REV-01,唯一 WARNING): `audit_validate.py:108-115`。重点: (a) 用附录 6.3 的前后对照复核——同一 tag 的 stat 输出,默认配置中文文件名为 `"...277\346\224\271....md"` 转义串,加 -c 后为明文,与 A1-v30 L18 declared 条目 `scripts/投资台账_修改指南.md` 精确匹配;(b) A1-v30 单文件校验 PASS(附录 6.2)是否足以证明成对假阳性消除(遗漏与多报同源于一个文件的两种表示);(c) 全量 WARNING 12→10 的差额是否恰为 A1-v30 的 2 条,余 10 条(v21×2/v22×2/v23×2/v24×2/v25×2)是否与 v32 轮 `--all` 输出的同文件检出逐条相同(仅 v23 中文串由转义显示变为明文显示,计数不变);(d) `-c` 作用于 git() 全部调用对 V5(rev-parse 纯 hex)与 V6 其他 ASCII 路径文件是否有任何可观察副作用。
2. **CHANGELOG 准确性**(REV-02): `CHANGELOG.md:15-26`。重点: v2.5.10 三条 bullet 与 3281ae7 commit message/实际 diff 三项改动一一对应;v2.5.9 四条 bullet 与 0a507e8 实际四项修复及 B1-v32 verified_issues 证据(含 61/61、17→20、12→0/3→0→15 条假警报合计)逐项核对,无夸大;"修复 B1-v32 REV-xx" 指认准确。
3. **夹具清理后测试仍有效**(REV-03): `test_publish_chain.py:294-353` 对照 `deploy_github_pages.py:572-576`。重点: (a) 3 个测试断言与生产三分支锁定关系是否与 0a507e8 版本完全一致(断言三行未动);(b) merge_base 取值语义——场景 1 `same111`(两端重合,base 即同值)、场景 2 `behind2`(本地领先 ⇒ git 真实语义 base=remote;注意与旧启发式实际返回 local 相比方向翻转,B1-v32 r01-03 已论证两端点均满足 L545 放行,见 self_review notes 第 2 点)、场景 3 `""`(无本地分支,rev-parse 返回空);(c) 删除 has_local 后 mock 链路: 生产 has_local 仍由 show-ref returncode=0 判 True,场景 3 local_sha_now='' 的产生路径(rev-parse refs/heads 返回入参空串)与清理前逐字相同,docstring 已将此约定文字化。

## 6. 附录

### 6.1 run_tests.py 全量输出(2026-08-16,仓库根目录)

命令: `PYTHONUTF8=1 .venv/bin/python run_tests.py`(exit 0)

```text
.............................................................
----------------------------------------------------------------------
Ran 61 tests in 0.018s

OK
[discover] test_consumer_asset_panel: 7 tests
[discover] test_peer_issuance_panel: 30 tests
[discover] test_publish_chain: 20 tests
[discover] test_sync_institution_profile: 4 tests
[site] protected 泄露自检通过: 无源 Excel/明文看板特征
[select] 文件名业务日期(20260807)与 mtime(2026年ABS发行台账-0801-定稿.xlsx)不一致,以文件名为准: 2026年ABS发行台账-0807-定稿.xlsx

[3/4] 同步到 gh-pages worktree...

[3/4] 同步到 gh-pages worktree...
[pages] gh-pages 无文件变化
[pages] 执行 git push,同步本地 gh-pages 到远端

[3/4] 同步到 gh-pages worktree...
[pages] gh-pages 无文件变化
[pages] 执行 git push,同步本地 gh-pages 到远端

[3/4] 同步到 gh-pages worktree...
[pages] gh-pages 无文件变化
[pages] 本地与远端已一致,跳过推送

[3/4] 同步到 gh-pages worktree...
M index.html
[pages] --no-push 已设置,未推送远端
[pages] 临时 worktree 已清理
```

说明: 三段"无文件变化"输出为夹具清理后的 3 个测试驱动真实 `publish_to_pages` 分支所打印,push 动作经 mock 捕获未真推;输出与 v32 轮(0a507e8)逐段一致,证明夹具清理未改变测试驱动的代码路径。链路测试 20 个清单与 v32 轮相同(函数名/数量不变,`grep -n "def test_" scripts/test_publish_chain.py` 尾三项仍在 L337/343/349)。

### 6.2 quotepath 修复实证(任务指定证据 2/3)

```text
$ PYTHONUTF8=1 .venv/bin/python scripts/audit_validate.py --file audit/submissions/A1-v30-actual-share-uv-r1.md
[PASS] A1-v30-actual-share-uv-r1.md

共校验 1 个文件(历史豁免跳过 0),CRITICAL 0,WARNING 0

$ PYTHONUTF8=1 .venv/bin/python scripts/audit_validate.py --all --skip-historical
[PASS] A1-v31-publish-hardening-r1.md
[PASS] A1-v32-audit-tooling-fix-r1.md
[PASS] B1-v29-runtime-hardening-r1.md
[PASS] B1-v30-actual-share-uv-r1.md
[PASS] B1-v31-publish-hardening-r1.md
[PASS] B1-v32-audit-tooling-fix-r1.md
[PASS] C1-v31-publish-hardening-r1.md
[PASS] C1-v32-audit-tooling-fix-r1.md

共校验 8 个文件(历史豁免跳过 32),CRITICAL 0,WARNING 0
```

A1-v30 PASS 即 REV-01 修复的直接证明: 其 changed_files(L18)声明 `scripts/投资台账_修改指南.md`,该文件确在 tag `audit/v2.5.7-v30-actual-share-uv-r01` commit 中;修复前 stat 转义串与明文声明互不匹配 → 遗漏1/多报1(B1-v32 Issue 原文实录的假阳性),修复后精确匹配 → 0/0。skip-historical 8 文件(较 v32 轮 5 文件新增 v32 轮三个产物)全 PASS。

### 6.3 REV-01 修复前后直接对照(同一命令,仅差 -c 参数)

```text
$ git show audit/v2.5.7-v30-actual-share-uv-r01 --stat --format= | grep '\\'
 ...277\346\224\271\346\214\207\345\215\227.md" |  6 +--        ← 默认 core.quotepath: 中文路径八进制转义

$ git -c core.quotepath=off show audit/v2.5.7-v30-actual-share-uv-r01 --stat --format= | grep '指南'
 scripts/投资台账_修改指南.md       |  6 +++---        ← 修复后: 明文输出,与 A1-v30 declared 精确匹配
```

audit_validate.py 的 git()(L108-115)已对该出口统一注入 `-c core.quotepath=off`(L113),V6 调用链 L209 `git("show", str(tag), "--stat", "--format=")` 自动受益,无需逐调用点修改。

### 6.4 全量 `--all` 对照(quotepath 修复的净效果)

```text
$ PYTHONUTF8=1 .venv/bin/python scripts/audit_validate.py --all
    CRITICAL: A1-v20-institution-stats-r1.md: git_tag audit/v2.0-v20-institution-stats-r01 不存在
    CRITICAL: A1-v22-pricing-r1.md: commit_hash 03225ef 与 tag 实际指向 1e14550 不一致
    CRITICAL: A1-v23-internal-merge-unify-r1.md: commit_hash e9cf091 与 tag 实际指向 1ef0612 不一致
    CRITICAL: A1-v25-match-rule-tune-r1.md: commit_hash ... 与 tag 实际指向不一致
    CRITICAL: A1-v26-uv-protection-r1.md: frontmatter 不可解析(缺 --- 块)
[PASS] A1-v30-actual-share-uv-r1.md        ← 修复前该文件 [WARN] 遗漏1/多报1
共校验 40 个文件(历史豁免跳过 0),CRITICAL 5,WARNING 10
```

与 v32 轮对照: CRITICAL 5 不变(同一批历史既存问题);WARNING 12→10,消除的 2 条恰为 A1-v30 成对假阳性,与 B1-v32 r01-01 记录"10 真 2 假"精确吻合——修复后余 10 条全部为真检出。余 10 条分布: v21(遗漏6/多报6)/v22(遗漏11/多报6)/v23(遗漏13/多报5)/v24(遗漏12/多报13)/v25(遗漏4/多报3)各 2 条,均为历史括号注记格式所致(v32 轮已披露的既有边界,正常使用走 `--skip-historical` 不触发)。附注: v23 遗漏清单中的中文文件名(如 `2026年ABS发行台账-0626-定稿.xlsx`)本轮起显示为明文,可读性改善,计数不变(仍 13,与 state.json 台账 REV-v2.3-v23-internal-merge-unify-r01-02 相符)。校验文件总数 37→40,新增为 v32 轮三产物(A1-v32/B1-v32/C1-v32),均 PASS。

### 6.5 git show 3281ae7 --stat

```text
commit 3281ae7001d86802779e5afb6b430426d30d87b9
Author: codebluce <codebluce@gmail.com>
Date:   Sun Aug 16 14:44:39 2026 +0800

    fix(audit): v33 收尾三项 (v2.5.10)
    ...

 CHANGELOG.md                  | 13 +++++++++++++
 scripts/audit_validate.py     |  7 ++++++-
 scripts/test_publish_chain.py | 24 ++++++++++++++----------
 3 files changed, 33 insertions(+), 11 deletions(-)
```

HEAD 即 3281ae7(`git log --oneline -1`)。上一轮 tag `audit/v2.5.9-v32-audit-tooling-fix-r01` 经 `git rev-parse --short` 校验指向 0a507e8,与 B1-v32 verified_tag_hash 一致。`git tag -l 'audit/v2.5.10*'` 为空——本报告仅写入送审文件,未做任何 git 操作;git_tag `audit/v2.5.10-v33-audit-cleanup-r01` 由控制平面在本报告 validate 通过后打于 3281ae7。
