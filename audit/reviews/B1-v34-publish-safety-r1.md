---
review_id: B1-v34-publish-safety-r1
submission_id: A1-v34-publish-safety-r1
slug: v34-publish-safety
skill_version: v2.5.11
round: 1
auditor: agent_b
created_at: "2026-08-16 20:47:00"

git_tag: audit/v2.5.11-v34-publish-safety-r01
verified_tag_hash: 009cf3b

verdict: APPROVED_WITH_CONDITIONS

issues:
  - id: REV-v2.5.11-v34-publish-safety-r01-01
    severity: WARNING
    category: DATA_INTEGRITY
    location: "scripts/test_publish_chain.py:457-516(RealGitIntegrationTest 覆盖范围)"
    description: "v26 验收标准第 3 条要求六类场景(无本地分支/落后/领先/分叉/无变化/push 失败)均有真实 Git 集成测试,当前仅'无本地分支+无变化'1 项落地真实 Git;落后/领先(场景2/3b)与分叉(L265)仍为 mock,push 失败子场景零覆盖(A 已如实披露)。"
    evidence: "快照 grep 'def test_': RealGitIntegrationTest 仅 2 测试(L477 无本地分支无变化、L493 QC 保旧);B 独立实 Git 演练证实 push 失败路径的 update-ref 不执行依赖代码顺序(deploy_github_pages.py:608-615)而非测试锁定。"
    suggested_fix: "后续 slug 补 3 类真实 Git 测试: (a) push 被远端拒绝(非快进)→ 断言 update-ref 未执行且 CalledProcessError 传播; (b) 本地与远端分叉 → 断言中止; (c) 无变化但 tracking ref 过期竞态。"
    blocks_approval: false
  - id: REV-v2.5.11-v34-publish-safety-r01-02
    severity: WARNING
    category: FUNCTION_EQUIVALENCE
    location: "scripts/test_publish_chain.py:493-516"
    description: "test_qc_failure_preserves_old_artifact 为逻辑复刻而非端到端: 直接调 verify_integrated_html 后手工重演 tmp→remove 模式,未调用生成器 main()。若未来 main() 的原子替换实现漂移(如误写 out_path),该测试仍绿灯,无法拦截回归。A 已自陈并请求 B 评判;B 代码评审确认当前 main 实现正确,但当轮测试无端到端锁定。"
    evidence: "快照 L508-514: '模拟生成器的原子替换路径(与 main 内实现一致)'——测试体与 gen_integrated_dashboard.py:430-459 是平行实现,非调用关系。"
    suggested_fix: "端到端化: 以受控小 Excel 或注入 mock panel 数调用 main(),预置旧产物→QC 必败→断言 exit code 非零且旧 SHA256 不变且 tmp 已删。"
    blocks_approval: false
  - id: REV-v2.5.11-v34-publish-safety-r01-03
    severity: INFO
    category: DOC_CONSISTENCY
    location: "scripts/deploy_github_pages.py:593-595"
    description: "无变化路径的 else 分支('本地引用落后于远端,执行同步推送')在当前接线下不可达: worktree 恒建于 refs/remotes/{remote}/{branch}(L567),L589-590 读的同一 tracking ref 在 worktree add 与 rev-parse 之间无任何更新操作,head_sha==remote_sha_now 是接线不变量(除并发外部 git 进程干预的病态情形)。该分支仅能被 mock(场景3b 伪造 head_sha='behind2x')触达,且提示文案仍写'本地引用落后'沿袭旧语义(实际比较对象已是 worktree HEAD vs tracking ref)。"
    evidence: "B 独立实 Git 演练(构造远端被第三方推进+站点内容与旧基线一致): 因 deploy 内部先 fetch(L545)再建 worktree,HEAD 必等于最新 tracking ref,结果走的是'有变化'正常路径而非该分支;与 A 报告'理论少见'相比,实为接线内不可达。"
    suggested_fix: "二选一: 注释标注该分支为防御性(并发 stale ref 场景)并修正打印文案,或删除该分支(场景3b 随之调整)。非阻断。"
    blocks_approval: false
  - id: REV-v2.5.11-v34-publish-safety-r01-04
    severity: INFO
    category: DOC_CONSISTENCY
    location: "audit/submissions/A1-v34-publish-safety-r1.md 附录 6.1 输出解读(d)"
    description: "A 将测试输出中的 `fatal: 'refs/heads/gh-pages' - not a valid ref` 归因为'mock 夹具内 subprocess 被替换后 git fetch 的无害 stderr 残留',归因不准确。B 单独运行 RealGitIntegrationTest(该类未 mock 任何 subprocess)该 fatal 仍出现——真实来源是生产代码 deploy_github_pages.py:555-557 `git show-ref --verify refs/heads/gh-pages` 在无本地分支时的预期失败 stderr 直通(run/subprocess 未捕获 stderr)。现象无害,但归因需更正,避免误导后续维护者去 mock 层找这条输出。"
    evidence: "命令 `PYTHONUTF8=1 .venv/bin/python scripts/test_publish_chain.py RealGitIntegrationTest`(无 mock)输出同一 fatal,且位于 show-ref 检查处;git show-ref --verify 对不存在引用的报错文本即此格式。另: 附录 6.2 加粗标记把改写测试 L368 计入'新增/改写 7 个'而漏标真正新增的 L240(§3 文字清单本身准确,20→27 净增 7 与 62→69 一致),属排版级小误。"
    suggested_fix: "下一份送审/归档报告勘误归因一句;6.2 加粗排版可留档不改。"
    blocks_approval: false
  - id: REV-v2.5.11-v34-publish-safety-r01-05
    severity: INFO
    category: INTERFACE_COMPAT
    location: "scripts/deploy_github_pages.py:681-682 / 428-431"
    description: "两项 A 已披露的残留留档确认: (a) B2 残余——--skip-generate 路径 latest_dashboard=None,提交消息日期经 latest_by_mtime(find_dashboard_files()) 二次扫描(L682),与 build_site 内部选择(L427)是两次独立 mtime 扫描,秒级窗口内文件变动理论上可致消息日期与 manifest 日期错配(风险极低,生成模式主路径无此问题);(b) B3 后半——'校验产物位于允许目录+错误信息说明允许根目录'未做,当前唯一调用方 main 传绝对路径,resolve() 已消除 ValueError 缺陷本体。"
    evidence: "快照 L679-682 双分支;L427 build_site 内部 latest_by_mtime 与 L682 是两处独立调用;relative_to(REPO_ROOT) 在 L493(resolve 后不再抛 ValueError)。"
    suggested_fix: "登记为后续增强: build_site 回传所选产物(或 main 层单次扫描传入),目录白名单校验。非本轮范围。"
    blocks_approval: false

