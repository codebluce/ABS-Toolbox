---
submission_id: A1-v34-publish-safety-r1
slug: v34-publish-safety
skill_version: v2.5.11
round: 1
created_at: "2026-08-16 20:24:47"
author: agent_a

git_tag: audit/v2.5.11-v34-publish-safety-r01
commit_hash: 009cf3b
previous_git_tag: audit/v2.5.10-v33-audit-cleanup-r01

changed_files:
  - CHANGELOG.md
  - audit/v26-abs-toolbox-fix-verification-audit-20260816.md
  - scripts/deploy_github_pages.py
  - scripts/gen_integrated_dashboard.py
  - scripts/test_publish_chain.py

status: PENDING_REVIEW

self_review:
  all_issues_addressed: true
  no_overengineering: true
  function_equivalence_verified: true
  edge_cases_covered: true
  notes: "对象为 v26 修复验收专项审计(非正式 B 轮,无 REV- ID): 优先级 A 全部 3 项 + 优先级 B 的 B1/B2/B3 fixed,B4(P2-05 浏览器兼容回退)wontfix-转专项留档。六点如实披露: (1) V6 校验器对长文件名的截断假阳性——实测 `git show 009cf3b --stat` 中 `audit/v26-abs-toolbox-fix-verification-audit-20260816.md`(55 字符)被 git 默认 stat 宽度截断显示为 `...-abs-toolbox-fix-verification-audit-20260816.md`,tag 打上后 `--file` 校验将报 遗漏1/多报1(同一文件的两种表示),与 v21-v25 历史边界同类,属校验器 stat 宽度限制而非本报告声明错误(附录 6.5 实测); (2) test_qc_failure_preserves_old_artifact(test_publish_chain.py:493-520)未端到端调用生成器 main(),其原子替换段是对 main 内实现的复刻(测试注释已自陈'与 main 内实现一致'),verify_integrated_html 及哈希比对为真实调用——A1 的端到端保障依赖代码评审而非该测试; (3) B2 残余边界: --skip-generate 路径(latest_dashboard=None)仍走 latest_by_mtime 二次扫描(deploy_github_pages.py:681-682),因 build_site 不回传其内部所选产物、main 无从获知,接口未改动;主路径(生成模式)已用实际产物; (4) B3 只实现 resolve(),v26 建议的后半'校验产物位于允许目录+错误信息说明允许根目录'未做(当前唯一消费方传绝对路径,属增强项); (5) no-push 语义按本轮定义: 在临时 worktree 内仍会创建 commit 对象(悬空,不进任何 ref,留在共享对象库直至 gc),随临时 worktree 清理消失,主仓库 refs/HEAD/工作区不变;build-only 则连 commit 都不创建——与 v26 验收标准第 2 条'所有 refs、HEAD 和工作区均不变化'对照,refs/HEAD/工作区两项均满足,对象库悬空对象如实说明(附录 6.6); (6) 无变化分支的比较对象由'本地 refs/heads vs refs/remotes'翻转为'detached HEAD vs refs/remotes'(deploy_github_pages.py:588-595),场景2 测试语义随之从'本地领先→push 本地引用'变为'HEAD≠远端→push HEAD:refs/heads',方向仍为同步推送,断言未变仍通过。"

