"""消金ABS存量余额，读取受控季度快照。"""
import calendar
import json
import re
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'data/abs_balance_snapshot.json'
TEMPLATE = Path(__file__).with_suffix('.html')
CHANNELS = ['上交所', '深交所', '银行间', '中保登', '非标']


def compute_data():
    source = json.loads(SNAPSHOT.read_text())
    cells = {(c['rowFrom'], c['colFrom']): c for c in source['cells']}
    periods = []
    checks = []
    for (row, col), header in sorted(cells.items()):
        label = header['cellText'].strip()
        if row != 26 or not label.endswith('余额口径'):
            continue
        stamp = label.removesuffix('余额口径')
        if stamp == '2024H1':
            year, month = 2024, 6
        elif len(stamp) == 8:
            year, month = int(stamp[:4]), int(stamp[4:6])
        elif len(stamp) == 6:
            year, month = int(stamp[:4]), int(stamp[4:])
        else:
            raise ValueError(f'无法识别余额时点: {label}')
        if month not in (3, 6, 9, 12):
            continue
        date = f'{year}-{month:02d}-{calendar.monthrange(year, month)[1]}'
        columns = []
        for c in range(col + 1, col + 7):
            name = cells[(27, c)]['cellText'].strip()
            columns.append((c, name))
        if [name for _, name in columns[:5]] != CHANNELS:
            raise ValueError(f'余额渠道表头不符: {label}')
        records = []
        for r in range(28, 36):
            name_cell = cells.get((r, col))
            if not name_cell or name_cell['cellText'].strip() in ('总计', '合计'):
                continue
            name = name_cell['cellText'].strip()
            amounts = {}
            refs = {}
            for c, channel in columns[:5]:
                cell = cells.get((r, c))
                if cell is None:
                    amounts[channel] = None
                    continue
                raw = str(cell['originalCellValue']).strip()
                if raw in ('', '-', '—'):
                    amounts[channel] = None
                    continue
                value = Decimal(raw.replace(',', ''))
                if not value.is_finite() or value < 0:
                    raise ValueError(f'无效余额: {r+1}, {c+1}')
                amounts[channel] = float(value)
                refs[channel] = [r + 1, c + 1]
            total_cell = cells.get((r, columns[-1][0]))
            if total_cell is None:
                raise ValueError(f'资产余额合计缺失: {label}, {name}')
            total = float(Decimal(str(total_cell['originalCellValue'])))
            known = sum(v for v in amounts.values() if v is not None)
            residual = round(total - known, 6)
            if abs(residual) > 0.02:
                raise ValueError(f'资产余额不平: {label}, {name}, {residual}')
            if residual:
                checks.append({'date': date, 'name': name, 'roundingResidual': residual})
            records.append({'name': name, 'channels': amounts, 'total': total,
                            'sourceRow': r + 1, 'sourceColumns': refs})
        if not records:
            raise ValueError('余额记录为空')
        total = sum(r['total'] for r in records)
        totals = {channel: sum(r['channels'][channel] or 0 for r in records)
                  for channel in CHANNELS}
        periods.append({'date': date, 'sourceLabel': label, 'records': records,
                        'total': total, 'channels': totals})
    periods.sort(key=lambda p: p['date'])
    if len({p['date'] for p in periods}) != len(periods):
        raise ValueError('余额时点重复')
    latest = periods[-1]
    assert len(periods) == 10
    assert abs(latest['total'] - 2240.6) < 1e-7
    assert abs(sum(latest['channels'].values()) - latest['total']) < 1e-7
    return {'periods': periods, 'channels': CHANNELS, 'source': source['source'],
            'sheet': source['sheet'], 'range': source['range'],
            'retrievedAt': source['retrievedAt'], 'unit': '表内未标注',
            'checks': checks}



def render_document():
    data = compute_data()
    encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    encoded = encoded.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    return TEMPLATE.read_text().replace('__DATA__', encoded)
