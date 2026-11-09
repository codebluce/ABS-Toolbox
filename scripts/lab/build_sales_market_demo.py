"""在原机构统计样式中分拆两市场销售表，仅生成独立Demo。"""
import contextlib
import hashlib
import io
import json
import re
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import gen_institution_stats as stats

OUT = ROOT / 'deliverables/analysis/sales_market_demo_20261109'
LEDGER = ROOT / 'deliverables/ledger/03_final/2026年ABS发行台账-1106-定稿.xlsx'
MARKETS = {'交易所': ['上交所', '深交所'], '银行间': ['银行间']}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with contextlib.redirect_stdout(io.StringIO()):
        data = stats.compute_data(str(LEDGER))
    df = data['df']
    project_venues = df[df['项目名称'].notna()][['项目名称', '发行场所']].drop_duplicates()
    if project_venues['项目名称'].duplicated().any():
        raise ValueError('同一项目存在不同市场')
    projects = data['projects'].merge(project_venues, on='项目名称', validate='one_to_one')
    tables = []
    blocks = []
    columns = [('name', '机构名称', 'col-name'), ('cnt', '销售项目数', 'col-cnt'),
               ('num', '参与项目规模(亿)', 'col-num'), ('pct', '规模占比', 'col-pct'),
               ('num', '投行认购规模(亿)', 'col-num')]
    for market, venues in MARKETS.items():
        subset = projects[projects['发行场所'].isin(venues)]
        names = set(subset['项目名称'])
        rows = df[df['项目名称'].isin(names)]
        total = float(subset['规模'].sum())
        market_ib = stats.role_ib_scale(stats.compute_ib_subscription(rows), 'sales')
        sales = stats.compute_sales_table(subset, stats.compute_ib_subscription(rows), total)
        if market == '银行间':
            allocations = []
            for _, project in subset.iterrows():
                institutions = dict.fromkeys(stats.normalize_stats_role(x.strip(), 'sales')
                                             for x in str(project['联席承销商']).split('/') if x.strip())
                for institution in institutions:
                    if institution in ('-', 'nan', 'None', ''):
                        continue
                    allocations.append({'机构名称': institution, '项目名称': project['项目名称'], '规模': project['规模']})
            sales = pd.DataFrame(allocations).groupby('机构名称').agg(销售项目数=('项目名称', 'count'), 参与项目规模=('规模', 'sum')).reset_index()
            sales['投行认购规模'] = sales['机构名称'].map(market_ib).fillna(0)
            sales['规模占比'] = (sales['参与项目规模'] / total * 100).round(2)
            sales = sales.sort_values('参与项目规模', ascending=False).reset_index(drop=True)
        ib_without_sales = {str(name): float(amount) for name, amount in market_ib.items()
                            if name not in set(sales['机构名称']) and amount > 0}
        tables.append({'market': market, 'venues': venues, 'totalScale': total,
                       'projects': len(subset), 'institutions': len(sales),
                       'rows': sales.to_dict(orient='records'),
                       'ibWithoutSalesRole': ib_without_sales})
        table = stats.build_stat_table(columns, stats.build_sales_rows(sales), stats.SECTION_COLORS['sales']['thead'])
        blocks.append(f'<div class="inst-stats-block inst-stats-block--sales" data-market="{market}">'
                      f'<div class="inst-stats-block-title">{market}销售机构统计'
                      f'<span class="inst-stats-block-meta">{len(sales)}家机构</span></div>'
                      f'<div class="market-caption">{len(subset)}个项目 · 市场总规模 {total:,.2f}亿</div>'
                      f'<div class="inst-stats-table-wrap">{table}</div></div>')
    # 各市场互斥，核验合并金额和项目数等于原表对应市场部分。
    included = projects[projects['发行场所'].isin(sum(MARKETS.values(), []))]
    combined = stats.compute_sales_table(included, stats.compute_ib_subscription(df[df['项目名称'].isin(included['项目名称'])]), float(included['规模'].sum()))
    joined = pd.DataFrame([row for table in tables for row in table['rows']]).groupby('机构名称')[['销售项目数', '参与项目规模']].sum()
    joined = joined[joined.index.map(stats.is_brokerage)]
    expected = combined.set_index('机构名称')[joined.columns].sort_index()
    pd.testing.assert_frame_equal(joined.sort_index(), expected, check_dtype=False, atol=1e-8, rtol=1e-8)
    original = stats.render_body(data, section_key='embedded')
    pattern = r'<div class="inst-stats-block inst-stats-block--sales" id="stats-sales">.*?(?=<div class="inst-stats-block inst-stats-block--custodian")'
    replacement = '<div class="market-pair">' + ''.join(blocks) + '</div>\n'
    body, count = re.subn(pattern, lambda _: replacement, original, flags=re.S)
    assert count == 1
    excluded = projects[~projects['发行场所'].isin(sum(MARKETS.values(), []))]
    extra_css = '''
body{background:#f4f5f7}.preview-top{max-width:1400px;margin:auto;padding:20px 20px 0;display:flex;justify-content:space-between;align-items:center;color:#0d1b2e}.preview-top b{font-size:18px}.preview-top span{font-size:11px;color:#6c7c8d}.inst-stats-grid{grid-template-columns:1fr}.market-pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;min-width:0}.market-caption{padding:8px 12px;color:#52657a;font-size:11px;background:#fff}.inst-stats-embed .inst-stats-table-wrap{max-height:410px}.preview-note{max-width:1400px;margin:0 auto;padding:0 20px 24px;font-size:11px;color:#6c7c8d;line-height:1.8}details{margin-top:8px}summary{cursor:pointer}details p{margin-top:5px}@media(max-width:960px){.market-pair{grid-template-columns:1fr}}@media(max-width:720px){.preview-top{padding:16px 10px 0}.preview-top b{font-size:16px}.inst-stats-embed .inst-stats-block{padding:0}.preview-note{padding:0 10px 20px}}
'''
    html = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>机构统计 · 销售机构分市场Demo</title><style>' + stats.CSS + stats.INST_STATS_EMBED_CSS + extra_css + '</style></head><body>'
    html += '<div class="preview-top"><b>机构统计</b><span>销售机构分市场 · Demo</span></div>' + body
    html += f'<div class="preview-note">统计截至 {data["meta"]["date_max"]} · 规模占比＝机构参与项目规模／对应市场总规模。联席销售项目分别计入各机构，占比不相加为100%。<details><summary>统计范围与口径</summary><p>交易所：上交所、深交所，沿用原券商口径；银行间包括台账列示的银行及券商销售机构。名称沿用现有归并规则；投行认购规模沿用中标份额并按项目所属市场拆分，银行未标投行的认购不并入这一列。</p><p>销售表不含中保登与非标等其他市场，共{len(excluded)}个项目、{float(excluded["规模"].sum()):,.2f}亿。管理人、托管行表沿用原统计范围。参与项目规模代表机构参与项目的全额规模，不代表该机构实际售出金额。</p></details></div></body></html>'
    (OUT / 'index.html').write_text(html)
    payload = {'source': str(LEDGER.relative_to(ROOT)), 'sourceSha256': hashlib.sha256(LEDGER.read_bytes()).hexdigest(), 'asOf': data['meta']['date_max'], 'tables': tables, 'excluded': {'projects': len(excluded), 'scale': float(excluded['规模'].sum())}, 'validation': 'market recombination equals original included-market statistics'}
    (OUT / 'data.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({t['market']: {k:t[k] for k in ['totalScale','projects','institutions']} for t in tables}, ensure_ascii=False))


if __name__ == '__main__':
    main()