review_focus:
  - "A1 原子替换真实完整性: gen_integrated_dashboard.py:430-457 的 tmp→QC→os.replace 链是否在所有异常路径(QC 失败/写中途异常/replace 前崩溃)下都不触碰旧正式产物;os.replace 同目录原子性依赖;测试 test_qc_failure_preserves_old_artifact(L493-520)为复刻逻辑非端到端,是否可接受(self_review notes 第 2 点)。"
  - "A2 副作用边界: publish_to_pages(deploy_github_pages.py:532-620)build_only 分支(L581-583/L597-601)是否真正零 git 写操作;no_push 分支(L604-605)update-ref 是否仅移入 push 成功之后(L610-615);--build-only 与 --no-push 互斥校验(L652-653);no-push 悬空 commit 对象的说明是否与代码一致(附录 6.6)。"
  - "A3 无变化分支重写: deploy_github_pages.py:586-595 比较对象翻转为 HEAD vs remote_ref 后,'HEAD 落后于远端'分支 push HEAD:refs/heads/(L594-595,cwd=worktree)是否 fast-forward 安全;真实 Git 集成测试 RealGitIntegrationTest(L457-491)对'无本地分支+无变化'的复现是否等价于 v26 §5.1 演练场景。"
  - "B1 严格语义: deploy_github_pages.py:117-122 raise 的触发条件(undated 非空且 fallback_mtime=False)是否覆盖'部分有日期部分无日期'场景(该场景按文件名日期正常选择,不触发 raise——请确认此语义合理);测试 L230-238/L240-246 正反两向。"
  - "B2+B3 一致性: B2(deploy_github_pages.py:679-682)主路径日期与实际产物同源、--skip-generate 残余 mtime 扫描的披露;B3(L428-431)resolve() 后 relative_to(REPO_ROOT) 是否不再抛 ValueError,防御性断言 is_absolute 在 resolve() 后恒真是否属可接受的显式失败点。"
  - "测试真实性: 69/69 中真实 Git 仅 2 个(RealGitIntegrationTest),其余 publish 分支测试仍 mock run/capture——mock 夹具(_run_no_change_publish L310-353 及 build-only/no-push 两测试)与生产 L577-618 分支的对应关系是否仍然锁定;62→69 新增 7 个测试清单与 CHANGELOG/commit message 声明是否逐项一致。"

---

# v34-publish-safety r1 送审报告

## 1. 变更摘要(200 字内)

落实 v26 修复验收专项审计(NEEDS_REVISION)优先级 A 全部三项 + B 三项: A1 生成器临时文件+QC 后 `os.replace` 原子替换,失败保旧产物;A2 新增 `--build-only` 真预览,`--no-push` 不再 update-ref;A3 无变化改比远端引用与 detached HEAD,推送用 `HEAD:refs/heads`;B1 `fallback_mtime=False` 严格语义;B2 提交消息日期取实际产物;B3 `build_site` 统一 `resolve()`。测试 62→69(含真实 Git 集成)。B4 转专项留档。commit 009cf3b,v2.5.11。

## 2. 上一轮 Issue 处理

上一轮对象: `audit/v26-abs-toolbox-fix-verification-audit-20260816.md`(工程修复验收专项审计,verdict NEEDS_REVISION,非正式 A/B/C 序列,无 REV- ID,沿用其 §8 优先级编号)。

