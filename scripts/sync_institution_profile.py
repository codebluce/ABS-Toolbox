#!/usr/bin/env python3
"""Build institution profile data from JoySpace Sheets rangeData exports.

This script is intentionally pure-local: it does not call JoySpace APIs itself.
Use the JoySpace MCP tool to export each owner worksheet rangeData, save them as
JSON files, then run this script to normalize them into data/机构画像数据.json.

Expected input directory layout:
  Inbox/joyspace_profile_sync/
    吴沛智.json
    李亦非.json
    姜守园.json
    邓殷洁.json
    高雅.json

Each file may be either:
  1. Raw MCP tool output list: [{"type":"text","text":"{...}"}]
  2. Parsed response object containing data.data.data.rangeData
  3. Direct list of rangeData cell objects
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "data" / "joyspace_profile_sync"
DEFAULT_OUTPUT = ROOT / "data" / "机构画像数据.json"
DEFAULT_META = ROOT / "data" / "机构画像数据.meta.json"
OWNER_SHEETS = ["吴沛智", "李亦非", "姜守园", "邓殷洁", "高雅", "李晨", "刘啸飞"]
BASE_HEADERS = {"机构名称", "机构名称（管理人/主承销商/销售机构）", "管理人及销售机构", "部门-职位-联系人", "批复情况", "额度使用情况"}
SKIP_NAMES = {"机构名称", "序号", "", "nan", "None"}
CONTACT_PLACEHOLDERS = {"", "-", "—", "暂无", "暂无联系人", "无联系人", "无人对接", "待补充", "待完善", "待更新", "无", "n/a", "na"}
CONTACT_BUSINESS_KEYWORDS = ("额度", "上限", "限额", "批复", "授信", "余额", "集中度", "本周", "目前", "预计", "推进", "沟通", "拜访", "尽调", "发行", "到期")
CONTACT_ASSET_KEYWORDS = ("白条", "金条", "白取", "保理", "金采", "采购融资", "京企贷", "企业主贷", "动产质押")


def _unwrap_payload(obj: Any) -> Any:
    if isinstance(obj, list) and obj and isinstance(obj[0], dict) and "text" in obj[0]:
        return _unwrap_payload(json.loads(obj[0]["text"]))
    if isinstance(obj, dict):
        data = obj.get("data")
        if isinstance(data, dict):
            nested = data.get("data")
            if isinstance(nested, dict) and "rangeData" in nested:
                return nested["rangeData"]
            if "rangeData" in data:
                return data["rangeData"]
        if "rangeData" in obj:
            return obj["rangeData"]
    return obj


def load_range_data(path: Path) -> list[dict]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    data = _unwrap_payload(obj)
    if not isinstance(data, list):
        raise ValueError(f"无法从 {path} 解析 rangeData list")
    return data


def matrix_from_range_data(range_data: list[dict]) -> tuple[list[list[str]], int, int]:
    max_row = max((int(c.get("rowFrom", 0)) for c in range_data), default=0)
    max_col = max((int(c.get("colFrom", 0)) for c in range_data), default=0)
    grid = [["" for _ in range(max_col + 1)] for _ in range(max_row + 1)]
    for cell in range_data:
        r = int(cell.get("rowFrom", 0))
        c = int(cell.get("colFrom", 0))
        val = cell.get("cellText")
        if val is None:
            val = cell.get("originalCellValue")
        grid[r][c] = str(val).strip() if val is not None else ""
    return grid, max_row, max_col


def is_date_header(value: str) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    if value in BASE_HEADERS or value in {"序号", "专项"}:
        return False
    # Typical headers: 0727-0731, 0608-0612, 0413-0417
    return any(ch.isdigit() for ch in value) and ("-" in value or "－" in value or "/" in value)


def is_name_header(value: str) -> bool:
    value = (value or "").strip()
    return value == "机构名称" or value.startswith("机构名称（") or value == "管理人及销售机构"


def is_contact_header(value: str) -> bool:
    value = (value or "").strip()
    return value in {"部门-职位-联系人", "联系人"}


def find_table_header_rows(grid: list[list[str]]) -> list[int]:
    rows = []
    for i, row in enumerate(grid):
        has_name = any(is_name_header(x) for x in row)
        has_contact = any(is_contact_header(x) for x in row)
        has_date = any(is_date_header(x) for x in row)
        if has_name and (has_contact or has_date):
            rows.append(i)
    return rows


def find_col(row: list[str], name: str) -> int | None:
    for i, v in enumerate(row):
        vv = str(v).strip()
        if vv == name:
            return i
        if name == "机构名称" and is_name_header(vv):
            return i
        if name == "部门-职位-联系人" and is_contact_header(vv):
            return i
    return None


def clean_text(v: str) -> str:
    v = (v or "").strip()
    return "" if v in {"nan", "None"} else v


def _contact_segments(value: str) -> list[str]:
    return [segment.strip() for segment in re.split(r"[\n；;]+", clean_text(value)) if segment.strip()]


def _looks_like_business_text(segment: str) -> bool:
    keyword_count = sum(keyword in segment for keyword in CONTACT_BUSINESS_KEYWORDS + CONTACT_ASSET_KEYWORDS)
    has_amount = bool(re.search(r"\d+(?:\.\d+)?\s*亿", segment))
    has_contact_shape = bool(re.search(r"[一-鿿]{2,5}\s*[-（(]", segment))
    return (keyword_count >= 2 or has_amount) and not has_contact_shape


def normalize_contact(value: str, approval: str = "", quota: str = "") -> tuple[str, list[str], list[str]]:
    """Return cleaned contact text, automatic actions, and manual-review hints."""
    original = clean_text(value)
    if original.lower() in CONTACT_PLACEHOLDERS:
        return "", ["placeholder_cleared"] if original else [], []

    actions, review, cleaned = [], [], []
    approval_quota = f"{clean_text(approval)} {clean_text(quota)}"
    for segment in _contact_segments(original):
        if segment.lower() in CONTACT_PLACEHOLDERS:
            actions.append("placeholder_segment_removed")
            continue
        # A business tail that duplicates existing approval/quota is safe to remove.
        if _looks_like_business_text(segment):
            actions.append("business_text_removed")
            continue
        tail_match = re.search(r"(白条|金条|白取|保理|总额度|额度|上限)", segment)
        if tail_match:
            head, tail = segment[:tail_match.start()].strip(), segment[tail_match.start():].strip()
            overlap = sum(token in approval_quota for token in ("白条", "金条", "保理", "额度", "上限", "授信"))
            if head and overlap >= 2 and (_looks_like_business_text(tail) or re.search(r"\d+(?:\.\d+)?\s*亿", tail)):
                cleaned.append(head)
                actions.append("business_tail_removed")
                continue
        cleaned.append(segment)

    seen, unique = set(), []
    for segment in cleaned:
        if segment not in seen:
            seen.add(segment)
            unique.append(segment)
        else:
            actions.append("duplicate_contact_removed")

    names_to_roles: dict[str, set[str]] = defaultdict(set)
    for segment in unique:
        match = re.match(r"([一-鿿]{2,5})[-（(](.+)", segment)
        if match:
            names_to_roles[match.group(1)].add(match.group(2).strip())
    for name, roles in names_to_roles.items():
        if len(roles) > 1:
            review.append(f"possible_role_conflict:{name}")
    return "; ".join(unique), actions, review


def build_records_for_owner(owner: str, range_data: list[dict]) -> list[dict]:
    grid, max_row, _ = matrix_from_range_data(range_data)
    header_rows = find_table_header_rows(grid)
    records: list[dict] = []
    seen = set()

    for idx, header_row in enumerate(header_rows):
        next_header = header_rows[idx + 1] if idx + 1 < len(header_rows) else max_row + 1
        header = grid[header_row]
        name_col = find_col(header, "机构名称")
        contact_col = find_col(header, "部门-职位-联系人")
        approval_col = find_col(header, "批复情况")
        quota_col = find_col(header, "额度使用情况")
        if name_col is None:
            continue
        date_cols = [(c, v.strip()) for c, v in enumerate(header) if is_date_header(v)]

        for r in range(header_row + 1, next_header):
            row = grid[r]
            name = clean_text(row[name_col] if name_col < len(row) else "")
            if name in SKIP_NAMES:
                continue
            contact = clean_text(row[contact_col]) if contact_col is not None and contact_col < len(row) else ""
            approval = clean_text(row[approval_col]) if approval_col is not None and approval_col < len(row) else ""
            quota = clean_text(row[quota_col]) if quota_col is not None and quota_col < len(row) else ""
            progress = []
            for c, date in date_cols:
                text = clean_text(row[c] if c < len(row) else "")
                if text:
                    progress.append({"date": date, "text": text})
            if not any([contact, approval, quota, progress]):
                continue
            key = (owner, name)
            if key in seen:
                # Same institution may appear in multiple blocks. Merge progress/contact conservatively.
                for rec in records:
                    if rec["owner"] == owner and rec["name"] == name:
                        if contact and contact not in rec["contact"]:
                            rec["contact"] = (rec["contact"] + "; " + contact).strip("; ")
                        if approval and not rec["approval"]:
                            rec["approval"] = approval
                        if quota and not rec["quota"]:
                            rec["quota"] = quota
                        rec["recent_progress"].extend(progress)
                        rec["progress_count"] = len(rec["recent_progress"])
                        break
                continue
            seen.add(key)
            records.append({
                "name": name,
                "category": "待分类",
                "owner": owner,
                "contact": contact,
                "approval": approval,
                "quota": quota,
                "progress_count": len(progress),
                "recent_progress": progress,
            })
    return records


def load_inst_dict(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("institution_to_person", {})


def _name_variants(name: str) -> set[str]:
    name = (name or "").strip()
    if not name:
        return set()
    variants = {name}
    for sep in ["/", "、", "&", "＆"]:
        if sep in name:
            variants.update(p.strip() for p in name.split(sep) if p.strip())
    # "广发证券:自营/资管" / "申万宏源：自营、汇智" also imply the base institution.
    for v in list(variants):
        for sep in [":", "："]:
            if sep in v:
                variants.add(v.split(sep)[0].strip())
    # Common business abbreviations in the JoySpace table.
    extra = set()
    for v in variants:
        extra.add(v.replace("交通银行", "交行"))
        extra.add(v.replace("交行", "交通银行"))
        extra.add(v.replace("重庆农", "重庆农商"))
        extra.add(v.replace("广州农商行", "广州农商"))
        extra.add(v.replace("东莞农商", "东莞农"))
    variants.update(x for x in extra if x)
    return variants


def _normalize_category(category: str) -> str:
    category = category or ""
    return (
        category.replace("ABS管理人(15家)", "券商")
        .replace("ABS销售机构(19家)", "券商")
        .replace("ABN主承销商(15家)", "银行")
        .replace("中保登管理人(11家)", "其他")
    )


def build_assignment_index(inst_dict: dict) -> dict[str, list[tuple[str, dict]]]:
    """Index the authoritative JoySpace first-sheet assignment table by name variants."""
    index: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for canonical_name, hit in inst_dict.items():
        for variant in _name_variants(canonical_name):
            index[variant].append((canonical_name, hit))
    return index


def resolve_assignment(name: str, assignment_index: dict[str, list[tuple[str, dict]]]) -> tuple[str, dict] | None:
    """Return the unique authoritative assignment for an institution, or None if ambiguous."""
    candidates: dict[str, dict] = {}
    for variant in _name_variants(name):
        for canonical_name, hit in assignment_index.get(variant, []):
            candidates[canonical_name] = hit
    if len(candidates) == 1:
        canonical_name, hit = next(iter(candidates.items()))
        return canonical_name, hit

    # Only use contains matching if it still resolves to a single canonical institution.
    contains_candidates: dict[str, dict] = {}
    for variant in _name_variants(name):
        if len(variant) < 3:
            continue
        for key_variant, entries in assignment_index.items():
            if len(key_variant) >= 3 and (variant in key_variant or key_variant in variant):
                for canonical_name, hit in entries:
                    contains_candidates[canonical_name] = hit
    if len(contains_candidates) == 1:
        canonical_name, hit = next(iter(contains_candidates.items()))
        return canonical_name, hit
    return None


def _merge_text(values: list[str]) -> str:
    seen, merged = set(), []
    for value in values:
        value = clean_text(value)
        if value and value not in seen:
            seen.add(value)
            merged.append(value)
    return "; ".join(merged)


def merge_records_by_assignment(records: list[dict], inst_dict: dict, contact_audit: list[dict] | None = None) -> tuple[list[dict], list[str]]:
    """Merge cross-owner records; the first-sheet assignment table owns owner/category."""
    assignment_index = build_assignment_index(inst_dict)
    groups: dict[str, list[dict]] = defaultdict(list)
    warnings: list[str] = []

    for rec in records:
        resolved = resolve_assignment(rec["name"], assignment_index)
        if resolved:
            canonical_name, hit = resolved
            rec = dict(rec)
            rec["name"] = canonical_name
            rec["owner"] = hit.get("person") or rec["owner"]
            rec["category"] = _normalize_category(hit.get("category") or "")
            groups[f"mapped:{canonical_name}"].append(rec)
        else:
            groups[f"unmapped:{rec['owner']}:{rec['name']}"].append(rec)
            if _name_variants(rec["name"]):
                warnings.append(f"未匹配权威负责人: {rec['name']} (来源 {rec['owner']})")

    merged_records = []
    for key, group in groups.items():
        primary = dict(group[0])
        before_contact = _merge_text([r.get("contact", "") for r in group])
        primary["approval"] = _merge_text([r.get("approval", "") for r in group])
        primary["quota"] = _merge_text([r.get("quota", "") for r in group])
        primary["contact"], actions, review = normalize_contact(before_contact, primary["approval"], primary["quota"])
        if not primary["contact"] and before_contact:
            actions.append("contact_cleared")
        if contact_audit is not None and (actions or review):
            contact_audit.append({
                "institution": primary["name"], "owner": primary["owner"], "before": before_contact,
                "after": primary["contact"], "actions": actions, "manual_review": review,
            })

        # approval/quota are business fields and must retain their own content unchanged.
        seen_progress, progress = set(), []
        for record in group:
            for item in record.get("recent_progress", []):
                item_key = (clean_text(item.get("date", "")), clean_text(item.get("text", "")))
                if item_key not in seen_progress and item_key[1]:
                    seen_progress.add(item_key)
                    progress.append({"date": item_key[0], "text": item_key[1]})
        primary["recent_progress"] = progress
        primary["progress_count"] = len(progress)
        merged_records.append(primary)

    merged_records.sort(key=lambda r: (r.get("category", ""), r.get("name", ""), r.get("owner", "")))
    return merged_records, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Build data/机构画像数据.json from JoySpace rangeData exports")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--meta", type=Path, default=DEFAULT_META)
    parser.add_argument("--contact-review-report", type=Path, default=None, help="联系人清洗审计报告 JSON 路径")
    parser.add_argument("--owners", nargs="*", default=OWNER_SHEETS)
    args = parser.parse_args()

    all_records: list[dict] = []
    source_files = []
    for owner in args.owners:
        path = args.input_dir / f"{owner}.json"
        if not path.exists():
            print(f"[WARN] 缺少 {owner} rangeData: {path}")
            continue
        records = build_records_for_owner(owner, load_range_data(path))
        print(f"[sync] {owner}: {len(records)} records")
        all_records.extend(records)
        source_files.append(str(path))

    if not all_records:
        raise RuntimeError("未生成任何机构画像记录")

    inst_dict = load_inst_dict(ROOT / "data" / "机构分配字典.json")
    contact_audit: list[dict] = []
    all_records, mapping_warnings = merge_records_by_assignment(all_records, inst_dict, contact_audit)
    for warning in mapping_warnings:
        print(f"[WARN] {warning}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(all_records, ensure_ascii=False, indent=2), encoding="utf-8")
    meta = {
        "source": "JoySpace 5QmWOOFQl19SdQUM1l3y",
        "synced_at": datetime.now().isoformat(timespec="seconds"),
        "record_count": len(all_records),
        "source_files": source_files,
        "builder": "scripts/sync_institution_profile.py",
    }
    args.meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = args.contact_review_report or (ROOT / "audit" / "profile_contact_review" / f"机构画像联系人清洗_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    contact_to_institutions: dict[str, list[str]] = defaultdict(list)
    for record in all_records:
        for segment in _contact_segments(record.get("contact", "")):
            contact_to_institutions[segment].append(record["name"])
    cross_institution_review = [
        {"reason": "cross_institution_reuse", "contact": contact, "institutions": sorted(set(institutions))}
        for contact, institutions in contact_to_institutions.items()
        if len(set(institutions)) > 1
    ]
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "records_scanned": len(all_records),
        "summary": dict(Counter(action for item in contact_audit for action in item["actions"])),
        "auto_fixed": [item for item in contact_audit if item["actions"]],
        "manual_review": [item for item in contact_audit if item["manual_review"]] + cross_institution_review,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[sync] wrote {args.output} ({len(all_records)} records)")
    print(f"[sync] wrote {args.meta}")
    print(f"[sync] wrote {report_path}")


if __name__ == "__main__":
    main()
