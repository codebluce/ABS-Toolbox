"""JoySpace 次级/夹层配售速查的 lab 独立预览。

首次导入: python3 scripts/lab/secondary_allocation_quick.py --import-dir <含1月.tsv…9月.tsv的目录>
后续预览: python3 scripts/lab/secondary_allocation_quick.py

TSV 必须从用户有权访问的 JoySpace 月份 sheet 复制取得；此脚本不连接线上表格。
快照只保留逐笔获配字段，不保留整本表及其辅助测算列。
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys

LAB_DIR = Path(__file__).resolve().parent
if str(LAB_DIR.parent) not in sys.path:
    sys.path.insert(0, str(LAB_DIR.parent))
from secondary_allocation_panel import ALLOCATION_CSS, SNAPSHOT_PATH, render_body
TEMPLATE_PATH = LAB_DIR / 'secondary_allocation_quick_template.html'
PREVIEW_PATH = LAB_DIR.parent.parent / 'deliverables' / 'dashboards' / '02_history' / 'lab_viz' / 'secondary_allocation_quick_preview.html'
SOURCE_URL = 'https://joyspace.jd.com/sheets/89PMGlBmUHUueYQ6Cl7L'
MONTHS = tuple(f'{m}月' for m in range(1, 10))


def cell(row: list[str], index: int) -> str:
    return row[index].strip() if index < len(row) else ''


def number(value: str) -> Decimal | None:
    try:
        return Decimal(value.strip().replace(',', ''))
    except (InvalidOperation, ValueError):
        return None


def as_number(value: Decimal) -> int | float:
    return int(value) if value == int(value) else float(value)


def rate(value: str) -> str:
    """Excel 百分数显示与原始小数并存；只规范纯数字小数。"""
    value = value.strip()
    parsed = number(value)
    if parsed is not None and parsed < 1:
        return f'{parsed * 100:.2f}%'
    return value or '—'


def allocation(month: str, level: str, investor: str, amount: Decimal, *,
               asset: str, project: str, manager: str, tenor: str, price: str,
               premium: str, scale: str, tranche: str, origin: str,
               status: str, source: str, section: str = '项目明细',
               original_amount: str = '') -> dict:
    return {
        'month': month, 'level': level, 'investor': investor.strip(),
        'amount_wan': as_number(amount), 'asset': asset or '—',
        'project': project, 'manager': manager or '—', 'tenor': tenor or '—',
        'price': rate(price), 'premium': rate(premium) if level == '次级' else '—',
        'scale': scale or '—', 'tranche': tranche or '—',
        'origin': origin or '—', 'status': status or '—',
        'source': source, 'section': section,
        'original_amount': original_amount,
    }


def parse_main(month: str, rows: list[list[str]]) -> list[dict]:
    result: list[dict] = []
    asset = ''
    context: dict | None = None
    is_april = month == '4月'
    for lineno, row in enumerate(rows, start=1):
        if cell(row, 2) == '项目名称':
            context = None
            # 有些重复表头 A 格直接写了资产类型。
            if cell(row, 0) not in ('', '资产类型', '序号'):
                asset = cell(row, 0).replace('\n', '')
            continue
        if month == '2月' and cell(row, 1) not in ('', '资产类型') and cell(row, 2):
            asset = cell(row, 1)
        elif cell(row, 0) not in ('', '资产类型', '序号', '中保登') and cell(row, 2):
            asset = cell(row, 0).replace('\n', '')
        if cell(row, 0) == '中保登':
            context = None
            continue
        if cell(row, 2):
            context = {
                'asset': asset, 'project': cell(row, 2), 'manager': cell(row, 3),
                'tenor': cell(row, 4), 'junior_price': cell(row, 8 if is_april else 7),
                'premium': cell(row, 9 if is_april else 8),
                'mezz_price': cell(row, 14 if is_april else 12),
                'scale': cell(row, 16 if is_april else 14),
                'tranche': cell(row, 17 if is_april else 15),
                'origin': cell(row, 18 if is_april else 16),
                'status': cell(row, 19 if is_april else 17),
            }
        if not context:
            continue
        junior_index, junior_amount = (5, 7) if is_april else (5, 6)
        mezz_index, mezz_amount = (11, 13) if is_april else (10, 11)
        # 3 月主表 G 格明确命名为「报量」/「次级券」，不可推断为最终分量。
        if month != '3月':
            amount = number(cell(row, junior_amount))
            investor = cell(row, junior_index)
            if investor and amount is not None and amount > 0:
                result.append(allocation(
                    month, '次级', investor, amount,
                    asset=context['asset'], project=context['project'],
                    manager=context['manager'], tenor=context['tenor'],
                    price=context['junior_price'], premium=context['premium'],
                    scale=context['scale'], tranche=context['tranche'],
                    origin=context['origin'], status=context['status'],
                    source=f'{month}!{chr(65 + junior_index)}{lineno}/{chr(65 + junior_amount)}{lineno}',
                ))
        amount = number(cell(row, mezz_amount))
        investor = cell(row, mezz_index)
        if investor and amount is not None and amount > 0:
            result.append(allocation(
                month, '夹层', investor, amount,
                asset=context['asset'], project=context['project'],
                manager=context['manager'], tenor=context['tenor'],
                price=context['mezz_price'], premium='',
                scale=context['scale'], tranche=context['tranche'],
                origin=context['origin'], status=context['status'],
                source=f'{month}!{chr(65 + mezz_index)}{lineno}/{chr(65 + mezz_amount)}{lineno}',
            ))
    return result


def parse_registration(month: str, rows: list[list[str]]) -> list[dict]:
    """1-3 月中保登独立分层，分量列分别是 C/C/D，原表单位万。"""
    if month not in ('1月', '2月', '3月'):
        return []
    result: list[dict] = []
    in_section = False
    project = ''
    tenor = ''
    scale = ''
    tranche = ''
    level = ''
    price = ''
    amount_col = 3 if month == '3月' else 2
    for lineno, row in enumerate(rows, start=1):
        b = cell(row, 1)
        if cell(row, 0) == '中保登':
            in_section = True
        if not in_section:
            continue
        if b.startswith('京') and not cell(row, 2) and not cell(row, 3):
            project = b
            tenor_match = re.search(r'[（(](\d+(?:\+\d+)+)[）)]', b)
            tenor = tenor_match.group(1) if tenor_match else ''
            scale_match = re.search(r'(\d+(?:\.\d+)?)\s*亿', b)
            scale = scale_match.group(1) if scale_match else ''
            tranche = level = price = ''
            continue
        if '设立' in b or '缴款' in b:
            matches = re.findall(r'[（(]([\d：:]+)[）)]', b)
            if matches:
                tranche = matches[-1].replace('：', ':')
            continue
        if re.match(r'^优先', b):
            level = ''
            continue
        if re.match(r'^(次级|中间级|夹层)', b):
            level = '次级' if b.startswith('次级') else '夹层'
            price_match = re.search(r'(\d+(?:\.\d+)?)\s*%', b)
            price = price_match.group(0).replace(' ', '') if price_match else ''
            continue
        amount = number(cell(row, amount_col))
        if project and level and b and amount is not None and amount > 0:
            result.append(allocation(
                month, level, b, amount,
                asset='中保登', project=project, manager='', tenor=tenor,
                price=price, premium='', scale=scale, tranche=tranche, origin='',
                status=cell(row, 5 if month == '3月' else 4),
                section='独立分层',
                source=f'{month}!B{lineno}/{chr(65 + amount_col)}{lineno}',
            ))
    return result


def parse_structured(month: str, rows: list[list[str]]) -> list[dict]:
    """5/6 月 3:1 结构化次级独立分层；原表以亿(e)计，面板统一换算为万。"""
    if month not in ('5月', '6月'):
        return []
    result: list[dict] = []
    investor_col, amount_col = (2, 3) if month == '5月' else (1, 2)
    project = ''
    level = ''
    price = ''
    tenor = ''
    scale = ''
    for lineno, row in enumerate(rows, start=1):
        b = cell(row, investor_col)
        if '3：1结构化次级' in b or '3:1结构化次级' in b:
            project = b
            level = price = tenor = scale = ''
            continue
        if not project:
            continue
        if re.search(r'\d+\+\d+\s*[，,]', b):
            m = re.search(r'(\d+\+\d+)\s*[，,]\s*(\d+(?:\.\d+)?)e', b, re.I)
            if m:
                tenor, scale = m.groups()
            continue
        if b.startswith('优先'):
            level = ''
            continue
        if b.startswith('次级'):
            level = '次级'
            price_match = re.search(r'(\d+(?:\.\d+)?)%', b)
            price = price_match.group(0) if price_match else ''
            continue
        amount = number(cell(row, amount_col))
        if b and level and amount is not None and amount > 0:
            result.append(allocation(
                month, level, b, amount * 10000,
                asset='结构化次级', project=project, manager='', tenor=tenor,
                price=price, premium='', scale=scale, tranche='3:1', origin='',
                status=cell(row, 5) if month == '5月' else '',
                section='独立分层', original_amount=f'{amount}亿',
                source=f'{month}!{chr(65 + investor_col)}{lineno}/{chr(65 + amount_col)}{lineno}',
            ))
    return result


def parse_month(month: str, rows: list[list[str]]) -> list[dict]:
    return parse_main(month, rows) + parse_registration(month, rows) + parse_structured(month, rows)


def import_snapshot(directory: Path, snapshot_date: str) -> dict:
    records: list[dict] = []
    for month in MONTHS:
        with (directory / f'{month}.tsv').open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.reader(stream, delimiter='\t'))
        if not rows or '项目名称' not in rows[0]:
            raise ValueError(f'{month}: 未识别 JoySpace 项目明细表头')
        records += parse_month(month, rows)
    return {
        'source_url': SOURCE_URL, 'source_title': '终版-26年次级分配',
        'snapshot_date': snapshot_date,
        'scope': '2026年1–9月；主项目块按投资人分量，另含中保登及3:1结构化分层；3月主表次级报量暂不计入',
        'records': records,
    }


def build_preview(snapshot: dict) -> str:
    template = TEMPLATE_PATH.read_text(encoding='utf-8')
    return (template.replace('__ALLOC_CSS__', ALLOCATION_CSS)
                    .replace('__ALLOC_PANEL__', render_body(snapshot, preview=True)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--import-dir', type=Path, help='临时 JoySpace 月份 TSV 所在目录')
    parser.add_argument('--snapshot-date', default=date.today().isoformat())
    args = parser.parse_args()
    if args.import_dir:
        snapshot = import_snapshot(args.import_dir, args.snapshot_date)
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    else:
        snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding='utf-8'))
    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW_PATH.write_text(build_preview(snapshot), encoding='utf-8')
    print(f'预览: {PREVIEW_PATH} ({len(snapshot["records"])} 条明细; 快照 {snapshot["snapshot_date"]})')


if __name__ == '__main__':
    main()
