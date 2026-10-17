"""本地电脑版月度投标机构 Demo；只读定稿，复用面板与已批准机构口径。"""
from pathlib import Path
from datetime import datetime
from decimal import Decimal, InvalidOperation
import argparse
from html import escape
import json
import math
import re
import sys

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import latest_bookkeeping_panel as panel
import latest_bookkeeping_qc as qc
from abs_common import normalize_investor_name
from institution_identity import registry

GROUPS = ('理财子', '银行', '公募基金', '券商', '其他')
THREE_GROUP_ASSETS = frozenset({'赊销白条', '金条白取混发', '信托金条', '白条取现',
                              '信托企业主贷', '小贷企业主贷', '保理', '金采'})
LAB = Path(__file__).resolve().parent
CLASSIFICATION = SCRIPTS.parent / 'data/机构分配字典.json'
FUND_RULES = LAB / 'monthly_bid_classification.json'
DEMO_ALIASES = LAB / 'monthly_bid_institution_aliases.json'


def _unique_object(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f'分类配置字段重复：{key}')
        result[key] = value
    return result


def fund_classification():
    """Demo专用分类，仅携带原名单与明确的前海开源简称。"""
    source = json.loads(FUND_RULES.read_text(encoding='utf-8'), object_pairs_hook=_unique_object)
    if not isinstance(source, dict) or source.get('schema') != 'monthly-bid-classification/v1':
        raise ValueError('Demo公募配置schema错误')
    names = source.get('publicFunds')
    if (not isinstance(names, list) or len(names) != 16 or
            any(not isinstance(n, str) or not n.strip() or n != n.strip() or not n.endswith('基金') for n in names) or
            len(set(names)) != len(names) or
            len({normalize_investor_name(n) for n in names}) != len(names)):
        raise ValueError('Demo公募名单必须为唯一、非空的完整基金名称')
    aliases = source.get('publicFundAliases')
    if aliases != {'前海开源': '前海开源基金'} or aliases['前海开源'] not in names:
        raise ValueError('Demo公募alias仅允许已登记的前海开源')
    origin = source.get('source')
    if (not isinstance(origin, dict) or not isinstance(origin.get('path'), str) or not origin['path'].strip() or
            origin.get('constant') != 'FUNDS' or
            not isinstance(origin.get('sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', origin['sha256'])):
        raise ValueError('Demo公募配置必须保留原FUNDS来源与SHA256')
    overrides = source.get('explicitCategoryOverrides', {})
    if not isinstance(overrides, dict) or any(
            not isinstance(name, str) or not name.strip() or name != name.strip() or group not in GROUPS
            for name, group in overrides.items()):
        raise ValueError('Demo显式分类必须为非空名称与合法板块')
    return source


def demo_aliases():
    source = json.loads(DEMO_ALIASES.read_text(encoding='utf-8'))
    result = {}
    for group in source['groups']:
        for alias in group['aliases']:
            if alias in result or alias == group['canonical']:
                raise ValueError('Demo别名重复或自身映射')
            result[alias] = (group['canonical'], group['reason'])
    if set(result) & {target for target, _ in result.values()}:
        raise ValueError('Demo别名必须为单跳')
    return result


def monthly_identity(raw, aliases):
    # 公司法律后缀可能位于部门括号前；原公共函数仅处理末尾公司后缀。
    formatted = re.sub(r'(股份有限公司|有限责任公司|有限公司)(?=[（(]|$)', '', raw.strip())
    if '信托' not in formatted:
        formatted = formatted.replace('(', '（').replace(')', '）')
    name = normalize_investor_name(formatted)
    target, reason = aliases.get(name, (name, '沿用项目机构别名与格式规则'))
    return target, reason


def category_lookup():
    """拆解分配表的展示组合只用于分类，不将组合成员当作身份别名。"""
    source = json.loads(CLASSIFICATION.read_text(encoding='utf-8'))
    result = {}
    for category, names in source['category_to_institutions'].items():
        for name in names:
            for part in re.split(r'[/&：:]', name):
                part = normalize_investor_name(part.strip())
                if '理财' in part and '信托' not in part:
                    group = '理财子'
                elif category in {'全国大行', '国股行', '城商行', '外资行'} or category.startswith('ABN主承销商'):
                    group = '银行'
                elif category == '公募基金':
                    group = category
                elif category == '券商' or category.startswith(('ABS管理人', 'ABS销售机构')):
                    group = '券商'
                else:
                    group = '其他'
                result.setdefault(part, group)
    funds = fund_classification()
    for name in funds['publicFunds']:
        result[normalize_investor_name(name)] = '公募基金'
    for alias in funds['publicFundAliases']:
        result[alias] = '公募基金'
    for bare in ('平安', '华夏', '中银', '建信'):
        if result.get(bare) == '公募基金':
            del result[bare]
    # 已登记的证券资管别名可用于识别板块，不因此合并资管与证券主体。
    for item in registry()['aliases']:
        if '证券' in item['alias'] and not any(t in item['alias'] for t in ('信托', '银行')):
            result.setdefault(item['canonical'], '券商')
    result.update(funds.get('explicitCategoryOverrides', {}))
    return result


def classify(name, lookup):
    if name in lookup:
        return lookup[name], '机构分配字典精确匹配'
    # 分类识别不改写机构身份；信托通道保留其他，避免按括号内客户认作理财/券商。
    if any(word in name for word in ('信托', '私募', '利曦', '保险', '养老', '财务', '保理', '小贷', '员工理财')):
        return '其他', '源名称行业标识'
    if '理财' in name:
        return '理财子', '源名称理财标识'
    if any(word in name for word in ('银行', '农商', '农金市')):
        return '银行', '源名称银行标识'
    if '基金' in name:
        # 不以“基金”二字自动断定公募，只匹配分配表已登记的公募全名。
        base = name.removesuffix('管理')
        if lookup.get(base) == '公募基金':
            return '公募基金', '机构分配字典公募名称匹配'
    if any(word in name for word in ('证券', '中信建投', '建投衍生品', '中金', '中国国际金融', '国泰海通', '国联民生', '申万宏源', '中信投顾')):
        return '券商', '源名称券商标识'
    return '其他', '分类未确认，保留其他'


class MonthlySourceError(ValueError):
    def __init__(self, issues):
        self.issues = issues
        super().__init__('全年月度源数据无效：' + '; '.join(i['message'] for i in issues)[:2000])


def _text(value):
    # 原始NaN不能经panel.text被折成空白。
    return '' if value is None else str(value).strip()


def _missing(value, field=''):
    return _text(value) in ('', '-', field)


def _number(value, field, row, issues):
    if _missing(value, field) or (field in ('申购利率', '成本') and _text(value) in ('自持', '不出表')):
        return None
    amount = None
    if not isinstance(value, bool) and isinstance(value, (str, int, float, Decimal)):
        try:
            amount = Decimal(str(value).strip())
            if (not amount.is_finite() or amount < 0 or
                    (field in ('申购利率', '成本') and amount > 1) or not math.isfinite(float(amount))):
                amount = None
        except (InvalidOperation, ValueError, OverflowError):
            amount = None
    if amount is None:
        issues.append({'level': 'FAIL', 'code': 'MONTHLY_SOURCE_VALUE', 'row': row,
                       'field': field, 'message': f'总表{row} {field}非法数值：{value!r}'})
    return amount


def _snapshot(ledger):
    import monthly_bookkeeping_qc as gate
    provenance = gate.build_provenance(ledger)
    # 独立固定配置指纹，即使并行门禁尚在迁移也检测配置变化。
    return {'provenance': provenance, 'fundRulesSha256': qc.file_sha256(FUND_RULES)}


def _ensure_snapshot(ledger, snapshot):
    if _snapshot(ledger) != snapshot:
        raise ValueError('生成期间源台账、分类、别名或组件源码变化，请重新生成')


def _institution(bucket, name, lookup):
    group, reason = classify(name, lookup)
    return bucket['institutions'].setdefault(name, {'name': name, 'group': group,
        'classificationReason': reason, 'months': [[] for _ in range(12)]})


def _empty_asset(asset):
    return {'institutions': [], 'counts': [0] * 12, 'visibleCounts': [0] * 12,
            'visibleGroups': GROUPS[:3] if asset in THREE_GROUP_ASSETS else GROUPS,
            'bubbleMaxSize': 1, 'projectCount': 0, 'projectCounts': [0] * 12,
            'totalAllocatedSize': 0, 'totalKnownAllocatedSize': 0,
            'allocationComplete': True, 'unknownAllocationRows': [], 'bidCount': 0, 'fallbackCount': 0}


def compute_monthly(ledger):
    """全年严格校验后聚合；部分披露与未知金额保留明确的状态。"""
    snapshot = _snapshot(ledger)
    lookup, aliases = category_lookup(), demo_aliases()
    records = qc.read_source(ledger)
    for pair in registry()['distinct']:
        if monthly_identity(pair['left'], aliases)[0] == monthly_identity(pair['right'], aliases)[0]:
            raise ValueError(f"已确认独立机构被合并：{pair['left']} / {pair['right']}")
    scoped, errors, warnings, evidence = [], [], [], set()
    assets, excluded, identity_changes, verified_amounts = {}, [], {}, {}
    for row in records:
        venue, date = _text(row['发行场所']), row['_date']
        if venue not in panel.ALLOWED_VENUES:
            continue
        asset = panel.ASSET_ALIASES.get(_text(row['资产类型']), _text(row['资产类型']))
        project = _text(row['项目名称'])
        if not date or not asset or not project:
            errors.append({'level': 'FAIL', 'code': 'MONTHLY_SOURCE_SCOPE', 'row': row['_row'],
                           'message': f"总表{row['_row']} 场内项目缺资产/项目/有效日期"})
            continue
        if not date.startswith('2026-'):
            continue
        month = int(date[5:7]) - 1
        key = asset, date, project, venue
        bucket = assets.setdefault(asset, {'institutions': {}, 'projectMonths': [set() for _ in range(12)]})
        bucket['projectMonths'][month].add((date, project, venue))
        if _text(row['发行场所']) != str(row['发行场所']):
            warnings.append({'level': 'WARN', 'code': 'MONTHLY_VENUE_TRIM', 'row': row['_row'],
                             'message': f"总表{row['_row']} 场所已trim为{venue}"})
        fields = ('申购利率', '穿透机构', '申购规模')
        header = all(_text(row[f]) == f for f in fields)
        has_evidence = not header and any(_text(row[f]) not in ('', '-') for f in fields)
        if has_evidence:
            evidence.add(key)
        if not header and any(_text(row[f]) == f for f in fields):
            errors.append({'level': 'FAIL', 'code': 'MONTHLY_LOCAL_HEADER', 'row': row['_row'],
                           'message': f"总表{row['_row']} WXY仅部分表头占位，不允许UV回退"})
        rate = _number(row['申购利率'], '申购利率', row['_row'], errors)
        size = _number(row['申购规模'], '申购规模', row['_row'], errors)
        amount = _number(row['认购份额'], '认购份额', row['_row'], errors)
        cost = _number(row['成本'], '成本', row['_row'], errors)
        raw, allocation_raw = _text(row['穿透机构']), _text(row['认购机构'])
        for field in ('穿透机构', '认购机构'):
            if not _missing(row[field], field) and not isinstance(row[field], str):
                errors.append({'level': 'FAIL', 'code': 'MONTHLY_SOURCE_INSTITUTION', 'row': row['_row'],
                               'message': f"总表{row['_row']} {field}必须是名称字符串"})
        bidder_missing = _missing(row['穿透机构'], '穿透机构')
        if not header and bidder_missing and any(not _missing(row[f], f) for f in ('申购利率', '申购规模')):
            errors.append({'level': 'FAIL', 'code': 'MONTHLY_ORPHAN_BID', 'row': row['_row'],
                           'message': f"总表{row['_row']} W/Y有披露但X机构缺失；不回退UV"})
        if _missing(row['认购机构'], '认购机构') and not _missing(row['认购份额'], '认购份额'):
            errors.append({'level': 'FAIL', 'code': 'MONTHLY_ORPHAN_ALLOCATION', 'row': row['_row'],
                           'message': f"总表{row['_row']} V有披露但U机构缺失"})
        scoped.append((row, key, month, raw, allocation_raw, rate, size, amount, cost, header))
    if errors:
        _ensure_snapshot(ledger, snapshot)
        raise MonthlySourceError(errors)
    for row, key, month, raw, _, rate, size, _, _, header in scoped:
        asset, date, project, venue = key
        if header or _missing(raw, '穿透机构'):
            continue
        if rate is None or size is None or size <= 0:
            excluded.append({'row': row['_row'], 'institution': raw,
                             'reason': '无有效申购利率或正申购规模（含自持）'})
            code = 'MONTHLY_ZERO_BID' if rate is not None and size == 0 else 'MONTHLY_BID_MISSING'
            warnings.append({'level': 'WARN', 'code': code, 'row': row['_row'],
                             'message': f"总表{row['_row']} 完整零申购或申购字段不完整；不计正申购规模，不以UV替代"})
            continue
        name, identity_reason = monthly_identity(raw, aliases)
        old_name = normalize_investor_name(raw)
        if old_name != name:
            change = identity_changes.setdefault(raw, {'raw': raw, 'previousName': old_name,
                'name': name, 'reason': identity_reason, 'rows': []})
            change['rows'].append(row['_row'])
        inst = _institution(assets[asset], name, lookup)
        verified_amounts['bids', row['_row']] = size
        inst['months'][month].append({'row': row['_row'], 'rawInstitution': raw, 'project': project,
            'date': date, 'rate': float(rate), 'size': float(size), 'venue': venue, 'track': 'bids'})
    allocation_totals, allocation_records, fallback_rows, unknown_records = {}, [], [], []
    for row, key, month, _, raw, _, _, amount, cost, _ in scoped:
        asset, date, project, venue = key
        if _missing(raw, '认购机构') or any(tag in raw + _text(row['成本']) for tag in ('自持', '不出表')):
            continue
        name, _ = monthly_identity(raw, aliases)
        total = allocation_totals.setdefault(asset, {'total': Decimal(0), 'institutions': {}, 'unknown': {}})
        if amount is None:
            total['unknown'].setdefault(name, []).append(row['_row'])
            unknown_records.append({'row': row['_row'], 'asset': asset, 'name': name,
                'rawInstitution': raw, 'date': date, 'project': project, 'venue': venue,
                'size': None, 'reason': 'U已披露、V未披露，配售金额未知'})
            warnings.append({'level': 'WARN', 'code': 'MONTHLY_ALLOCATION_UNKNOWN', 'row': row['_row'],
                             'message': f"总表{row['_row']} 非自持U已披露而V缺失；{asset}所有中标占比使用未知"})
            continue
        total['total'] += amount
        total['institutions'][name] = total['institutions'].get(name, Decimal(0)) + amount
        if amount <= 0:
            continue
        allocation_records.append({'row': row['_row'], 'asset': asset, 'name': name,
            'rawInstitution': raw, 'date': date, 'size': float(amount)})
        if month < 3 and key not in evidence:
            inst = _institution(assets[asset], name, lookup)
            verified_amounts['allocations', row['_row']] = amount
            inst['months'][month].append({'row': row['_row'], 'rawInstitution': raw,
                'project': project, 'date': date, 'rate': float(cost) if cost is not None else None,
                'size': float(amount), 'venue': venue, 'track': 'allocations'})
            fallback_rows.append(row['_row'])
    output = {}
    for asset, bucket in assets.items():
        project_count = sum(len(projects) for projects in bucket['projectMonths'])
        allocated = allocation_totals.get(asset, {'total': Decimal(0), 'institutions': {}, 'unknown': {}})
        complete = not allocated['unknown']
        for inst in bucket['institutions'].values():
            inst['participationCount'] = len({(bid['date'], bid['project'], bid['venue'])
                                             for month in inst['months'] for bid in month})
            inst['monthCount'] = sum(bool(month) for month in inst['months'])
            inst['participationRate'] = inst['participationCount'] / project_count if project_count else None
            known = allocated['institutions'].get(inst['name'], Decimal(0))
            unknown = allocated['unknown'].get(inst['name'], [])
            inst['knownAllocatedSize'] = float(known)
            inst['allocationComplete'] = not unknown
            inst['unknownAllocationRows'] = unknown
            inst['allocatedSize'] = None if unknown else float(known)
            inst['allocationShare'] = float(known / allocated['total']) if complete and allocated['total'] else None
            inst['monthlyBidSizes'] = [float(sum((verified_amounts[r['track'], r['row']] for r in month if r['track'] == 'bids'), Decimal(0))) for month in inst['months']]
            inst['monthlyFallbackSizes'] = [float(sum((verified_amounts[r['track'], r['row']] for r in month if r['track'] == 'allocations'), Decimal(0))) for month in inst['months']]
            inst['monthlySizes'] = [float(sum((verified_amounts[r['track'], r['row']] for r in month), Decimal(0))) for month in inst['months']]
            inst['monthlyTracks'] = ['mixed' if {r['track'] for r in month} == {'bids', 'allocations'} else
                                     month[0]['track'] if month else '' for month in inst['months']]
        institutions = sorted(bucket['institutions'].values(), key=lambda inst: (
            GROUPS.index(inst['group']), -inst['participationCount'], -inst['monthCount'], inst['name']))
        visible_groups = GROUPS[:3] if asset in THREE_GROUP_ASSETS else GROUPS
        visible = [inst for inst in institutions if inst['group'] in visible_groups]
        output[asset] = {'institutions': institutions,
            'counts': [sum(bool(inst['months'][m]) for inst in institutions) for m in range(12)],
            'bubbleMaxSize': max((size for inst in visible for size in inst['monthlySizes']), default=1),
            'visibleGroups': visible_groups,
            'visibleCounts': [sum(bool(inst['months'][m]) for inst in visible) for m in range(12)],
            'projectCounts': [len(p) for p in bucket['projectMonths']], 'projectCount': project_count,
            'totalKnownAllocatedSize': float(allocated['total']),
            'totalAllocatedSize': float(allocated['total']) if complete else None,
            'allocationComplete': complete,
            'unknownAllocationRows': sorted(r for rows in allocated['unknown'].values() for r in rows),
            'bidCount': sum(r['track'] == 'bids' for inst in institutions for month in inst['months'] for r in month),
            'fallbackCount': sum(r['track'] == 'allocations' for inst in institutions for month in inst['months'] for r in month)}
    _ensure_snapshot(ledger, snapshot)
    return {'year': 2026, 'groups': GROUPS, 'assets': output,
            'sourceSha256': snapshot['provenance']['sourceSha256'],
            'provenance': snapshot['provenance'],
            'fallbackRows': fallback_rows, 'allocationRecords': allocation_records,
            'unknownAllocationRecords': unknown_records,
            'classificationSha256': qc.file_sha256(CLASSIFICATION), 'excluded': excluded,
            'fundRulesSha256': snapshot['fundRulesSha256'],
            'demoAliasesSha256': qc.file_sha256(DEMO_ALIASES),
            'identityChanges': list(identity_changes.values()), 'dataWarnings': warnings,
            'generatedAt': datetime.now().astimezone().isoformat(timespec='seconds')}


def _qc_status(monthly):
    report = monthly.get('auditQc', {})
    return report.get('status', 'UNCHECKED'), report


def render_component(data, monthly, preview=True):
    """可集成的真实组件，包括两套唯一内联数据与JS。"""
    status, report = _qc_status(monthly)
    if not preview and status != 'PASS':
        raise ValueError('月度组件尚未通过独立门禁，禁止正式渲染')
    body = panel.render_body(data, preview=preview)
    anchor = '    <div class="lb-project-row">'
    assert body.count(anchor) == 1
    section = '''    <section class="lb-monthly" aria-labelledby="lb-monthly-title">
      <div class="lb-monthly-heading"><div><h2 id="lb-monthly-title">2026年月度投标机构</h2></div>
        <div class="lb-monthly-actions"><input id="lb-monthly-search" type="search" placeholder="查找投标机构" aria-label="查找全年投标机构"><button id="lb-monthly-expand" type="button" aria-expanded="false">展开全表</button></div></div>
      <div id="lb-monthly-scroll" class="lb-monthly-scroll" tabindex="0" aria-label="月度投标矩阵，可滚动查看"><table class="lb-monthly-table"><caption class="lb-sr-only">固定机构行与一至十二月份列，实心气泡面积表示月度规模；每类资产独立计算尺度，1—3月完全未披露W/X/Y的项目以实际配售补充</caption><thead id="lb-monthly-head"></thead><tbody id="lb-monthly-rows"></tbody></table></div>
      <div class="lb-monthly-note"><span class="lb-monthly-legend-solid"></span> 月度申购规模 · 1—3月完全未披露W/X/Y的项目以实际配售规模补充；悬停查看金额及口径。气泡按当前资产独立缩放。参与率＝参与项目次数 ÷ 当前资产2026年项目总数；按参与率降序。中标规模占比＝机构全年U/V实际配售规模 ÷ 该资产全部机构实际配售总规模（含未展示板块，剔除明确自持 / 不出表，仅交易所 / 银行间）；0%表示未见获配记录或明确零获配；金额未披露、资产分母不完整时显示—。</div>
    </section>
'''
    if status != 'PASS':
        failures = [item for item in report.get('issues', [])
                    if item.get('level') == 'FAIL' or item.get('blocksRelease')]
        details = ''.join('<li>' + escape(str(item.get('code', ''))) + '：' +
                          escape(str(item.get('message', ''))) + '</li>' for item in failures)
        summary = ('独立门禁未通过，' + str(len(failures)) + '项阻断；仅供预览，禁止正式放行。'
                   if status == 'FAIL' else '独立门禁尚未完成；仅供预览，禁止正式放行。')
        banner = ('<div class="lb-monthly-qc-banner" role="alert" data-qc-status="' + escape(status) +
                  '"><strong>' + summary + '</strong>' + ('<ul>' + details + '</ul>' if details else '') + '</div>')
        section = section.replace('    <section class="lb-monthly" aria-labelledby="lb-monthly-title">',
                                  '    <section class="lb-monthly" aria-labelledby="lb-monthly-title">' + banner, 1)
    body = body.replace(anchor, section + anchor)
    # 全年观察与最近项目明细分为两张卡片，项目选择属于下方明细卡片。
    body = body.replace('aria-label="资产与项目选择"', 'aria-label="资产选择与全年投标观察"', 1)
    project_row, count = re.subn(r'    <div class="lb-project-row">.*?</div>\n', '', body, count=1)
    assert count == 1
    row = re.search(r'    <div class="lb-project-row">.*?</div>\n', body).group(0)
    body = project_row
    summary_anchor = '  <section class="lb-card lb-project-summary" aria-label="项目概况">'
    assert body.count(summary_anchor) == 1
    project_header = ('  <section class="lb-card lb-project-block" aria-labelledby="lb-project-block-title">\n'
                      '    <div class="lb-project-block-heading"><h2 id="lb-project-block-title">最近项目簿记</h2>'
                      + row.replace('<div class="lb-project-row">', '<div class="lb-project-row">', 1).strip()
                      + '</div>\n')
    body = body.replace(summary_anchor, project_header + summary_anchor, 1)
    body = body.replace('  <p class="lb-preview-note">', '  </section>\n  <p class="lb-preview-note">', 1)
    encoded = json.dumps(monthly, ensure_ascii=False, allow_nan=False).replace('<', '\\u003c').replace('&', '\\u0026')
    body += '<script id="lb-monthly-data" type="application/json">' + encoded + '</script><script>' + (LAB/'monthly_bid_institutions_demo.js').read_text(encoding='utf-8') + '</script>'
    return body


def component_css():
    return (SCRIPTS / 'latest_bookkeeping_panel.css').read_text(encoding='utf-8') + (LAB / 'monthly_bid_institutions_demo.css').read_text(encoding='utf-8')


def build_document(data, monthly, preview=True):
    body = render_component(data, monthly, preview=preview)
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>最新簿记 · 2026年月度投标机构 Demo</title><style>body{margin:0;}' +
            component_css() + '</style></head><body>' + body + '</body></html>')


