---
submission_id: A2-v26-uv-protection-r2
slug: v26-uv-protection
skill_version: v2.5.1
round: 2
created_at: "2026-07-18 16:40:00"
author: agent_a
git_tag: audit/v2.5.1-v26-uv-protection-r02
commit_hash: 3d5335a
previous_git_tag: audit/v2.5.1-v26-uv-protection-r01
changed_files:
  - scripts/increment_merge.py
  - CHANGELOG.md
  - audit/submissions/A1-v26-uv-protection-r1.md
status: PENDING_REVIEW
addressed_issues:
  - id: REV-v2.5.1-v26-uv-protection-r01-01
    resolution: fixed
    evidence: "scripts/increment_merge.py:L1326-1331(L1328 tempfile.mkstemp → L1330 wb_a.save(tmp_path) 先写临时文件)+L1421-1424(run_enhanced_qc)+L1427-1437(qc_fails>0 时 os.remove(tmp_path)+close_workbook+return [BLOCKED])+L1444(QC PASS 后 os.replace(tmp_path, output_path))。save 已从 QC 前(r1 L1272)移到临时文件,QC PASS 后才 replace 到正式输出,FAIL 时删除临时文件不落盘。"
  - id: REV-v2.5.1-v26-uv-protection-r01-02
    resolution: fixed
    evidence: "本 A2 changed_files 已补记送审报告自身(A1-v26-uv-protection-r1.md +1 行,3d5335a stat 实际 3 文件:increment_merge.py+CHANGELOG.md+A1 报告)。与 v25 REV-01 同类,送审报告入 commit 属惯例。"
  - id: REV-v2.5.1-v26-uv-protection-r01-03
    resolution: fixed
    evidence: "scripts/increment_merge.py:L795-799(QC 7.20 注释 v2.5.1 REV-03 改用 项目名+分层+机构 匹配键,不再用行号直接对比)+L803(target_project_names 用项目名做豁免)+L805-821(collect_uv_multiset 用 Counter 多重集 (项目名,分层,机构,V))+L823-834(orig_ms/out_ms 多重集差集,orig独有=丢失篡改/out独有=新增篡改)。rebook 删行后行号不对齐问题已用项目名匹配键彻底规避;同机构多笔认购 key 冲突由 Counter 多重集解决(详见 §2 修复链说明)。"
self_review:
  all_issues_addressed: true
  no_overengineering: true
  function_equivalence_verified: true
  edge_cases_covered: true
  notes: "r2 修复实际跨两个 commit:3d5335a(REV-01/02/03 初修,QC 7.20 用 dict 项目名匹配键)+ fc5ae99(v2.5.2 修复 3d5335a 引入的 #ABS-004 回归:dict 遍历崩溃+同机构多笔认购 key 冲突误报,改用 Counter 多重集)。r02 tag 指向 3d5335a(已双推),但运行核查基线建议用 fc5ae99 或当前 HEAD(已含 Counter 最终修复)。后续 v27(c9c2626)/v29(1ed4874)对同一 QC 阻断区域叠加 close_workbook/save_workbook_atomic 加固,属独立 slug 范畴,不纳入本轮 r2 审计范围但进一步降低了资源泄漏风险。"
review_focus:
  - "核查 REV-01(tmp+os.replace 真阻断):scripts/increment_merge.py:L1326-1331 临时文件保存、L1427-1437 FAIL 删 tmp+return、L1444 PASS 后 os.replace。确认 FAIL 时正式 output_path 不被写入。"
  - "核查 REV-03(QC 7.20 匹配键):L799-844 用 (项目名,分层,机构,V) Counter 多重集,不再用行号直接对比。确认 rebook 删行后 ws_orig_protected vs ws_out 行号不对齐不再导致误判/漏判。"
  - "运行核查基线:r02 tag→3d5335a 含 #ABS-004 回归(dict 遍历崩溃),真跑台账会崩。B 审计端到端核查请基于 fc5ae99 或当前 HEAD(已含 Counter 修复),3d5335a 仅作 REV-01/02/03 代码逻辑核查基线。"
  - "核查 #ABS-004 回归已闭环:fc5ae99 CHANGELOG v2.5.2 段记录 0706 台账+东裕4号续发簿记录入 QC 7.1/7.2/7.3/7.20 全 PASS。"
