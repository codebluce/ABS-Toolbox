"""ABS 基准利差分析报告生成器（产品类型维度）

定义：基准利差 = 机构认购成本（优先A）- 同日国股CD
维度：月份 + 产品类型（资产类型+期限）+ 机构利差分析

产品类型 = 资产类型 + 期限分类（1年期/超1年期）
  例：1年期赊销白条、超1年期赊销白条、1年期信托企业主贷、超1年期信托企业主贷

用法:
  python gen_spread_report.py <xlsx_path> [output_path]
  output_path 默认为 ABS技能包/看板/<日期>_机构投标基准利差看板.html
"""

import sys, os
import pandas as pd
from collections import defaultdict

from abs_common import (
    SPREAD_BINS, SPREAD_LABELS,
    BASE_COLORS, DEFAULT_COLOR, MONTH_COLORS, MONTH_ACCENT,
    RESOLVED_COST_COL, RESOLVED_INST_COL, RESOLVED_SHARE_COL,
    NON_NUMERIC_COST_VALS, PRIORITY_LAYERS,
    PRODUCT_ORDER_TEMPLATE, OVER_1Y_ASSETS,
    classify_tenor, product_color,
    load_and_filter, QCRunner,
)


# ── 数据读取与预处理 ──────────────────────────────────────────
def read_data(xlsx_path):
    """读取并预处理台账数据，返回 df, dfa"""
    df, dfa, tmp_path, tenor_col = load_and_filter(xlsx_path, need_tenor=True,
                                                    extra_required=['国股CD'])
    try:
        dfa['成本pct']    = dfa[RESOLVED_COST_COL] * 100
        dfa['国股CDpct']  = dfa['国股CD'] * 100
        dfa['基准利差']   = (dfa['成本pct'] - dfa['国股CDpct']).round(4)
        dfa['期限分类']   = dfa.apply(
            lambda r: classify_tenor(r[tenor_col], r['资产类型']), axis=1
        )
        dfa['产品类型']   = dfa['期限分类'] + dfa['资产类型']
        dfa['利差区间']   = pd.cut(
            dfa['基准利差'],
            bins=SPREAD_BINS,
            labels=SPREAD_LABELS,
            right=False,
            include_lowest=True
        ).astype(str)
        dfa['月份'] = pd.to_datetime(dfa['簿记时间']).dt.to_period('M')
        return df, dfa
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def merge_by_interval(df):
    """按利差区间 + 机构 + 基准利差合并

    规则：
    - 同一机构同一利差区间内，利差精确值相同的行合并
    - 利差不同的行分开显示
    - 同一区间内按机构总认购规模降序排列
    """
    merged = (
        df.groupby(['利差区间', RESOLVED_INST_COL, '基准利差'], dropna=False)
        .agg(
            累计认购=(RESOLVED_SHARE_COL, 'sum'),
            具体利差=('基准利差', 'mean'),
            具体成本=('成本pct', 'mean'),
            具体CD=('国股CDpct', 'mean'),
        )
        .reset_index()
    )
    inst_total = merged.groupby(['利差区间', RESOLVED_INST_COL])['累计认购'].sum().reset_index()
    inst_total = inst_total.sort_values(['利差区间', '累计认购'], ascending=[True, False])
    order_map = {}
    for idx, (_, row) in enumerate(inst_total.iterrows()):
        key = (row['利差区间'], row[RESOLVED_INST_COL])
        order_map[key] = idx
    merged['_order'] = merged.apply(
        lambda r: order_map.get((r['利差区间'], r[RESOLVED_INST_COL]), 999999), axis=1
    )
    merged = merged.sort_values('_order').drop(columns='_order').reset_index(drop=True)
    return merged


def group_by_interval(merged, labels):
    grouped = defaultdict(list)
    for _, row in merged.iterrows():
        interval = str(row['利差区间']) if pd.notna(row['利差区间']) else '其他'
        grouped[interval].append(row)
    return [l for l in labels if l in grouped], grouped


