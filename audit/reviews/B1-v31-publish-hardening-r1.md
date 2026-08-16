---
review_id: B1-v31-publish-hardening-r1
submission_id: A1-v31-publish-hardening-r1
slug: v31-publish-hardening
skill_version: v2.5.8
round: 1
auditor: agent_b
created_at: "2026-08-16 13:55:21"

git_tag: audit/v2.5.8-v31-publish-hardening-r01
verified_tag_hash: f612eec

verdict: APPROVED_WITH_CONDITIONS

issues:
  - id: REV-v2.5.8-v31-publish-hardening-r01-01
    severity: WARNING
    category: DOC_CONSISTENCY
    blocks_approval: false
    summary: "CHANGELOG v2.5.8 '修复全部 P1/P2/P3 问题'表述超出实际处理范围(P3-04/P3-06 未处理、P3-05 部分完成)"
    evidence: "CHANGELOG.md L17 '修复 v25 端到端专项审计(NEEDS_REVISION)的全部 P1/P2/P3 问题:';实际:P3-04 无任何前端命名空间改动(TAB_JS 仅改 DOMContentLoaded 首屏激活,diff 无 selectSub 作用域收敛),P3-06 manifest 无前一版字段(deploy_github_pages.py L452-460 manifest dict 仅含 generatedAt/latest/archive 等,无 previous),P3-05 仅 24 处路径修正未建单一版本源。A 已在送审报告 §2/self_review notes 主动声明该差异,诚实性确认,该差异不影响 v25 §10 验收标准中与本 commit 相关的 5 条"
    suggested_fix: "下次触碰 CHANGELOG.md 时将'全部 P1/P2/P3'改为准确范围(如'P1×3/P2×6 全部,P3×6 中 3 项完成/1 项部分/2 项转入阶段 C')"
  - id: REV-v2.5.8-v31-publish-hardening-r01-02
    severity: WARNING
    category: DOC_CONSISTENCY
    blocks_approval: false
    summary: "audit_validate.py 模块 docstring 声明的 V6 检查(changed_files 与 git show <tag> --stat 对比)未实现"
    evidence: "tag 快照 scripts/audit_validate.py L14 docstring 'V6 A 文件 changed_files 与 git show <tag> --stat 对比(遗漏→WARNING)';grep 全文件无 'show'/'--stat' 调用,git() 仅用于 'tag -l'(L161/L164)与 'rev-parse'(L167),_validate_a(L180-194)无任何 changed_files 对比逻辑"
    suggested_fix: "实现 V6(解析 git show <tag> --stat 路径集与 frontmatter changed_files 求差,遗漏→WARNING),或从 docstring 删除 V6 条目"
  - id: REV-v2.5.8-v31-publish-hardening-r01-03
    severity: WARNING
    category: FUNCTION_EQUIVALENCE
    blocks_approval: false
    summary: "audit_validate.py parse_frontmatter 对 list-of-dict 多字段条目只保留首个键,后续字段被静默丢弃,对格式合规的 B 文件产生假 WARNING(--strict 下假失败)"
    evidence: "用 tag 快照解析 audit/reviews/B1-v30-actual-share-uv-r1.md 实测:issues 解析结果为 [{'id': 'REV-v2.5.7-v30-actual-share-uv-r01-01'}],severity/category/blocks_approval 全部丢失(该文件 L14-16 实际含 severity: INFO/category: FUNCTION_EQUIVALENCE/blocks_approval: false);根因在 parse_frontmatter L63-79:容器为非空 list 后,非列表项行既不升级为 dict 也无法附加到 list 条目,被 continue 丢弃。A §6.2 将原因归为'summary 换行嵌套项的宽松解析'不准确——severity 等单行字段同样丢失——但 A 已如实披露 WARNING 现象且该脚本非发布链路组件"
    suggested_fix: "解析器记录当前 list 条目指针,非列表项行且容器为 list-of-dict 时写入最后一个 entry;或 B 模板改为单行 issue 条目"
  - id: REV-v2.5.8-v31-publish-hardening-r01-04
    severity: INFO
    category: FUNCTION_EQUIVALENCE
    blocks_approval: false
    summary: "publish_to_pages 无变化且非 no_push 路径的引用比对分支(L562-577)无测试覆盖;其中本地无 gh-pages 分支的边缘组合会执行必然失败的 push"
    evidence: "scripts/test_publish_chain.py L246-298 仅覆盖分叉中止与有变化+no_push 两路;deploy_github_pages.py L568-571:has_local=False 时 local_sha_now='' 恒不等于 remote_sha_now → L576 push gh-pages:gh-pages 无本地分支必然报错(方向安全:run check=True 抛错中止,不会错误发布)"
    suggested_fix: "下轮补测:无变化+引用一致跳过 push、无变化+本地领先执行 push、无本地分支场景"

