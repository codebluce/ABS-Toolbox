"""把 JoySpace 导出的《管理人与投资人进展表》Excel 转成机构画像所需的 rangeData JSON。

为什么需要这一步
----------------
机构画像原来靠 JoySpace 的逐格接口导出 rangeData，一个页签几百个单元格、
每个单元格十几行 JSON，人工或模型都不适合反复搬运。JoySpace 自带“导出为 Excel”，
一次就能拿到整本工作簿；这里把 Excel 还原成同一套 rangeData 结构，
下游 `sync_institution_profile.py` 不用改。

用法：
  python scripts/import_institution_profile_xlsx.py \
      --xlsx ~/Downloads/2026年ABS管理人与投资人进展表.xlsx \
      --out-dir data/joyspace_profile_sync/20261114
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
OWNER_SHEETS = ["吴沛智", "李亦非", "姜守园", "邓殷洁", "高雅"]


def cell_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def sheet_to_range_data(ws) -> list[dict]:
    cells = []
    for row in ws.iter_rows():
        for cell in row:
            text = cell_text(cell.value)
            if not text:
                continue
            cells.append({
                "rowFrom": cell.row - 1,
                "colFrom": cell.column - 1,
                "cellText": text,
            })
    return cells


def main() -> None:
    parser = argparse.ArgumentParser(description="JoySpace 进展表 Excel → rangeData JSON")
    parser.add_argument("--xlsx", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--owners", nargs="*", default=OWNER_SHEETS)
    args = parser.parse_args()

    wb = openpyxl.load_workbook(args.xlsx, data_only=True)
    missing = [name for name in args.owners if name not in wb.sheetnames]
    if missing:
        raise SystemExit(f"工作簿缺少页签：{missing}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for owner in args.owners:
        cells = sheet_to_range_data(wb[owner])
        path = args.out_dir / f"{owner}.json"
        path.write_text(json.dumps(cells, ensure_ascii=False), encoding="utf-8")
        print(f"[export] {owner}: {len(cells)} cells → {path}")
    wb.close()


if __name__ == "__main__":
    main()
