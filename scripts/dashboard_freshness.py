"""看板各面板的“数据截止日”取自来源本身，而不是生成时间。

为什么不用生成时间
------------------
看板每周重生成一次，但各面板的数据新鲜度并不相同：台账是当周最新，
机构画像的 JoySpace 快照可能还停在两周前，次级配售快照更早。用生成时间
统一标注，等于给旧数据盖新日期——这正是“看起来更新了、其实没有”的来源。

所以这里逐面板回到来源取日期；取不到就返回 None，由生成器阻断，
不允许出现没有截止日的面板。
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        # Excel 日期序列号（1900 起算），2024–2026 落在 45000–47000 区间
        if 20000 <= value <= 70000:
            from openpyxl.utils.datetime import from_excel
            return from_excel(value).date()
        return None
    text = str(value).strip()
    if not text:
        return None
    numbers = re.findall(r'\d+', text)
    if len(numbers) == 1 and len(numbers[0]) == 8:
        numbers = [numbers[0][:4], numbers[0][4:6], numbers[0][6:]]
    if len(numbers) >= 3:
        year, month, day = (int(part) for part in numbers[:3])
    elif len(numbers) == 2:
        year, month, day = int(numbers[0]), int(numbers[1]), 1
    else:
        return None
    if year < 100:
        year += 2000
    if not 1990 <= year <= 2100:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def iso(value) -> str | None:
    parsed = _as_date(value)
    return parsed.isoformat() if parsed else None


def _find_column(sheet, name: str, max_rows: int = 4):
    """按表头文字定位列，返回 (表头行号, 列号)。

    历史台账（2024 年）的列顺序与近两年不同，按固定列号取会读到别的内容，
    所以一律以表头为准；找不到就返回 None。
    """
    for row_index, row in enumerate(
            sheet.iter_rows(min_row=1, max_row=max_rows, values_only=True), start=1):
        for column_index, value in enumerate(row, start=1):
            if value is None:
                continue
            if str(value).strip() == name:
                return row_index, column_index
    return None


def _column_values(path, name: str):
    book = openpyxl.load_workbook(path, data_only=True, read_only=True)
    try:
        sheet = book['总表'] if '总表' in book.sheetnames else book.active
        position = _find_column(sheet, name)
        if not position:
            return []
        header_row, column = position
        return [row[0] for row in sheet.iter_rows(
            min_row=header_row + 1, min_col=column, max_col=column, values_only=True)]
    finally:
        book.close()


def ledger_bookkeeping_cutoff(path) -> str | None:
    """台账里最新一条簿记时间（哪一天之前的事实已全部纳入）。

    按表头“簿记时间”定位列；该列不存在（历史年台账布局不同）时返回 None，
    由调用方退回到年度末。
    """
    latest = None
    for value in _column_values(path, '簿记时间'):
        parsed = _as_date(value)
        if parsed and (latest is None or parsed > latest):
            latest = parsed
    return latest.isoformat() if latest else None


def ledger_months(path) -> list[str]:
    """台账覆盖的月份（B 列），用于说明区间。"""
    months = []
    for value in _column_values(path, '月份'):
        text = str(value or '').strip()
        if re.fullmatch(r'\d{1,2}\s*月?', text) and text not in months:
            months.append(text)
    return months


def snapshot_date(filename: str, *keys, default: str | None = None) -> str | None:
    """从 data/ 下的快照 JSON 取抓取日期，按 keys 逐层下钻。"""
    path = DATA / filename
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding='utf-8'))
    for key in keys:
        if not isinstance(data, dict) or key not in data:
            data = None
            break
        data = data[key]
    if not isinstance(data, (str, int)) and data is not None:
        return None
    return iso(data) or default


def peer_issuance_cutoff(path) -> tuple[str | None, str]:
    """同业发行动态里最新一条簿记日，以及该记录所属周标签。"""
    import peer_issuance_panel
    records = peer_issuance_panel.parse_dynamics(Path(path))
    latest = None
    week = ''
    for record in records:
        parsed = _as_date(record.get('date'))
        if parsed and (latest is None or parsed >= latest):
            latest = parsed
            week = record.get('week') or week
    return (latest.isoformat() if latest else None), week


def latest_period(filename: str) -> str | None:
    """半年更新的表（消金资产）取最新数据期间，而不是导入时间。"""
    from datetime import datetime, timedelta

    path = DATA / filename
    if not path.is_file():
        return None
    snapshot = json.loads(path.read_text(encoding='utf-8'))
    cells = {(c.get('rowFrom'), c.get('colFrom')): c for c in snapshot.get('cells', [])}
    latest = None
    for col in range(5, 23):
        cell = cells.get((3, col))
        if not cell:
            continue
        try:
            day = (datetime(1899, 12, 30) + timedelta(days=int(cell.get('originalCellValue')))).date()
        except (TypeError, ValueError):
            continue
        if latest is None or day > latest:
            latest = day
    return latest.isoformat() if latest else None


def badge(date_text: str, source: str, note: str = '') -> str:
    """把截止日渲染成面板顶部的一行小字。"""
    note_html = f'<span class="df-note">{note}</span>' if note else ''
    return (
        f'<div class="data-freshness" data-asof="{date_text}">'
        f'<span class="df-label">数据截至</span>'
        f'<b>{date_text}</b>'
        f'<span class="df-source">{source}</span>'
        f'{note_html}'
        '</div>'
    )


FRESHNESS_CSS = """
.data-freshness {
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
  margin: 0 0 14px; padding: 7px 12px;
  background: rgba(64, 96, 160, .06); border-left: 3px solid rgba(64, 96, 160, .45);
  border-radius: 6px; font-size: 12.5px; color: #4a5568; line-height: 1.5;
}
.data-freshness .df-label { color: #7b8794; }
.data-freshness b { font-size: 13.5px; color: #22324d; letter-spacing: .3px; }
.data-freshness .df-source { color: #6b7a90; }
.data-freshness .df-note { color: #8a94a3; }
@media (max-width: 640px) {
  .data-freshness { font-size: 11.5px; padding: 6px 9px; gap: 6px; }
  .data-freshness .df-note { display: none; }
}
"""