verified_issues:
  - id: v26-P1-01
    a_claim: fixed
    b_verification: verified
    evidence: "gen_integrated_dashboard.py:430-459 快照逐行核实: L433 tmp_out=out_path+'.qc-tmp' 同目录,L434-441 写 tmp+对 tmp 做 QC,L444 QC 通过才 os.replace(同目录 rename,POSIX 原子),L454-458 失败仅 os.remove(tmp_out)+exit(1)。三类异常路径推演: 写 tmp 中途异常→异常传播、旧产物未触碰;replace 前崩溃→旧产物未触碰;QC 失败→只删 tmp。tmp 残留 '.qc-tmp' 不影响正式产物且下次运行覆盖(A 披露可接受,B 认同)。deploy 侧 generate_dashboard 以 check=True 子进程调生成器,QC exit 1 → CalledProcessError → 发布链中止。测试为逻辑复刻(见 Issue 02)但 27/27 实跑通过,B 独立演练中 verify_integrated_html 真实调用。"
  - id: v26-P1-02
    a_claim: fixed
    b_verification: verified
    evidence: "deploy_github_pages.py 快照: build_only 分支 L581-583(无变化)与 L597-600(有变化只打印 diff)均在 git commit(L603)之前 return,零 git 写操作;no_push 分支 L604-605 提交不推送;update-ref(L615)已移入 else 内、真实 push(L608-611)成功之后;互斥校验 L652-653。B 独立实 Git 演练(tempfile 裸仓库+clone,无本地 gh-pages): 有变化+no_push → changed=True 且 show-ref 快照与 HEAD 逐项比对均不变;有变化+build_only → 零 commit/update-ref/push 且 refs/HEAD 不变;与 A 附录 6.6 的悬空 commit 对象披露一致(对象库残留、不进任何 ref,超出 v26 字面三项的诚实说明)。"
  - id: v26-P2-01
    a_claim: fixed
    b_verification: verified
    evidence: "deploy_github_pages.py:586-596 快照: 无变化时比较 rev-parse HEAD(cwd=worktree)与 rev-parse refs/remotes/{remote}/{branch},一致即'无需推送'成功返回;确需推送用 HEAD:refs/heads/{branch} 且 cwd=worktree(L595),不再依赖主仓库不存在的 refs/heads src refspec。B 独立实 Git 演练精确复现 v26 §5.1 场景(远端有 gh-pages/本地无/内容一致): 零 push、changed=False、refs/HEAD 不变——修复真实有效。测试 RealGitIntegrationTest.test_no_local_branch_no_change_publish_succeeds(L477-491)确为真跑 git(bare+clone+真实 push 断言链),非 mock。"
  - id: v26-P2-02
    a_claim: fixed
    b_verification: verified
    evidence: "deploy_github_pages.py:116-124 快照: undated 非空 ∧ fallback_mtime=False → raise FileNotFoundError,消息含全部候选路径 f'{[str(p) for p in undated]}';'部分有日期部分无日期'场景走 dated 分支按文件名日期正常选择、不触发 raise——符合 v26'无业务日期候选必须明确失败'的意图(禁回退针对的是完全无可解析日期时的静默 mtime 兜底),语义合理。测试 L230-238(严格→抛错且消息含文件名)/L240-246(默认 True 向后兼容)双向,实跑通过。附注: 生产调用方(find_latest_ledger L133)当前未传 fallback_mtime=False,严格模式处于休眠可用状态——参数语义已真实,接线属后续决策,不构成缺陷。"
  - id: v26-P2-03
    a_claim: fixed
    b_verification: verified
    evidence: "deploy_github_pages.py:679-682 快照: 生成模式 latest_dashboard is not None → date_tag=dashboard_date(latest_dashboard),与 build_site 内 manifest latestDate(L465)同源同产物,不再二次扫描;--skip-generate 残余二次扫描(L681-682)A 已如实披露,该模式下 main 本无已确定产物,v26 指认的主路径错配缺陷已修复。残余定级 INFO(Issue 05)。"
  - id: v26-P2-04
    a_claim: fixed
    b_verification: verified
    evidence: "deploy_github_pages.py:428-431 快照: latest_dashboard.resolve() 后 L493 relative_to(REPO_ROOT) 不再因相对路径抛 ValueError——v26 指认的缺陷本体已修复;'校验产物位于允许目录'建议后半未做(A 披露为增强项,B 认同: 唯一调用方传绝对路径)。防御性断言 is_absolute 在 resolve() 后恒真,属显式失败点而非逻辑必需,A 已披露,无害。"
  - id: v26-P2-05
    a_claim: wontfix
    b_verification: verified
    evidence: "wontfix 决策合理性核实: v26 §8 自身口径'性能拆分可在可靠性门禁完成后推进',将 B4 列为优先级 B 末位且与可靠性门禁解耦;A 已在 CHANGELOG v2.5.11 '未做'行(CHANGELOG.md:30)登记并声明转专项 slug。属范围管理而非逃避,处理妥当。"

