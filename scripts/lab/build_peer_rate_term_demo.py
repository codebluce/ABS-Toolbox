"""同业发行卡片：AAA利率按期限拆分 + 最近一笔发行明细 Demo。"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import peer_issuance_panel as p  # noqa: E402

OUT = ROOT / 'deliverables/dashboards/03_test/peer_rate_term_demo_20261112'
SOURCE = ROOT / 'deliverables/dashboards/03_source/peer_issuance/同业发行完整已录底稿_20261104.xlsx'
SHORT_COLOR = '#2a78d6'
LONG_COLOR = '#c98747'
SHORT_MAX = Decimal('1.1')
ZERO = Decimal('0')

# 仅本Demo的卡片归并：京东金条、白条取现（自主支付）及其混池合并为京东现金贷。
CARD_GROUPS = {
    '京东金条': '京东现金贷',
    '京东自主支付资产': '京东现金贷',
    '京东金条白取混池': '京东现金贷',
}
SCOPE_ORDER = ['京东金条', '京东自主支付资产', '京东金条白取混池']
ORIGINATOR_ALIASES = {
    '深圳海豚小贷': '海豚小贷',
    '美团三快小贷': '美团小贷',
}
FAMILY_ORDER = ['网商贷', '蚂蚁系资产', '抖音系资产', '腾讯微众系资产',
                '美团系资产', '度小满系资产', '京东系资产', '其他']
CN_NUM = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}


def cn_number(value: str) -> str:
    if value.isdigit():
        return value
    if value == '十':
        return '10'
    if '十' in value:
        left, right = value.split('十', 1)
        tens = CN_NUM.get(left, 1) if left else 1
        ones = CN_NUM.get(right, 0) if right else 0
        return str(tens * 10 + ones)
    return str(CN_NUM.get(value, value))


def card_name(base_asset: str) -> str:
    return CARD_GROUPS.get(base_asset, base_asset)


def family_of(name: str) -> str:
    if name == '网商贷':
        return '网商贷'
    if name.startswith('蚂蚁'):
        return '蚂蚁系资产'
    if name.startswith('抖音'):
        return '抖音系资产'
    if name.startswith('腾讯') or name.startswith('微众'):
        return '腾讯微众系资产'
    if name.startswith('美团'):
        return '美团系资产'
    if name.startswith('度小满'):
        return '度小满系资产'
    if name.startswith('京东'):
        return '京东系资产'
    return '其他'


def normalize_originator(name: str) -> str:
    """先走已确认的信托全称映射，再补本Demo发现的同类简称。"""
    normalized = p.normalize_trust_originator(name)
    return ORIGINATOR_ALIASES.get(normalized, normalized)


def short_project_name(product: str) -> str:
    """把产品全称压成便于卡片阅读的项目简称，保留原始全称在悬浮提示中。"""
    text = str(product or '')
    text = re.sub(r'^.*?(?:有限责任公司|有限公司|股份有限公司)', '', text)
    text = re.sub(r'\d{4}年度', '', text)
    text = re.sub(r'第([一二三四五六七八九十\d]+)期', lambda match: f'{cn_number(match.group(1))}期', text)
    text = re.sub(r'^(\d+期)(.+)$', r'\2\1', text)
    text = re.sub(r'[（(][^）)]*[）)]', '', text)
    for suffix in ('定向资产支持商业票据', '定向资产支持票据', '资产支持专项计划',
                   '资产支持商业票据', '资产支持计划'):
        text = text.replace(suffix, '')
    text = text.replace('京东白条', '').replace('京东科技', '').strip()
    return text[:22] or str(product or '—')


def latest_record(records: list[dict], bucket: str) -> dict | None:
    def in_bucket(record: dict) -> bool:
        term = record.get('term')
        if term is None or record.get('aaa') is None or record.get('date') is None:
            return False
        return term <= SHORT_MAX if bucket == 'short' else term > SHORT_MAX
    candidates = [record for record in records if in_bucket(record)]
    return max(candidates, key=lambda record: record['date']) if candidates else None


def build_cards(records: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        grouped[card_name(record['base_asset'])].append(record)
    ranked = sorted(grouped.items(), key=lambda item: -sum(r['amount'] for r in item[1]))
    latest_date = max(r['date'] for r in records if r['date'])
    cards = []
    for name, recs in ranked:
        amount = sum((r['amount'] for r in recs), ZERO)
        monthly = {month: ZERO for month in range(1, 13)}
        for record in recs:
            month = p.month_key(record)
            if month:
                monthly[month] += record['amount']
        week_dates: dict[str, date] = {}
        for record in recs:
            if record['date'] and (record['week'] not in week_dates or record['date'] < week_dates[record['week']]):
                week_dates[record['week']] = record['date']
        weeks = sorted(week_dates, key=lambda week: week_dates[week])
        weekly_short, weekly_long = [], []
        for week in weeks:
            week_records = [r for r in recs if r['week'] == week]
            short_avg = p.weighted_avg([(r['aaa'], r['amount']) for r in week_records
                                        if r['term'] is not None and r['term'] <= SHORT_MAX])
            long_avg = p.weighted_avg([(r['aaa'], r['amount']) for r in week_records
                                       if r['term'] is not None and r['term'] > SHORT_MAX])
            if short_avg is not None:
                weekly_short.append({'week': week, 'date': week_dates[week], 'avg': short_avg})
            if long_avg is not None:
                weekly_long.append({'week': week, 'date': week_dates[week], 'avg': long_avg})
        originator_totals: dict[str, Decimal] = {}
        for record in recs:
            originator = normalize_originator(record['originator'])
            originator_totals[originator] = originator_totals.get(originator, ZERO) + record['amount']
        originators = [{'name': name_, 'amount': value}
                       for name_, value in sorted(originator_totals.items(), key=lambda item: -item[1])]
        current_month = latest_date.month
        previous_month = current_month - 1
        mom_rows = []
        for entry in originators:
            cur = sum((r['amount'] for r in recs
                       if normalize_originator(r['originator']) == entry['name']
                       and p.month_key(r) == current_month), ZERO)
            prev = sum((r['amount'] for r in recs
                        if normalize_originator(r['originator']) == entry['name']
                        and p.month_key(r) == previous_month), ZERO)
            delta = cur - prev
            status = ('新增' if prev == ZERO and cur > ZERO else '增长' if delta > ZERO else '下降' if delta < ZERO else '持平')
            mom_rows.append({'name': entry['name'], 'prev': prev, 'cur': cur, 'delta': delta, 'status': status})
        mom_rows.sort(key=lambda row: -(row['cur'] + row['prev']))
        scope = [name_ for name_ in SCOPE_ORDER if name_ in {r['base_asset'] for r in recs}]
        if not scope:
            scope = sorted({r['base_asset'] for r in recs})
        cards.append({
            'name': name,
            'family': family_of(name),
            'asset_type': recs[0]['asset_type'] if recs else '',
            'count': len(recs),
            'amount': amount,
            'monthly': monthly,
            'weekly_rates_short': weekly_short,
            'weekly_rates_long': weekly_long,
            'term_counts': {
                'short': sum(1 for r in recs if r['term'] is not None and r['term'] <= SHORT_MAX),
                'long': sum(1 for r in recs if r['term'] is not None and r['term'] > SHORT_MAX),
                'missing': sum(1 for r in recs if r['term'] is None),
            },
            'latest_short': latest_record(recs, 'short'),
            'latest_long': latest_record(recs, 'long'),
            'originators': originators,
            'mom': {'current_month': current_month, 'previous_month': previous_month, 'rows': mom_rows},
            'scope': scope,
        })
    cards.sort(key=lambda card: (FAMILY_ORDER.index(card['family']), -card['amount'], card['name']))
    return cards


def rate_chart(short: list[dict], long: list[dict], width: int = 560, height: int = 176) -> str:
    all_points = short + long
    if not all_points:
        return '<div class="peer-issuance-spark-empty">暂无利率数据</div>'
    date_by_week = {point['week']: point.get('date') for point in all_points}
    weeks = sorted(date_by_week, key=lambda week: date_by_week[week] or date.min)
    values = [point['avg'] for point in all_points]
    low, high = min(values), max(values)
    pad = (high - low) * Decimal('0.15') if high > low else Decimal('0.001')
    lo, hi = low - pad, high + pad
    left, right, top, bottom = Decimal(46), Decimal(width - 10), Decimal(10), Decimal(height - 30)

    def x_at(week: str) -> Decimal:
        if len(weeks) == 1:
            return (left + right) / 2
        return left + (right - left) * Decimal(weeks.index(week)) / Decimal(len(weeks) - 1)

    def y_at(value: Decimal) -> Decimal:
        return bottom - (value - lo) / (hi - lo) * (bottom - top)

    parts = [f'<svg class="peer-issuance-chart peer-rate-chart" viewBox="0 0 {width} {height}" role="img" aria-label="AAA利率走势：1年期与2年期">']
    for index in range(5):
        value = lo + (hi - lo) * Decimal(index) / Decimal(4)
        y = y_at(value)
        parts.append(f'<line x1="{float(left):.0f}" y1="{float(y):.1f}" x2="{float(right):.0f}" y2="{float(y):.1f}" stroke="#e8eaee"/>')
        parts.append(f'<text x="{float(left) - 6:.0f}" y="{float(y) + 3:.1f}" font-size="9" fill="#999" text-anchor="end">{p.rate_pct(value)}</text>')
    parts.append(f'<line x1="{float(left):.0f}" y1="{float(top):.0f}" x2="{float(left):.0f}" y2="{float(bottom):.0f}" stroke="#c9cdd4"/>')
    parts.append(f'<line x1="{float(left):.0f}" y1="{float(bottom):.0f}" x2="{float(right):.0f}" y2="{float(bottom):.0f}" stroke="#c9cdd4"/>')
    step = 2 if len(weeks) <= 12 else 3 if len(weeks) <= 24 else 4
    label_indexes = set(range(0, len(weeks), step)) | {len(weeks) - 1}
    if len(label_indexes) > 1:
        previous = max(index for index in label_indexes if index != len(weeks) - 1)
        if len(weeks) - 1 - previous < step:
            label_indexes.discard(previous)
    for index in sorted(label_indexes):
        week = weeks[index]
        day = date_by_week[week]
        label = day.strftime('%m/%d') if day else week[:10]
        anchor = 'start' if index == 0 else 'end' if index == len(weeks) - 1 else 'middle'
        parts.append(f'<text x="{float(x_at(week)):.1f}" y="{float(bottom) + 14:.0f}" font-size="9" fill="#999" text-anchor="{anchor}">{label}</text>')
    for points, color, label in ((short, SHORT_COLOR, '1年期'), (long, LONG_COLOR, '2年期')):
        by_week = {point['week']: point['avg'] for point in points}
        segment, segments = [], []
        for week in weeks:
            if week in by_week:
                segment.append((x_at(week), y_at(by_week[week])))
            elif segment:
                segments.append(segment)
                segment = []
        if segment:
            segments.append(segment)
        for segment in segments:
            if len(segment) > 1:
                polyline = ' '.join(f'{float(x):.1f},{float(y):.1f}' for x, y in segment)
                parts.append(f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="1.8"/>')
        for week, value in by_week.items():
            day = date_by_week[week]
            title = f'{day.isoformat() if day else week} {label} {p.rate_pct(value)}'
            parts.append(f'<circle cx="{float(x_at(week)):.1f}" cy="{float(y_at(value)):.1f}" r="2.4" fill="{color}"><title>{title}</title></circle>')
    parts.append('</svg>')
    return ''.join(parts)


def legend(short: list[dict], long: list[dict]) -> str:
    def last(points: list[dict]) -> dict | None:
        return max(points, key=lambda item: item.get('date') or date.min) if points else None
    short_latest, long_latest = last(short), last(long)
    return (f'<div class="peer-rate-legend"><span><i style="background:{SHORT_COLOR}"></i>1年期（≤1.1年）'
            f'<b>{p.rate_pct(short_latest["avg"]) if short_latest else "—"}</b></span>'
            f'<span><i style="background:{LONG_COLOR}"></i>2年期（>1.1年）'
            f'<b>{p.rate_pct(long_latest["avg"]) if long_latest else "—"}</b></span></div>')


def latest_item(label: str, color: str, record: dict | None) -> str:
    if not record:
        return (f'<div class="peer-latest-row"><div class="peer-latest-left"><div class="peer-latest-head">'
                f'<span class="peer-latest-badge" style="--c:{color}">{label}</span><span>暂无发行</span></div>'
                '<div class="peer-latest-project peer-latest-empty">该期限档暂无有效发行记录</div></div>'
                '<div class="peer-latest-right"><div class="peer-latest-rate">—</div></div></div>')
    return (f'<div class="peer-latest-row"><div class="peer-latest-left"><div class="peer-latest-head">'
            f'<span class="peer-latest-badge" style="--c:{color}">{label}</span><span>{record["date"].isoformat()}</span></div>'
            f'<div class="peer-latest-project" title="{p.safe_text(record["product"])}">{p.safe_text(short_project_name(record["product"]))}</div>'
            f'<div class="peer-latest-sub">{p.safe_text(record["base_asset"])}</div></div>'
            f'<div class="peer-latest-right"><div class="peer-latest-rate">{p.rate_pct(record["aaa"])}</div>'
            f'<div class="peer-latest-facts">AAA年限 {record["term"]:.2f}年 · 发行规模 {p.yi(record["amount"])} 亿</div></div></div>')


def card_html(card: dict, latest_date: date) -> str:
    counts = card['term_counts']
    missing = f' · 期限缺失 {counts["missing"]} 期' if counts['missing'] else ''
    note = (f'1年期 {counts["short"]} 期 · 2年期 {counts["long"]} 期{missing}。'
            '周度加权平均；1.1年整无样本，按≤1.1年归1年期、>1.1年归2年期。')
    scope = '、'.join(card['scope'])
    scope_html = f'<p class="peer-scope">统计范围：{p.safe_text(scope)}</p>' if len(card['scope']) > 1 else ''
    latest_html = (f'<div class="peer-latest-list">{latest_item("1年期", SHORT_COLOR, card["latest_short"])}'
                   f'{latest_item("2年期", LONG_COLOR, card["latest_long"])}</div>')
    return (f'<section class="peer-issuance-card"><div class="peer-issuance-card-head">'
            f'<h3>{p.safe_text(card["name"])}</h3><span class="peer-issuance-tag">{p.safe_text(card["asset_type"])}</span>'
            f'<span class="peer-issuance-card-amount">{p.yi(card["amount"])} 亿 · {card["count"]} 期</span></div>'
            f'{scope_html}<h4>月度发行规模（亿元）</h4><div class="peer-issuance-months">{p.month_cells(card["monthly"])}</div>'
            f'<h4>AAA 发行利率走势（周度加权，按期限拆分）</h4>{legend(card["weekly_rates_short"], card["weekly_rates_long"])}'
            f'{rate_chart(card["weekly_rates_short"], card["weekly_rates_long"])}'
            f'<p class="peer-rate-note">{note}</p>'
            f'<h4>最近一笔发行</h4>{latest_html}'
            f'<h4>原始权益人发行规模与月度变化</h4>{p.originator_rows(card["originators"], card["amount"], card["mom"], latest_date)}</section>')


def family_section(family: str, cards: list[dict], latest_date: date) -> str:
    total = sum((card['amount'] for card in cards), ZERO)
    single = ' single' if len(cards) == 1 else ''
    return (f'<section class="peer-family-section"><div class="peer-family-head"><h2>{p.safe_text(family)}</h2>'
            f'<span>{len(cards)}张卡片 · {p.yi(total)}亿</span></div>'
            f'<div class="peer-issuance-cards{single}">' + ''.join(card_html(card, latest_date) for card in cards) + '</div></section>')


def main() -> None:
    records = p.parse_dynamics(SOURCE)
    cards = build_cards(records)
    latest_date = max(r['date'] for r in records if r['date'])
    extra_css = '''
body{margin:0}.demo-wrap{max-width:1420px;margin:auto;padding:24px}.demo-head{background:linear-gradient(135deg,#1a3a5c,#0d1b2e);color:#fff;padding:24px 28px;border-radius:10px 10px 0 0}.demo-head h1{margin:0;font-size:24px}.demo-head p{margin:7px 0 0;color:#dce7f2;font-size:13px;line-height:1.7}.peer-issuance-cards{margin-top:0}.peer-family-section{margin-top:18px}.peer-family-head{display:flex;align-items:baseline;gap:10px;margin:0 0 10px;padding:0 2px}.peer-family-head h2{font-size:16px;color:#0d1b2e;margin:0}.peer-family-head span{font-size:11px;color:#8a8f98}.peer-issuance-cards.single{grid-template-columns:1fr}.peer-rate-legend{display:flex;gap:18px;flex-wrap:wrap;font-size:11px;color:#52514e;margin:0 0 4px}.peer-rate-legend span{display:inline-flex;align-items:center;gap:6px}.peer-rate-legend i{width:9px;height:9px;border-radius:2px;display:inline-block}.peer-rate-legend b{font-variant-numeric:tabular-nums;color:#0d1b2e}.peer-rate-chart{height:auto}.peer-rate-note{font-size:10px;color:#8a8f98;line-height:1.6;margin:2px 0 0}.peer-scope{font-size:10px;color:#8a8f98;margin:2px 0 0}.peer-latest-list{border:1px solid #e8eaee;border-radius:7px;overflow:hidden;background:#fbfcfd}.peer-latest-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:14px;align-items:center;padding:10px 12px}.peer-latest-row+.peer-latest-row{border-top:1px solid #edf0f3}.peer-latest-left{min-width:0}.peer-latest-head{display:flex;align-items:center;gap:8px;font-size:10px;color:#8a8f98}.peer-latest-badge{display:inline-flex;align-items:center;border-left:3px solid var(--c);padding-left:6px;font-size:11px;font-weight:700;color:#0d1b2e}.peer-latest-project{font-size:13px;font-weight:700;color:#0d1b2e;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.peer-latest-sub{font-size:10px;color:#8a8f98;margin-top:2px}.peer-latest-right{display:flex;flex-direction:column;align-items:flex-end;gap:2px;white-space:nowrap}.peer-latest-rate{font-size:22px;font-weight:700;color:#0d1b2e;font-variant-numeric:tabular-nums;line-height:1.1}.peer-latest-facts{font-size:10px;color:#52514e}.peer-latest-empty{font-size:11px;color:#a0a6ae;font-weight:400}
@media(max-width:900px){.demo-wrap{padding:14px}.peer-issuance-cards{grid-template-columns:1fr}}
@media(max-width:620px){.peer-latest-row{grid-template-columns:1fr;gap:4px}.peer-latest-right{align-items:flex-start}.peer-latest-facts{white-space:normal}}
'''
    html = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>同业发行 · AAA利率期限拆分Demo</title><style>' + p.PEER_ISSUANCE_COMPONENT_CSS + extra_css + '</style></head><body>'
            '<div class="peer-issuance-root"><div class="demo-wrap"><div class="demo-head">'
            '<h1>同业发行 · 发行主体卡片</h1>'
            f'<p>数据截至 {latest_date.isoformat()} · 全部资产卡片</p></div>'
            + ''.join(family_section(family, [card for card in cards if card['family'] == family], latest_date)
                      for family in FAMILY_ORDER if any(card['family'] == family for card in cards))
            + '</div></div></body></html>')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'index.html').write_text(html, encoding='utf-8')
    payload = {
        'source': str(SOURCE.relative_to(ROOT)),
        'latestDate': latest_date.isoformat(),
        'rule': {'short': 'term <= 1.1', 'long': 'term > 1.1'},
        'cardGroups': CARD_GROUPS,
        'cards': [{key: card[key] for key in ('name', 'family', 'asset_type', 'amount', 'count', 'term_counts',
                                               'weekly_rates_short', 'weekly_rates_long',
                                               'latest_short', 'latest_long', 'scope')} for card in cards],
    }
    (OUT / 'data.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=p.json_default) + '\n', encoding='utf-8')
    print(json.dumps({'cards': len(cards), 'latestDate': latest_date.isoformat(),
                      'terms': {card['name']: card['term_counts'] for card in cards},
                      'latest': {card['name']: {'short': card['latest_short'] and card['latest_short']['product'],
                                                'long': card['latest_long'] and card['latest_long']['product']} for card in cards}},
                     ensure_ascii=False, default=str))


if __name__ == '__main__':
    main()
