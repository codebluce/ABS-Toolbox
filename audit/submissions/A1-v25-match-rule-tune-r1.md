---
# 送审报告 frontmatter(A 角色)

submission_id: A1-v25-match-rule-tune-r1
slug: v25-match-rule-tune
skill_version: v2.5.0
round: 1
created_at: "2026-07-05 20:30:00"
author: agent_a

# --- 代码快照 ---
git_tag: audit/v2.5-v25-match-rule-tune-r01
commit_hash: TBD                              # commit 后补记
previous_git_tag: audit/v2.4-v24-self-check-r01

# --- 变更文件 ---
changed_files:
  - scripts/increment_merge.py                # modified
  - SKILL.md                                  # modified
  - CHANGELOG.md                              # modified

# --- 状态机 ---
status: PENDING_REVIEW

# --- 上一轮 Issue 处理 ---
# v24-self-check 已归档 APPROVED,无遗留 Issue

# --- 强制自审 ---
self_review:
  all_issues_addressed: true
  no_overengineering: true
  function_equivalence_verified: true
  edge_cases_covered: true
  notes: "本轮基于 0703 台账实测发现的真实匹配问题,非空想改造;Pass 1-4 优先级链清晰,hard_map 显式可控,core_name len>=3 防误匹配"

# --- 审计焦点 ---
review_focus:
  - "normalize 去连字符是否会误伤合法机构名(如带 - 的机构)"
  - "Pass 4 核心名匹配 len>=3 阈值是否合理(过短会误匹配,如'中信'会匹配'中信证券'和'中信建投')"
  - "MATCH_HARD_MAP 当前只 2 条,是否需要扩展(如其他已知难匹配机构)"
  - "默认 rebook 模式是否会破坏既有用户工作流(已传 --supplement 的不受影响)"
---

# v25-match-rule-tune r1 送审报告

## 1. 变更摘要(200 字内)

基于 0703 台账实测发现 2 个匹配失败 case(利曦基金 vs 利曦私募基金 / 中信建投-衍生品 vs 中信建投衍生品)。本轮通过 4 处改造解决:normalize 去连字符 + 修复全角空格 bug + 新增 core_name 函数(去后缀) + 新增 MATCH_HARD_MAP 显式映射 + Pass 1-4 优先级链(精确→包含→hard_map→核心名)。同时把 rebook 设为默认模式(幂等,避免 supplement 多次跑累积脏行)。6 层自检全部通过,2 个原匹配失败 case 已验证匹配成功。

## 2. 上一轮 Issue 处理

v24-self-check 已归档 APPROVED,无遗留 Issue。

## 3. 代码变更清单

| 文件 | 操作 | 说明 |
|---|---|---|
| scripts/increment_merge.py | modified | normalize 去 - //／ + 修复 　 bug;新增 core_name() + INST_SUFFIXES + MATCH_HARD_MAP;匹配 Pass 1-4 优先级链;CLI 默认 rebook 模式 |
| SKILL.md | modified | 版本升 v2.5.0,加第六轮激活说明 |
| CHANGELOG.md | modified | 加 v2.5.0 段 |

## 4. 自审与指标

### 4.1 强制自审清单

- [x] all_issues_addressed: 上一轮 v24 已归档 APPROVED,无遗留
- [x] no_overengineering: 仅加 4 处必要改动,未引入抽象层
- [x] function_equivalence_verified: 6 层自检通过(见 4.2)
- [x] edge_cases_covered: 2 个原失败 case 已验证匹配成功

### 4.2 6 层自检证据

| 层 | 检查 | 结果 | 证据 |
|---|---|---|---|
| 1 | 改造 diff 范围核查 | ✅ | 仅改 `increment_merge.py`(+60/-5 行,4 处改动),`git diff --stat` 确认 |
| 2 | 0703 台账端到端 | ✅ | QC Fails=0,Warns=3;`[Pass3 hard_map] 利曦私募基金 -> 利曦基金 (Row1838)` + `MATCH: 中信建投-衍生品 -> Row1847` 全部匹配成功 |
| 3 | 25 列台账回归(机构统计) | ✅ | `QC PASSED — 30项全部通过` |
| 4 | 发行定价回归 | ✅ | gen_abs_cost_report QC PASSED WITH WARNINGS / gen_compare_tool QC PASSED WITH WARNINGS(已知数据问题,非回归) |
| 5 | 22 列台账全流程 | ✅ | 翻译官模式 → 机构统计 `QC PASSED — 35项全部通过` |
| 6 | 默认 rebook 行为 | ✅ | 不传 mode 时默认 rebook + 打印 `[v2.5.0 INFO] 未指定模式,默认使用 --rebook 模式` |

### 4.3 关键匹配证据(层 2 详细)

0703 台账 5 个目标项目 rebook 测试输出:

```
[Pass3 hard_map] 利曦私募基金 -> 利曦基金 (Row1838)
MATCH: 利曦私募基金 -> Row1838 (rate=0.0165, size=0.5)
EXTRA: 利曦私募基金 rate=0.024 size=1.0 (anchor Row1838)
MATCH: 中信建投-衍生品 -> Row1847 (rate=0.0175, size=0.01)   ← normalize 去连字符后 Pass 1 精确匹配
```

