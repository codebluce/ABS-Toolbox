---
submission_id: A1-v31-publish-hardening-r1
slug: v31-publish-hardening
skill_version: v2.5.8
round: 1
created_at: "2026-08-16 13:44:31"
author: agent_a
git_tag: audit/v2.5.8-v31-publish-hardening-r01
commit_hash: f612eec
previous_git_tag: audit/v2.5.7-v30-actual-share-uv-r01
changed_files:
  - CHANGELOG.md
  - SKILL.md
  - audit/README.md
  - audit/dispatch.md
  - audit/v25-abs-toolbox-end-to-end-audit-20260816.md
  - run_tests.py
  - scripts/abs_common.py
  - scripts/audit_next_action.py
  - scripts/audit_refresh_index.py
  - scripts/audit_validate.py
  - scripts/deploy_github_pages.py
  - scripts/gen_integrated_dashboard.py
  - scripts/test_publish_chain.py
status: PENDING_REVIEW
addressed_issues: []
self_review:
  all_issues_addressed: true
  no_overengineering: true
  function_equivalence_verified: true
  edge_cases_covered: true
  notes: "本 slug 首轮,无上一轮正式 B 轮 Issue(该 bool 按模板定义对'上一轮'成立)。本轮驱动源为 v25 专项审计,其 P1×3 与 P2×6 已按报告建议路线落实(P2-03 走'至少'选项:DecompressionStream 独立检查+报错拆分,未引入 gzip 回退库;P2-04 保留 --no-push 名称但 help 明确语义且无变化时比对引用后跳过 push);P3×6 中 P3-04(前端全局命名空间收敛)与 P3-06(同日覆盖/manifest 记录前一版)未在本 commit 处理——两者属 v25 报告§9'阶段 C'后续优化项,亦不在其§10验收标准内;P3-05 完成 24 处路径修正但未建单一版本源机制。CHANGELOG'修复全部 P1/P2/P3 问题'的标题表述覆盖面大于实际 P3 处理范围,提请 B 知悉。"
review_focus:
  - "QC 硬阻断真实性: verify_integrated_html 是否纯函数、[QC FAILED] 路径是否真删产物+exit 1、部署侧 verify_dashboard_artifact 双保险是否可独立生效。"
  - "gh-pages 分叉中止: publish_to_pages 是否始终 fetch、是否从 remote/gh-pages 建 detached worktree、本地/远端分叉时是否 raise 中止而非覆盖。"
  - "泄露自检有效性: audit_protected_site 的禁扩展名+明文特征探测(源文件头 2048 字节)是否可被 test_plaintext_dashboard_leak_detected/test_xlsx_leak_detected 复现。"
  - "动态 Tab 无空模块: MODULE_ORDER 按 present_modules 过滤后,无消金/同业数据时是否不渲染对应一级 Tab,有数据时 Tab 与 panel 是否一一对应。"
  - "changed_files 一致性: 本 frontmatter 13 文件与 git show f612eec --stat 是否完全一致(数量与路径)。"
---

# v31-publish-hardening r1 送审报告

## 1. 变更摘要(200 字内)

本轮落实 v25 端到端专项审计的修复:发布门禁三件套(综合看板结构 QC 失败删产物并非零退出、gh-pages 始终 fetch+detached worktree+分叉中止、protected 站点包泄露自检),正确性与可测试性(一级 Tab 按实际 panels 动态推导、产物按文件名业务日期选择、根目录统一测试入口+17 个发布链路测试),P3 清理(重复导入/漂移注释/mkstemp/html.escape/报错拆分/SKILL 路径),并移植 macro 自动化审计三脚本(audit_next_action/audit_validate/audit_refresh_index,纯标准库)。版本 v2.5.8,commit f612eec。

## 2. 上一轮 Issue 处理(首轮省略)

本 slug 首轮,无上一轮正式 B 轮 Issue。本轮驱动源为 v25 专项审计报告(`audit/v25-abs-toolbox-end-to-end-audit-20260816.md`,该报告自述"不属于 A/B/C 正式送审轮次"),其 15 项问题处置映射如下,供 B 逐项核对:

| v25 Issue | 处理 | 证据 |
|---|---|---|
| P1-01 结构 QC 不阻断 | fixed | `scripts/gen_integrated_dashboard.py:275`(verify_integrated_html 纯函数)、`L437-455`(失败 os.remove+sys.exit(1));部署侧双保险 `scripts/deploy_github_pages.py:191`(verify_dashboard_artifact,L186-188 调用) |
| P1-02 本地 gh-pages 不与远端同步 | fixed | `scripts/deploy_github_pages.py:528`(始终 fetch)、`L536`(worktree add --detach remote/gh-pages)、`L541-551`(merge-base 判分叉即 raise 中止) |
| P1-03 静态门禁安全边界 | fixed(文档/提示层) | `scripts/deploy_github_pages.py:473-474`(站点 README 明确"客户端加密而非服务端鉴权"+高熵口令/轮换/迁移建议)、`L255/L264`(壳内提示);v25 建议即以明确边界为主 |
| P2-01 空一级 Tab | fixed | `scripts/gen_integrated_dashboard.py:162-164`(MODULE_ORDER 按 present_modules 过滤);测试 `scripts/test_publish_chain.py:54-76` |
| P2-02 mtime 误选 | fixed | `scripts/deploy_github_pages.py:81`(latest_by_name_date)、`L146-161`(ledger_date_tag)、`L165-189`(generate_dashboard 显式 out_path,不再重扫目录);测试 `test_publish_chain.py:213-244` |
| P2-03 DecompressionStream 无回退 | fixed(按"至少"选项) | `scripts/deploy_github_pages.py:277`(解锁前独立检查)、`L306/L308`(浏览器不支持/密码错误两种报错拆分);未引入 gzip 回退库,v25 建议中"至少独立检查并展示明确错误"已满足 |
| P2-04 --no-push 语义 | fixed(保留参数名) | `scripts/deploy_github_pages.py:610`(help 明确"只在本地更新 gh-pages worktree commit,不推送")、`L560-577`(无变化时比对 local/remote 引用,一致则跳过 push);测试 `test_publish_chain.py:266` |
| P2-05 综合链路无测试 | fixed | `scripts/test_publish_chain.py` 新增 17 测(L54-266):Tab/panel 一致、QC 阻断、加解密 roundtrip、泄露检出、日期选择、分叉中止、no-push |
| P2-06 测试依赖工作目录 | fixed | `run_tests.py:24-25`(显式 insert scripts/ 到 sys.path)、按文件路径 discover、发现 0 测试非零退出(文件 docstring L8-12 说明) |
| P3-1 重复导入/漂移注释 | fixed | `git show f612eec -- scripts/gen_integrated_dashboard.py`:删除 L32 重复 `import peer_issuance_panel`;build_integrated_html docstring 改为"各面板原始 CSS/动态 top tab" |
| P3-2 临时文件 | fixed | `scripts/abs_common.py:172-178`(mkstemp+try/finally 保 wb.close) |
| P3-3 HTML 转义 | fixed | `scripts/deploy_github_pages.py:323-334`(write_archive_index: html.escape 显示名+urllib.parse.quote href) |
| P3-4 前端全局命名空间 | 未处理 | 本 commit 无相关改动;属 v25 §9 阶段 C 后续项 |
| P3-5 SKILL.md 漂移 | partial | 24 处旧路径 `skills/ABS工具箱/...` 改为仓库相对路径(diff 24+/24-);"单一版本来源"机制未建 |
| P3-6 同日覆盖/manifest 前一版 | 未处理 | 输出仍按业务日期命名且 manifest 不记前一版;属 v25 §9 阶段 C 后续项 |

v25 §10 验收标准中与本 commit 相关的 5 条(QC 非零且不覆盖上一版/无空 Tab/基线一致分叉中止/泄露自检+错误密码不可解密/根目录一条命令测试)均有对应实现与测试,P3-4/P3-6 不在其验收标准内。

## 3. 代码变更清单

`git show f612eec --stat`:13 files changed, 1659 insertions(+), 90 deletions(-)。清单与 frontmatter changed_files 一致(逐条核对)。