| v26 编号 | 严重程度 | 处理方式 | 证据 |
|---|---|---|---|
| P1-01(优先级 A1)QC 失败破坏上一版产物 | P1 | fixed | `scripts/gen_integrated_dashboard.py:430-457`: L433 `tmp_out = out_path + '.qc-tmp'`,写入与 QC(L436-443)均针对临时文件;L444 QC 通过后 `os.replace(tmp_out, out_path)` 原子替换(同目录,替换瞬间前正式产物始终是旧版);失败分支 L454-457 仅 `os.remove(tmp_out)`,旧产物内容与哈希不变。测试 `test_publish_chain.py:493-520`: 预置旧产物→QC 必败→旧 SHA256 不变且 tmp 已删(注: 该测试原子替换段为对 main 实现的复刻,见 self_review notes 第 2 点) |
| P1-02(优先级 A2)`--no-push` 移动本地发布分支 | P1 | fixed | `scripts/deploy_github_pages.py:634-635` 参数语义重定义+新增 `--build-only`;L652-653 互斥校验;`publish_to_pages` L532 新增 build_only 形参;L581-583 无变化时 build-only 直接返回;L597-601 有变化时 build-only 打印 diff 后返回(不 commit);L604-605 no-push 提交不推送且不动引用;`update-ref` 从原"无条件执行"移入 push 成功之后(L610-615)。测试: L382-417(build-only 零 git 写操作)、L420-455(no-push 无 update-ref)。no-push 在临时 worktree 内仍创建悬空 commit 对象的如实说明见附录 6.6 |
| P2-01(优先级 A3)无本地分支且无变化时 push 报 src refspec 错误 | P2 | fixed | `scripts/deploy_github_pages.py:586-595`: 无变化时 `rev-parse HEAD` 与 `rev-parse refs/remotes/{remote}/{branch}` 比较,一致即"无需推送"成功退出;确需推送改 `HEAD:refs/heads/{branch}` 且 `cwd=worktree`(L595,不再用主仓库不存在的 `refs/heads` src refspec)。真实 Git 集成测试 `test_publish_chain.py:457-491`(bare 远端+clone,本地无 gh-pages 分支、内容一致→零 push 成功返回),对应 v26 §5.1 演练复现;mock 测试 L368-374(场景3 改断言为 pushes==[])+ L375-380(新增场景3b: HEAD 落后→HEAD:refs/heads 形式) |
| P2-02(优先级 B1)`fallback_mtime=False` 无效 | P2 | fixed | `scripts/deploy_github_pages.py:117-122`: undated 非空且 fallback_mtime=False 时 raise FileNotFoundError,消息含全部候选清单(实测候选路径入错误文本);有日期场景不受影响。测试 `test_publish_chain.py:230-238`(严格→抛错且消息含文件名)、L240-246(默认回退仍可用,向后兼容) |
| P2-03(优先级 B2)提交消息日期与实际产物错配 | P2 | fixed | `scripts/deploy_github_pages.py:679-682`: `latest_dashboard is not None` 时 `date_tag = dashboard_date(latest_dashboard)`(即本次生成/传入的实际产物),不再二次 mtime 扫描;残余: `--skip-generate` 路径 latest_dashboard=None 仍走 `latest_by_mtime(find_dashboard_files())`(L681-682),因 build_site 不回传内部所选产物,接口未动,如实披露 |
| P2-04(优先级 B3)`build_site` 相对路径不健壮 | P2 | fixed | `scripts/deploy_github_pages.py:428-431`: `latest_dashboard = latest_dashboard.resolve()` 后续 relative_to 不再因相对路径抛 ValueError;L430-431 防御性断言。v26 建议后半"校验产物位于允许目录+错误信息说明允许根目录"未做(当前唯一调用方 main 传绝对路径,属增强项,如实披露) |
| P2-05(优先级 B4)浏览器兼容回退与性能验收 | P2 | wontfix | 转专项留档: 兼容回退需引入第三方 inflate 库或自实现 gzip 解压,超出本轮"发布安全可靠性门禁"范围;与 v26 §8 口径一致("性能拆分可在可靠性门禁完成后推进")。已记入 CHANGELOG v2.5.11 条目"未做"行(CHANGELOG.md:30),留待后续性能与兼容专项 slug 处理 |

v26 验收标准(§8)对照: 第 1 条(QC 失败非零+旧产物哈希不变)→ 上述 P1-01;第 2 条(build-only/no-push 后 refs/HEAD/工作区不变)→ 上述 P1-02+附录 6.6;第 3 条(真实 Git 集成覆盖)→ 部分(无本地分支✓/无变化✓/落后✓(场景3b mock)/领先✓/分叉✓(L265 既有)/push 失败✗未覆盖,如实披露);第 4 条(文件/manifest/消息同一业务日期同一源产物)→ B2 主路径达成;第 5 条(禁用回退明确失败)→ B1;第 6 条(目标浏览器解锁+性能预算)→ B4 wontfix 未做。

## 3. 代码变更清单

`git show 009cf3b --stat`: 5 files changed, 418 insertions(+), 35 deletions(-)。与 frontmatter changed_files 一致(逐条核对,附录 6.4)。注意: git stat 输出将长文件名 `audit/v26-abs-toolbox-fix-verification-audit-20260816.md` 截断显示为 `...-abs-toolbox-fix-verification-audit-20260816.md`,frontmatter 声明完整路径(此差异对 V6 校验的影响见 self_review notes 第 1 点与附录 6.5)。