---

# v26-uv-protection r2 送审报告

## 1. 变更摘要(200 字内)

本轮为 v26 r1(NEEDS_REVISION)的 A-fix 修复轮,处理 B1 的 3 个 Issue:REV-01(CRITICAL,QC FAIL 阻断无效,save 在 QC 前)改 tmp+os.replace 真阻断;REV-02(WARNING,changed_files 遗漏送审报告)补记;REV-03(WARNING,rebook 行号对齐风险)QC 7.20 改用 (项目名,分层,机构,V) 匹配键。修复实际跨 3d5335a(REV-01/02/03)+fc5ae99(#ABS-004 回归+Counter 最终修复)两 commit。

## 2. 上一轮 Issue 处理

| Issue ID | 严重程度 | 处理方式 | 证据 |
|---|---|---|---|
| REV-v2.5.1-v26-uv-protection-r01-01 | CRITICAL | fixed | increment_merge.py:L1326-1331(tmpfile+save)+L1427-1437(FAIL 删 tmp+return)+L1444(PASS os.replace)。save 已移到 QC 后,FAIL 阻断真生效 |
| REV-v2.5.1-v26-uv-protection-r01-02 | WARNING | fixed | 本 A2 changed_files 补记 A1 报告自身(3d5335a stat 3 文件含 A1-v26-uv-protection-r1.md) |
| REV-v2.5.1-v26-uv-protection-r01-03 | WARNING | fixed | increment_merge.py:L799-844 QC 7.20 改用 (项目名,分层,机构,V) Counter 多重集,不再用行号对比 |

### 2.1 r2 修复链如实披露(重要)

r02 tag 指向 `3d5335a`,但 r2 的完整修复实际跨两个 commit:

| commit | 内容 | 对应 Issue |
|---|---|---|
| `3d5335a`(r02 tag) | REV-01 save 移到 QC 后(tmp+rename)+ REV-02 changed_files 补记 + REV-03 QC 7.20 改 dict 项目名匹配键 | REV-01/02/03 初修 |
| `fc5ae99`(v2.5.2) | 修复 3d5335a 引入的 #ABS-004 回归:①dict 遍历崩溃(get_all_projects 返回 dict 误按三元组解包)②同机构多笔认购 key 冲突误报(东裕3-10/优先A 交银理财 V=2.7 和 V=0.25 dict 覆盖)。改用 Counter 多重集 (项目名,分层,机构,V) | REV-03 完整修复 + #ABS-004 回归闭环 |

**说明**:r02 tag 已双推不可变,指向 `3d5335a`。`3d5335a` 修复了 B1 的 3 个 Issue,但其 QC 7.20 用 dict 是 REV-03 的"中间修复态"(解决了行号对齐,但引入 key 冲突)。`fc5ae99` 才是 REV-03 的"最终修复态"(Counter 多重集)。B 审计端到端核查请基于 `fc5ae99` 或当前 HEAD(已含 Counter 修复),`3d5335a` 仅作 REV-01/02/03 代码逻辑核查基线(真跑台账会触发 #ABS-004 崩溃)。

后续 v27(`c9c2626`)/v29(`1ed4874`)对同一 QC 阻断区域叠加 `close_workbook`/`save_workbook_atomic` 加固,属独立 slug 范畴,不纳入本轮 r2 审计范围,但进一步降低了资源泄漏风险(已在 v27/v29 各自 C1 归档)。

## 3. 代码变更清单

| 文件 | 操作 | 说明 |
|---|---|---|
| `scripts/increment_merge.py` | modified | REV-01:save 从 QC 前(L1272)移到临时文件,QC PASS 后 os.replace,FAIL 时 os.remove;REV-03:QC 7.20 改 (项目名,分层,机构,V) Counter 多重集。3d5335a +87/-28 行,fc5ae99 +80/-43 行(Counter 重构) |
| `CHANGELOG.md` | modified | 3d5335a 补 v2.5.1 r1 修复记录;fc5ae99 新增 v2.5.2 段(#ABS-004 回归修复+验证) |
| `audit/submissions/A1-v26-uv-protection-r1.md` | modified | REV-02:3d5335a 补记送审报告自身入 commit(+1 行) |

## 4. 自审与指标

### 4.1 强制自审清单

- [x] all_issues_addressed: B1 的 1 CRITICAL(REV-01)+ 2 WARNING(REV-02/03)全部 fixed,提供当前 HEAD 代码行号证据。
- [x] no_overengineering: 仅改 QC 阻断架构(tmp+os.replace)和 QC 7.20 匹配键(行号→项目名→Counter),无多余抽象。
- [x] function_equivalence_verified: py_compile 通过;fc5ae99 端到端验证(0706台账+东裕4号续发)QC 7.1/7.2/7.3/7.20 全 PASS。
- [x] edge_cases_covered: 覆盖 QC FAIL 阻断不落盘、rebook 删行后行号不对齐、同机构多笔认购 key 冲突(东裕3-10/优先A 交银理财 V=2.7+0.25)。

### 4.2 5 层自检证据

| 层 | 检查 | 结果 | 证据 |
|---|---|---|---|
| 1 | 文件字节对比 | ✅ | git show 3d5335a --stat:3 文件(increment_merge.py+CHANGELOG+A1);git show fc5ae99 --stat:4 文件(increment_merge.py+CHANGELOG+pitfall_log+.gitignore)。r2 修复链合计改动 increment_merge.py 两轮(+87/-28 再 +80/-43) |
| 2 | 端到端穿行 | ✅ | fc5ae99 commit message 记录:0706 台账增量合并+东裕4号续发簿记录入,QC 7.1(WXY_Y=21.9=detail 21.9 diff=0)/7.2(114项目全保留)/7.3(东裕4号 rows 1900-1920)/7.20(非目标 UV 保留 PASS)全 PASS,Fails=0 Warns=3(已知数据问题) |
| 3 | 逐 cell diff | SKIP | 本轮为 bugfix 非原样迁入,5 层自检不强制(v26 r1 惯例);功能等价性由层 2 端到端 QC PASS 保证 |
| 4 | 模块 smoke | ✅ | `python -m py_compile scripts/increment_merge.py` → PY_COMPILE_OK(当前 HEAD 实测);fc5ae99 端到端 smoke 即层 2 |
| 5 | 回归测试 | ✅ | fc5ae99 修复后,后续 v27/v28/v29/v30 四轮综合看板端到端生成均通过(13 panel + Tab JS 齐全),increment_merge 在 v27/v29 又经 close_workbook/save_workbook_atomic 加固,无回归 |

### 4.3 py_compile 实测(当前 HEAD)

```text
python -m py_compile scripts/increment_merge.py
PY_COMPILE_OK increment_merge
python -m py_compile scripts/gen_institution_stats.py
PY_COMPILE_OK gen_institution_stats
```

## 5. 审计焦点(给 B 的提示)

1. **REV-01 真阻断核查**:读 `increment_merge.py:L1326-1444`,确认 (a)save 写 tmp_path 不写 output_path;(b)qc_fails>0 分支 os.remove(tmp_path)+return,output_path 从未被写入;(c)qc_fails==0 分支 os.replace(tmp_path, output_path) 原子替换。对比 r1 `1ad1a89:L1272` save 在 QC 前的差异。
2. **REV-03 匹配键核查**:读 `L799-844`,确认 (a)target_project_names 用项目名做豁免(L803);(b)collect_uv_multiset 用 Counter (项目名,分层,机构,V) 多重集(L808);(c)orig_ms/out_ms 差集判定(L827-834)。确认 rebook 删行后行号不对齐不再影响判定。
3. **#ABS-004 回归核查**:读 `fc5ae99` 的 CHANGELOG v2.5.2 段 + commit message,确认 dict 遍历崩溃+key 冲突误报已由 Counter 修复,0706 台账端到端 PASS。
4. **运行基线提示**:r02 tag→3d5335a 含 #ABS-004 回归,真跑台账会崩。B 端到端核查请用 fc5ae99 或当前 HEAD;3d5335a 仅作代码逻辑核查。
5. **后续加固归属**:v27/v29 的 close_workbook/save_workbook_atomic 是独立 slug 加固,不纳入 r2 审计范围,但 B 可顺带确认当前 HEAD 的 L1429-1432 close_workbook 四句柄清理无资源泄漏。

## 6. 附录

### 6.1 r2 修复链 commit 全文

**3d5335a**(r02 tag,REV-01/02/03 初修):

```text
fix(increment_merge): REV-01 save移到QC后 + REV-03 行号对齐修复 (r1)

B1审计 NEEDS_REVISION 修复:
- REV-01 (CRITICAL): wb_a.save()从QC前移到临时文件,QC PASS后rename,FAIL时删除
- REV-02 (WARNING): changed_files补记送审报告自身
- REV-03 (WARNING): QC 7.20改用(项目名,分层,机构)做匹配键,不再用行号直接对比
```

**fc5ae99**(v2.5.2,#ABS-004 回归修复 + REV-03 完整修复):

```text
fix(increment_merge): QC 7.20 r2 修复 dict遍历崩溃+匹配键误报 (#ABS-004)
r1 修复 REV-03 引入两个回归 bug,本次 r2 修复:
1. dict 遍历崩溃: get_all_projects() 返回 dict, r1 误写三元组解包 → ValueError
   修复: 改用 .items() 遍历
2. 匹配键不唯一误报: (项目名,分层,机构) 作 dict key 时,同机构多笔认购
   (东裕3-10/优先A 交银理财 V=2.7 和 V=0.25) key 冲突,dict 只留最后 V → 误报 FAIL
   修复: 改用 Counter 多重集对比 (项目名,分层,机构,V),同机构多笔认购各自计数
验证: 0706台账增量合并+东裕4号续发簿记录入, QC 7.1/7.2/7.3/7.20 全PASS
```

### 6.2 当前 HEAD 关键代码段(REV-01 真阻断)

```text
increment_merge.py:L1326-1331
  # v2.5.1: 先保存到临时文件，QC PASS 后 os.replace 到 output_path
  # 这样 QC FAIL 时不会留下错误文件（REV-01 修复）
  tmp_fd, tmp_path = tempfile.mkstemp(suffix='.xlsx', dir=os.path.dirname(output_path) or '.')
  os.close(tmp_fd)
  wb_a.save(tmp_path)            # ← 写临时文件,不写 output_path

increment_merge.py:L1421-1437
  qc_fails, qc_warns = run_enhanced_qc(ws_out, ws_orig_protected, ...)
  qc_fails += qc_pre_fails
  # v2.5.1: QC FAIL 阻断——删除临时文件，不生成 output，直接退出
  if qc_fails > 0:
      os.remove(tmp_path)        # ← FAIL 删临时文件
      close_workbook(wb_out); close_workbook(wb_orig)
      close_workbook(wb_b); close_workbook(wb_a)
      print(f"[BLOCKED] {mode_label} aborted due to {qc_fails} QC FAIL(s).")
      print(f"[BLOCKED] Output file NOT saved. Temp file deleted.")
      return                     # ← output_path 从未被写入

increment_merge.py:L1444
  os.replace(tmp_path, output_path)  # ← QC PASS 后原子替换
```

### 6.3 当前 HEAD 关键代码段(REV-03 Counter 多重集)

```text
increment_merge.py:L799-844
  # v2.5.1 REV-03: rebook 删行后行号不对齐,改用 (项目名+分层+机构) 匹配键
  # v2.5.2 r2 修复: ...改用 Counter 多重集对比 (项目名,分层,机构,V)
  target_project_names = set(key for key, _, _ in target_projects)  # 项目名豁免
  def collect_uv_multiset(ws):
      ms = Counter()
      projects = get_all_projects(ws)
      for proj_name, info in projects.items():
          if proj_name in target_project_names: continue
          pstart, pend = info['start'], info['end']
          for r in range(pstart, pend + 1):
              u = ws.cell(row=r, column=21).value
              v = ws.cell(row=r, column=22).value
              layer = ws.cell(row=r, column=16).value
              if u is not None:
                  key = (proj_name, str(layer).strip() if layer else '', str(u).strip(), v)
                  ms[key] += 1
      return ms
  orig_ms = collect_uv_multiset(ws_orig_protected)
  out_ms = collect_uv_multiset(ws_out)
  only_in_orig = orig_ms - out_ms   # 丢失或被篡改
  only_in_out = out_ms - orig_ms    # 新增或被篡改
```
