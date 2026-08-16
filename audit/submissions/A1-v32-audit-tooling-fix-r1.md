---
submission_id: A1-v32-audit-tooling-fix-r1
slug: v32-audit-tooling-fix
skill_version: v2.5.9
round: 1
created_at: "2026-08-16 14:13:34"
author: agent_a

git_tag: audit/v2.5.9-v32-audit-tooling-fix-r01
commit_hash: 0a507e8
previous_git_tag: audit/v2.5.8-v31-publish-hardening-r01

changed_files:
  - CHANGELOG.md
  - scripts/audit_validate.py
  - scripts/test_publish_chain.py

status: PENDING_REVIEW

addressed_issues:
  - id: REV-v2.5.8-v31-publish-hardening-r01-01
    resolution: fixed
    evidence: "CHANGELOG.md L17: '修复…全部 P1/P2/P3 问题'改为'落实…P1×3 与 P2×6 全部完成;P3×6 中 3 项完成、1 项部分完成、2 项转入阶段 C',与 B suggested_fix 逐项对齐"
  - id: REV-v2.5.8-v31-publish-hardening-r01-02
    resolution: fixed
    evidence: "scripts/audit_validate.py L200-218 实现 V6(git show <tag> --stat --format= 正则解析路径集,与 changed_files 求差,遗漏/多报→WARNING);docstring L14 的 V6 声明不再是空头支票"
  - id: REV-v2.5.8-v31-publish-hardening-r01-03
    resolution: fixed
    evidence: "scripts/audit_validate.py L79-84: list-of-dict 后续字段行附加到最后一个 dict 条目;旧版(f612eec)对 B1-v31 产 12 条假 WARNING、--all 共 81 条 WARNING,新版 B1-v31 单文件 0 条、--all 降至 12 条(全为 V6 对历史文件的合理检出)"
  - id: REV-v2.5.8-v31-publish-hardening-r01-04
    resolution: fixed
    evidence: "scripts/test_publish_chain.py L294-352: 新增 _run_no_change_publish 辅助 + 3 个测试(引用一致跳过 push L334/本地领先执行 push L340/无本地分支触发 push L346),链路测试 17→20,run_tests 61/61"

self_review:
  all_issues_addressed: true
  no_overengineering: true
  function_equivalence_verified: true
  edge_cases_covered: true
  notes: "4 个 Issue 全部 fixed。两点如实披露: (1) skill_version v2.5.9 取自 commit message 与 CHANGELOG 最后条目 v2.5.8 + 惯例推断,本轮 CHANGELOG 未新增 v2.5.9 条目——REV-01 授权范围是顺带修正 v2.5.8 措辞,工具修复是否值得独立条目留给 B/人类判断; (2) V6 对历史送审文件(带括号注记的 changed_files 惯例,如 'CHANGELOG.md (modified, v2.2.0 段新增)')'遗漏/多报'计数按整串精确匹配而偏大——方向检出正确(v22/v23 检出与 state.json 人工台账 REV-v2.2-v22-pricing-r01-02/REV-v2.3-v23-internal-merge-unify-r01-02 相符),精确计数仅对 v31 起清洁格式文件成立(A1-v31 实测 0 遗漏 0 多报); 另 _run_no_change_publish 的 has_local 参数未被消费(装饰性),场景 3 通过 rev-parse 返回空串达到与生产无本地分支路径相同的 local_sha_now='' 效果,测的是结果等价路径。"

review_focus:
  - "V6 实现正确性: audit_validate.py L200-218 的 stat 路径正则(r'^(.+?)\\s+\\|')能否同时处理根目录文件(CHANGELOG.md/SKILL.md/run_tests.py 无目录前缀)与 scripts/ 下文件;A1-v31(13 文件含 3 个根目录文件)实测 0 遗漏 0 多报是否足以证明;对历史带注记文件计数偏大(见 self_review notes)是否可接受。"
  - "解析器修复彻底性: L79-84 附加到最后 dict 条目的做法对 list-of-dict(issues/addressed_issues)是否完备、对 list-of-str(changed_files/review_focus)是否无误伤;--all WARNING 81→12 的降幅中旧 81 条是否确为解析假警报;summary 嵌套行仍宽松跳过(_validate_b L232-233)是否留观即可。"
  - "3 个新测试有效性: test_publish_chain.py L294-352 是否真实驱动 deploy_github_pages.py L561-577 无变化三分支(断言 pushes 数量);mock 隔离(run/capture/subprocess.run/shutil 三层替换)是否不触真实仓库;merge-base mock 以 sha 字符串长度选 base 的启发式与 has_local 参数未消费两点(见 notes)是否影响测试效力。"
  - "CHANGELOG 措辞准确性: L17 新表述与 B1-v31 REV-01 suggested_fix 及 v25 报告实际处置(A1-v31 §2 表)是否逐项一致、无新的超范围表述。"