| 文件 | 操作 | 说明 |
|---|---|---|
| `CHANGELOG.md` | modified (+17/-0) | L15-30 新增 v2.5.11 条目: 优先级 A×3 + B×3 逐项 + 测试 62→69 + B4 未做说明 |
| `audit/v26-abs-toolbox-fix-verification-audit-20260816.md` | added (+170/-0) | v26 复审报告入库(对象文档随修复 commit 一并归档) |
| `scripts/deploy_github_pages.py` | modified (+48/-18) | A2/A3(publish_to_pages L532-620 重构无变化与 no-push/build-only 分支,update-ref 移入 push 后)+ B1(L117-122)+ B2(L679-682)+ B3(L428-431)+ 参数与互斥(L634-635/652-653) |
| `scripts/gen_integrated_dashboard.py` | modified (+13/-9) | A1: tmp `.qc-tmp` 写入→QC→`os.replace` 原子替换(L430-457),失败只删 tmp |
| `scripts/test_publish_chain.py` | modified (+171/-7) | 新增 7 测试: fallback False 抛错(L230)/fallback True 兼容(L240)/场景3 改断言(L368)/场景3b(L375)/build-only 零副作用(L382)/no-push 不动引用(L420)/真实 Git 类 RealGitIntegrationTest(L457: 无本地分支无变化 L477 + QC 保旧产物 L493);夹具 `_run_no_change_publish` 增 head_sha 参数(L310) |

## 4. 自审与指标

### 4.1 强制自审清单

- [x] all_issues_addressed: v26 优先级 A 全部 3 项 + B 的 B1/B2/B3 fixed,B4 wontfix-转专项留档(理由见 §2,符合 v26 §8"性能拆分可在可靠性门禁完成后推进"口径);验收标准 6 条中第 3 条"push 失败"子场景与第 6 条未覆盖,已如实披露。
- [x] no_overengineering: A1 为写路径替换(2 处路径改 tmp+1 处 os.replace+2 行注释);A2 为分支前移与参数新增,未引入新抽象层;B1 是 5 行 raise;B2 是 4 行三元分支;B3 是 1 行 resolve+2 行防御断言;全部仍纯标准库。B3 防御性断言 `is_absolute()` 在 resolve() 后恒真,保留为显式失败点而非逻辑必需(notes 第 4 点披露)。
- [x] function_equivalence_verified: 69/69(附录 6.1);发布链 27/27 单独通过(附录 6.2);行为变化即 v26 要求的三项语义修正本身,非目标行为无回归: 选台账逻辑(文件名业务日期优先)、加密往返、protected 泄漏门禁、动态 Tab 测试全部未动且通过;无变化三分支打印输出与新旧语义对应关系逐段核对(附录 6.1 输出解读)。
- [x] edge_cases_covered: 无变化×(HEAD==远端/HEAD 落后/无本地分支)、有变化×(正常/no-push/build-only)、fallback_mtime False/True 双向、QC 失败保旧哈希、分叉中止(既有)、本地 refs 比较既有场景 1/2 断言保留;真实 Git 覆盖"无本地分支+无变化"原故障路径。未覆盖: push 失败(push 成功后才 update-ref,失败路径无专门测试)、--skip-generate 的 B2 残余、V6 校验器长文件名截断(校验工具边界非本轮代码)。

### 4.2 5 层自检证据

| 层 | 检查 | 结果 | 证据 |
|---|---|---|---|
| 1 | 文件变更边界 | ✅ | `git show 009cf3b --stat` 5 文件与 changed_files 逐条一致(附录 6.4;长名截断显示差异已在 §3 说明);HEAD 即 009cf3b;scripts/CHANGELOG/audit 工作区干净(仅本报告新增) |
| 2 | 端到端穿行 | ✅ | run_tests.py 69/69 OK(7+31+27+4),输出含真实 Git 段落(fetch/worktree add --detach/status/无文件变化/无需推送/worktree remove 全链真实命令打印)与 build-only/no-push 新分支打印(附录 6.1) |
| 3 | 门禁有效性 | ✅ | QC 硬阻断路径改造后语义反而在失败侧更强(旧产物先被覆盖再删除 → 从未触碰);真实 Git 测试直接复现 v26 §5.1 故障场景并验证修复(附录 6.1 中段);`audit_validate.py --all --skip-historical` 11 文件全 PASS 0 CRITICAL 0 WARNING(附录 6.3,含 v33 轮三个新产物) |
| 4 | 修复前后对照 | ✅ | A3: 修复前该场景 `git push origin gh-pages:gh-pages` fatal(v26 §5.1 实录),修复后真实仓库零 push 成功返回(L477-491);B1: 修复前返回 mtime 文件违反参数(v26 §5 复现),修复后 raise 含候选清单;无变化三分支输出文本前后对照见附录 6.1 |
| 5 | 回归 | ✅ | 69/69(62→69 净增 7 与新增测试清单一一对应);publish 既有 8 测试中 6 个断言未动,场景 3 断言按新语义改写(旧断言"触发 push"正是 v26 判定的缺陷行为);校验器输出较 v33 轮无恶化(11 文件 vs 8 文件全 PASS,新增为 v33 轮产物) |

