"""JoySpace 数据源登记表：统一管理取数入口、新鲜度检查和快照写回。

为什么要有这个脚本
------------------
机构速查、次级速查、消金资产、风险表现四个面板的数据都来自 JoySpace，
但取数方式各不相同（整本导出 / 单页签读取 / 指定区域 rangeData），
页面和页签编号也只存在于历史对话里。结果就是：台账每周更新，面板却停在几周前，
而且没人说得清该去读哪张表、哪个页签。

这里把“哪张表、哪个页签、什么方式、写到哪个文件”固化成 data/joyspace_sources.json，
脚本负责校验登记表、对比快照与台账的日期差、并给出可直接执行的取数指令。

用法：
  python scripts/joyspace_sources.py list
  python scripts/joyspace_sources.py check
  python scripts/joyspace_sources.py check --strict
  python scripts/joyspace_sources.py apply --dataset asset_distribution \
      --input /tmp/range.json --date 2026-11-14
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "joyspace_sources.json"
DEFAULT_LEDGER_DIR = ROOT / "deliverables" / "ledger" / "03_final"

REQUIRED = ("key", "label", "page_url", "page_id", "sheets", "target", "date_field", "refresh")


def load_registry(path: Path | None = None) -> dict:
    path = path or REGISTRY
    data = json.loads(path.read_text(encoding="utf-8"))
    datasets = data.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        raise ValueError("数据源登记表为空")
    seen = set()
    for item in datasets:
        missing = [field for field in REQUIRED if not item.get(field)]
        if missing:
            raise ValueError(f"{item.get('key', '?')} 缺少字段：{missing}")
        if item["key"] in seen:
            raise ValueError(f"数据集 key 重复：{item['key']}")
        seen.add(item["key"])
        if not item["page_id"]:
            raise ValueError(f"{item['key']} 缺少 page_id")
        for sheet in item["sheets"]:
            if not sheet.get("name") or sheet.get("sheet_id") is None:
                raise ValueError(f"{item['key']} 的页签缺少 name/sheet_id：{sheet}")
    return data


def read_url(dataset: dict, sheet: dict) -> str:
    return f"{dataset['page_url']}?sheetId={sheet['sheet_id']}"


def _dig(payload, dotted: str):
    cur = payload
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def snapshot_date(dataset: dict) -> str | None:
    path = ROOT / dataset["target"]
    if not path.exists():
        return None
    value = _dig(json.loads(path.read_text(encoding="utf-8")), dataset["date_field"])
    return str(value)[:10] if value else None


def ledger_cutoff(path: Path | None = None) -> str | None:
    if path is None:
        finals = sorted(DEFAULT_LEDGER_DIR.glob("2026年ABS发行台账-*-定稿.xlsx"))
        if not finals:
            return None
        path = finals[-1]
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb.worksheets[0]
    header = [str(c.value or "").replace("\n", "") for c in next(ws.iter_rows(max_row=1))]
    if "簿记时间" not in header:
        wb.close()
        return None
    col = header.index("簿记时间") + 1
    latest = None
    for row in ws.iter_rows(min_row=2, min_col=col, max_col=col, values_only=True):
        value = row[0]
        if hasattr(value, "date"):
            value = value.date()
        if isinstance(value, date) and (latest is None or value > latest):
            latest = value
    wb.close()
    return latest.isoformat() if latest else None


def cmd_list(_args) -> int:
    data = load_registry()
    for item in data["datasets"]:
        print(f"\n[{item['key']}] {item['label']}  取数方式={item['refresh']}")
        print(f"  页面: {item['page_url']}")
        for sheet in item["sheets"]:
            print(f"    - {sheet['name']} (sheetId={sheet['sheet_id']})  {read_url(item, sheet)}")
        print(f"  写入: {item['target']}（日期字段 {item['date_field']}）")
        if item.get("apply_command"):
            print(f"  应用: {item['apply_command']}")
    return 0


def stale_datasets(cutoff: str, max_lag: int = 7) -> list[tuple[str, str | None, int | None]]:
    """返回落后超过 max_lag 天的数据集：(label, 快照日期, 落后天数)。"""
    base = date.fromisoformat(cutoff)
    result = []
    for item in load_registry()["datasets"]:
        value = snapshot_date(item)
        if not value:
            result.append((item["label"], None, None))
            continue
        lag = (base - date.fromisoformat(value)).days
        if lag > max_lag:
            result.append((item["label"], value, lag))
    return result


def cmd_check(args) -> int:
    data = load_registry()
    cutoff = ledger_cutoff(args.ledger)
    if not cutoff:
        print("[joyspace] 读不到台账最新簿记日，无法判断新鲜度", file=sys.stderr)
        return 2
    base = date.fromisoformat(cutoff)
    rows, stale = [], []
    for item in data["datasets"]:
        value = snapshot_date(item)
        if not value:
            rows.append((item["label"], "缺失", "-", item["refresh"]))
            stale.append(item)
            continue
        lag = (base - date.fromisoformat(value)).days
        rows.append((item["label"], value, f"{lag} 天", item["refresh"]))
        if lag > args.max_lag:
            stale.append(item)
    print(f"台账最新簿记日：{cutoff}（阈值 {args.max_lag} 天）")
    print(f"{'面板':<10}{'快照日期':<14}{'落后':<8}取数方式")
    for label, value, lag, refresh in rows:
        print(f"{label:<10}{value:<14}{lag:<8}{refresh}")
    if not stale:
        print("\n全部在阈值内。")
        return 0
    print("\n需要刷新：")
    for item in stale:
        print(f"\n[{item['label']}] {item['refresh_hint']}")
        for sheet in item["sheets"]:
            print(f"    读取: {read_url(item, sheet)}")
        if item.get("apply_command"):
            print(f"    应用: {item['apply_command']}")
    return 1 if args.strict else 0


def _unwrap(payload):
    """兼容三种输入：MCP 原始响应、rangeData 列表、带 rangeData 的对象。"""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, str):
        payload = json.loads(payload)
    for path in (("data", "data", "data", "rangeData"), ("data", "data", "rangeData"), ("data", "rangeData")):
        cur = payload
        ok = True
        for part in path:
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and isinstance(cur, list):
            return cur
    if isinstance(payload, dict) and isinstance(payload.get("rangeData"), list):
        return payload["rangeData"]
    raise ValueError("无法从输入解析 rangeData 列表")


def cells_from_xlsx(path: Path, item: dict) -> list[dict]:
    """把导出的 Excel 按登记表的区域还原成 rangeData。

    日期单元格必须保留 Excel 序列号：消金资产面板用 originalCellValue 反算表头日期，
    只给文本会让表头全部失效。
    """
    import openpyxl
    from datetime import datetime as _dt

    cfg = item["range"]
    sheet_name = item["sheets"][0]["name"]
    wb = openpyxl.load_workbook(path, data_only=True)
    if sheet_name not in wb.sheetnames:
        raise SystemExit(f"{path.name} 缺少页签：{sheet_name}")
    ws = wb[sheet_name]
    cells = []
    for row in range(cfg["row_from"] + 1, cfg["row_to"] + 2):
        for col in range(cfg["col_from"] + 1, cfg["col_to"] + 2):
            value = ws.cell(row, col).value
            if value is None or str(value).strip() == "":
                continue
            cell = {"rowFrom": row - 1, "colFrom": col - 1}
            if isinstance(value, _dt):
                cell["originalCellValue"] = (_dt(value.year, value.month, value.day) - _dt(1899, 12, 30)).days
                cell["cellText"] = value.strftime("%Y-%m")
            else:
                text = str(value).strip()
                if isinstance(value, float) and value.is_integer():
                    text = str(int(value))
                cell["originalCellValue"] = text
                cell["cellText"] = text
            cells.append(cell)
    wb.close()
    return cells


def cmd_apply(args) -> int:
    data = load_registry()
    item = next((d for d in data["datasets"] if d["key"] == args.dataset), None)
    if not item:
        print(f"未登记的数据集：{args.dataset}", file=sys.stderr)
        return 2
    if item["key"] != "asset_distribution":
        print(f"[{item['label']}] 暂不支持自动写回，请按提示重建：{item['refresh_hint']}", file=sys.stderr)
        return 3

    if getattr(args, "xlsx", None):
        cells = cells_from_xlsx(args.xlsx, item)
    else:
        if not args.input:
            print("需要 --input <rangeData.json> 或 --xlsx <导出文件>", file=sys.stderr)
            return 2
        cells = _unwrap(json.loads(Path(args.input).read_text(encoding="utf-8")))
    target = ROOT / item["target"]
    snapshot = json.loads(target.read_text(encoding="utf-8"))
    range_cfg = item["range"]
    snapshot["cells"] = cells
    snapshot["retrievedAt"] = args.date
    snapshot["sheet"] = item["sheets"][0]["name"]
    snapshot["sheetId"] = item["sheets"][0]["sheet_id"]
    snapshot["source"] = item["page_url"]
    snapshot["range"] = (
        f"{chr(65 + range_cfg['col_from'])}{range_cfg['row_from'] + 1}:"
        f"{chr(65 + range_cfg['col_to'])}{range_cfg['row_to'] + 1}"
    )
    target.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[apply] {item['label']}: {len(cells)} cells → {target}（{args.date}）")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="JoySpace 数据源登记表与新鲜度检查")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="列出登记的数据源与页签")
    p_list.set_defaults(func=cmd_list)

    p_check = sub.add_parser("check", help="对比快照与台账最新簿记日")
    p_check.add_argument("--ledger", type=Path, default=None)
    p_check.add_argument("--max-lag", type=int, default=7)
    p_check.add_argument("--strict", action="store_true", help="有落后时返回非零")
    p_check.set_defaults(func=cmd_check)

    p_apply = sub.add_parser("apply", help="把 rangeData 写回快照")
    p_apply.add_argument("--dataset", required=True)
    p_apply.add_argument("--input", type=Path, default=None)
    p_apply.add_argument("--xlsx", type=Path, default=None, help="JoySpace 导出的 Excel，按登记区域还原")
    p_apply.add_argument("--date", required=True)
    p_apply.set_defaults(func=cmd_apply)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
