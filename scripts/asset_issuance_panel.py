"""发行统计：逐期去重汇总，桌面与手机共用隔离的离线组件。"""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    '2025': ROOT / 'deliverables/ledger/01_source/2025年ABS发行台账.xlsx',
    '2026': ROOT / 'deliverables/ledger/03_final/2026年ABS发行台账-1030-定稿.xlsx',
}
CHANNELS = {'上交所': '交易所', '深交所': '交易所', '银行间': '银行间',
            '平层非标': '非标', '结构化非标': '非标', '非标': '非标', '中保登': '保登'}
ASSET_GROUPS = {
    '白条': ('赊销白条', '信托白条', '白条非标'),
    '现金贷': ('信托金条', '小贷金条', '信托白取', '白条取现', '白条取现非标',
              '白条取现非标（中保登）', '金条&白取混发', '金条&白取&白条混发',
              '金条&白取&信托白条混发'),
    '企业主贷': ('小贷企业主贷', '信托企业主贷', '企业主贷'),
    '保理': ('保理', '外部保理', '外部保理非标'),
    '金采': ('金采',),
    '汽车融资租赁': ('汽车融资租赁',),
    '动产质押': ('动产质押',),
    '京企贷': ('京企贷',),
}
ASSET_TO_GROUP = {asset: group for group, assets in ASSET_GROUPS.items() for asset in assets}
YEAR_ASSET_OVERRIDES = {
    '2025': {'小贷京小贷': '京企贷', '采购融资': '京企贷', '融资租赁': '融资租赁'},
}
TEMPLATE = Path(__file__).with_name('asset_issuance_panel.html')
CONSUMER_TEMPLATE = Path(__file__).with_name('consumer_abs_panel.html')
FRAME_ID = 'issuance-statistics-frame'


def date_value(value, epoch):
    if isinstance(value, (int, float)):
        value = from_excel(value, epoch)
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d')
    raise ValueError(f'无法识别簿记日期：{value!r}')


def read_year(year, path):
    book = load_workbook(path, read_only=True, data_only=True)
    sheet = book.worksheets[0]
    rows = sheet.iter_rows(values_only=True)
    ix = {v: i for i, v in enumerate(next(rows)) if v is not None}
    projects = {}
    for number, row in enumerate(rows, 2):
        name = row[ix['项目名称']]
        if not name:
            continue
        key = (row[ix['序号']], name)
        scale = Decimal(str(row[ix['规模']]))
        if scale <= 0:
            raise ValueError(f'{year} 第{number}行规模无效')
        date = date_value(row[ix['簿记时间']], book.epoch)
        asset = str(row[ix['资产类型']]).strip()
        venue = str(row[ix['发行场所']]).strip() if '发行场所' in ix else ''
        channel = CHANNELS.get(venue, '待补充')
        if venue and channel == '待补充':
            raise ValueError(f'未登记渠道：{venue}')
        signature = (asset, venue, scale, date)
        if key in projects:
            if projects[key]['signature'] != signature:
                raise ValueError(f'{year}项目头信息不一致：{key}')
            projects[key]['rows'].append(number)
            continue
        projects[key] = dict(signature=signature, name=str(name), serial=row[ix['序号']],
                             asset=asset, rawAsset=str(row[ix['资产类型']]), venue=venue,
                             channel=channel, scale=scale, date=date, rows=[number])
    book.close()
    records = sorted(projects.values(), key=lambda r: r['date'], reverse=True)
    assets = defaultdict(lambda: defaultdict(Decimal))
    totals = defaultdict(Decimal)
    group_names = ['融资租赁' if year == '2025' and name == '汽车融资租赁' else name
                   for name in ASSET_GROUPS]
    group_totals = {name: Decimal(0) for name in group_names}
    group_totals['其他待归类'] = Decimal(0)
    for p in records:
        assets[p['asset']][p['channel']] += p['scale']
        totals[p['channel']] += p['scale']
        p['group'] = YEAR_ASSET_OVERRIDES.get(year, {}).get(
            p['asset'], ASSET_TO_GROUP.get(p['asset'], '其他待归类'))
        group_totals[p['group']] += p['scale']
    total = sum(totals.values(), Decimal(0))
    assert sum(sum(a.values(), Decimal(0)) for a in assets.values()) == total
    assert sum(group_totals.values(), Decimal(0)) == total
    for p in records:
        p.pop('signature')
        p['scale'] = float(p['scale'])
    return dict(year=year, source=path.name, sheet=sheet.title,
                sourceSha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                count=len(records), total=float(total), asOf=max(p['date'] for p in records),
                channelComplete='发行场所' in ix, records=records,
                channels={k: float(v) for k, v in totals.items()},
                groups=[dict(name=k, total=float(v), count=sum(p['group'] == k for p in records),
                             assets=sorted({p['asset'] for p in records if p['group'] == k}))
                        for k, v in group_totals.items()],
                assets=[dict(name=k, channels={c: float(v) for c, v in a.items()},
                             total=float(sum(a.values(), Decimal(0)))) for k, a in assets.items()])



def compute_data(ledger):
    paths = {**SOURCES, '2026': Path(ledger)}
    data = {year: read_year(year, path) for year, path in paths.items()}
    for year, path in paths.items():
        if data[year]['sourceSha256'] != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError('发行统计生成期间源表发生变化')
    return data


def render_issuance_document(data):
    encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    encoded = encoded.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    return TEMPLATE.read_text(encoding='utf-8').replace('__DEMO_DATA__', encoded)


def render_document(data):
    import abs_balance_panel
    pages = {'issuance': render_issuance_document(data), 'balance': abs_balance_panel.render_document()}
    encoded = json.dumps(pages, ensure_ascii=False, separators=(',', ':'))
    encoded = encoded.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    return CONSUMER_TEMPLATE.read_text(encoding='utf-8').replace('__DATA__', encoded)


def render_body(data):
    document = escape(render_document(data), quote=True)
    return (f'<iframe id="{FRAME_ID}" title="消金ABS" srcdoc="{document}" '
            'style="display:block;width:100%;height:calc(100vh - 140px);min-height:600px;border:0;"></iframe>')


class _FrameParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.documents = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'iframe' and values.get('id') == FRAME_ID:
            self.documents.append(values.get('srcdoc', ''))


def extract_document(html):
    parser = _FrameParser()
    parser.feed(html)
    if len(parser.documents) != 1 or not parser.documents[0]:
        raise ValueError('发行统计组件缺失或重复')
    return parser.documents[0]


def verify_document(document, ledger):
    wrapper_marker = '<script id="consumer-abs-data" type="application/json">'
    if document.count(wrapper_marker) != 1:
        raise ValueError('消金ABS组件数据缺失或重复')
    pages = json.loads(document.split(wrapper_marker, 1)[1].split('</script>', 1)[0])
    if set(pages) != {'issuance', 'balance'}:
        raise ValueError('消金ABS缺少发行规模或存量余额')
    issuance = pages['issuance']
    marker = '<script id="issuance-data" type="application/json">'
    if issuance.count(marker) != 1:
        raise ValueError('发行统计数据标记缺失或重复')
    encoded = issuance.split(marker, 1)[1].split('</script>', 1)[0]
    data = json.loads(encoded)
    if set(data) != {'2025', '2026'}:
        raise ValueError('发行统计年份必须为2025与2026')
    for year, path in {'2025': SOURCES['2025'], '2026': Path(ledger)}.items():
        if data[year]['sourceSha256'] != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError(f'{year}发行统计来源陈旧，请完整重建看板')
    if document != render_document(data):
        raise ValueError('发行统计界面实现陈旧或内容不一致')
    return data