verified_issues: []

conditions:
  - "CHANGELOG '全部 P1/P2/P3' 措辞修正(REV-01)可在下次触碰 CHANGELOG 时顺带完成,无需单独送审"
  - "audit_validate.py 的 V6 实现与解析器 list-of-dict 修复(REV-02/03)建议并入下一 slug;修复前 --strict 模式的 WARNING 判读需人工复核"
  - "v25 §10 第 6 条验收项(浏览器性能预算)未在本 commit 范围内,A §2 以'与本 commit 相关的 5 条'表述已隐含排除,属 v25 §9 阶段 C 事项,留待后续阶段确认"
---

# v31-publish-hardening r1 审计意见

## 0. 总体结论

**Verdict**: APPROVED_WITH_CONDITIONS

A 声称的 5 项审计焦点经 git tag 快照逐项核实全部属实(5/5 PASS),测试 58/58 与 17/17 真实复跑通过,tag 指向 f612eec 校验一致;存在 3 个 WARNING + 1 个 INFO 的非阻断 Issue(CHANGELOG 措辞超范围、新校验脚本 docstring 与实现不符、解析器缺陷、一处测试盲区),均有明确修复方向,不影响本轮通过。

## 1. 上一轮 Issue 验证

本 slug 首轮,无上一轮 B 轮 Issue(verified_issues 为空)。驱动源 v25 专项审计的 15 项处置映射逐项核对见 §2.2/§3。

## 2. 需求合规审查

### 2.1 上一轮 Issue 全覆盖

首轮无上一轮 Issue。v25 专项审计(非正式 A/B/C 轮次)P1×3/P2×6 的 fixed 声明全部核实(见 §2.2 焦点 1-4 与 §3.3);P3-04/P3-06 未处理、P3-05 部分完成与 A 自述一致。

### 2.2 review_focus 回应(5 焦点逐项)

**焦点 1 — QC 硬阻断真实性: PASS**
- `verify_integrated_html` 纯函数属实: 快照 `gen_integrated_dashboard.py` L275-288,输入 `(content: str, expected_panel_count: int)` 返回问题列表,无 print/IO/文件操作。
- 失败路径属实: L437-455。L449 打印 `[QC FAILED]`;L450-452 `os.remove(out_path)` 删本次异常产物;L455 `sys.exit(1)` 位于 try/except 之外——OSError 删失败时仍非零退出(方向安全:部署侧 `run(check=True)` 会因退出码中止)。产物按业务日期命名(L175),删除失败也不会覆盖上一版文件。
- 预期 panel 数公式 L440 `8 + len(by_year) + consumer + peer` 与实际 append 逐一对账: pricing×4(L346-349)+机构画像×4(L350/357/360/367/370/391/394,wlz/credit/credit_total 异常路径也追加占位 panel,不漏计)+台账按年(L410-411)+消金(L377)+同业(L384),一致。
- 部署侧双保险属实: `deploy_github_pages.py` L186-188 生成子进程成功后再调 `verify_dashboard_artifact`(L191-202),独立检查 panel 容器/selectModule/selectSub 存在性,缺失即 raise RuntimeError;测试 `test_publish_chain.py` L109-118 用 `<html>empty</html>` 断言 RuntimeError。该函数未复用生成器代码,是真正独立的第二层(注:仅查存在性不查数量,比生成器 QC 弱,但作为兜底成立)。

**焦点 2 — publish_to_pages 加固: PASS**
- 始终 fetch: L528 `run(["git", "fetch", remote, branch])` 无条件执行,位于一切分支判断之前,check=True 失败即中止。
- detached worktree: L529-536 先 `show-ref --verify refs/remotes/{remote}/{branch}`,远端不存在即 raise;L550 `git worktree add --detach <tmp> refs/remotes/{remote}/{branch}`,基线取自远端引用而非本地分支。
- 分叉中止: L541-549,本地分支存在时取 local/remote/merge-base 三个 sha,`local != remote 且 base 非任一端点`即 raise"发布中止",不覆盖;本地落后(base==remote)或领先(base==local)均放行,提交路径 L589-591 `update-ref` 将本地分支对齐到基于远端的新提交,保持一致。
- 无变化先比对引用: L561-577,diff_status 为空时 no_push 直接跳过;否则先取 local/remote 引用,一致跳过 push,不一致才 push。与旧版(f612eec^ L403-409 无条件 push)对比确认为行为改进。
- 测试 `test_diverged_local_aborts`(test_publish_chain.py L246-264)mock 三条 capture 返回构造分叉,断言 RuntimeError 含"分叉",真实覆盖判定逻辑。