conditions:
  - "C1(测试矩阵补全): 后续 slug 补真实 Git 集成测试覆盖 push 失败(update-ref 不得执行)、本地/远端分叉中止、无变化 stale-ref 竞态,使 v26 验收标准第 3 条六类场景完整闭环(对应 Issue 01)"
  - "C2(QC 测试端到端化): test_qc_failure_preserves_old_artifact 改为真实调用生成器 main() 注入 QC 必败,锁定'exit 非零+旧产物哈希不变+tmp 已删'(对应 Issue 02)"
  - "C3(文档勘误): 下一份报告更正附录 6.1(d) 对 fatal stderr 的归因(来源为生产代码 show-ref --verify 的预期 stderr,非 mock 残留)(对应 Issue 04)"
  - "C4(留档增强): B2 --skip-generate 双扫描统一、B3 目录白名单校验登记为后续增强项,不阻断本轮(对应 Issue 05)"
---

# v34-publish-safety r1 审计意见

## 0. 总体结论

**Verdict**: APPROVED_WITH_CONDITIONS

v26 优先级 A 全部 3 项 + B1/B2/B3 修复经 tag 快照代码评审与 B 独立真实 Git 演练(临时裸仓库,未触碰真实仓库/远端)逐项证实真实有效,测试 69/69 与发布链 27/27 复跑一致;但 v26 验收标准第 3 条(真实 Git 六场景矩阵)仅落地 1/6、QC 保旧测试为逻辑复刻非端到端,A 均已如实披露——达标但有小遗留,附 4 项条件放行。

