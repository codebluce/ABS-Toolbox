"""把台账中的简单算术公式固化为数值，保留原始文件不变。"""
from __future__ import annotations

import argparse
import re
from decimal import Decimal
from pathlib import Path

import openpyxl
from openpyxl.utils import column_index_from_string


def normalize_formula_cells(ws) -> int:
    cache: dict[tuple[int, int], Decimal] = {}

    def cell_decimal(row: int, col: int) -> Decimal:
        if (row, col) in cache:
            return cache[(row, col)]
        value = ws.cell(row, col).value
        if isinstance(value, str) and value.startswith('='):
            result = evaluate(value[1:], row, col)
        elif value is None or str(value).strip() == '':
            result = Decimal(0)
        else:
            result = Decimal(str(value))
        cache[(row, col)] = result
        return result

    def evaluate(expr: str, row: int, col: int) -> Decimal:
        def replace_ref(match):
            ref = match.group(0).replace('$', '')
            letters = re.match(r'[A-Z]+', ref).group(0)
            number = int(ref[len(letters):])
            return str(cell_decimal(number, column_index_from_string(letters)))
        expr = re.sub(r'\$?[A-Z]{1,3}\$?\d+', replace_ref, expr)
        expr = re.sub(r'(\d+(?:\.\d+)?)%', lambda m: str(Decimal(m.group(1)) / 100), expr)
        expr = re.sub(r'(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])', r"Decimal('\1')", expr)
        if not re.fullmatch(r"[0-9A-Za-z_'().+\-*/\s]+", expr):
            raise ValueError(f'{ws.title}!{openpyxl.utils.get_column_letter(col)}{row}: 无法安全计算公式 {expr!r}')
        return eval(expr, {'__builtins__': {}}, {'Decimal': Decimal})

    count = 0
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and cell.value.startswith('='):
                cell.value = float(cell_decimal(cell.row, cell.column))
                count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sheet', default='总表', help='只处理指定工作表，默认总表')
    args = parser.parse_args()
    wb = openpyxl.load_workbook(args.input)
    if args.sheet not in wb.sheetnames:
        raise ValueError(f'工作表不存在: {args.sheet}')
    total = normalize_formula_cells(wb[args.sheet])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.output)
    wb.close()
    print(f'已固化 {total} 个公式单元格: {args.output}')


if __name__ == '__main__':
    main()