**焦点 3 — 泄露自检有效性: PASS**
- 检测逻辑真实有效: `audit_protected_site`(deploy L378-409)(a)禁扩展名 {.xlsx,.xls,.csv,.env,.py} 经 `rglob("*")` 递归扫描、`suffix.lower()` 大小写不敏感,命中记"敏感文件泄露";(b)明文特征两级探测:文件含 `<!DOCTYPE html>`(大写,源 HTML 特征;解锁壳是 `<!doctype html>` 小写,L235,天然不误报)且含源文件头 2048 字节连续片段才记"疑似明文看板泄露";manifest.json/README.md/.nojekyll 白名单。头部 2048 字节长片段对"整文件误拷"这一真实事故场景可靠。
- 3 个测试真实覆盖: `test_clean_shell_passes`(L171-179,壳不误报)、`test_xlsx_leak_detected`(L181-192,构造 data.xlsx 断言 RuntimeError"敏感文件")、`test_plaintext_dashboard_leak_detected`(L194-207,leaked.html 写入与源相同内容,断言 RuntimeError"明文看板")。
- 调用点 L446-447 在 protected 分支内、manifest/README 写入(L469/L490)之前执行——审计时 manifest 尚未生成,白名单实际为前向兼容设计,无漏检后果(见 §3.3 INFO 备注)。

**焦点 4 — 动态 Tab: PASS**
- L161-164: `MODULE_ORDER` 固定顺序 + `present_modules = {p[0] for p in panels}` + 列表推导过滤,无 panel 的模块不进 `MODULES`;L167-171 Tab 按钮、L177-207 子 Tab 容器与 panel div 均只遍历 `MODULES`。无消金/同业源时 `asset_overview`/`peer_issuance` 不在 present_modules,一级 Tab 确实不渲染。
- 首屏激活由 DOM 首个 `.tab-button` 决定(L141-144),对任意过滤后的模块集合稳健。
- 测试三覆盖: 最小源组合断言 tabs==[progress,ledger,pricing] 且 NotIn 两个可选模块(L54-64)、全量源断言完整顺序(L66-75)、Tab↔sub-tabs-pane 一一对应(L77-88)。
- 边界: 若 panels 出现 MODULE_ORDER 之外的未知模块 key,会被静默过滤,但渲染 panel 数将低于 QC 预期数而触发硬阻断,有兜底。

**焦点 5 — changed_files 一致性: PASS**
- `git show f612eec --stat` 实跑: 13 files changed, 1659 insertions(+), 90 deletions(-),文件集与 frontmatter changed_files 13 条逐条一致,无遗漏无多报;A §6.4 附录与实际输出一致。
- `git rev-parse audit/v2.5.8-v31-publish-hardening-r01` = f612eec892cfe7db904c8a3dae7a269f6b16c04f,与 frontmatter commit_hash 一致,tag 真实存在且指向正确。

### 2.3 5 层自检证据复核

| 层 | A 声称 | B 复核 | verified |
|---|---|---|---|
| 1 | diff 为空(13 文件一致) | `git show f612eec --stat` 逐条核对一致,1659+/90- 相符 | ✅ |
| 2 | 端到端穿行 | 本地复跑 run_tests.py 输出含 `[site] protected 泄露自检通过`/`[select] ...以文件名为准`/`M index.html`/`--no-push 未推送`/`worktree 已清理`,与 A §6.1 一致 | ✅ |
| 3 | 门禁有效性 | test_panel_count_mismatch_detected/test_missing_switch_js_detected/test_verify_dashboard_artifact_raises_on_bad/test_wrong_password 均为异常路径断言,代码核实(见焦点 1/3) | ✅ |
| 4 | 发布基线 | test_diverged_local_aborts 断言 raise;test_no_push_no_git_push_called 断言 pushes==[](mock 经 deploy_github_pages.run/capture/subprocess.run 三层替换,不触真实仓库,见 §3.3) | ✅ |
| 5 | 回归 | 本机实跑 `PYTHONUTF8=1 .venv/bin/python run_tests.py` → `Ran 58 tests ... OK`(7+30+17+4);`scripts/test_publish_chain.py` 单独跑 → `Ran 17 tests ... OK` | ✅ |

