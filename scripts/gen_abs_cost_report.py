"""ABS机构认购成本分布报告生成器（月份+资产类型双维度版）

用法:
  python gen_abs_cost_report.py <xlsx_path> [output_path]
  output_path 默认为 ABS技能包/看板/<日期>_机构投标利率看板.html
"""

import sys
import os
import pandas as pd
from collections import defaultdict

from abs_common import (
    COST_BINS, COST_LABELS, ASSET_COLORS, DEFAULT_COLOR,
    MONTH_COLORS, MONTH_ACCENT,
    RESOLVED_COST_COL, RESOLVED_INST_COL, RESOLVED_SHARE_COL,
    NON_NUMERIC_COST_VALS, PRIORITY_LAYERS,
    COST_BIN_LOWER_NON_PREF,
    is_preferential_asset,
    load_and_filter, QCRunner,
)


# ── 成本区间配置（abs_common已定义COST_BINS/LABELS，此处保留引用）──
# COST_BINS / COST_LABELS 从 abs_common 导入

# ── 数据读取与预处理 ──────────────────────────────────────────
def read_data(xlsx_path):
    """读取并预处理台账数据，返回 df, dfa"""
    df, dfa, tmp_path, _ = load_and_filter(xlsx_path, need_tenor=False)
    try:
        dfa[RESOLVED_COST_COL + 'pct'] = dfa[RESOLVED_COST_COL] * 100
        dfa['成本区间'] = pd.cut(
            dfa[RESOLVED_COST_COL + 'pct'],
            bins=COST_BINS,
            labels=COST_LABELS,
            right=False,
            include_lowest=True
        ).astype(str)
        dfa['月份'] = dfa['簿记时间'].dt.to_period('M')
        return df, dfa
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def merge_by_interval(df):
    """按成本区间+机构+基准利差合并

    规则：
    - 同一机构同一区间内，利差相同的行合并（累计认购+保留最小成本）
    - 利差不同的行分开显示
    - 同一区间内按机构总认购规模降序排列
    """
    df = df.copy()
    df['基准利差'] = df['实际成本pct'] - df['国股CD'] * 100

    merged = (
        df.groupby(['成本区间', RESOLVED_INST_COL, '基准利差'], dropna=False)
        .agg(
            累计认购=(RESOLVED_SHARE_COL, 'sum'),
            具体成本=(RESOLVED_COST_COL, 'first'),
        )
        .reset_index()
    )
    inst_total = merged.groupby(['成本区间', RESOLVED_INST_COL])['累计认购'].sum().reset_index()
    inst_total = inst_total.sort_values(['成本区间', '累计认购'], ascending=[True, False])
    order_map = {}
    for idx, (_, row) in enumerate(inst_total.iterrows()):
        key = (row['成本区间'], row[RESOLVED_INST_COL])
        order_map[key] = idx
    merged['_order'] = merged.apply(
        lambda r: order_map.get((r['成本区间'], r[RESOLVED_INST_COL]), 999999), axis=1
    )
    merged = merged.sort_values('_order').drop(columns='_order').reset_index(drop=True)
    return merged


def group_by_interval(merged, labels):
    grouped = defaultdict(list)
    for _, row in merged.iterrows():
        interval = str(row['成本区间']) if pd.notna(row['成本区间']) else '其他'
        grouped[interval].append(row)
    return [l for l in labels if l in grouped], grouped


def build_interval_cell(row_list, tc, row_idx):
    """区间单元格：仅第一行输出（带rowspan），其余行返回空字符串"""
    if row_idx != 0:
        return ''
    n = len(row_list)
    sample_cost = f"{row_list[0]['具体成本'] * 100:.3f}%"
    return (
        f'<td rowspan="{n}" class="interval-cell">'
        f'<div class="interval-label">{row_list[0]["成本区间"]}</div>'
        f'<div class="cost-badge" style="background:{tc}">{sample_cost}</div>'
        f'</td>'
    )