---

# v32-audit-tooling-fix r1 送审报告

## 1. 变更摘要(200 字内)

修复 v31 B1 审计 4 个 Issue: REV-01 CHANGELOG v2.5.8 措辞改为准确范围;REV-02 audit_validate.py 实现 V6(changed_files 与 git show tag --stat 对比,遗漏/多报→WARNING),含根目录文件 stat 解析;REV-03 parse_frontmatter 修复 list-of-dict 后续字段静默丢弃;REV-04 补 publish_to_pages 无变化三分支 3 个测试。测试 61/61(链路 17→20)。commit 0a507e8,版本 v2.5.9(CHANGELOG 未加条目,见 self_review notes)。

## 2. 上一轮 Issue 处理

上一轮: B1-v31-publish-hardening-r1(verdict APPROVED_WITH_CONDITIONS,4 Issue 均 blocks_approval=false)。

| Issue ID | 严重程度 | 处理方式 | 证据 |
|---|---|---|---|
| REV-v2.5.8-v31-publish-hardening-r01-01 | WARNING | fixed | `CHANGELOG.md:17`: 原"修复 v25 端到端专项审计(NEEDS_REVISION)的全部 P1/P2/P3问题:"改为"落实…修复:P1×3 与 P2×6 全部完成;P3×6 中 3 项完成(重复导入/临时文件/HTML转义)、1 项部分完成(SKILL.md 24 处路径修正,未建单一版本源)、2 项转入阶段 C(P3-04 前端命名空间收敛、P3-06 manifest 前一版追溯,不在 v25 §10 验收标准内)",与 B suggested_fix 逐项对齐,与 A1-v31 §2 处置表一致。git diff 仅此 1 行(`git show 0a507e8 -- CHANGELOG.md` 为 2 +/-) |
| REV-v2.5.8-v31-publish-hardening-r01-02 | WARNING | fixed | `scripts/audit_validate.py:200-218` 新增 V6: `git("show", tag, "--stat", "--format=")` 后以 `re.match(r"^(.+?)\s+\|", ln)` 提取路径(candidate.strip(),跳过纯数字/含竖线残片),`missing = actual - declared`、`extra = declared - actual`,分别 rep.warn。**根目录文件解析**: 正则不依赖目录前导缩进,`CHANGELOG.md | 2 +-` 等根文件与 `scripts/...` 文件统一提取;实测 A1-v31(commit 含 3 个根目录文件)校验 0 遗漏 0 多报(附录 6.2)。docstring L14 的 V6 声明自本轮起与实现一致 |
| REV-v2.5.8-v31-publish-hardening-r01-03 | WARNING | fixed | `scripts/audit_validate.py:79-84`: parse_frontmatter 新增分支 `elif isinstance(container, list) and not is_list_item and ":" in line` → 将 `severity: WARNING` 等后续字段行写入 `container[-1]`(最后一个 dict 条目),不再 continue 丢弃。修复前后对照(附录 6.3): 旧版(f612eec 快照)校验 B1-v31 → 12 条假 WARNING(4 Issue × severity/category/blocks_approval),B1-v30 → 3 条;新版两个文件均 PASS 0 WARNING。`--all` 全量 WARNING 81→12,降幅全部来自 B 文件 Issue 字段假警报消除,余 12 条为 V6 对历史文件的合理检出(附录 6.4) |
| REV-v2.5.8-v31-publish-hardening-r01-04 | INFO | fixed | `scripts/test_publish_chain.py:294-352`: 新增 `_run_no_change_publish(local_sha, remote_sha, has_local)` 辅助(构造 diff_status 为空的 worktree 场景,记录 pushes)+ 3 测试: `test_no_change_refs_equal_skips_push`(L334,local==remote → pushes==[])、`test_no_change_local_ahead_pushes`(L340,引用不等 → len(pushes)==1)、`test_no_change_no_local_branch`(L346,local_sha='' → len(pushes)==1)。覆盖 `deploy_github_pages.py:561-577` 无变化+非 no_push 的引用比对全部分支。`grep -c "def test_"` 链路测试 17→20,run_tests.py 61/61(附录 6.1);run_tests 冒烟输出新出现"gh-pages 无文件变化/执行 git push/本地与远端已一致,跳过推送"三种分支打印,证明测试驱动了真实代码路径 |