## 5. 审计焦点(给 B 的提示)

1. **A1 原子替换真实完整性**(P1-01): `gen_integrated_dashboard.py:430-457`。重点: (a) QC 失败/写 tmp 中途异常/replace 前崩溃三类路径是否都不触碰 `out_path` 旧内容(写 tmp 失败会自然抛异常,tmp 残留 `.qc-tmp` 不影响正式产物,是否可接受);(b) `os.replace` 同目录原子性在目标文件已存在时的平台语义;(c) 测试 L493-520 为复刻 main 逻辑而非端到端调用(注释自陈),其保障价值与局限(self_review notes 第 2 点)。
2. **A2 副作用边界**(P1-02): `deploy_github_pages.py:532-620`。重点: build_only 分支是否零 git 写操作(测试 L382-417 用 git_ops==[] 断言 commit/update-ref/push 均不出现);no_push 时 update-ref 是否只在 push 分支内(L610-615);互斥校验 L652-653;no-push 悬空 commit 对象与 v26 验收标准第 2 条"refs、HEAD、工作区不变"的对照说明(附录 6.6)是否如实。
3. **A3 无变化分支重写**(P2-01): `deploy_github_pages.py:586-595`。重点: 比较对象翻转(本地引用→detached HEAD)后,"HEAD 落后于远端"分支 push HEAD:refs/heads/(L594-595, cwd=worktree)是否 fast-forward 安全、非快进时行为;`RealGitIntegrationTest`(L457-491)的 bare+clone 构造是否等价于 v26 §5.1 演练(本地无 gh-pages、内容一致);场景3b(L375-380)mock 的 head_sha="behind2x" 语义。
4. **B1 严格语义**(P2-02): `deploy_github_pages.py:117-122`。重点: raise 触发条件(undated 非空 ∧ fallback_mtime=False);"部分候选有日期"场景不触发 raise(按文件名日期正常选)是否符合 v26 建议"无业务日期候选必须明确失败"的字面与意图;两向测试 L230-246。
5. **B2+B3**(P2-03/P2-04): `deploy_github_pages.py:679-682 / 428-431`。重点: B2 主路径与 `--skip-generate` 残余扫描的披露是否准确(build_site 不回传所选产物,改接口超出本轮最小修复是否合理);B3 resolve() 后 relative_to 不抛 ValueError、防御断言恒真是否可接受。
6. **测试真实性**: 69 中真实 Git 仅 2 个,其余 publish 分支仍 mock run/capture。重点: mock 夹具(L310-353/_run_no_change_publish、L382-455 两测试)与生产 L577-618 分支的锁定关系;新增 7 测试清单与 CHANGELOG.md:29、commit message 声明逐项核对;62→69 的差额恰为 7。

## 6. 附录

### 6.1 run_tests.py 全量输出(2026-08-16,仓库根目录)

命令: `PYTHONUTF8=1 .venv/bin/python run_tests.py`(exit 0)