## 1. 上一轮 Issue 验证(v26 专项审计,无 REV- ID,按其 P 编号)

| Issue ID | A 声称 | B 验证 | 证据 | verified |
|---|---|---|---|---|
| v26-P1-01 QC 失败破坏旧产物 | fixed | verified | frontmatter verified_issues 详列(gen_integrated_dashboard.py:430-459 逐行+异常路径推演) | ✅ |
| v26-P1-02 --no-push 移动本地引用 | fixed | verified | deploy_github_pages.py:581-615 分支顺序+B 实 Git 演练 refs/HEAD 快照不变 | ✅ |
| v26-P2-01 无本地分支无变化 push 报错 | fixed | verified | deploy_github_pages.py:586-596+B 实 Git 精确复现 v26 §5.1: 零 push 成功返回 | ✅ |
| v26-P2-02 fallback_mtime=False 无效 | fixed | verified | deploy_github_pages.py:116-124 raise 含候选清单+双向测试实跑通过 | ✅ |
| v26-P2-03 消息日期错配 | fixed | verified | deploy_github_pages.py:679-682 主路径同源;--skip-generate 残余已披露(Issue 05) | ✅ |
| v26-P2-04 build_site 相对路径 | fixed | verified | deploy_github_pages.py:428-431 resolve() 消除 ValueError;建议后半未做已披露 | ✅ |
| v26-P2-05 浏览器兼容/性能 | wontfix | verified(决策合理) | CHANGELOG.md:30 登记未做+转专项,与 v26 §8'性能拆分可在可靠性门禁完成后推进'口径一致 | ✅ |

**v26 验收标准(§8)逐条对照**(任务指定第 8 项):

| 标准 | 结论 | 依据 |
|---|---|---|
| 1. QC 失败非零+旧产物哈希不变 | **达标** | 代码 L430-459 经 B 评审证实;行为测试为逻辑复刻(Issue 02,条件 C2),A1 缺陷修复本身真实 |
| 2. build-only/no-push 后 refs、HEAD、工作区不变 | **达标** | B 独立实 Git 演练两模式均验证三项不变(零 git 写操作/零 update-ref);no-push 悬空 commit 对象为超出字面的诚实披露(6.6),不违反字面三项 |
| 3. 六类场景真实 Git 集成测试 | **部分达标** | 真实 Git 仅'无本地分支+无变化'(L477)+QC 保旧(L493,非 git 场景);落后/领先/分叉为 mock,push 失败零覆盖(Issue 01,条件 C1) |
| 4. 文件/manifest/消息同一业务日期同一源产物 | **达标(主路径)** | 生成模式 build_site 内 manifest(L465)与消息 date_tag(L680)同源 latest_dashboard;--skip-generate 双扫描残余已披露(Issue 05) |
| 5. 禁 mtime 回退时明确失败 | **达标** | L117-122 raise FileNotFoundError 含候选清单;注: 生产调用方当前未启用严格模式,参数语义已真实可用 |
| 6. 浏览器解锁+性能预算 | 未达(wontfix) | 非本轮 slug 范围,已登记转专项,v26 自身允许后置 |

按 verdict 标准: 标准 3 部分达标 + 无新 CRITICAL → APPROVED_WITH_CONDITIONS。

## 2. 需求合规审查

### 2.1 上一轮 Issue 全覆盖

v26 列优先级 A 三项 + B 四项: A1/A2/A3、B1/B2/B3 均 fixed 且经 B 独立验证(§1 表);B4 wontfix 有 CHANGELOG 登记与 v26 口径依据。全覆盖,无遗漏。