# ── CSS（内联于生成器，不拆分）───────────────────────────────
CSS = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: "PingFang SC","Microsoft YaHei","Helvetica Neue",Arial,sans-serif;
         background:#f4f5f7; color:#1a1a2e; font-size:13px; }

  /* 顶部横幅 */
  .page-banner { background: linear-gradient(135deg,#0d1b2e 0%,#1a3a5c 60%,#0d2a40 100%);
                 color:#fff; padding:18px 32px 16px; }
  .banner-top { display:flex; align-items:flex-end; justify-content:space-between; }
  .banner-tag { font-size:10px; letter-spacing:2px; text-transform:uppercase; color:#7db8e8; margin-bottom:4px; }
  .banner-title { font-size:20px; font-weight:700; letter-spacing:.5px; }
  .banner-subtitle { font-size:11px; color:#a0bfd4; margin-top:3px; }
  .banner-badge { background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.25);
                  border-radius:4px; padding:5px 12px; font-size:11px; color:#c8dded;
                  text-align:right; line-height:1.7; }
  .banner-badge strong { color:#fff; font-size:13px; }

  /* 概览卡片 */
  .overview { padding:14px 32px; background:#fff; border-bottom:1px solid #e0e4ea; }
  .overview-label { font-size:10px; letter-spacing:2px; color:#8a9ab5; text-transform:uppercase; margin-bottom:10px; }
  .summary-cards { display:flex; gap:10px; flex-wrap:wrap; }
  .summary-card { background:#fafbfc; border:1px solid #e4e8ee; border-radius:5px;
                  padding:10px 16px; min-width:120px; flex:1; }
  .sc-title { font-size:11px; color:#6b7a95; margin-bottom:4px; }
  .sc-val { font-size:18px; font-weight:700; color:#1a1a2e; line-height:1; }
  .sc-unit { font-size:10px; font-weight:400; color:#8a9ab5; }
  .sc-sub { font-size:11px; color:#9aa5b5; margin-top:3px; }

  /* 说明栏 */
  .note-bar { padding:8px 32px; background:#fffbec; border-bottom:1px solid #ffe58f;
               font-size:11px; color:#7a6010; line-height:1.5; }
  .note-bar span { margin-right:16px; }

  /* 主内容 */
  .content { padding:18px 32px 32px; }

  /* 月份区块 */
  .month-section { margin-bottom:28px; border-radius:6px; overflow:hidden;
                    box-shadow:0 1px 3px rgba(0,0,0,.07); }
  .month-header { padding:12px 16px 10px; color:#fff; }
  .month-title-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; }
  .month-label { font-size:16px; font-weight:700; letter-spacing:1px; }
  .month-kpis { display:flex; align-items:center; font-size:12px; color:rgba(255,255,255,.8); }
  .kpi { padding:0 8px; }
  .kpi-val { font-weight:700; color:#fff; font-size:14px; }
  .kpi-unit { font-size:10px; font-weight:400; }
  .kpi-sep { opacity:.4; }

  /* 月度资产汇总行 */
  .monthly-asset-row { display:flex; gap:10px; flex-wrap:wrap; }
  .monthly-asset-chip { background:rgba(255,255,255,.12); border-radius:4px; padding:5px 12px;
                         display:flex; align-items:center; gap:8px; flex:1; min-width:130px; }
  .chip-name { font-size:11px; color:rgba(255,255,255,.85); flex:1; }
  .chip-val { font-size:14px; font-weight:700; color:#fff; }
  .chip-unit { font-size:10px; font-weight:400; color:rgba(255,255,255,.7); margin-left:1px; }
  .chip-sub { font-size:10px; color:rgba(255,255,255,.6); }

  /* 月份体内资产网格 */
  .month-body { display:grid; grid-template-columns:repeat(auto-fill,minmax(420px,1fr));
                 gap:14px; padding:14px; background:""" + MONTH_ACCENT + """; }

  /* 资产区块 */
  .asset-block { background:#fff; border-radius:5px; overflow:hidden;
                 box-shadow:0 1px 2px rgba(0,0,0,.06); }
  .asset-hdr { display:flex; align-items:center; justify-content:space-between;
               padding:8px 14px; color:#fff; }
  .asset-title { font-size:13px; font-weight:700; letter-spacing:.5px; }
  .asset-sub { font-size:11px; color:rgba(255,255,255,.75); }

  /* 数据表格 */
  .data-table { width:100%; border-collapse:collapse; background:#fff; table-layout:fixed; }
  .data-table thead th { color:#fff; padding:8px 12px; text-align:left;
                          font-size:11px; font-weight:600; letter-spacing:.3px; }
  .data-table thead th:nth-child(1) { width:140px; }
  .data-table thead th:nth-child(3) { width:120px; text-align:right; }
  .data-table tbody tr:nth-child(even) { background:#f7f9fc; }
  .data-table tbody tr:hover { background:#eef3fa; }
  .data-table tbody tr:not(:last-child) td { border-bottom:1px solid #eaeef4; }

  .interval-cell { padding:7px 12px; vertical-align:middle; border-right:1px solid #dde3ed;
                   background:#f9fafc!important; white-space:nowrap; }
  .interval-label { font-size:12px; font-weight:600; color:#2a3a55; margin-bottom:3px; }
  .cost-badge { display:inline-block; font-size:10px; color:#fff;
                 padding:1px 6px; border-radius:3px; }
  .inst-cell { padding:7px 12px; font-weight:500; color:#1a2a40; font-size:12px; }
  .share-cell { padding:7px 12px; font-variant-numeric:tabular-nums; font-weight:600;
                 color:#1a3a5c; text-align:right; font-size:12px; white-space:nowrap; }
  .unit { font-size:10px; font-weight:400; color:#8a9ab5; margin-left:2px; }

  .footer { padding:14px 32px; border-top:1px solid #e0e4ea;
            font-size:11px; color:#9aa5b5; text-align:center; }
"""


# ── 构建函数（数据层）──────────────────────────────────────────
def build_asset_block_data(sub_df):
    """从 sub_df 计算资产块所需数据（纯数据，无 HTML）"""
    merged = merge_by_interval(sub_df)
    active_labels, grouped = group_by_interval(merged, COST_LABELS)
    # 把每行数据序列化为可渲染的 dict
    rows_data = []
    for interval in active_labels:
        rows = grouped[interval]
        for i, row in enumerate(rows):
            rows_data.append({
                'interval': interval,
                'rows': rows,
                'idx': i,
                'inst': row[RESOLVED_INST_COL],
                'cum_share': float(row["累计认购"]),
            })
    return {
        'merged': merged,
        'active_labels': active_labels,
        'grouped': grouped,
        'rows_data': rows_data,
        'total_share': float(sub_df['实际份额'].sum()),
        'unique_inst': int(merged['实际机构'].nunique()),
    }


def build_month_section_data(mlabel, mdf, month_idx, asset_order):
    """从 mdf 计算月份段所需数据（含每个 asset 的 block_data + chip 数据）"""
    chips_data = []
    asset_blocks_data = []
    for asset in asset_order:
        sub = mdf[mdf['资产类型'] == asset]
        if len(sub) == 0:
            continue
        block_data = build_asset_block_data(sub)
        chips_data.append({
            'asset': asset,
            'asset_total': float(sub['实际份额'].sum()),
            'asset_inst': block_data['unique_inst'],
        })
        asset_blocks_data.append({'asset': asset, 'block_data': block_data})

    return {
        'mlabel': mlabel,
        'month_idx': month_idx,
        'month_total': float(mdf['实际份额'].sum()),
        'month_count': int(len(mdf)),
        'month_inst': int(mdf['实际机构'].nunique()),
        'chips_data': chips_data,
        'asset_blocks_data': asset_blocks_data,
    }


# ── 渲染函数（纯 HTML）─────────────────────────────────────────
def render_asset_block(asset_name, block_data):
    color = ASSET_COLORS.get(asset_name, DEFAULT_COLOR)
    hc, tc = color['header'], color['tag']

    rows_html = []
    for r in block_data['rows_data']:
        cells = [build_interval_cell(r['rows'], tc, r['idx'])]
        cells.append(f'<td class="inst-cell">{r["inst"]}</td>')
        cells.append(f'<td class="share-cell">{r["cum_share"]:.3f}<span class="unit">亿</span></td>')
        rows_html.append('<tr>' + ''.join(cells) + '</tr>')

    unique_inst = block_data['unique_inst']
    total_share = block_data['total_share']

    return f'''
  <div class="asset-block">
    <div class="asset-hdr" style="background:{hc}">
      <span class="asset-title">{asset_name}</span>
      <span class="asset-sub">{unique_inst}家 · {total_share:.2f}亿</span>
    </div>
    <table class="data-table">
      <thead><tr>
        <th style="background:{hc};width:140px">成本区间</th>
        <th style="background:{hc}">认购机构</th>
        <th style="background:{hc};width:120px;text-align:right">累计认购</th>
      </tr></thead>
      <tbody>{''.join(rows_html)}</tbody>
    </table>
  </div>'''


def render_summary_cards(dfa, asset_order):
    asset_summary = dfa.groupby('资产类型').agg(
        笔数=('实际机构', 'count'), 认购合计=('实际份额', 'sum')
    ).reindex(asset_order)
    cards = ''
    for asset, row_s in asset_summary.iterrows():
        color = ASSET_COLORS.get(asset, DEFAULT_COLOR)
        cards += f'''
    <div class="summary-card" style="border-top:3px solid {color["tag"]}">
      <div class="sc-title">{asset}</div>
      <div class="sc-val">{row_s["认购合计"]:.2f} <span class="sc-unit">亿</span></div>
      <div class="sc-sub">{int(row_s["笔数"])}笔认购</div>
    </div>'''
    return cards


def render_month_section(section_data):
    mc = MONTH_COLORS[section_data['month_idx'] % len(MONTH_COLORS)]
    mlabel = section_data['mlabel']
    month_total = section_data['month_total']
    month_count = section_data['month_count']
    month_inst = section_data['month_inst']

    chips = ''
    for chip in section_data['chips_data']:
        color = ASSET_COLORS.get(chip['asset'], DEFAULT_COLOR)
        chips += f'''
        <div class="monthly-asset-chip" style="border-left:3px solid {color["tag"]}">
          <span class="chip-name">{chip["asset"]}</span>
          <span class="chip-val">{chip["asset_total"]:.2f}<span class="chip-unit">亿</span></span>
          <span class="chip-sub">{chip["asset_inst"]}家</span>
        </div>'''

    asset_blocks = ''.join(
        render_asset_block(item['asset'], item['block_data'])
        for item in section_data['asset_blocks_data']
    )

    return f'''
  <div class="month-section">
    <div class="month-header" style="background:{mc}">
      <div class="month-title-row">
        <span class="month-label">{mlabel}</span>
        <div class="month-kpis">
          <span class="kpi"><span class="kpi-val">{month_total:.2f}</span><span class="kpi-unit">亿</span></span>
          <span class="kpi-sep">|</span>
          <span class="kpi"><span class="kpi-val">{month_inst}</span>家机构</span>
          <span class="kpi-sep">|</span>
          <span class="kpi"><span class="kpi-val">{month_count}</span>笔</span>
        </div>
      </div>
      <div class="monthly-asset-row">{chips}</div>
    </div>
    <div class="month-body">{asset_blocks}
    </div>
  </div>'''


# ── 兼容旧接口 ─────────────────────────────────────────────────
def build_asset_block(asset_name, sub_df):
    return render_asset_block(asset_name, build_asset_block_data(sub_df))


def build_summary_cards(dfa, asset_order):
    return render_summary_cards(dfa, asset_order)


def build_month_section(mlabel, mdf, month_idx, asset_order):
    return render_month_section(build_month_section_data(mlabel, mdf, month_idx, asset_order))


# ── 数据计算层（供综合看板调用）──────────────────────────────
def compute_data(xlsx_path):
    """读取台账 + 计算所有数据 + QC precheck，返回数据 dict"""
    print(f'Loading: {xlsx_path}')
    df, dfa = read_data(xlsx_path)
    print(f'优先A记录: {len(dfa)} 条 | 资产类型: {dfa["资产类型"].nunique()} 种')

    asset_order = dfa.groupby('资产类型').size().sort_values(ascending=False).index.tolist()
    months = sorted(dfa['月份'].unique(), key=lambda x: x.to_timestamp(), reverse=True)
    month_labels = [str(m) for m in months]

    total_records = len(dfa)
    total_share_all = dfa['实际份额'].sum()
    total_inst = dfa['实际机构'].nunique()
    date_min = pd.to_datetime(dfa['簿记时间']).dt.strftime('%Y-%m-%d').min()
    date_max = pd.to_datetime(dfa['簿记时间']).dt.strftime('%Y-%m-%d').max()

    # 预计算每个月份段的 section_data
    month_sections_data = []
    for idx, mlabel in enumerate(month_labels):
        mdf = dfa[dfa['月份'].astype(str) == mlabel]
        section_data = build_month_section_data(mlabel, mdf, idx, asset_order)
        month_sections_data.append(section_data)

    meta = {
        'total_records': total_records,
        'total_share_all': float(total_share_all),
        'total_inst': int(total_inst),
        'date_min': date_min,
        'date_max': date_max,
        'month_labels': month_labels,
        'asset_order': asset_order,
    }

    # QC precheck
    qc_passed = run_qc(df, dfa, out_path=None, month_labels=month_labels,
                       asset_order=asset_order, precheck_only=True)
    if not qc_passed:
        raise RuntimeError('[QC] ABS成本分布报告预检未通过')

    return {
        'df': df,
        'dfa': dfa,
        'meta': meta,
        'month_sections_data': month_sections_data,
        'xlsx_basename': os.path.basename(xlsx_path),
        'xlsx_path': xlsx_path,
    }


def render_body(data):
    """渲染 body 片段（不含 <!DOCTYPE>/<html>/<head>）"""
    dfa = data['dfa']
    meta = data['meta']
    xlsx_basename = data['xlsx_basename']

    month_sections = ''.join(
        render_month_section(sd) for sd in data['month_sections_data']
    )
    cards = render_summary_cards(dfa, meta['asset_order'])

    return f'''
<div class="page-banner">
  <div class="banner-top">
    <div>
      <div class="banner-tag">ABS Investor Analysis · Priority A</div>
      <div class="banner-title">优先A 机构认购成本分布分析</div>
      <div class="banner-subtitle">按月份 + 资产类型分类 · 成本区间步长 0.05%</div>
    </div>
    <div class="banner-badge">
      数据期间 <strong>{meta["date_min"]} ~ {meta["date_max"]}</strong><br>
      优先A <strong>{meta["total_records"]}</strong> 笔 · 总额 <strong>{meta["total_share_all"]:.2f} 亿</strong> · <strong>{meta["total_inst"]}</strong> 家机构
    </div>
  </div>
</div>

<div class="overview">
  <div class="overview-label">各资产类型合计</div>
  <div class="summary-cards">{cards}</div>
</div>

<div class="note-bar">
  <span>筛选条件：分层情况 = "优先A"</span>
  <span>月份按簿记时间确定</span>
  <span>成本区间步长 0.05%，左闭右开</span>
  <span>同一机构同利差的多笔认购已合并</span>
</div>

<div class="content">{month_sections}</div>

<div class="footer">
  数据来源：{xlsx_basename} · 生成时间：{pd.Timestamp('today').strftime('%Y-%m-%d')} · 分析报告员 Peizhi Wu
</div>'''


def render_html(data):
    """渲染完整 HTML 文档（含 <!DOCTYPE>/<html>/<head>）"""
    body = render_body(data)
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ABS 优先A 机构认购成本分布分析</title>
<style>{CSS}</style>
</head>
<body>{body}
</body>
</html>'''


# ── 自我检查 ──────────────────────────────────────────────────
def run_qc(df, dfa, out_path, month_labels, asset_order, precheck_only=False):
    """生成后自我检查：数据完整性 + 业务逻辑 + 输出质量"""
    qc = QCRunner('ABS成本分布报告')
    qc.header()
    df_raw = df.copy()

    print('\n【1】数据完整性')
    ok, warn, fail = qc.ok, qc.warn, qc.fail

    ok(f'机构数：{dfa[RESOLVED_INST_COL].nunique()}家 | 资产类型：{len(asset_order)}种 | 月份：{len(month_labels)}个月')

    raw_priority_a = len(df_raw[df_raw['分层情况'].isin(PRIORITY_LAYERS)])
    report_records = len(dfa)
    if raw_priority_a == report_records:
        ok(f'优先A记录数一致：原始={raw_priority_a}条，报告={report_records}条')
    else:
        fail(f'优先A记录数不一致：原始={raw_priority_a}条，报告={report_records}条，差异={abs(raw_priority_a - report_records)}条')

    raw_total = df_raw[df_raw['分层情况'].isin(PRIORITY_LAYERS)]['认购份额'].sum()
    report_total = dfa['实际份额'].sum()
    if report_total >= raw_total - 0.001:
        ok(f'认购总额一致：{report_total:.4f}亿（resolve后≥原始TUV总额）')
        if report_total > raw_total + 0.001:
            inc = report_total - raw_total
            ok(f'  resolve后较TUV新增：{inc:.4f}亿（补充簿记数据）')
    else:
        fail(f'认购总额不一致：原始={raw_total:.4f}亿，报告={report_total:.4f}亿，差={abs(raw_total - report_total):.4f}亿')

    min_cost, max_cost = dfa['实际成本pct'].min(), dfa['实际成本pct'].max()
    min_share, max_share = dfa['实际份额'].min(), dfa['实际份额'].max()
    neg_shares = (dfa['实际份额'] <= 0).sum()
    if min_cost >= 0.5 and max_cost <= 10:
        ok(f'成本范围正常：{min_cost:.2f}% ~ {max_cost:.2f}%')
    else:
        warn(f'成本范围异常：{min_cost:.4f}% ~ {max_cost:.4f}%（期望0.5%~10%）')
    if min_share > 0:
        ok(f'份额范围正常：{min_share:.4f}亿 ~ {max_share:.4f}亿，均>0')
    else:
        warn(f'{neg_shares}条记录认购份额≤0，请检查')

    # 成本 bin 范围校验（保理类下限 1.30%，非保理类下限 1.50%）
    # bin 已扩展下限到 1.30%，所以保理类 1.30-1.50% 不会 NaN；这里检查 < 1.30% 的真实异常
    nan_count = dfa['成本区间'].isna().sum()
    pref_mask = dfa['资产类型'].apply(is_preferential_asset)
    if nan_count == 0:
        ok('无成本区间外记录（NaN=0）')
    else:
        nan_df = dfa[dfa['成本区间'].isna()]
        nan_pref = int((nan_df['资产类型'].apply(is_preferential_asset)).sum())
        nan_non_pref = nan_count - nan_pref
        if nan_non_pref > 0:
            nan_costs_non_pref = nan_df[~nan_df['资产类型'].apply(is_preferential_asset)]['实际成本pct'].unique()
            fail(f'{nan_non_pref}条非保理类记录落在成本区间外（超出1.50%-2.50%），涉及成本值：{[round(c,4) for c in nan_costs_non_pref]}')
        if nan_pref > 0:
            nan_costs_pref = nan_df[nan_df['资产类型'].apply(is_preferential_asset)]['实际成本pct'].unique()
            fail(f'{nan_pref}条保理类记录落在成本区间外（超出1.30%-2.50%），涉及成本值：{[round(c,4) for c in nan_costs_pref]}')

    # 非保理类资产成本下限校验：bin 已扩展到 1.30%，但非保理类 < 1.50% 视为异常
    non_pref_low = dfa[~pref_mask & (dfa['实际成本pct'] < COST_BIN_LOWER_NON_PREF)]
    if len(non_pref_low) == 0:
        ok(f'非保理类资产成本均 ≥ {COST_BIN_LOWER_NON_PREF:.2f}%')
    else:
        fail(f'{len(non_pref_low)}条非保理类记录成本 < {COST_BIN_LOWER_NON_PREF:.2f}%（异常），涉及：{non_pref_low[["项目名称","资产类型","实际成本pct"]].to_dict("records")}')

    raw_months = sorted(pd.to_datetime(df_raw[df_raw['分层情况'].isin(PRIORITY_LAYERS)]['簿记时间'])
                        .dt.to_period('M').unique(), key=lambda x: x.to_timestamp())
    raw_month_labels = [str(m) for m in raw_months]
    missing_months = set(raw_month_labels) - set(month_labels)
    if not missing_months:
        ok(f'月份覆盖完整：{month_labels}')
    else:
        fail(f'报告缺少月份：{sorted(missing_months)}')

    raw_assets = set(df_raw[df_raw['分层情况'].isin(PRIORITY_LAYERS)]['资产类型'].unique())
    report_assets = set(asset_order)
    missing_assets = raw_assets - report_assets
    if not missing_assets:
        ok(f'资产类型覆盖完整：{asset_order}')
    else:
        fail(f'报告缺少资产类型：{missing_assets}')

    print('\n【2】业务逻辑')
    dfa_qc = dfa.copy()
    dfa_qc['基准利差'] = dfa_qc['实际成本pct'] - dfa_qc['国股CD'] * 100

    excluded = df_raw[df_raw['分层情况'].str.startswith('优先A', na=False) & (df_raw['分层情况'] != '优先A')]
    if excluded.empty:
        ok('无"优先A1/优先A2"等相似分层被误匹配')
    else:
        excluded_types = excluded['分层情况'].value_counts().to_dict()
        warn(f'以下分层已被正确排除（共{len(excluded)}条）：{excluded_types}')

    multi_inst = dfa_qc.groupby(['成本区间', RESOLVED_INST_COL])['基准利差'].nunique().reset_index()
    expanded = multi_inst[multi_inst['基准利差'] > 1]
    if expanded.empty:
        ok('无同机构+区间内利差不同需展开的情况')
    else:
        ok(f'{len(expanded)}组同机构+区间内利差不同，记录已正确展开（不合并）')

    merged_all = (
        dfa_qc.groupby(['成本区间', RESOLVED_INST_COL, '基准利差'], dropna=False)
        .agg(累计认购=(RESOLVED_SHARE_COL, 'sum'))
        .reset_index()
    )
    if len(merged_all) < len(dfa):
        ok(f'合并生效：原始{len(dfa)}条 → 合并后{len(merged_all)}条（合并{len(dfa)-len(merged_all)}条）')
    elif len(merged_all) == len(dfa):
        ok(f'无需合并：每条记录均唯一（共{len(dfa)}条）')
    else:
        warn(f'合并后记录数({len(merged_all)})多于原始({len(dfa)})，请检查groupby逻辑')

    sort_fail = False
    for asset in asset_order:
        sub = dfa[dfa['资产类型'] == asset].copy()
        sub['基准利差'] = sub['实际成本pct'] - sub['国股CD'] * 100
        merged = (
            sub.groupby(['成本区间', RESOLVED_INST_COL, '基准利差'], dropna=False)
            .agg(累计认购=(RESOLVED_SHARE_COL, 'sum'))
            .reset_index()
        )
        inst_total = merged.groupby(['成本区间', RESOLVED_INST_COL])['累计认购'].sum().reset_index()
        inst_total = inst_total.sort_values(['成本区间', '累计认购'], ascending=[True, False])
        # 验证跨机构排序：同区间内按机构总份额降序
        for interval_label in inst_total['成本区间'].dropna().unique():
            grp = inst_total[inst_total['成本区间'] == interval_label]['累计认购'].tolist()
            if grp != sorted(grp, reverse=True):
                warn(f'【{asset}】区间"{interval_label}"排序异常：{grp}')
                sort_fail = True
    if not sort_fail:
        ok('各资产各区间内机构认购规模均为降序排列')

    print('\n【3】输出质量')
    if not precheck_only:
        file_size_kb = os.path.getsize(out_path) / 1024
        if file_size_kb < 1:
            fail(f'输出文件过小（{file_size_kb:.1f}KB），HTML内容可能未写入')
        elif file_size_kb < 5:
            warn(f'输出文件较小（{file_size_kb:.1f}KB），请确认内容完整性')
        else:
            ok(f'输出文件大小正常：{file_size_kb:.1f}KB')

        with open(out_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        month_section_count = html_content.count('class="month-section"')
        if month_section_count == len(month_labels):
            ok(f'HTML月份区块数量正确：{month_section_count}个')
        else:
            fail(f'HTML月份区块数量不符：期望{len(month_labels)}个，实际{month_section_count}个')

        total_str = f'{report_total:.2f}'
        if total_str in html_content:
            ok(f'HTML中包含正确总额文字：{total_str}亿')
        else:
            warn(f'HTML中未找到总额"{total_str}"，请检查banner数据是否正确渲染')
    else:
        ok(f'输出质量检查在输出文件写入后执行（预检模式跳过）')

    return qc.summary()


# ── 主入口 ──────────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python gen_abs_cost_report.py <xlsx_path> [output_path]")
        sys.exit(1)

    xlsx_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None

    if out_path is None:
        date_tag = pd.Timestamp('today').strftime('%Y%m%d')
        kanban_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', 'deliverables', 'dashboards', '01_latest'
        )
        os.makedirs(kanban_dir, exist_ok=True)
        out_path = os.path.join(kanban_dir, f'{date_tag}_机构投标利率看板.html')

    try:
        data = compute_data(xlsx_path)
    except ValueError as e:
        print(f'[INPUT ERROR] {e}')
        sys.exit(1)
    except Exception as e:
        print(f'[ERROR] {e}')
        sys.exit(1)

    html = render_html(data)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Done: {out_path}')
    print(f'月份: {data["meta"]["month_labels"]}')
    print(f'资产类型: {data["meta"]["asset_order"]}')
    run_qc(data['df'], data['dfa'], out_path, data['meta']['month_labels'],
           data['meta']['asset_order'], precheck_only=False)