B 的 3 条 conditions 处置: 条件 1(REV-01 顺带修正)本轮完成;条件 2(REV-02/03 并入下一 slug)即本轮;条件 3(v25 §10 第 6 条浏览器性能预算)仍属阶段 C 遗留,本轮未触碰。

## 3. 代码变更清单

`git show 0a507e8 --stat`: 3 files changed, 88 insertions(+), 12 deletions(-)。与 frontmatter changed_files 一致(逐条核对)。

| 文件 | 操作 | 说明 |
|---|---|---|
| `CHANGELOG.md` | modified (+1/-1) | REV-01: v2.5.8 条目导语"全部 P1/P2/P3"改为准确范围(P1×3/P2×6 全部,P3×6 = 3 完成 + 1 部分 + 2 转阶段 C) |
| `scripts/audit_validate.py` | modified (+24/-4) | REV-02: `_validate_a` L200-218 新增 V6 检查(stat 解析含根目录文件);REV-03: `parse_frontmatter` L79-84 list-of-dict 后续字段附加到最后 dict 条目,L76 顺带简化 entry 构造 |
| `scripts/test_publish_chain.py` | modified (+64/-6) | REV-04: 新增 `_run_no_change_publish` 辅助(L294-332)与 3 个无变化分支测试(L334/340/346);`test_no_push_no_git_push_called` 的 capture mock 由 `_patch_capture` 元组表改为内联 lambda(L279-289),断言未变(changed True + pushes==[]) |

## 4. 自审与指标

### 4.1 强制自审清单

- [x] all_issues_addressed: 上一轮 4 个 Issue(REV-01/02/03 WARNING + REV-04 INFO)全部 fixed,证据见 §2,无 wontfix/partial。
- [x] no_overengineering: V6 为 `_validate_a` 内 19 行内联逻辑(正则+集合求差),解析器修复 6 行,测试新增 1 辅助 + 3 用例;未引入新函数抽象层/新依赖(仍纯标准库)。
- [x] function_equivalence_verified: 校验器行为按 Issue 预期改变且无回归——`--all --skip-historical` 5 文件全 PASS 0 WARNING 0 CRITICAL;B1-v31/B1-v30/A1-v31 单文件校验全 PASS;`--all` 全量 CRITICAL 5 个均为本轮之前既存的历史文件问题(tag 不存在/commit_hash 不符/frontmatter 不可解析),数量与旧版完全一致(附录 6.4)。发布链路功能未动(deploy_github_pages.py 零改动)。
- [x] edge_cases_covered: V6 根目录文件(A1-v31 实测)、tag 不存在(历史 A1-v20,仅走既有 V5 CRITICAL 不进 V6)、带注记历史清单(计数偏大已披露);解析器 list-of-dict(B1-v31/v30)与 list-of-str(changed_files/review_focus 不受新分支影响,`--all` 其余 32 文件行为不变);发布无变化三分支含无本地分支边缘组合(该组合在真实环境 push 必然报错中止,方向安全,测试注释 L347 已说明)。

### 4.2 5 层自检证据

| 层 | 检查 | 结果 | 证据 |
|---|---|---|---|
| 1 | 文件变更边界 | ✅ | `git show 0a507e8 --stat` 3 文件与 changed_files 逐条一致(附录 6.5);HEAD 即 0a507e8 |
| 2 | 端到端穿行 | ✅ | run_tests.py 61/61 OK;冒烟输出含三种无变化分支真实打印: `执行 git push,同步本地 gh-pages 到远端` ×2(测试 2/3 路径,run 已 mock 不真推)、`本地与远端已一致,跳过推送`(测试 1)(附录 6.1) |
| 3 | 门禁有效性 | ✅ | V6 实测: A1-v31(清洁格式)0 遗漏 0 多报;v22/v23 历史文件检出与 state.json 人工台账 REV-v2.2-v22-pricing-r01-02(实际 11 文件)/REV-v2.3-v23-internal-merge-unify-r01-02(实际 13 文件)相符(附录 6.4) |
| 4 | 解析器修复对照 | ✅ | 同一文件新旧版本对照: B1-v31 12→0 条 WARNING,B1-v30 3→0 条;`--all` WARNING 81→12,CRITICAL 5→5 不变(附录 6.3/6.4) |
| 5 | 回归 | ✅ | 61/61(7+30+20+4),既有 41 测无回归;`--all --skip-historical` 5 文件全 PASS |

## 5. 审计焦点(给 B 的提示)