```text
...........................................................From /var/folders/hb/.../T/tmpbjdebyrd/remote
 * branch            gh-pages   -> FETCH_HEAD
cd23e1f8785d2ed4cfed28e0a722fb94d11974d8 refs/remotes/origin/gh-pages
fatal: 'refs/heads/gh-pages' - not a valid ref
Preparing worktree (detached HEAD cd23e1f)
HEAD is now at cd23e1f init
..........
----------------------------------------------------------------------
Ran 69 tests in 0.505s

OK
[discover] test_consumer_asset_panel: 7 tests
[discover] test_peer_issuance_panel: 31 tests
[discover] test_publish_chain: 27 tests
[discover] test_sync_institution_profile: 4 tests
[site] protected 泄漏自检通过: 无源 Excel/明文看板特征
[select] 文件名业务日期(20260807)与 mtime(2026年ABS发行台账-0801-定稿.xlsx)不一致,以文件名为准: 2026年ABS发行台账-0807-定稿.xlsx

[3/4] 同步到 gh-pages worktree...
[pages] build-only 预览:检测到文件变化(如正式发布将提交以下内容),未创建提交/未动引用/未推送
M index.html

[3/4] 同步到 gh-pages worktree...

[3/4] 同步到 gh-pages worktree...
[pages] gh-pages 无文件变化
[pages] 本地引用落后于远端,执行同步推送

[3/4] 同步到 gh-pages worktree...
[pages] gh-pages 无文件变化
[pages] 本地引用落后于远端,执行同步推送

[3/4] 同步到 gh-pages worktree...
[pages] gh-pages 无文件变化
[pages] 远端 gh-pages 与本次产物一致,无需推送

[3/4] 同步到 gh-pages worktree...
[pages] gh-pages 无文件变化
[pages] 远端 gh-pages 与本次产物一致,无需推送

[3/4] 同步到 gh-pages worktree...
M index.html
[pages] --no-push 已设置,未推送远端,本地引用保持不变
[pages] 临时 worktree 已清理

[3/4] 同步到 gh-pages worktree...
M index.html
[pages] --no-push 已设置,未推送远端,本地引用保持不变
[pages] 临时 worktree 已清理

[3/4] 同步到 gh-pages worktree...
$ git fetch origin gh-pages
$ git worktree add --detach /var/folders/hb/.../T/abs_pages_uw_xnf4r/worktree refs/remotes/origin/gh-pages
$ git add -A
[pages] gh-pages 无文件变化
[pages] 远端 gh-pages 与本次产物一致,无需推送
$ git worktree remove --force /var/folders/hb/.../T/abs_pages_uw_xnf4r/worktree
```

输出解读: (a) 顶部 `From .../remote` 至 `HEAD is now at cd23e1f init` 段为 `RealGitIntegrationTest` 真实 Git 输出(fetch/worktree add --detach 于真实临时 bare 仓库);(b) "本地引用落后于远端,执行同步推送"×2 = 场景2(旧'本地领先'语义,现按 HEAD≠远端触发)+ 场景3b,"无需推送"×2 = 场景1+真实 Git 无本地分支,push 动作经 mock/真实各有对应断言;(c) 末段 5 行真实命令打印为真实 Git 集成测试全程;(d) `fatal: 'refs/heads/gh-pages' - not a valid ref` 为 mock 夹具内 subprocess 被替换后 git fetch 的无害 stderr 残留,unittest 结果 OK 证明不影响判定。中间一段空"[3/4]"为 build_only 无变化 mock 分支(真实输出首行 print 后立即 return)。

### 6.2 test_publish_chain.py 单独运行(任务指定证据 2)

命令: `PYTHONUTF8=1 .venv/bin/python scripts/test_publish_chain.py`(exit 0)

```text
Ran 27 tests in 0.478s

OK
```