### 2.4 诚实性核查(任务第 6 项)

A 在 self_review notes 与 §2 主动声明: CHANGELOG"修复全部 P1/P2/P3"与实际有差异(P3-04/P3-06 未处理、P3-05 部分)。**该声明属实**: CHANGELOG L17 确写"全部",而 P3-04 在本 commit 无命名空间收敛改动、P3-06 的 manifest 无前一版字段、P3-05 仅 24 处路径替换(diff 中 `skills/ABS工具箱/` 旧路径 24-/24+ 实数核对相符)。核对 v25 报告: P3-04/P3-05/P3-06 均属 §9 阶段 C"性能与维护性"事项,不在 §10 六条验收标准前五条之内;第 6 条(浏览器性能预算)未实现,A 以"与本 commit 相关的 5 条"措辞界定范围,未虚报完成度。诚实行为予以确认,差异本身形成 REV-01(WARNING,不阻断)。

## 3. 代码质量审查

### 3.1 CRITICAL(功能等价性 / 数据完整性)

无 Issue。检查范围: 5 项焦点对应的全部代码路径(生成器 QC/Tab/panel 计数、部署 fetch/worktree/分叉/推送、加密 roundtrip、泄露自检、测试 mock 隔离),含与 f612eec^ 旧版逐段对比。

### 3.2 WARNING(文档一致性 / 接口兼容性)

| Issue | 摘要 |
|---|---|
| REV-v2.5.8-v31-publish-hardening-r01-01 | CHANGELOG"全部 P1/P2/P3"表述超出实际处理范围(A 已主动披露) |
| REV-v2.5.8-v31-publish-hardening-r01-02 | audit_validate.py docstring 声明的 V6 检查未实现 |
| REV-v2.5.8-v31-publish-hardening-r01-03 | audit_validate.py 解析器丢弃 list-of-dict 条目第 2 个及之后的字段,对合规 B 文件产生假 WARNING(实测复现);A §6.2 对成因的归因(-summary 换行所致)不准确,但现象已如实披露 |

三个 WARNING 均不阻断: REV-01 是措辞问题且已披露;REV-02/03 属新增审计工具自身缺陷,不影响发布链路功能,且该工具默认模式下 WARNING 不致失败。

### 3.3 INFO(改进建议)

- REV-v2.5.8-v31-publish-hardening-r01-04: publish_to_pages 无变化+非 no_push 的引用比对分支无测试;本地无 gh-pages 分支且无变化的组合会执行必然失败的 push(方向安全,中止而非错误发布)。
- 备注(不立 Issue): audit_protected_site 在 manifest.json/README.md 写入之前执行,docstring 第 3 条"manifest 中不得出现明文 HTML 文件本体"实际无对应显式检查——manifest 由 json.dumps 从受控 dict 生成,无法夹带 HTML,风险可忽略,但 docstring 与实现有轻微言过其实。
- mock 隔离核实(任务第 8 项): test_diverged_local_aborts/test_no_push_no_git_push_called 通过 `mock.patch("deploy_github_pages.run")`+`mock.patch("deploy_github_pages.capture")`+`mock.patch("subprocess.run")` 三层替换,git fetch/worktree add/commit/push 及 has_remote/has_local 探测均不触真实仓库;后者另 mock shutil.copytree/copy2/remove_worktree_contents,site 目录在 tempfile.TemporaryDirectory 中,测试隔离成立。

## 4. 下一轮指引

无需修改轮(NEEDS_REVISION 不适用)。通知 Agent C 归档,附带 conditions:
1. REV-01 CHANGELOG 措辞下次触碰时顺带修正,不需单独送审;
2. REV-02/REV-03(audit_validate 的 V6 实现与 list-of-dict 解析)建议并入下一 slug,修复前 `--strict` 的 WARNING 判读需人工复核;
3. v25 §10 第 6 条(浏览器性能预算)为阶段 C 遗留,后续阶段跟踪。

发布链路本体(QC 硬阻断/分叉中止/泄露自检/动态 Tab/去 mtime 化/统一测试入口)可进入受控发布使用。