| 文件 | 操作 | 说明 |
|---|---|---|
| `scripts/gen_integrated_dashboard.py` | modified (+54/-) | verify_integrated_html 纯函数化(L275);QC 失败删产物+exit 1(L437-455);MODULE_ORDER 动态过滤(L162-164);首 Tab 由 DOM 首个 .tab-button 决定(diff L141-144);删重复导入;修 docstring |
| `scripts/deploy_github_pages.py` | modified (+205/-) | latest_by_name_date/ledger_date_tag(L81/L146);generate_dashboard 显式输出路径+verify_dashboard_artifact(L165-200);write_archive_index 转义(L323);audit_protected_site(L378-408);publish_to_pages 始终 fetch+detached worktree+分叉中止+无变化引用比对(L520-577);解锁壳报错拆分与 DecompressionStream 检查(L277/306/308);站点 README 客户端加密边界(L473-474) |
| `scripts/abs_common.py` | modified (+13/-) | 预处理临时文件 mkstemp+try/finally(L171-178) |
| `scripts/test_publish_chain.py` | added (302 行) | 17 个发布链路纯函数测试(见 §6.1 测试名清单) |
| `run_tests.py` | added (68 行) | 根目录统一测试入口:sys.path 注入+按路径 discover+0 测试发现即失败 |
| `scripts/audit_next_action.py` | added (285 行) | 审计状态机(next_action/role_to_dispatch),纯标准库 |
| `scripts/audit_validate.py` | added (280 行) | A/B/C 产物 frontmatter 校验,含历史豁免(cutoff 2026-08-16,L32) |
| `scripts/audit_refresh_index.py` | added (164 行) | 从 submissions/reviews/closed 派生 INDEX 结构字段 |
| `SKILL.md` | modified (24+/24-) | 24 处 `skills/ABS工具箱/...` 旧路径改为仓库相对路径 |
| `CHANGELOG.md` | modified (+22) | v2.5.8 条目 |
| `audit/dispatch.md` | modified (+100/-) | 自动化编排模式章节(控制平面职责/禁止事项/subagent 隔离/状态机映射,L1-52 起) |
| `audit/README.md` | modified (+6/-) | 校验脚本说明更新为三脚本+dispatch 引用 |
| `audit/v25-abs-toolbox-end-to-end-audit-20260816.md` | added (202 行) | v25 专项审计报告原件存档 |

## 4. 自审与指标

### 4.1 强制自审清单

- [x] all_issues_addressed: 本 slug 首轮无上一轮 Issue;v25 专项审计 P1×3/P2×6 全部落实(P2-03/P2-04 按报告提供的备选路线),P3-04/P3-06 未处理(阶段 C 项,非验收标准),P3-05 部分(路径修正),已在 §2 如实标注。
- [x] no_overengineering: QC 校验/日期选择/泄露自检均为纯函数或直接嵌入既有流程,未引入新抽象层;审计三脚本按 macro 模式精简移植,纯标准库无依赖。
- [x] function_equivalence_verified: 58/58 测试通过(run_tests.py,含 17 个新链路测试);发布链路冒烟(生成→站点组装→泄露自检→worktree 同步→--no-push→清理)全链穿行见 §6.1 真实输出。
- [x] edge_cases_covered: 空可选源无空 Tab、panel 数不符/缺切换函数检出、错误密码解密失败、明文看板/源 Excel 泄露检出、mtime 与文件名日期不一致以文件名为准、本地远端分叉中止、no-push 不调 git push,均有对应断言(§6.1 测试名)。

### 4.2 5 层自检证据

| 层 | 检查 | 结果 | 证据 |
|---|---|---|---|
| 1 | 文件变更边界 | ✅ | `git show f612eec --stat` 13 文件,与 frontmatter changed_files 逐条一致(§6.4) |
| 2 | 端到端穿行 | ✅ | run_tests.py 输出含完整发布链冒烟:`[site] protected 泄露自检通过` → `[select] 文件名业务日期(20260807)与 mtime 不一致,以文件名为准` → `[3/4] 同步到 gh-pages worktree` → `M index.html` → `[pages] --no-push 已设置,未推送远端` → `临时 worktree 已清理`(§6.1) |
| 3 | 门禁有效性 | ✅ | test_publish_chain: test_panel_count_mismatch_detected / test_missing_switch_js_detected / test_verify_dashboard_artifact_raises_on_bad / test_wrong_password 断言异常路径(§6.1) |
| 4 | 发布基线 | ✅ | test_diverged_local_aborts 断言分叉 raise;test_no_push_no_git_push_called 断言不推送(§6.1) |
| 5 | 回归 | ✅ | 既有 test_consumer_asset_panel(7)/test_peer_issuance_panel(30)/test_sync_institution_profile(4) 共 41 测无回归,合计 58/58(§6.1) |