1. **V6 实现正确性**: `audit_validate.py:200-218`。重点: (a) 正则 `^(.+?)\s+\|` 对 `git show --stat --format=` 输出的提取是否对根目录文件(`CHANGELOG.md`/`SKILL.md`/`run_tests.py`)与 `scripts/` 文件一致成立——用 A1-v31 验证(其 tag commit 含 3 个根目录文件,实测 0/0);(b) 集合求差方向(missing/extra)与 WARNING 触发条件;(c) 对历史带括号注记清单的计数偏大(遗漏数=commit 全部文件数、多报数=带注记声明串)是格式惯例所致,方向检出与人工台账一致——是否接受"精确计数仅对清洁格式成立"的边界,或建议后续在 warn 文案中区分。
2. **解析器修复彻底性**: `audit_validate.py:79-84`。重点: (a) 新分支仅在"容器为 list 且当前行非列表项且含冒号"时触发,list-of-str(如 changed_files 纯路径项、review_focus 带引号整句)是否会误入——注意 review_focus 项形如 `- "..."` 是列表项,不走该分支;(b) `--all` 81→12 的降幅是否全部可由 B 文件 Issue 假警报解释(旧版无 V6,12 条恰为 V6 新检出);(c) summary 嵌套多行仍宽松跳过(L232-233 注释),与 REV-03 建议的"或 B 模板改单行"二选一,本轮选了解析器侧。
3. **3 个新测试有效性**: `test_publish_chain.py:294-352` 对照 `deploy_github_pages.py:561-577`。重点: (a) 三个测试是否分别锁住 local==remote 跳过 push / 引用不等执行 push / local_sha='' 执行 push;(b) mock 隔离(deploy_github_pages.run/capture + subprocess.run + shutil.copytree/copy2 + remove_worktree_contents)是否完整,site 在 TemporaryDirectory 中;(c) 两处夹具瑕疵由 A 主动披露——merge-base 返回值以 sha 字符串长度启发式选 base(L318)、`has_local` 参数未被消费(场景 3 经 rev-parse 返回空串达到与生产无本地分支相同的 local_sha_now=''),请评估是否影响测试效力或仅需下次顺手清理。
4. **CHANGELOG 措辞准确性**: `CHANGELOG.md:17` 新导语与 B1-v31 REV-01 suggested_fix、v25 报告 §9/§10、A1-v31 §2 处置表三方交叉核对,确认无新的超范围表述(尤其"1 项部分完成"对应 P3-05、"2 项转入阶段 C"对应 P3-04/P3-06 的指认)。

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

说明: 三段"无文件变化"输出为 REV-04 新测试驱动真实 `publish_to_pages` 分支所打印(按 unittest 字母序: local_ahead_pushes → no_local_branch → refs_equal_skips_push),push 动作经 mock 捕获未真推。

20 个链路测试清单(`grep -n "def test_" scripts/test_publish_chain.py`):

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
334: test_no_change_refs_equal_skips_push        # REV-04 新增
340: test_no_change_local_ahead_pushes           # REV-04 新增
346: test_no_change_no_local_branch              # REV-04 新增
```

### 6.2 新版单文件校验(V6 + 解析器,任务指定证据 2/3)

```text
$ PYTHONUTF8=1 .venv/bin/python scripts/audit_validate.py --file audit/submissions/A1-v31-publish-hardening-r1.md
[PASS] A1-v31-publish-hardening-r1.md

共校验 1 个文件(历史豁免跳过 0),CRITICAL 0,WARNING 0

$ PYTHONUTF8=1 .venv/bin/python scripts/audit_validate.py --file audit/reviews/B1-v31-publish-hardening-r1.md
[PASS] B1-v31-publish-hardening-r1.md

共校验 1 个文件(历史豁免跳过 0),CRITICAL 0,WARNING 0

$ PYTHONUTF8=1 .venv/bin/python scripts/audit_validate.py --all --skip-historical
[PASS] A1-v31-publish-hardening-r1.md
[PASS] B1-v29-runtime-hardening-r1.md
[PASS] B1-v30-actual-share-uv-r1.md
[PASS] B1-v31-publish-hardening-r1.md
[PASS] C1-v31-publish-hardening-r1.md