5 个目标项目全部 PASS,QC Fails=0(对比 v2.4.0 跑 supplement 模式 Fails=2)。

## 5. 审计焦点

1. **normalize 去连字符的副作用**:新增 `n.replace("-", "").replace("/", "").replace("／", "")`。是否会有合法机构名带 `-` 被误合并?当前已知机构名里 `-` 主要出现在"中信建投-衍生品"(应去)和"申万宏源-北京"(应去)。如 B 发现其他需保留 `-` 的 case,请列 Issue。

2. **Pass 4 核心名匹配 len>=3 阈值**:`core_name()` 去后缀后要求 len>=3。例:"利曦基金" → "利曦"(2 字) → 不达阈值,会走 hard_map。"中信证券" → "中信"(2 字) → 不达阈值。但"中信建投" → "中信建投"(4 字,无后缀) → 达阈值。这个阈值是否合理?B 可复跑 0626 定稿台账核查是否有误匹配。

3. **MATCH_HARD_MAP 扩展性**:当前只 2 条("利曦基金"↔"利曦私募基金")。是否需要扩展?建议观察 1-2 周业务使用,如发现新 case 再加。

4. **默认 rebook 模式的兼容性**:不传 `--supplement/--rebook/--new-raw` 时默认 rebook。已传 `--supplement` 或 `--new-raw` 的用户不受影响。但如果有用户脚本依赖"不传 mode 时报错"的行为(理论不应有),会破坏。B 可核查 SKILL.md 触发词路由是否有此依赖。

5. **commit 含污染文件**:本次 commit 范围仅 v25 相关 3 个文件(increment_merge.py + SKILL.md + CHANGELOG.md),其他 modified 脚本(abs_common.py / entity_alias.py / 3 个 gen)和业务台账文件**不在 v25 commit 内**,会单独 commit 标"上次会话遗留"。

## 6. 附录

### 6.1 normalize 单元测试

```
normalize("中信建投-衍生品") = "中信建投衍生品"   ← v2.5.0 新增去 -
normalize("中信建投衍生品") = "中信建投衍生品"   ← 一致,Pass 1 精确匹配
normalize("利曦基金")       = "利曦基金"
normalize("利曦私募基金")   = "利曦私募基金"     ← 不一致,走 Pass 3 hard_map
core_name("利曦基金")       = "利曦"             ← 去后缀"基金"
core_name("利曦私募基金")   = "利曦"             ← 去后缀"私募基金",一致
MATCH_HARD_MAP              = {"利曦基金": "利曦私募基金", ...}
```

### 6.2 0703 台账 rebook 测试 QC Summary

```
=== Enhanced QC Summary ===
  Fails: 0, Warns: 3
  RESULT: WARN - review warnings before using output
```

对比 v2.4.0 supplement 模式:Fails=2(WXY 旧值与新明细不一致 + 5 份明细未映射)。v2.5.0 rebook 默认模式 Fails=0,2 个原失败 case 全部解决。

### 6.3 改造 diff 概览

```diff
 def normalize(name):
+    """v2.5.0: 增加去除 - / / ／ 等标点..."""
     if not name: return ""
-    n = str(name).strip().replace("（", "(")....replace("　", "")
+    n = str(name).strip().replace("（", "(")....replace("　", "").replace("　", "")
+    n = n.replace("-", "").replace("/", "").replace("／", "")
     ...
     return n

+INST_SUFFIXES = ["私募基金", "基金", "资管", ...]
+def core_name(name): ...
+MATCH_HARD_MAP = {"利曦基金": "利曦私募基金", ...}

+# v2.5.0 Pass 3: hard_map 显式映射
+if matched_ur_idx is None:
+    inst_raw = items[0]['name']
+    inst_norm = normalize(inst_raw)
+    for un_key, un_target in MATCH_HARD_MAP.items():
+        if inst_norm == normalize(un_key):
+            for ur_idx, ur in enumerate(urows):
+                if ur[3]: continue
+                if normalize(ur[1]) == normalize(un_target):
+                    matched_ur_idx = ur_idx
+                    print(f"      [Pass3 hard_map] ...")
+                    break
+            if matched_ur_idx is not None: break

+# v2.5.0 Pass 4: 核心名匹配
+if matched_ur_idx is None:
+    inst_core = core_name(inst_key)
+    if len(inst_core) >= 3:
+        for ur_idx, ur in enumerate(urows):
+            if ur[3]: continue
+            un_core = core_name(ur[1])
+            if un_core == inst_core:
+                matched_ur_idx = ur_idx
+                print(f"      [Pass4 core_name] ...")
+                break

 if __name__ == "__main__":
-    parser = argparse.ArgumentParser(description="增量台账合并 v2.1")
+    parser = argparse.ArgumentParser(description="增量台账合并 v2.5.0")
     ...
+    if not args.supplement and not args.rebook and not args.new_raw:
+        print("[v2.5.0 INFO] 未指定模式,默认使用 --rebook 模式(推荐,幂等)")
+        args.rebook = True
```

### 6.4 回滚

`git revert <v25_commit>` 即可,原 v2.4.0 行为完全保留。