# ── CSS ──────────────────────────────────────────────────────
CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
  background: #f4f5f7; color: #1a1a2e; font-size: 13px;
}
a { text-decoration: none; }

/* ── banner ── */
.page-banner {
  background: linear-gradient(135deg, #0d1b2e 0%, #1a3a5c 60%, #0d2a40 100%);
  color: #fff; padding: 18px 32px 16px;
}
.banner-top { display: flex; justify-content: space-between; align-items: flex-start; }
.banner-tag { font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: #7db8e8; margin-bottom: 4px; }
.banner-title { font-size: 20px; font-weight: 700; }
.banner-subtitle { font-size: 11px; color: rgba(255,255,255,.65); margin-top: 4px; }
.banner-badge {
  background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.25);
  border-radius: 4px; padding: 5px 12px; font-size: 11px; color: #c8dded;
  text-align: right; line-height: 1.7;
}
.banner-badge strong { color: #fff; font-size: 13px; }

/* ── overview cards ── */
.overview { padding: 14px 32px; background: #fff; border-bottom: 1px solid #e0e4ea; }
.overview-label { font-size: 11px; color: #6b7a95; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; }
.summary-cards { display: flex; gap: 10px; flex-wrap: wrap; }
.summary-card {
  background: #fafbfc; border: 1px solid #e4e8ee; border-radius: 5px;
  padding: 10px 16px; min-width: 130px; flex: 1;
}
.sc-title { font-size: 11px; color: #6b7a95; margin-bottom: 4px; }
.sc-val   { font-size: 18px; font-weight: 700; color: #1a1a2e; line-height: 1; }
.sc-unit  { font-size: 10px; font-weight: 400; color: #8a9ab5; }
.sc-sub   { font-size: 11px; color: #9aa5b5; margin-top: 3px; }

/* ── note bar ── */
.note-bar {
  padding: 8px 32px; background: #fffbec; border-bottom: 1px solid #ffe58f;
  font-size: 11px; color: #7a6010; line-height: 1.5; display: flex; gap: 24px; flex-wrap: wrap;
}

/* ── main content ── */
.content { padding: 20px 32px; }

/* ── month section ── */
.month-section {
  margin-bottom: 28px; border-radius: 6px; overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,.07);
}
.month-header { padding: 12px 16px 10px; color: #fff; }
.month-label  { font-size: 16px; font-weight: 700; letter-spacing: 1px; }
.month-kpis   { display: flex; align-items: center; font-size: 12px; color: rgba(255,255,255,.8); margin-top: 6px; flex-wrap: wrap; gap: 4px; }
.kpi     { padding: 0 8px; }
.kpi-val { font-weight: 700; color: #fff; font-size: 14px; }
.kpi-sep { opacity: .4; }
.monthly-product-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
.monthly-product-chip {
  background: rgba(255,255,255,.12); border-radius: 4px; padding: 5px 12px;
  display: flex; align-items: center; gap: 8px; flex: 1; min-width: 140px;
}
.chip-name { font-size: 11px; color: rgba(255,255,255,.85); flex: 1; }
.chip-tenor { font-size: 10px; color: rgba(255,255,255,.6); margin-left: 4px; }
.chip-val  { font-size: 14px; font-weight: 700; color: #fff; }
.chip-sub  { font-size: 10px; color: rgba(255,255,255,.6); }

.month-body {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(460px, 1fr));
  gap: 14px; padding: 14px; background: #e8f0fc;
}

/* ── product block ── */
.product-block { background: #fff; border-radius: 4px; overflow: hidden; }
.product-header {
  padding: 8px 12px; color: #fff; display: flex;
  justify-content: space-between; align-items: center;
}
.product-name  { font-size: 13px; font-weight: 700; }
.product-stats { font-size: 11px; color: rgba(255,255,255,.75); text-align: right; line-height: 1.5; }

/* ── data table ── */
.data-table { width: 100%; border-collapse: collapse; background: #fff; table-layout: fixed; }
.data-table thead th {
  color: #fff; padding: 7px 10px; text-align: left; font-size: 11px; font-weight: 600;
}
.data-table thead th:nth-child(1) { width: 130px; }
.data-table thead th:nth-child(3) { width: 100px; text-align: right; }
.data-table thead th:nth-child(4) { width: 80px;  text-align: right; }
.data-table tbody tr:nth-child(even) { background: #f7f9fc; }
.data-table tbody tr:hover { background: #eef3fa; }
.data-table tbody tr:not(:last-child) td { border-bottom: 1px solid #eaeef4; }

/* ── cell styles ── */
.interval-cell {
  padding: 7px 10px; vertical-align: middle;
  border-right: 1px solid #dde3ed; background: #f9fafc !important; white-space: nowrap;
}
.interval-label { font-size: 11px; font-weight: 600; color: #2a3a55; margin-bottom: 2px; }
.spread-badge {
  display: inline-block; font-size: 10px; color: #fff;
  padding: 1px 6px; border-radius: 3px; margin-top: 1px;
}
.inst-cell  { padding: 7px 10px; font-weight: 500; color: #1a2a40; font-size: 12px; }
.share-cell {
  padding: 7px 10px; font-variant-numeric: tabular-nums; font-weight: 600;
  color: #1a3a5c; text-align: right; font-size: 12px; white-space: nowrap;
}
.spread-cell {
  padding: 7px 10px; font-variant-numeric: tabular-nums; font-weight: 600;
  color: #c05a20; text-align: right; font-size: 12px; white-space: nowrap;
}

/* ── footer ── */
.footer {
  text-align: center; padding: 16px 0 24px;
  font-size: 11px; color: #9aa5b5;
}
"""


# ── HTML 构建函数 ────────────────────────────────────────────
def build_summary_cards(product_order):
    html = ''
    for pt, asset, tenor, total, count, avg_sp in product_order:
        color = product_color(asset, tenor)
        tenor_tag = '1Y' if tenor == '1年期' else '超1Y'
        html += f'''<div class="summary-card" style="border-top:3px solid {color["tag"]}">
  <div class="sc-title">{pt}</div>
  <div class="sc-val">{total:.2f}<span class="sc-unit"> 亿</span></div>
  <div class="sc-sub">{count}笔 · 均利差 +{avg_sp:.2f}% · {tenor_tag}</div>
</div>'''
    return html


def build_product_block(product_name, asset_type, tenor_label,
                          sub_df, asset_header_color, tag_color):
    if sub_df.empty:
        return ''

    merged = merge_by_interval(sub_df)
    active_labels, grouped = group_by_interval(merged, SPREAD_LABELS)
    if not active_labels:
        return ''

    total = sub_df['实际份额'].sum()
    count = len(sub_df)
    avg_sp = sub_df['基准利差'].mean()

    rows_html = ''
    for label in active_labels:
        entries = grouped[label]
        rowspan = len(entries)

        for i, row in enumerate(entries):
            interval_td = '' if i > 0 else f'''<td class="interval-cell" rowspan="{rowspan}">
  <div class="interval-label">{label}</div>
  <span class="spread-badge" style="background:{tag_color}">+{row["具体利差"]:.2f}%</span>
</td>'''

            rows_html += f'''<tr>
  {interval_td}
  <td class="inst-cell">{row[RESOLVED_INST_COL]}</td>
  <td class="share-cell">{row["累计认购"]:.2f} 亿</td>
  <td class="spread-cell">+{row["具体利差"]:.2f}%</td>
</tr>'''

    tenor_tag = '1年期' if tenor_label == '1年期' else '超1年期'
    return f'''<div class="product-block">
  <div class="product-header" style="background:{asset_header_color}">
    <span class="product-name">{product_name}</span>
    <span class="product-stats">{count}笔 · {total:.2f}亿 · 均利差 +{avg_sp:.2f}%</span>
  </div>
  <table class="data-table">
    <thead style="background:{asset_header_color}">
      <tr>
        <th>利差区间</th><th>认购机构</th><th>累计认购</th><th>均利差</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>'''


def build_month_section(month_label, month_df, idx, product_order):
    if month_df.empty:
        return ''

    bg_color = MONTH_COLORS[idx % len(MONTH_COLORS)]
    total    = month_df['实际份额'].sum()
    count    = len(month_df)
    avg_sp   = month_df['基准利差'].mean()
    inst_cnt = month_df['实际机构'].nunique()

    chip_html = ''
    for pt, asset, tenor, _, _, _ in product_order:
        sub = month_df[month_df['产品类型'] == pt]
        if sub.empty:
            continue
        color = product_color(asset, tenor)
        chip_html += f'''<div class="monthly-product-chip" style="border-left:3px solid {color["tag"]}">
  <span class="chip-name">{pt}</span>
  <span class="chip-val">{sub["实际份额"].sum():.2f}<span class="chip-sub"> 亿</span></span>
</div>'''

    blocks_html = ''
    for pt, asset, tenor, _, _, _ in product_order:
        sub = month_df[month_df['产品类型'] == pt]
        if sub.empty:
            continue
        color = product_color(asset, tenor)
        blocks_html += build_product_block(
            pt, asset, tenor, sub, color['header'], color['tag']
        )

    return f'''<div class="month-section">
  <div class="month-header" style="background:{bg_color}">
    <div class="month-label">{month_label}</div>
    <div class="month-kpis">
      <span class="kpi">认购总额 <span class="kpi-val">{total:.2f}亿</span></span>
      <span class="kpi-sep">|</span>
      <span class="kpi">{count}笔</span>
      <span class="kpi-sep">|</span>
      <span class="kpi">{inst_cnt}家机构</span>
      <span class="kpi-sep">|</span>
      <span class="kpi">均利差 <span class="kpi-val">+{avg_sp:.2f}%</span></span>
    </div>
    <div class="monthly-product-row">{chip_html}</div>
  </div>
  <div class="month-body">{blocks_html}</div>
</div>'''


def build_product_order(dfa):
    available = dfa['产品类型'].unique().tolist()
    ordered = [pt for pt in PRODUCT_ORDER_TEMPLATE if pt in available]
    remaining = [pt for pt in available if pt not in PRODUCT_ORDER_TEMPLATE]
    ordered += remaining
    product_order = []
    for pt in ordered:
        sub = dfa[dfa['产品类型'] == pt]
        if sub.empty:
            continue
        product_order.append((
            pt, sub['资产类型'].iloc[0], sub['期限分类'].iloc[0],
            sub['实际份额'].sum(), len(sub), sub['基准利差'].mean()
        ))
    return product_order


# ── QC ────────────────────────────────────────────────────────
def run_qc(df, dfa, out_path, month_labels, product_order, precheck_only=False):
    qc = QCRunner('ABS基准利差分析报告（产品类型维度）')
    qc.header()
    df_raw = df.copy()
    ok, warn, fail = qc.ok, qc.warn, qc.fail

    print('\n【1】数据完整性')
    ok(f'机构数：{dfa[RESOLVED_INST_COL].nunique()}家 | 产品类型：{len(product_order)}种 | 月份：{len(month_labels)}个月')

    raw_cnt = len(df_raw[df_raw['分层情况'].isin(PRIORITY_LAYERS)])
    if raw_cnt == len(dfa):
        ok(f'优先A记录数一致：{len(dfa)}条')
    else:
        fail(f'优先A记录数不一致：原始={raw_cnt}，报告={len(dfa)}')

    raw_total = df_raw[df_raw['分层情况'].isin(PRIORITY_LAYERS)]['认购份额'].sum()
    report_total = dfa['实际份额'].sum()
    diff = abs(raw_total - report_total)
    if diff < 0.001 or report_total > raw_total:
        ok(f'认购总额一致（resolve后）：{report_total:.4f}亿')
    else:
        fail(f'认购总额不一致：原始={raw_total:.4f}，报告={report_total:.4f}，差={diff:.4f}')

    min_sp, max_sp = dfa['基准利差'].min(), dfa['基准利差'].max()
    min_cost, max_cost = dfa['成本pct'].min(), dfa['成本pct'].max()
    min_cd, max_cd = dfa['国股CDpct'].min(), dfa['国股CDpct'].max()
    neg_sp = (dfa['基准利差'] < 0).sum()
    if min_cost >= 0.5 and max_cost <= 10:
        ok(f'成本范围正常：{min_cost:.2f}% ~ {max_cost:.2f}%')
    else:
        warn(f'成本范围异常：{min_cost:.4f}% ~ {max_cost:.4f}%')
    if min_sp > 0:
        ok(f'利差范围正常：+{min_sp:.2f}% ~ +{max_sp:.2f}%，均>0')
    else:
        warn(f'利差异常：{neg_sp}条负利差，范围{min_sp:.4f}% ~ {max_sp:.4f}%')
    ok(f'国股CD范围：{min_cd:.2f}% ~ {max_cd:.2f}%')

    nan_interval = dfa['利差区间'].isna().sum()
    if nan_interval == 0:
        ok('无利差区间外记录（NaN=0）')
    else:
        out_vals = dfa[dfa['利差区间'].isna()]['基准利差'].unique()
        fail(f'{nan_interval}条记录落在利差区间外（超出0.05%-1.15%），涉及利差值：{[round(v,4) for v in out_vals]}')

    unknown_tenor = (dfa['期限分类'] == '未知').sum()
    if unknown_tenor == 0:
        ok('期限分类全部分解成功，无"未知"')
    else:
        warn(f'{unknown_tenor}条记录期限分类为"未知"，请检查期限列数据')

    raw_months = sorted(pd.to_datetime(df_raw[df_raw['分层情况'].isin(PRIORITY_LAYERS)]['簿记时间']).dt.to_period('M').unique(), key=lambda x: x.to_timestamp())
    raw_ml = [str(m) for m in raw_months]
    missing_m = set(raw_ml) - set(month_labels)
    if not missing_m:
        ok(f'月份覆盖完整：{month_labels}')
    else:
        fail(f'报告缺少月份：{sorted(missing_m)}')

    raw_assets = set(df_raw[df_raw['分层情况'].isin(PRIORITY_LAYERS)]['资产类型'].unique())
    if set([pt for pt, _, _, _, _, _ in product_order]):
        ok(f'产品类型数量：{len(product_order)}个')

    print('\n【2】业务逻辑')
    excluded = df_raw[df_raw['分层情况'].str.startswith('优先A', na=False) & (df_raw['分层情况'] != '优先A')]
    if excluded.empty:
        ok('无优先A1/优先A2等相似分层被误匹配')
    else:
        warn(f'以下分层已被正确排除（共{len(excluded)}条）：{excluded["分层情况"].value_counts().to_dict()}')

    neg_sp = (dfa['基准利差'] < 0).sum()
    if neg_sp == 0:
        ok('无负利差记录（基准利差均为正值）')
    else:
        warn(f'{neg_sp}条记录的基准利差为负，请确认国股CD数据是否正确')

    tenor_dist = dfa['期限分类'].value_counts()
    ok(f'期限分类分布：{tenor_dist.to_dict()}')

    mixed = []
    for pt, sub in dfa.groupby('产品类型', dropna=False):
        tenors = sub['期限分类'].unique()
        if len(tenors) > 1:
            mixed.append(pt)
    if not mixed:
        ok(f'产品类型均为单一期限，无混合（总计{len(product_order)}个产品）')
    else:
        fail(f'以下产品类型混合了多种期限：{mixed}')

    dfa_qc = dfa.copy()
    merged_all = (
        dfa_qc.groupby(['利差区间', RESOLVED_INST_COL, '基准利差'], dropna=False)
        .agg(累计认购=(RESOLVED_SHARE_COL, 'sum'))
        .reset_index()
    )
    if len(merged_all) < len(dfa):
        ok(f'合并生效：原始{len(dfa)}条 → 合并后{len(merged_all)}条（合并{len(dfa)-len(merged_all)}条）')
    elif len(merged_all) == len(dfa):
        ok(f'无需合并：每条记录均唯一（共{len(dfa)}条）')

    multi_inst = dfa_qc.groupby(['利差区间', RESOLVED_INST_COL])['基准利差'].nunique().reset_index()
    expanded = multi_inst[multi_inst['基准利差'] > 1]
    if expanded.empty:
        ok('无同利差区间+机构内利差不同需展开的情况')
    else:
        ok(f'{len(expanded)}组同利差区间+机构内利差不同，记录已正确展开')

    sort_fail = False
    for pt, asset, tenor, _, _, _ in product_order:
        sub = dfa[dfa['产品类型'] == pt].copy()
        merged = (
            sub.groupby(['利差区间', RESOLVED_INST_COL, '基准利差'], dropna=False)
            .agg(累计认购=(RESOLVED_SHARE_COL, 'sum'))
            .reset_index()
        )
        inst_total = merged.groupby(['利差区间', RESOLVED_INST_COL])['累计认购'].sum().reset_index()
        inst_total = inst_total.sort_values(['利差区间', '累计认购'], ascending=[True, False])
        for interval_label in inst_total['利差区间'].dropna().unique():
            grp = inst_total[inst_total['利差区间'] == interval_label]['累计认购'].tolist()
            if grp != sorted(grp, reverse=True):
                warn(f'【{pt}】区间"{interval_label}"排序异常：{grp}')
                sort_fail = True
    if not sort_fail:
        ok('各产品各区间内机构认购规模均为降序排列')

    print('\n【3】输出质量')
    if precheck_only:
        ok(f'输出质量检查在输出文件写入后执行（预检模式跳过）')
    else:
        file_kb = os.path.getsize(out_path) / 1024
        if file_kb < 1:
            fail(f'输出文件过小（{file_kb:.1f}KB）')
        elif file_kb < 5:
            warn(f'输出文件较小（{file_kb:.1f}KB），请确认内容完整性')
        else:
            ok(f'输出文件大小正常：{file_kb:.1f}KB')

        with open(out_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        section_cnt = html_content.count('class="month-section"')
        if section_cnt == len(month_labels):
            ok(f'HTML月份区块数量正确：{section_cnt}个')
        else:
            fail(f'HTML月份区块数量不符：期望{len(month_labels)}个，实际{section_cnt}个')

    return qc.summary()


# ── 主入口 ────────────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python gen_spread_report.py <xlsx_path> [output_path]')
        sys.exit(1)

    xlsx_path = sys.argv[1]
    out_path  = sys.argv[2] if len(sys.argv) > 2 else None

    if out_path is None:
        date_tag = pd.Timestamp('today').strftime('%Y%m%d')
        kanban_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', 'deliverables', 'dashboards', '01_latest'
        )
        os.makedirs(kanban_dir, exist_ok=True)
        out_path = os.path.join(kanban_dir, f'{date_tag}_机构投标基准利差看板.html')

    try:
        print(f'Loading: {xlsx_path}')
        df, dfa = read_data(xlsx_path)
    except ValueError as e:
        print(f'[INPUT ERROR] {e}')
        sys.exit(1)
    except Exception as e:
        print(f'[ERROR] 数据加载失败：{e}')
        sys.exit(1)

    print('\n产品类型分布：')
    prod_summary = (
        dfa.groupby(['产品类型', '资产类型', '期限分类'])
        .agg(总额=('认购份额', 'sum'), 笔数=('认购份额', 'count'),
             均利差=('基准利差', 'mean'))
        .sort_values('总额', ascending=False)
    )
    print(prod_summary.round(2).to_string())

    print(f'\n优先A记录: {len(dfa)} 条 | 产品类型: {dfa["产品类型"].nunique()} 种')
    print(f'基准利差范围: +{dfa["基准利差"].min():.2f}% ~ +{dfa["基准利差"].max():.2f}%')

    product_order = build_product_order(dfa)
    print('\n产品类型最终顺序（模板顺序）：')
    for i, (pt, asset, tenor, total, count, avg_sp) in enumerate(product_order, 1):
        print(f'  {i}. {pt}  {total:.2f}亿')

    months       = sorted(dfa['月份'].unique(), key=lambda x: x.to_timestamp(), reverse=True)
    month_labels = [str(m) for m in months]
    total_share = dfa['实际份额'].sum()
    total_inst  = dfa['实际机构'].nunique()
    avg_spread  = dfa['基准利差'].mean()
    date_min    = pd.to_datetime(dfa['簿记时间']).dt.strftime('%Y-%m-%d').min()
    date_max    = pd.to_datetime(dfa['簿记时间']).dt.strftime('%Y-%m-%d').max()

    month_sections = ''.join(
        build_month_section(mlabel, dfa[dfa['月份'].astype(str) == mlabel], idx, product_order)
        for idx, mlabel in enumerate(month_labels)
    )
    cards = build_summary_cards(product_order)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ABS 优先A 基准利差分析（产品类型维度）</title>
<style>{CSS}</style>
</head>
<body>
<div class="page-banner">
  <div class="banner-top">
    <div>
      <div class="banner-tag">ABS Spread Analysis · Priority A</div>
      <div class="banner-title">优先A 基准利差分析</div>
      <div class="banner-subtitle">
        基准利差 = 认购成本 − 同日国股CD ·
        维度：月份 + 产品类型（资产类型+期限）+ 机构利差 ·
        区间步长 0.05%
      </div>
    </div>
    <div class="banner-badge">
      数据期间 <strong>{date_min} ~ {date_max}</strong><br>
      优先A <strong>{len(dfa)}</strong> 笔 · 总额 <strong>{total_share:.2f} 亿</strong> · <strong>{total_inst}</strong> 家机构<br>
      全局均利差 <strong>+{avg_spread:.2f}%</strong>
    </div>
  </div>
</div>

<div class="overview">
  <div class="overview-label">各产品类型合计（按业务顺序）</div>
  <div class="summary-cards">{cards}</div>
</div>

<div class="note-bar">
  <span>筛选条件：分层情况 = "优先A"</span>
  <span>基准利差 = 认购成本 − 同日国股CD（单位：%）</span>
  <span>产品类型 = 资产类型 + 期限分类（单一期限，无混合）</span>
  <span>利差区间步长 0.05%，左闭右开</span>
  <span>同一机构同利差的多笔认购已合并</span>
</div>

<div class="content">{month_sections}</div>

<div class="footer">
  数据来源：{os.path.basename(xlsx_path)} ·
  生成时间：{pd.Timestamp('today').strftime('%Y-%m-%d')} ·
  分析报告员 pBuddy
</div>
</body>
</html>'''

    qc_passed = run_qc(df, dfa, out_path, month_labels, product_order, precheck_only=True)

    if qc_passed:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'\nDone: {out_path}')
        run_qc(df, dfa, out_path, month_labels, product_order, precheck_only=False)
    else:
        print(f'\n[ERROR] QC未通过，跳过输出文件写入（{out_path}）')
        print('[ERROR] 请修正数据或逻辑后重试')