def _attach_qc(monthly, report):
    failures = sum(item.get('level') == 'FAIL' for item in report.get('issues', []))
    warnings = sum(item.get('level') == 'WARN' for item in report.get('issues', []))
    blocks = sum(item.get('level') == 'FAIL' or bool(item.get('blocksRelease')) for item in report.get('issues', []))
    monthly['auditQc'] = {**report, 'summary': {'failCount': failures, 'warnCount': warnings, 'blockCount': blocks},
                          'releaseBlocked': report.get('status') != 'PASS'}


def main(argv=None):
    import monthly_bookkeeping_qc as gate
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ledger', type=Path, help='默认读取最新定稿台账')
    parser.add_argument('--strict', action='store_true', help='严格门禁检查；任何FAIL退出非0且不写产物')
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError('请指定新的 Demo 路径，避免覆盖已有产物')
    ledger = args.ledger or panel.find_latest_final()
    try:
        snapshot = _snapshot(ledger)
        monthly = compute_monthly(ledger)
        before_report = gate.verify_data(monthly, ledger, raise_on_fail=False)
        _attach_qc(monthly, before_report)
        data = panel.compute_data(ledger)
        if data['provenance']['sourceSha256'] != monthly['sourceSha256']:
            raise ValueError('最近项目与全年月表的源表指纹不一致')
        content = build_document(data, monthly)
        html_report = gate.verify_html(content, ledger, raise_on_fail=False)
        _attach_qc(monthly, html_report)
        content = build_document(data, monthly)
        final_report = gate.verify_html(content, ledger, raise_on_fail=False)
        _ensure_snapshot(ledger, snapshot)
        if args.strict and final_report['status'] != 'PASS':
            print(json.dumps({'demo': None, 'ledger': str(ledger), 'mode': 'strict',
                              'auditQc': final_report}, ensure_ascii=False, allow_nan=False, indent=2))
            return 1
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(content)
        try:
            written_report = gate.verify_html(args.output.read_text(encoding='utf-8'), ledger, raise_on_fail=False)
            _ensure_snapshot(ledger, snapshot)
            if args.strict and written_report['status'] != 'PASS':
                args.output.unlink()
                print(json.dumps({'demo': None, 'ledger': str(ledger), 'mode': 'strict',
                                  'auditQc': written_report}, ensure_ascii=False, allow_nan=False, indent=2))
                return 1
        except (OSError, ValueError):
            args.output.unlink(missing_ok=True)
            raise
        print(json.dumps({'demo': str(args.output.resolve()), 'ledger': str(ledger),
            'mode': 'strict' if args.strict else 'preview', 'auditQc': written_report,
            'assets': {name: {'institutions': len(x['institutions']), 'bids': x['bidCount'],
                             'fallbacks': x['fallbackCount'], 'monthlyCounts': x['counts']}
                       for name, x in monthly['assets'].items()},
            'excludedNonBids': monthly['excluded'], 'dataWarnings': monthly['dataWarnings']},
            ensure_ascii=False, allow_nan=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError) as error:
        report = getattr(error, 'report', None) or {'status': 'FAIL', 'issues': getattr(error, 'issues', [
            {'level': 'FAIL', 'code': 'MONTHLY_GENERATION', 'message': str(error)}])}
        print(json.dumps({'demo': None, 'ledger': str(ledger), 'auditQc': report},
                         ensure_ascii=False, allow_nan=False, indent=2))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
