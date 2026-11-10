"""用最新标准同业发行表更新完整底稿，同时保留已确认的华泰补录项目。"""
from __future__ import annotations

import argparse
import hashlib
import json
from copy import copy
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import openpyxl

from peer_issuance_panel import as_date, normalize_product_key, parse_dynamics, parse_rate, parse_term


def source_records(path: Path) -> dict[str, dict]:
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb.worksheets[0]
    headers = [str(v or '').replace('\n', '').replace(' ', '') for v in next(ws.values)]
    index = {name: i for i, name in enumerate(headers)}
    required = ['簿记日期', '产品名称', '产品类型', '场所', '原始权益人/发起机构', '基础资产',
                '资产类型', '规模(亿)', '簿记时间', '设立时间', 'AAA证券票面利率',
                'AAA档证券期限(年)', 'AAA档证券占比', 'AA+证券票面利率',
                'AA+档证券期限(年)', 'AA+档证券占比']
    missing = [name for name in required if name not in index]
    if missing:
        raise ValueError(f'{path.name} 缺少列: {missing}')
    records = {}
    for row_number, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
        product = str(row[index['产品名称']] or '').strip()
        if not product:
            continue
        key = normalize_product_key(product)
        if key in records:
            raise ValueError(f'{path.name} 产品名称重复: {product}')
        def value(name):
            return row[index[name]]
        records[key] = {
            'week': str(value('簿记日期') or '').strip(), 'product': product,
            'product_type': str(value('产品类型') or '').strip(),
            'venue': str(value('场所') or '').strip(),
            'originator': str(value('原始权益人/发起机构') or '').strip(),
            'base_asset': str(value('基础资产') or '').strip(),
            'asset_type': str(value('资产类型') or '').strip(),
            'amount': Decimal(str(value('规模(亿)') or 0)),
            'date': as_date(value('簿记时间')), 'establish': as_date(value('设立时间')),
            'aaa': parse_rate(value('AAA证券票面利率')),
            'term': parse_term(value('AAA档证券期限(年)')),
            'aaa_share': value('AAA档证券占比'),
            'aa_rate': parse_rate(value('AA+证券票面利率')),
            'aa_term': parse_term(value('AA+档证券期限(年)')),
            'aa_share': value('AA+档证券占比'),
            'source_row': row_number,
        }
    wb.close()
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--supplement-json', type=Path, nargs='*', default=None,
                        help='华泰补录白名单；缺省时自动读取底稿同目录的 *.supplement.json 与 *.update.json')
    parser.add_argument('--label-date', default=date.today().isoformat(),
                        help='写入底稿的更新日期标签（默认当天）')
    args = parser.parse_args()

    source = source_records(args.source)
    current = parse_dynamics(args.current)
    supplement_paths = args.supplement_json
    if not supplement_paths:
        # 补录项目必须逐周保留，靠人工传参迟早会漏；默认把同目录的白名单全读进来。
        base = args.current.parent
        supplement_paths = sorted(base.glob('*.supplement.json')) + sorted(base.glob('*.update.json'))
        print(f'[supplement] 未显式指定，自动读取 {len(supplement_paths)} 份白名单')
    known_supplements = set()
    for path in supplement_paths:
        data = json.loads(path.read_text(encoding='utf-8'))
        for item in data.get('entries', []) + data.get('additions', []):
            known_supplements.add(normalize_product_key(item.get('project') or item.get('product')))

    # 同一项目在标准源中由“和富”更正为“和盛”，按日期、金额、机构一致确认后替换名称。
    rename = {
        normalize_product_key('深圳市财付通网络金融小额贷款有限公司2026年度和富第2期定向资产支持票据'):
        normalize_product_key('深圳市财付通网络金融小额贷款有限公司2026年度和盛第2期定向资产支持票据')
    }

    wb = openpyxl.load_workbook(args.current)
    ws = wb.worksheets[0]
    # 底稿首表存在跨行合并单元格；更新副本先取消合并，保留左上角原值。
    for merged in list(ws.merged_cells.ranges):
        ws.unmerge_cells(str(merged))
    row_by_key = {}
    for row in range(2, ws.max_row + 1):
        product = str(ws.cell(row, 2).value or '').strip()
        if product:
            row_by_key[normalize_product_key(product)] = row

    matched = set()
    additions, modifications, retained, renames = [], [], [], []
    for record in current:
        key = normalize_product_key(record['product'])
        target_key = rename.get(key, key)
        row = row_by_key[key]
        if target_key in source:
            new = source[target_key]
            matched.add(target_key)
            changed = {}
            for field in ['product_type', 'venue', 'originator', 'base_asset', 'asset_type', 'amount', 'date', 'aaa', 'term']:
                if record[field] != new[field]:
                    changed[field] = {'before': str(record[field]), 'after': str(new[field])}
            if key != target_key:
                renames.append({'before': record['product'], 'after': new['product'], 'row': row})
            if changed:
                modifications.append({'product': new['product'], 'row': row, 'changes': changed})
            values = [new['week'], new['product'], new['product_type'], new['venue'], new['originator'],
                      new['base_asset'], new['asset_type'], float(new['amount']),
                      datetime.combine(new['date'], datetime.min.time()) if new['date'] else None,
                      datetime.combine(new['establish'], datetime.min.time()) if new['establish'] else None,
                      float(new['aaa']) if new['aaa'] is not None else None,
                      float(new['term']) if new['term'] is not None else None,
                      new['aaa_share'], float(new['aa_rate']) if new['aa_rate'] is not None else None,
                      float(new['aa_term']) if new['aa_term'] is not None else None, new['aa_share']]
            for col, value in enumerate(values, 1):
                ws.cell(row, col, value)
        elif key in known_supplements:
            retained.append({'product': record['product'], 'amount': str(record['amount']), 'reason': '华泰补录项目，标准源未包含'})
        else:
            raise ValueError(f'标准源缺少未登记历史项目，拒绝删除: {record["product"]}')

    end = max(row_by_key.values())
    for key, new in source.items():
        if key in matched:
            continue
        end += 1
        values = [new['week'], new['product'], new['product_type'], new['venue'], new['originator'],
                  new['base_asset'], new['asset_type'], float(new['amount']),
                  datetime.combine(new['date'], datetime.min.time()) if new['date'] else None,
                  datetime.combine(new['establish'], datetime.min.time()) if new['establish'] else None,
                  float(new['aaa']) if new['aaa'] is not None else None,
                  float(new['term']) if new['term'] is not None else None,
                  new['aaa_share'], float(new['aa_rate']) if new['aa_rate'] is not None else None,
                  float(new['aa_term']) if new['aa_term'] is not None else None, new['aa_share']]
        for col, value in enumerate(values, 1):
            cell = ws.cell(end, col, value)
            cell._style = copy(ws.cell(2, col)._style)
        ws.cell(end, 19, args.source.name)
        ws.cell(end, 20, f'{args.label_date} 标准源新增')
        ws.cell(end, 21, new['establish'].isoformat() if new['establish'] else None)
        ws.cell(end, 22, '发行动态（2026）')
        ws.cell(end, 23, new['source_row'])
        ws.cell(end, 24, '按标准源资产方归属')
        additions.append({'product': new['product'], 'date': str(new['date']), 'amount': str(new['amount'])})

    # 底稿是逐周滚动更新的，上一轮的核对页要先清掉，否则会留下两页同名记录。
    if '本次标准源更新核对' in wb.sheetnames:
        del wb['本次标准源更新核对']
    audit = wb.create_sheet('本次标准源更新核对')
    audit.append(['类型', '项目', '日期/金额', '说明'])
    for item in additions:
        audit.append(['新增', item['product'], f"{item['date']} / {item['amount']}", '标准源新增'])
    for item in modifications:
        audit.append(['修订', item['product'], '', json.dumps(item['changes'], ensure_ascii=False)])
    for item in retained:
        audit.append(['保留', item['product'], item['amount'], item['reason']])
    for item in renames:
        audit.append(['改名', item['before'], '', f"改为 {item['after']}"])
    audit.freeze_panes = 'A2'
    audit.auto_filter.ref = audit.dimensions
    notes = wb['数据口径与来源']
    notes.append(['本次标准源', args.source.name])
    notes.append(['本次源SHA256', hashlib.sha256(args.source.read_bytes()).hexdigest()])
    notes.append(['本次更新日期', args.label_date])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix('.stage.xlsx')
    wb.save(temp)
    temp.replace(args.output)
    wb.close()

    result = {
        'before_count': len(current), 'after_count': len(current) + len(additions),
        'additions': additions, 'modifications': modifications,
        'retained_supplements': retained, 'renames': renames,
        'source_sha256': hashlib.sha256(args.source.read_bytes()).hexdigest(),
    }
    args.output.with_suffix('.update.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: len(v) if isinstance(v, list) else v for k, v in result.items()},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