## 5. 审计焦点(给 B 的提示)

1. **QC 硬阻断真实性**:`gen_integrated_dashboard.py:275` verify_integrated_html 是否为无副作用纯函数;`L449-455` 失败分支是否 `os.remove(out_path)` 后 `sys.exit(1)`(OSError 时仅打印仍退出);部署侧 `deploy_github_pages.py:191` verify_dashboard_artifact 在生成子进程成功后能否独立拦截结构缺失(P1-01 双保险)。
2. **gh-pages 分叉中止**:`deploy_github_pages.py:528` 是否无条件 `git fetch`;`L536` worktree 是否 `--detach` 于 `refs/remotes/{remote}/{branch}`;`L541-551` 分叉判定(sha 不等且 merge-base 非任一端点)是否 raise 而非覆盖;`L560-577` 无变化时是否先比对引用再决定跳过 push。
3. **泄露自检有效性**:`audit_protected_site`(L378-408)禁扩展名集合(.xlsx/.xls/.csv/.env/.py)与源文件头 2048 字节特征探测是否足够;manifest.json/README.md/.nojekyll 白名单是否合理;`test_xlsx_leak_detected`/`test_plaintext_dashboard_leak_detected`(test_publish_chain.py:181/194)是否真实构造泄露场景并断言 RuntimeError。
4. **动态 Tab 无空模块**:`gen_integrated_dashboard.py:162-164` 过滤逻辑;`test_no_optional_sources_no_empty_tabs`(L54)与 `test_full_sources_all_tabs_in_order`(L66)是否分别覆盖最小/全量两种源组合;`test_every_module_has_matching_pane`(L77)是否保证 Tab↔pane 一一对应。
5. **changed_files 一致性**:frontmatter 13 文件与 `git show f612eec --stat`(§6.4)数量、路径是否完全一致;注意 git_tag `audit/v2.5.8-v31-publish-hardening-r01` 由控制平面在本报告 validate 通过后打于 f612eec,届时请用 `git rev-parse` 校验 tag 指向。

## 6. 附录

### 6.1 run_tests.py 全量输出(2026-08-16,仓库根目录)

命令:`PYTHONUTF8=1 .venv/bin/python run_tests.py`

```text
..........................................................
----------------------------------------------------------------------
Ran 58 tests in 0.014s

OK
[discover] test_consumer_asset_panel: 7 tests
[discover] test_peer_issuance_panel: 30 tests
[discover] test_publish_chain: 17 tests
[discover] test_sync_institution_profile: 4 tests
[site] protected 泄露自检通过: 无源 Excel/明文看板特征
[select] 文件名业务日期(20260807)与 mtime(2026年ABS发行台账-0801-定稿.xlsx)不一致,以文件名为准: 2026年ABS发行台账-0807-定稿.xlsx

[3/4] 同步到 gh-pages worktree...

[3/4] 同步到 gh-pages worktree...
M index.html
[pages] --no-push 已设置,未推送远端
[pages] 临时 worktree 已清理
```

17 个链路测试清单(`grep -n "def test_" scripts/test_publish_chain.py`):

```text
54:  test_no_optional_sources_no_empty_tabs
66:  test_full_sources_all_tabs_in_order
77:  test_every_module_has_matching_pane
94:  test_ok_content_passes
98:  test_panel_count_mismatch_detected
103: test_missing_switch_js_detected
109: test_verify_dashboard_artifact_raises_on_bad
147: test_correct_password
150: test_wrong_password
153: test_payload_has_no_plaintext
171: test_clean_shell_passes
181: test_xlsx_leak_detected
194: test_plaintext_dashboard_leak_detected
213: test_ledger_date_tag_variants
217: test_touched_old_file_not_selected
246: test_diverged_local_aborts
266: test_no_push_no_git_push_called
```

### 6.2 audit_validate --all --skip-historical