### 2.2 review_focus 回应(A 送审 §5 六点,任务指定 1-6 项)

1. **A1 原子替换真实完整性: PASS**。快照 gen_integrated_dashboard.py:433-459: (a) 写 tmp 中途异常 → 异常传播,旧 out_path 未触碰,tmp 残留可接受(下次覆盖);replace 前崩溃同理;(b) os.replace 同目录(out_path+'.qc-tmp')同文件系统,目标已存在时 POSIX rename 原子语义;(c) 测试 L493-516 为复刻(注释自陈'与 main 内实现一致'),verify_integrated_html 与哈希比对为真实调用——复刻与 main 当前实现 B 逐行比对一致,但当轮无端到端锁定,定 WARNING Issue 02。A 的自我评判(可接受但如实披露)成立。
2. **A2 副作用边界: PASS**。build_only 两处 return(L581-583/L597-600)均在 commit(L603)前,测试 L382-417 以 git_ops==[] 锁定三类命令;no_push 分支 L604-605;update-ref(L615)在 else 块内、push(L608-611)之后,代码顺序无歧义;互斥 L652-653。B 实 Git 演练独立复证三模式副作用边界与 6.6 说明逐项一致。
3. **A3 无变化分支重写: PASS(附 Issue 03)**。比较对象翻转后 push 用 HEAD:refs/heads/{branch} + cwd=worktree,fast-forward 安全性:B 演练验证该 push 建立在 fetch 后最新 tracking ref 基线上,正常路径为快进;非快进(push 被拒)时 run() 抛 CalledProcessError,update-ref 不执行(代码顺序),但此子场景无测试(Issue 01)。RealGitIntegrationTest(L457-491)的 bare+clone 构造与 v26 §5.1 演练等价(远端有 gh-pages、clone 无本地该分支、内容一致),真跑 git 无 mock,L477-491 断言链真实。另发现: 'HEAD 落后'else 分支在当前接线内不可达(worktree 恒建于 tracking ref,head_sha==remote_ref 为不变量),场景3b 仅能以伪造 head_sha 强制触达——定 INFO Issue 03,非正确性风险。
4. **B1 严格语义: PASS**。触发条件 undated 非空 ∧ fallback_mtime=False;部分有日期场景按文件名日期正常选择不触发 raise——该语义正确对应 v26 意图(禁的是'完全无日期时静默 mtime 兜底',不是禁止与无日期文件共存)。两向测试 L230-246 实跑通过。附注: 生产调用方未传 fallback_mtime=False,严格模式休眠可用(见 §1 verified 详注)。
5. **B2+B3: PASS(附 Issue 05)**。B2 主路径日期与实际产物同源;--skip-generate 残余二次扫描披露准确(build_site 不回传所选产物,改接口超出最小修复,B 认同该范围决策,风险为秒级窗口内 mtime 变动的理论错配)。B3 resolve() 后 relative_to 不抛 ValueError,防御断言恒真属显式失败点,A 披露无害,B 认同。
6. **测试真实性: PASS**。B 复跑 run_tests.py → `Ran 69 tests in 0.535s / OK`(discover 7+31+27+4),test_publish_chain.py 单独 → `Ran 27 tests / OK`,与附录 6.1/6.2 一致。父提交(009cf3b^)test_publish_chain 为 20 测试 → 27,净增 7 与 62→69 差额吻合;新测试清单核实: L230/L240/L375/L382/L420/L477/L493 为新增,L368 为既有测试改写(A §3 表述准确;附录 6.2 加粗把 L368 计入'新增/改写 7 个'而漏标 L240,排版级小误,见 Issue 04)。mock 夹具 _run_no_change_publish(L313-354)的 fake_capture 分支映射与生产 L559-561/L589-590 的命令模式仍一一对应,锁定关系未失效。CHANGELOG/commit message 对新增测试为概括性列举('fallback 严格语义'涵盖两向测试),数量一致,无实质出入。

### 2.3 5 层自检证据复核

