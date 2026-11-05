"""JoySpace资产余额快照：离线风险表现组件，桌面与手机共用。"""
from datetime import datetime, timedelta
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'data/risk_performance_snapshot.json'
TEMPLATE = Path(__file__).with_suffix('.html')
FRAME_ID = 'risk-performance-frame'


def compute_data():
    data = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    if set(data['pages']) != {'dynamic', 'static'}:
        raise ValueError('风险表现必须同时包含动态池与静态池')
    return data


def render_document(data):
    encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    return TEMPLATE.read_text(encoding='utf-8').replace('__DATA__', encoded)


def render_body(data=None):
    document = escape(render_document(data if data is not None else compute_data()), quote=True)
    return (f'<iframe id="{FRAME_ID}" title="风险表现" srcdoc="{document}" '
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
        raise ValueError('风险表现组件缺失或重复')
    return parser.documents[0]


def verify_document(document):
    if document != render_document(compute_data()):
        raise ValueError('风险表现来源或实现陈旧，请完整重建看板')