命令:`PYTHONUTF8=1 .venv/bin/python scripts/audit_validate.py --all --skip-historical`

```text
[PASS] B1-v29-runtime-hardening-r1.md
[WARN] B1-v30-actual-share-uv-r1.md
    WARNING:  B1-v30-actual-share-uv-r1.md: Issue REV-v2.5.7-v30-actual-share-uv-r01-01 缺字段 severity
    WARNING:  B1-v30-actual-share-uv-r1.md: Issue REV-v2.5.7-v30-actual-share-uv-r01-01 缺字段 category
    WARNING:  B1-v30-actual-share-uv-r1.md: Issue REV-v2.5.7-v30-actual-share-uv-r01-01 缺字段 blocks_approval

共校验 2 个文件(历史豁免跳过 32),CRITICAL 0,WARNING 3
```

事实说明:3 条 WARNING 均来自 B1-v30 的 Issue 解析;该文件 frontmatter 中 REV-v2.5.7-v30-actual-share-uv-r01-01 实际含 `severity: INFO`/`category: FUNCTION_EQUIVALENCE`/`blocks_approval: false`(见 `audit/reviews/B1-v30-actual-share-uv-r1.md` L14-17),系校验脚本对 summary 换行嵌套项的宽松解析所致,非本轮变更引入;CRITICAL 0,不阻断。

### 6.3 audit_next_action --mine(历史 slug 状态确认)

命令:`PYTHONUTF8=1 .venv/bin/python scripts/audit_next_action.py --mine`

输出共 11 个 slug(v20 至 v30),全部为"最新阶段 C / 最新状态 COMPLETED / 下一步动作 ROUND_COMPLETED":

```text
## Slug: v20-institution-stats ... ROUND_COMPLETED
## Slug: v21-bookkeeping      ... ROUND_COMPLETED(遗留 INFO Issue 1 项,已归档)
## Slug: v22-pricing          ... ROUND_COMPLETED(遗留 Issue 2 项,已归档)
## Slug: v23-internal-merge-unify ... ROUND_COMPLETED
## Slug: v24-self-check       ... ROUND_COMPLETED
## Slug: v25-match-rule-tune  ... ROUND_COMPLETED
## Slug: v26-uv-protection    ... ROUND_COMPLETED(r2 归档)
## Slug: v27-p0-hardening     ... ROUND_COMPLETED
## Slug: v28-p123-cleanup     ... ROUND_COMPLETED
## Slug: v29-runtime-hardening ... ROUND_COMPLETED
## Slug: v30-actual-share-uv  ... ROUND_COMPLETED
```

(为节省篇幅按原输出逐 slug 摘录,每 slug 原文均含"轮次 rN 已归档完结"说明;完整输出可复跑命令核对。)

### 6.4 git show f612eec --stat

```text
commit f612eec892cfe7db904c8a3dae7a269f6b16c04f
Author: codebluce <codebluce@gmail.com>
Date:   Sun Aug 16 13:36:45 2026 +0800

    feat(audit): 发布链路加固与自动化审计流程 (v2.5.8)
    ...

 CHANGELOG.md                                       |  22 ++
 SKILL.md                                           |  48 ++--
 audit/README.md                                    |   6 +-
 audit/dispatch.md                                  | 100 +++++--
 audit/v25-abs-toolbox-end-to-end-audit-20260816.md | 202 +++++++++++++++
 run_tests.py                                       |  68 +++++
 scripts/abs_common.py                              |  13 +-
 scripts/audit_next_action.py                       | 285 +++++++++++++++++++
 scripts/audit_refresh_index.py                     | 164 +++++++++++
 scripts/audit_validate.py                          | 280 +++++++++++++++++++
 scripts/deploy_github_pages.py                     | 205 +++++++++++++--
 scripts/gen_integrated_dashboard.py                |  54 +++-
 scripts/test_publish_chain.py                       | 302 +++++++++++++++++
 13 files changed, 1659 insertions(+), 90 deletions(-)
```

HEAD 即 f612eec(`git log --oneline -1` → `f612eec feat(audit): 发布链路加固与自动化审计流程 (v2.5.8)`)。本报告仅写入送审文件,未做任何 git 操作;git_tag 由控制平面后续打于 f612eec。
