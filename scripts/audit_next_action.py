#!/usr/bin/env python3
"""audit_next_action.py — 根据 audit/state.json 推荐下一步动作(自动化审计编排)

移植自 macro-allocation-strategy/scripts/next_action.py,适配 abs-toolbox 的
state.json 结构(按 slug 分组: slugs.{slug}.submissions/reviews/closed + status)。

状态机:
  slug 不存在                     → SUBMIT_A1(首轮送审, role=A)
  status=PENDING_REVIEW(有A无B)   → WAIT_FOR_B(role=B)
  status=NEEDS_REVISION           → SUBMIT_NEXT_A(role=A-fix, round+1)
  B verdict=APPROVED* 且无 C      → WAIT_FOR_C(role=C)
  status=COMPLETED(有C)           → ROUND_COMPLETED(terminal)
  其他/矛盾状态                   → UNKNOWN(需人工)

用法:
  python scripts/audit_next_action.py --slug v31-publish-hardening
  python scripts/audit_next_action.py --mine              # 列出所有 slug
  python scripts/audit_next_action.py --slug X --json     # JSON 输出(控制平面解析)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = SKILL_ROOT / "audit" / "state.json"

APPROVE_VERDICTS = {"APPROVED", "APPROVED_WITH_CONDITIONS"}

# 终态/需人工/同轮次动作集合(供 --json 编排字段)
TERMINAL_ACTIONS = {"ROUND_COMPLETED", "REJECTED_TERMINAL"}
HUMAN_ACTIONS = {"BLOCKED", "UNKNOWN"}
SAME_ROUND_ACTIONS = {"WAIT_FOR_B", "WAIT_FOR_C"}


def load_state() -> dict | None:
    if not STATE_PATH.exists():
        return None
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def file_round(name: str) -> int:
    """从 A1-xxx-r2.md 类文件名提取轮次号,失败返回 0。"""
    m = re.search(r"-r(\d+)", name or "")
    return int(m.group(1)) if m else 0


def latest_of(names: list[str]) -> str | None:
    if not names:
        return None
    return max(names, key=file_round)


def read_verdict(slug_dir_names: dict, reviews: list[str]) -> str | None:
    """从最新 B 文件 frontmatter 读 verdict(轻量解析,不做完整校验)。"""
    latest = latest_of(reviews)
    if not latest:
        return None
    path = SKILL_ROOT / "audit" / "reviews" / latest
    if not path.exists():
        return None
    m = re.search(r"^verdict:\s*(\S+)", path.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def decide_action(state: dict, slug: str) -> dict:
    slugs = state.get("slugs", {})
    info = slugs.get(slug)

    open_issues = [i for i in state.get("issues", []) if i.get("slug") == slug and i.get("status") == "open"]

    # Case 1: slug 未登记 → 首轮送审
    if not info:
        return {
            "slug": slug,
            "current_round": 0,
            "next_round": 1,
            "latest_stage": None,
            "latest_file": None,
            "latest_status": None,
            "action": "SUBMIT_A1",
            "agent": "A",
            "message": f"提交 A1-{slug}-r1.md 送审(首次送审)",
            "open_issues": [],
            "is_blocked": False,
        }

    status = info.get("status")
    subs = info.get("submissions") or []
    revs = info.get("reviews") or []
    clos = info.get("closed")
    cur_round = info.get("current_round") or 1

    # Case 2: 已送审待审计
    if status == "PENDING_REVIEW":
        if not subs:
            return _unknown(slug, info, "status=PENDING_REVIEW 但 submissions 为空")
        return {
            "slug": slug,
            "current_round": cur_round,
            "next_round": cur_round,
            "latest_stage": "A",
            "latest_file": latest_of(subs),
            "latest_status": status,
            "action": "WAIT_FOR_B",
            "agent": "B",
            "message": f"等待 Agent B 复审 {latest_of(subs)}",
            "open_issues": open_issues,
            "is_blocked": False,
        }

    # Case 3: 需修复 → A-fix 新轮次
    if status == "NEEDS_REVISION":
        return {
            "slug": slug,
            "current_round": cur_round,
            "next_round": cur_round + 1,
            "latest_stage": "B",
            "latest_file": latest_of(revs),
            "latest_status": status,
            "action": "SUBMIT_NEXT_A",
            "agent": "A",
            "message": f"按最新 B 审计意见修复,提交 A{{N}}-{slug}-r{cur_round + 1}.md",
            "open_issues": open_issues,
            "is_blocked": False,
        }

    # Case 4: 审计通过待归档(status 仍为 REVIEWED/或 verdict 已 APPROVED 但无 closed)
    if clos:
        return {
            "slug": slug,
            "current_round": cur_round,
            "next_round": cur_round + 1,
            "latest_stage": "C",
            "latest_file": clos if isinstance(clos, str) else latest_of(clos),
            "latest_status": "COMPLETED",
            "action": "ROUND_COMPLETED",
            "agent": None,
            "message": f"轮次 r{cur_round} 已归档完结。可开启新 slug 或终止。",
            "open_issues": open_issues,
            "is_blocked": False,
        }

    # 无 closed:看最新 B verdict 决定等 C 还是修
    verdict = info.get("verdict") or read_verdict(info, revs)
    if verdict in APPROVE_VERDICTS and revs:
        return {
            "slug": slug,
            "current_round": cur_round,
            "next_round": cur_round,
            "latest_stage": "B",
            "latest_file": latest_of(revs),
            "latest_status": f"REVIEWED / {verdict}",
            "action": "WAIT_FOR_C",
            "agent": "C",
            "message": f"B verdict={verdict},等待 Agent C 归档",
            "open_issues": open_issues,
            "is_blocked": False,
        }
    if verdict == "NEEDS_INFO":
        return {
            "slug": slug,
            "current_round": cur_round,
            "next_round": cur_round + 1,
            "latest_stage": "B",
            "latest_file": latest_of(revs),
            "latest_status": status,
            "action": "SUBMIT_NEXT_A",
            "agent": "A",
            "message": f"B verdict=NEEDS_INFO,补充证据/答疑(尽量不消耗轮次)",
            "open_issues": open_issues,
            "is_blocked": False,
        }
    if verdict == "REJECTED":
        return {
            "slug": slug,
            "current_round": cur_round,
            "next_round": cur_round,
            "latest_stage": "B",
            "latest_file": latest_of(revs),
            "latest_status": "REJECTED",
            "action": "REJECTED_TERMINAL",
            "agent": None,
            "message": "B verdict=REJECTED,slug 终止",
            "open_issues": open_issues,
            "is_blocked": False,
        }
    return _unknown(slug, info, f"无法推导(status={status}, verdict={verdict})")


def _unknown(slug: str, info: dict, why: str) -> dict:
    return {
        "slug": slug,
        "current_round": info.get("current_round"),
        "next_round": None,
        "latest_stage": None,
        "latest_file": None,
        "latest_status": info.get("status"),
        "action": "UNKNOWN",
        "agent": None,
        "message": f"状态异常,需人工介入: {why}",
        "open_issues": [],
        "is_blocked": True,
    }


def enrich_for_orchestration(state: dict, result: dict) -> dict:
    """为 --json 增加稳定的自动化编排字段(参考 macro next_action.py)。"""
    action = result.get("action")
    agent = result.get("agent")
    role = agent
    if action == "SUBMIT_NEXT_A":
        role = "A-fix" if (result.get("current_round") or 0) >= 1 else "A"
    result.update({
        "role_to_dispatch": role,
        "terminal": action in TERMINAL_ACTIONS,
        "requires_human": action in HUMAN_ACTIONS,
        "same_round": action in SAME_ROUND_ACTIONS,
        "reason_code": action,
    })
    return result


def render(result: dict) -> str:
    lines = [
        f"## Slug: {result['slug']}",
        f"- 当前轮次: r{result.get('current_round') or '-'}",
        f"- 下一轮次: r{result.get('next_round') or '-'}",
        f"- 最新阶段: {result.get('latest_stage') or '-'}",
        f"- 最新文件: {result.get('latest_file') or '(无)'}",
        f"- 最新状态: {result.get('latest_status') or '-'}",
        f"- 下一步动作: **{result['action']}**",
        f"- 执行角色: {result.get('role_to_dispatch') or '(人工/无)'}",
        f"- 说明: {result['message']}",
    ]
    if result.get("is_blocked"):
        lines.append("- ⚠️ 状态: BLOCKED,需人工介入")
    if result.get("open_issues"):
        lines.append(f"- 待处理 Issue({len(result['open_issues'])}): " + ", ".join(i.get("id", "?") for i in result["open_issues"]))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="审计状态机:推荐下一步动作")
    parser.add_argument("--slug", help="指定 slug(必填,除非 --mine)")
    parser.add_argument("--mine", action="store_true", help="列出所有 slug 的下一步动作")
    parser.add_argument("--json", action="store_true", help="JSON 输出(控制平面解析)")
    args = parser.parse_args()

    state = load_state()
    if state is None:
        print("[ERROR] audit/state.json 不存在或损坏", file=sys.stderr)
        return 2

    if args.mine:
        results = []
        for slug in state.get("slugs", {}):
            r = enrich_for_orchestration(state, decide_action(state, slug))
            results.append(r)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print("\n\n".join(render(r) for r in results))
        return 0

    if not args.slug:
        print("[ERROR] 必须指定 --slug SLUG 或 --mine", file=sys.stderr)
        return 2

    result = enrich_for_orchestration(state, decide_action(state, args.slug))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0 if not result.get("requires_human") else 1


if __name__ == "__main__":
    sys.exit(main())
