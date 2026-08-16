#!/usr/bin/env python3
"""audit_validate.py — abs-toolbox 审计产物校验脚本(纯标准库)

移植自 macro-allocation-strategy/scripts/validate_audit.py,适配精简 8 字段
frontmatter,去掉 pydantic/yaml/OOS 门禁/_manifest 依赖。

校验项:
  V1  frontmatter 可解析 + id 与文件名一致
  V2  A 文件必填字段(submission_id/slug/round/created_at/author/git_tag/
      commit_hash/changed_files/status) + self_review 4 bool 联动
  V3  B 文件 verdict 枚举 + issues 必填子字段 + verified_issues 链
  V4  C 文件 final_verdict 枚举 + audit_escape_risks 非空 + all_issues_resolved
  V5  git_tag 存在且 commit_hash 与 tag 指向一致
  V6  A 文件 changed_files 与 git show <tag> --stat 对比(遗漏→WARNING)

用法:
  python scripts/audit_validate.py --file audit/submissions/A1-xxx-r1.md
  python scripts/audit_validate.py --all --skip-historical
  python scripts/audit_validate.py --file ... --strict   # WARNING 也失败
退出码: 0=通过(可有 WARNING) / 1=仅 WARNING 且 --strict / 2=有 CRITICAL
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
AUDIT_DIR = SKILL_ROOT / "audit"
HISTORICAL_CUTOFF = "2026-08-16"  # 此日期前的文件适用历史豁免(--skip-historical)

VERDICTS = {"APPROVED", "APPROVED_WITH_CONDITIONS", "NEEDS_REVISION", "NEEDS_INFO", "REJECTED"}
SEVERITIES = {"CRITICAL", "WARNING", "INFO"}
BOOL_KEYS = ("all_issues_addressed", "no_overengineering", "function_equivalence_verified", "edge_cases_covered")


def parse_frontmatter(text: str) -> dict:
    """简易 YAML frontmatter 解析:顶层 key: value + 一级缩进列表项/字典项。

    覆盖本项目模板实际用到的子集,不做完整 YAML。
    """
    fm = {}
    if not text.startswith("---"):
        return fm
    end = text.find("\n---", 3)
    if end < 0:
        return fm
    block = text[4:end] if text[3] == "\n" else text[3:end]
    current_key = None
    for raw in block.split("\n"):
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        if raw.startswith("  ") or raw.startswith("- "):
            # 嵌套行:挂在最近的顶层 key 下。按首个非列表行决定容器类型:
            #   "key: v" 缩进行 → dict 容器(self_review 类)
            #   "- item" 列表行 → list 容器(changed_files 类)
            if current_key is None:
                continue
            line = raw.strip()
            is_list_item = line.startswith("- ")
            container = fm.get(current_key)
            if container is None:
                container = fm[current_key] = {} if not is_list_item else []
            # 空占位 [] 且遇到 dict 型行 → 升级为 dict
            if not is_list_item and isinstance(container, list) and not container:
                container = fm[current_key] = {}
            if isinstance(container, dict) and not is_list_item and ":" in line:
                k, _, v = line.partition(":")
                container[k.strip()] = _scalar(v.strip())
            elif isinstance(container, list) and is_list_item:
                item = line[2:].strip()
                if ":" in item:
                    k, _, v = item.partition(":")
                    container.append({k.strip(): _scalar(v.strip())})
                else:
                    container.append(_scalar(item))
            elif isinstance(container, list) and not is_list_item and ":" in line:
                # list-of-dict 的后续字段行(如 "- id: X" 之后的 severity: WARNING):
                # 附加到容器最后一个 dict 条目,不再静默丢弃(REV-03)
                k, _, v = line.partition(":")
                if container and isinstance(container[-1], dict):
                    container[-1][k.strip()] = _scalar(v.strip())
            continue
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", raw)
        if m:
            key, val = m.group(1), m.group(2).strip()
            current_key = key
            if val == "":
                fm[key] = None  # 占位,由首个嵌套行决定容器类型
            else:
                fm[key] = _scalar(val)
    return fm


def _scalar(v: str):
    v = v.strip().strip('"').strip("'")
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    if v == "null" or v == "":
        return None
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def git(*args: str) -> str | None:
    try:
        # core.quotepath=off: 关闭非 ASCII 路径的八进制转义,中文文件名原样输出
        # (REV-v2.5.9-v32-r01-01: 转义导致 V6 对中文名产生成对假阳性)
        proc = subprocess.run(
            ["git", "-c", "core.quotepath=off", *args],
            cwd=SKILL_ROOT, capture_output=True, text=True,
        )
        return proc.stdout.strip() if proc.returncode == 0 else None
    except OSError:
        return None


class Report:
    def __init__(self, path: Path):
        self.path = path
        self.critical: list[str] = []
        self.warnings: list[str] = []

    def crit(self, msg: str):
        self.critical.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    @property
    def ok(self):
        return not self.critical


def validate_file(path: Path, rep: Report, skip_historical: bool = False) -> bool:
    """返回 False 表示文件按历史豁免跳过。"""
    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)

    # 历史豁免:created_at/closed_at 早于截止日,或文件名内日期早于截止日
    # (A1-v26 等早期文件无标准 frontmatter,按内容日期豁免)
    created = str(fm.get("created_at") or fm.get("closed_at") or "")
    m_date = re.search(r"(\d{4}-\d{2}-\d{2})", text[:3000])
    content_date = m_date.group(1) if m_date else ""
    eff_date = created[:10] or content_date
    if skip_historical and eff_date and eff_date < HISTORICAL_CUTOFF:
        return False

    if not fm:
        rep.crit(f"{path.name}: frontmatter 不可解析(缺 --- 块)")
        return True

    name = path.name
    # V1 id 一致性:A/C 的自 id 必须与文件名一致;B 文件的 submission_id 指向被审 A 文件,不比对
    for id_key in ("submission_id", "review_id", "closed_id"):
        if id_key not in fm:
            continue
        if id_key == "submission_id" and path.parent.name == "reviews":
            continue
        if fm[id_key] != path.stem:
            rep.crit(f"{name}: {id_key}={fm[id_key]} 与文件名 {path.stem} 不一致")

    # V5 git tag
    tag = fm.get("git_tag")
    commit = fm.get("commit_hash")
    if tag and not commit:
        # C 文件无 commit_hash 字段则跳过 hash 一致性
        if not git("tag", "-l", str(tag)):
            rep.warn(f"{name}: git_tag {tag} 不存在于本地 tag 列表")
    elif tag and commit:
        if not git("tag", "-l", str(tag)):
            rep.crit(f"{name}: git_tag {tag} 不存在")
        else:
            full = git("rev-parse", str(tag))
            if full and not full.startswith(str(commit)):
                rep.crit(f"{name}: commit_hash {commit} 与 tag 实际指向 {full[:len(str(commit))]} 不一致")

    if path.parent.name == "submissions":
        _validate_a(name, fm, rep)
    elif path.parent.name == "reviews":
        _validate_b(name, fm, rep)
    elif path.parent.name == "closed":
        _validate_c(name, fm, rep)
    return True


def _validate_a(name: str, fm: dict, rep: Report):
    required = ["submission_id", "slug", "skill_version", "round", "created_at", "author", "git_tag", "commit_hash", "changed_files", "status"]
    for k in required:
        v = fm.get(k)
        if v is None or v == [] or v == "":
            rep.crit(f"{name}: A 文件必填字段缺失/为空: {k}")
    sr = fm.get("self_review")
    if not isinstance(sr, dict):
        rep.crit(f"{name}: self_review 缺失或结构错误")
        return
    for bk in BOOL_KEYS:
        if bk not in sr:
            rep.crit(f"{name}: self_review.{bk} 缺失(4 bool 必填)")
    if any(sr.get(bk) is False for bk in BOOL_KEYS if bk in sr) and fm.get("status") != "BLOCKED":
        rep.crit(f"{name}: self_review 任一 false 时 status 必须 BLOCKED(当前 {fm.get('status')})")
    # V6: changed_files 与 git show <tag> --stat 对比(遗漏/多报 → WARNING)(REV-02 实现)
    tag = fm.get("git_tag")
    declared = fm.get("changed_files")
    if isinstance(declared, list) and tag and git("tag", "-l", str(tag)):
        stat = git("show", str(tag), "--stat", "--format=")
        actual = set()
        for ln in stat.split("\n"):
            m2 = re.match(r"^(.+?)\s+\|", ln)
            if m2:
                candidate = m2.group(1).strip()
                # 跳过汇总行(纯数字统计)与重命名箭头外的目录文件
                if candidate and not candidate.isdigit() and "|" not in candidate:
                    actual.add(candidate)
        missing = actual - set(map(str, declared))
        extra = set(map(str, declared)) - actual
        if missing:
            rep.warn(f"{name}: changed_files 遗漏 {len(missing)} 个文件未声明: {sorted(missing)}")
        if extra:
            rep.warn(f"{name}: changed_files 多报 {len(extra)} 个不在 commit 中: {sorted(extra)}")


def _validate_b(name: str, fm: dict, rep: Report):
    if fm.get("verdict") not in VERDICTS:
        rep.crit(f"{name}: verdict={fm.get('verdict')} 不在枚举 {sorted(VERDICTS)}")
    issues = fm.get("issues")
    if issues is None:
        rep.crit(f"{name}: issues 字段缺失(无 Issue 也要显式空列表)")
    elif isinstance(issues, list):
        for it in issues:
            if not isinstance(it, dict):
                continue
            for k in ("id", "severity", "category", "blocks_approval", "summary"):
                if k == "summary":  # 模板里 summary 在嵌套行,解析宽松处理
                    continue
                if k not in it:
                    rep.warn(f"{name}: Issue {it.get('id', '?')} 缺字段 {k}")
            if it.get("severity") and it["severity"] not in SEVERITIES:
                rep.warn(f"{name}: Issue {it.get('id')} severity={it['severity']} 非标准")


def _validate_c(name: str, fm: dict, rep: Report):
    if fm.get("final_verdict") not in VERDICTS:
        rep.crit(f"{name}: final_verdict={fm.get('final_verdict')} 不在枚举")
    risks = fm.get("audit_escape_risks")
    if not risks:
        rep.crit(f"{name}: audit_escape_risks 不得为空(无风险也要显式写明检查范围)")
    if not isinstance(fm.get("all_issues_resolved"), bool):
        rep.crit(f"{name}: all_issues_resolved 必须为 bool")


def main() -> int:
    parser = argparse.ArgumentParser(description="审计产物校验")
    parser.add_argument("--file", type=Path, help="单文件校验")
    parser.add_argument("--all", action="store_true", help="校验全部 A/B/C 产物")
    parser.add_argument("--skip-historical", action="store_true", help="跳过 2026-08-16 前的历史文件")
    parser.add_argument("--strict", action="store_true", help="WARNING 也视为失败")
    args = parser.parse_args()

    if not args.file and not args.all:
        print("必须指定 --file 或 --all", file=sys.stderr)
        return 2

    targets: list[Path] = []
    if args.file:
        targets = [args.file if args.file.is_absolute() else SKILL_ROOT / args.file]
    else:
        for sub in ("submissions", "reviews", "closed"):
            targets += sorted((AUDIT_DIR / sub).glob("[ABC]*-*.md"))

    checked = skipped = 0
    all_crit: list[str] = []
    all_warn: list[str] = []
    for p in targets:
        if not p.exists():
            print(f"[ERROR] 文件不存在: {p}", file=sys.stderr)
            return 2
        rep = Report(p)
        try:
            handled = validate_file(p, rep, args.skip_historical)
        except Exception as exc:  # noqa: BLE001
            rep.crit(f"{p.name}: 校验异常 {exc}")
            handled = True
        if not handled:
            skipped += 1
            continue
        checked += 1
        all_crit += rep.critical
        all_warn += rep.warnings
        status = "FAIL" if rep.critical else ("WARN" if rep.warnings else "PASS")
        print(f"[{status}] {p.name}")
        for m in rep.critical:
            print(f"    CRITICAL: {m}")
        for m in rep.warnings:
            print(f"    WARNING:  {m}")

    print(f"\n共校验 {checked} 个文件(历史豁免跳过 {skipped}),CRITICAL {len(all_crit)},WARNING {len(all_warn)}")
    if all_crit:
        return 2
    if all_warn and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