| 层 | A 声称 | B 复核 | verified |
|---|---|---|---|
| 1 | 文件边界 ✅ | tag 经 `git rev-parse` 验证指向 009cf3b;`git show 009cf3b --stat=250` 完整路径 5 文件与 changed_files 逐条一致(任务指定第 9 项;默认宽度截断现象属实,见下) | ✅ |
| 2 | 端到端穿行 ✅ | B 复跑 69/69 OK,输出含真实 Git 段与 build-only/no-push 新分支打印,与 6.1 吻合 | ✅ |
| 3 | 门禁有效性 ✅ | QC 旧产物保护由 B 代码评审+异常路径推演证实;v26 §5.1 故障场景由 B 独立实 Git 演练复现修复 | ✅ |
| 4 | 修复前后对照 ✅ | A3: 修复前 fatal src refspec(v26 §5.1 实录)→ B 演练零 push 成功;B1: 修复前静默回退 → 现 raise 含候选清单 | ✅ |
| 5 | 回归 ✅ | 62→69 差额 7 与新测试清单一一对应;场景1/2 断言保留、场景3 按新语义改写(旧断言即 v26 判定缺陷) | ✅ |

**A 披露 4 点边界逐项评估**(任务指定第 7 项):

| 披露点 | B 评估 | 处置 |
|---|---|---|
| (1) V6 长文件名截断假阳性 | 现象真实: B 实测 `git show 009cf3b --stat` 截断 55 字符路径为 `...-` 前缀,`--stat=250` 恢复完整且与 frontmatter 一致;tag 后提交 98689ac 已将 audit_validate.py L209 改为 `--stat=250` 修复。校验器工具边界,非本 slug 声明错误 | 留档(已修复,无需 Issue) |
| (2) QC 测试为逻辑复刻 | 属实,复刻与 main 当前实现一致但无漂移防护 | Issue 02(WARNING,条件 C2) |
| (3) no-push 悬空 commit 对象 | 与代码一致,B 实 Git 演练证实 refs/HEAD/工作区三项不变、对象不进任何 ref;v26 字面标准满足,披露超出字面诚实 | 留档(无 Issue) |
| (4) push 失败子场景未覆盖 | 属实,update-ref 不执行仅由代码顺序保证,无测试锁定 | Issue 01(WARNING,条件 C1) |

## 3. 代码质量审查

### 3.1 CRITICAL(功能等价性 / 数据完整性)

无 CRITICAL Issue。检查范围: tag 快照 gen_integrated_dashboard.py 全量写路径、deploy_github_pages.py 的 latest_by_name_date/build_site/publish_to_pages/main 主链、test_publish_chain.py 全部 27 测试、CHANGELOG 与 commit message 一致性、B 独立真实 Git 演练 5 场景(无本地分支×无变化/有变化+no-push/有变化+build-only/stale-ref/正常发布+update-ref 对齐)。

### 3.2 WARNING(文档一致性 / 接口兼容性)

- **Issue 01**(REV-...-01): 真实 Git 矩阵 1/6,push 失败零覆盖——v26 验收标准第 3 条部分达标的核心原因。
- **Issue 02**(REV-...-02): QC 保旧测试为逻辑复刻非端到端,存在实现漂移盲区。

### 3.3 INFO(改进建议)

- **Issue 03**(REV-...-03): 无变化 else 分支接线内不可达+文案沿袭旧语义。
- **Issue 04**(REV-...-04): 附录 6.1(d) fatal stderr 归因错误(真实来源为生产代码 show-ref --verify 的预期 stderr 直通,B 以无 mock 单独运行证实);附录 6.2 加粗排版小误。
- **Issue 05**(REV-...-05): B2 --skip-generate 双扫描残余 + B3 目录白名单未做,登记后续增强。

## 4. 下一轮指引

Verdict 为 APPROVED_WITH_CONDITIONS,可进入 Agent C 归档流程;4 项 conditions(真实 Git 矩阵补全 / QC 测试端到端化 / stderr 归因勘误 / 双扫描与白名单留档)建议归入下一个专项 slug 或常规迭代,不消耗本轮轮次。Issue 01/02 为 WARNING 不阻断,但 C 归档时应在 audit_escape_risks 中登记: "QC 原子替换与 push 失败路径的保障当前依赖代码评审+逻辑复刻测试,端到端锁定待补"。