27 个测试清单(`grep -n "def test_"`,类内计数): DynamicTabsTest×3(L55/67/78)、VerifyHtmlTest×4(L95/99/104/110)、CryptoRoundTripTest×3(L148/151/154)、AuditProtectedSiteTest×3(L172/182/195)、LedgerSelectionTest×4(L214/218/**230**/240)、PublishToPagesTest×8(L265/285/356/362/**368/375/382/420**)、RealGitIntegrationTest×2(**L477/493**)。加粗为本轮新增/改写 7 个(62→69 差额恰为 7,逐一对应当 v26 项)。

### 6.3 audit_validate.py(任务指定证据 3)

命令: `PYTHONUTF8=1 .venv/bin/python scripts/audit_validate.py --all --skip-historical`(exit 0)

```text
[PASS] A1-v31-publish-hardening-r1.md
[PASS] A1-v32-audit-tooling-fix-r1.md
[PASS] A1-v33-audit-cleanup-r1.md
[PASS] B1-v29-runtime-hardening-r1.md
[PASS] B1-v30-actual-share-uv-r1.md
[PASS] B1-v31-publish-hardening-r1.md
[PASS] B1-v32-audit-tooling-fix-r1.md
[PASS] B1-v33-audit-cleanup-r1.md
[PASS] C1-v31-publish-hardening-r1.md
[PASS] C1-v32-audit-tooling-fix-r1.md
[PASS] C1-v33-audit-cleanup-r1.md

共校验 11 个文件(历史豁免跳过 32),CRITICAL 0,WARNING 0
```

较 v33 轮 8 文件新增 A1/B1/C1-v33 三产物(均 PASS)。本报告未列入本轮校验——git_tag `audit/v2.5.11-v34-publish-safety-r01` 由控制平面在本报告落盘后打于 009cf3b,tag 打上前 `--file` 会因 V5 报"git_tag 不存在"CRITICAL(既定流程,与 v33 轮相同)。

### 6.4 git show 009cf3b --stat(任务指定证据 4)

```text
commit 009cf3bdffc75da499e03b588951e3e311c2207e
Author: codebluce <codebluce@gmail.com>
Date:   Sun Aug 16 20:08:08 2026 +0800

    fix(publish): v26 复审优先级 A 全部+B 三项 (v2.5.11)
    ...

 CHANGELOG.md                                       |  17 ++
 ...-abs-toolbox-fix-verification-audit-20260816.md | 170 ++++++++++++++++++
 scripts/deploy_github_pages.py                     |  66 +++++---
 scripts/gen_integrated_dashboard.py                |  22 +--
 scripts/test_publish_chain.py                      | 178 ++++++++++++++++++-
 5 files changed, 418 insertions(+), 35 deletions(-)
```

HEAD 即 009cf3b(`git log --oneline -1`)。上一轮 tag `audit/v2.5.10-v33-audit-cleanup-r01` 经 `git rev-parse --short` 验证指向 3281ae7。3281ae7 与 009cf3b 之间另有 4 个非本 slug 提交(0bee2a6 归档/f8b7780 deploy 修正/c463306 与 570335c 看板产物同步),均属 v33 归档与时序内提交,不在本 slug 变更范围。`git tag -l 'audit/v2.5.11*'` 为空——本报告仅写入送审文件,未做任何 git 操作。

### 6.5 V6 长文件名截断边界实测(self_review notes 第 1 点佐证)

```text
$ git -c core.quotepath=off show 009cf3b --stat --format= | grep '|'   # 解析得 5 个路径:
['...-abs-toolbox-fix-verification-audit-20260816.md', 'CHANGELOG.md',
 'scripts/deploy_github_pages.py', 'scripts/gen_integrated_dashboard.py',
 'scripts/test_publish_chain.py']
```

git stat 默认宽度将 55 字符长路径截断为 `...` 前缀形式。tag 打上后 V6 以该形式与 frontmatter 完整路径 `audit/v26-abs-toolbox-fix-verification-audit-20260816.md` 比对,将报"遗漏 1(截断串)/多报 1(完整串)"成对 WARNING——同一物理文件的两种表示,与 v21-v25 历史边界同类(校验器 stat 宽度限制),非本报告声明错误。B 可用 `git show audit/v2.5.11-v34-publish-safety-r01 --stat=250 --format=` 人工复核完整路径一致。

### 6.6 no-push/build-only 副作用说明(对应 v26 验收标准第 2 条)

v26 验收标准第 2 条: "build-only/no-push 后仓库所有 refs、HEAD 和工作区均不变化"。本轮实现的三种模式副作用边界如实如下:

| 模式 | git commit | update-ref | push | 主仓库 refs/HEAD/工作区 | 残留 |
|---|---|---|---|---|---|
| `--build-only` | 否(L597-601 有变化也只打印 diff) | 否 | 否 | 均不变 | 无(仅临时 worktree 生命周期) |
| `--no-push` | **是**,在临时 detached worktree 内(L604) | 否(已移入 push 成功后) | 否 | 均不变 | commit 对象写入共享对象库成为悬空对象(不进任何 ref,不可达,待 gc 回收);临时 worktree 与 .git/worktrees 元数据随 finally 清理 |
| 正常发布 | 是 | 是(仅 push 成功后,L610-615) | 是 | refs/heads/{branch} 对齐发布基线(预期行为) | 无 |

即: v26 标准字面上的"refs、HEAD、工作区"三项在 build-only 与 no-push 下均不变化(测试 L382-417/L420-455 分别以 git_ops==[]/ref_updates==[] 锁定);no-push 与 build-only 的差异在于临时 worktree 内是否创建悬空 commit 对象——该对象随临时目录清理从引用角度完全消失,但物理上留在对象库,特此如实说明,不做超出字面的声称。
