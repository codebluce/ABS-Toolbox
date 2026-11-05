"""JoySpace资产余额快照：离线资产分布组件，桌面与手机共用。"""
from datetime import datetime, timedelta
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'data/asset_distribution_snapshot.json'
TEMPLATE = Path(__file__).with_suffix('.html')
FRAME_ID = 'asset-distribution-frame'


def compute_data():
    raw = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    cells = {(c['rowFrom'], c['colFrom']): c for c in raw['cells']}
    periods = []
    for col in range(5, 23):
        date = (datetime(1899, 12, 30) + timedelta(days=int(cells[(3, col)]['originalCellValue']))).strftime('%Y-%m-%d')
        if date >= '2023-01-01':
            periods.append({'col': col, 'date': date})
    def value(row, col):
        cell = cells.get((row, col))
        return None if cell is None else float(cell['originalCellValue'])
    assets = []
    for name, start, total in [('白条', 4, 9), ('金条', 10, 14), ('白条取现', 15, 19)]:
        parts = [{'name': cells[(row, 3)]['cellText'], 'row': row + 1,
                  'values': [value(row, p['col']) for p in periods]} for row in range(start, total)]
        totals = [value(total, p['col']) for p in periods]
        if any(v is None or v <= 0 for v in totals):
            raise ValueError('资产分布总余额缺失或无效')
        assets.append({'name': name, 'parts': parts, 'totals': totals})
    return {'periods': periods, 'assets': assets, 'source': raw['source'], 'sheet': raw['sheet'],
            'retrievedAt': raw['retrievedAt'], 'unit': '原表未注明'}


def render_document(data):
    encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    return TEMPLATE.read_text(encoding='utf-8').replace('__DATA__', encoded)


def render_body(data=None):
    document = escape(render_document(data if data is not None else compute_data()), quote=True)
    return (f'<iframe id="{FRAME_ID}" title="资产分布" srcdoc="{document}" '
            'style="display:block;width:100%;height:calc(100vh - 140px);min-height:600px;border:0;"></iframe>')


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.documents = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'iframe' and attrs.get('id') == FRAME_ID:
            self.documents.append(attrs.get('srcdoc', ''))


def extract_document(html):
    parser = _Parser()
    parser.feed(html)
    if len(parser.documents) != 1 or not parser.documents[0]:
        raise ValueError('资产分布组件缺失或重复')
    return parser.documents[0]


def verify_document(document):
    if document != render_document(compute_data()):
        raise ValueError('资产分布来源或实现陈旧，请完整重建看板')
