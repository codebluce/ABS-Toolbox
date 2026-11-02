"""将簿记明细的申购规模从万元换算为亿元，保留原文件不变。"""
from __future__ import annotations

import argparse
from decimal import Decimal
from pathlib import Path

import openpyxl


def convert_detail_amounts(input_path: Path, output_path: Path, divisor: Decimal,
                           project_name: str | None = None,
                           booking_date: str | None = None,
                           manager: str | None = None) -> int:
    """按档位表头逐段换算 C 列申购规模；返回换算的单元格数。"""
    if divisor <= 0:
        raise ValueError('divisor must be positive')
    wb = openpyxl.load_workbook(input_path)
    ws = wb.active
    converted = 0
    in_section = False
    for row in range(1, ws.max_row + 1):
        first = str(ws.cell(row, 1).value or '').strip()
        if '申购利率' in first:
            in_section = True
            ws.cell(row, 3, '申购规模（亿元）')
            continue
        if in_section:
            value = ws.cell(row, 3).value
            if value is None or str(value).strip() == '':
                in_section = False
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                ws.cell(row, 3, float(Decimal(str(value)) / divisor))
                converted += 1
    if project_name:
        ws['A1'], ws['B1'] = '项目名称', project_name
    if booking_date:
        ws['A2'], ws['B2'] = '簿记日期', booking_date
    if manager:
        ws['A3'], ws['B3'] = '管理人', manager
    ws['E1'] = '金额单位：原始表为万元，已除以10000换算为亿元；口径为申购规模，不是中标配售规模'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    wb.close()
    return converted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--divisor', type=Decimal, default=Decimal('10000'))
    parser.add_argument('--project')
    parser.add_argument('--booking-date')
    parser.add_argument('--manager')
    args = parser.parse_args()
    count = convert_detail_amounts(args.input, args.output, args.divisor,
                                   args.project, args.booking_date, args.manager)
    print(f'已换算 {count} 个申购规模单元格: {args.output}')


if __name__ == '__main__':
    main()