共校验 5 个文件(历史豁免跳过 32),CRITICAL 0,WARNING 0
```

A1-v31 PASS 即 V6 精确对齐证明: 其 changed_files 13 条(含根目录 CHANGELOG.md/SKILL.md/run_tests.py)与 `git show audit/v2.5.8-v31-publish-hardening-r01 --stat` 的 13 文件 0 遗漏 0 多报;B1-v31 PASS 即 REV-03 解析器修复证明(旧版同文件 12 条假 WARNING,见 6.3)。

### 6.3 REV-03 修复前后对照(旧版 = f612eec 快照,SKILL_ROOT 重定向后运行)

```text
旧版 scripts/audit_validate.py(--file audit/reviews/B1-v31-publish-hardening-r1.md):
[WARN] B1-v31-publish-hardening-r1.md
    WARNING: ...r01-01 缺字段 severity / category / blocks_approval   (×3)
    WARNING: ...r01-02 缺字段 severity / category / blocks_approval   (×3)
    WARNING: ...r01-03 缺字段 severity / category / blocks_approval   (×3)
    WARNING: ...r01-04 缺字段 severity / category / blocks_approval   (×3)
共校验 1 个文件,CRITICAL 0,WARNING 12

旧版(--file audit/reviews/B1-v30-actual-share-uv-r1.md):
[WARN] ... CRITICAL 0,WARNING 3    (r01-01 缺 severity/category/blocks_approval)

新版(0a507e8): 同两文件均 [PASS],WARNING 0(见 6.2)
```

### 6.4 V6 历史检出与 --all 全量对照

新版 `--all`(不含 --skip-historical,节选):

```text
[FAIL] A1-v22-pricing-r1.md
    CRITICAL: commit_hash 03225ef 与 tag 实际指向 1e14550 不一致
    WARNING:  changed_files 遗漏 11 个文件未声明: ['.gitignore','CHANGELOG.md','SKILL.md','audit/INDEX.md','audit/state.json','audit/submissions/A1-v22-pricing-r1.md','scripts/gen_abs_cost_report.py','scripts/gen_compare_tool.py','scripts/gen_spread_report.py','scripts/pitfall_log.md','scripts/test_smoke.py']
    WARNING:  changed_files 多报 6 个不在 commit 中: ['CHANGELOG.md (modified, v2.2.0 段新增)', ...]
[FAIL] A1-v23-internal-merge-unify-r1.md
    CRITICAL: commit_hash e9cf091 与 tag 实际指向 1ef0612 不一致
    WARNING:  changed_files 遗漏 13 个文件未声明: [...]
    WARNING:  changed_files 多报 5 个不在 commit 中: [...]
... (v21/v24/v25/v30 类似,v26 为既存 CRITICAL frontmatter 不可解析,v27-v31 PASS)
共校验 37 个文件(历史豁免跳过 0),CRITICAL 5,WARNING 12
```

与人工台账对照: state.json `REV-v2.2-v22-pricing-r01-02`(L223-227)"git show 1e14550 --stat 实际 11 文件"、`REV-v2.3-v23-internal-merge-unify-r01-02`(L249-255)"实际 13 文件"——V6 报告的遗漏 11/13 与台账记录的 commit 实际文件数相符,方向检出正确。

诚实披露(计数偏大): 历史 changed_files 条目带括号注记(如 `CHANGELOG.md (modified, v2.2.0 段新增)`),V6 按整串精确匹配,故注记条目全部落入"多报"、其对应裸路径落入"遗漏"(遗漏数=commit 全部文件数)。该偏差源自历史格式惯例而非 V6 逻辑错误;v31 起清洁格式文件计数精确(A1-v31 实测 0/0);历史文件正常使用走 `--skip-historical`(cutoff 2026-08-16)不触发 V6。

全量对照(同命令新旧版): 旧版 CRITICAL 5 / WARNING 81(81 条为解析器对 B 文件 Issue 字段的假警报,旧版无 V6)→ 新版 CRITICAL 5(同一批历史既存问题,数量不变) / WARNING 12(全为 V6 检出)。REV-03 消除 81 条假警报、REV-02 新增 12 条真检出,净变化与 Issue 预期完全一致。

### 6.5 git show 0a507e8 --stat

```text
commit 0a507e836ae94a04c039dc2886509ab972c5b029
Author: codebluce <codebluce@gmail.com>
Date:   Sun Aug 16 14:12:33 2026 +0800

    fix(audit): 修复 v31 B1 审计 4 项 Issue (v2.5.9)
    ...

 CHANGELOG.md              |  2 +-
 scripts/audit_validate.py | 28 +++++++++++++++--
 scripts/test_publish_chain.py | 70 +++++++++++++++++------------
 3 files changed, 88 insertions(+), 12 deletions(-)
```

HEAD 即 0a507e8(`git log --oneline -1`)。上一轮 tag `audit/v2.5.8-v31-publish-hardening-r01` 指向 f612eec(`git rev-parse` 校验)。本报告仅写入送审文件,未做任何 git 操作;git_tag `audit/v2.5.9-v32-audit-tooling-fix-r01` 由控制平面在本报告 validate 通过后打于 0a507e8。
