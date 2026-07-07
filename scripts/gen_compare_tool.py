"""生成ABS机构成本比对工具HTML（含期限维度 + 成本微调）

工具二（发行定价 Skill）
- 下拉选择：产品类型（资产类型+期限）
- 下拉选择：期限筛选（全部/1年期/超1年期）
- 数字输入框 + /- 按钮：目标成本上限，步长0.01%，范围1.50%~2.50%
- 输出：符合条件的机构排名（按实际成本升序，成本相同时按认购份额降序）
- 结果列：# | 认购机构 | 簿记日期 | 实际成本 | 基准利差 | 认购份额

产品类型 = 资产类型 + 期限分类（单一期限，无混合）
基准利差 = 成本(%) - 国股CD(%)
"""

import sys, os
import pandas as pd
import json

from abs_common import (
    RESOLVED_COST_COL, RESOLVED_INST_COL, RESOLVED_SHARE_COL,
    NON_NUMERIC_COST_VALS, PRIORITY_LAYERS,
    PRODUCT_ORDER_TEMPLATE,
    classify_tenor, resolve_tenor_col,
    load_and_filter, QCRunner,
)


# ── 数据加载 ──────────────────────────────────────────────────
def load_data(xlsx_path):
    """读取并预处理台账数据，返回 df, dfa"""
    df, dfa, tmp_path, tenor_col = load_and_filter(xlsx_path, need_tenor=True,
                                                    extra_required=['国股CD'])
    try:
        dfa['簿记时间'] = pd.to_datetime(dfa['簿记时间'], errors='coerce')
        dfa['月份'] = dfa['簿记时间'].dt.to_period('M')
        dfa['成本pct'] = dfa[RESOLVED_COST_COL] * 100
        dfa['国股CDpct'] = dfa['国股CD'] * 100
        dfa['基准利差'] = (dfa['成本pct'] - dfa['国股CDpct']).round(4)
        dfa['期限分类'] = dfa.apply(
            lambda r: classify_tenor(r[tenor_col], r['资产类型']), axis=1
        )
        dfa['产品类型'] = dfa['期限分类'] + dfa['资产类型']
        # Preserve columns for insight panel
        if '分层情况' not in dfa.columns:
            dfa['分层情况'] = '优先A'
        if '对应金额（亿）' not in dfa.columns:
            dfa['对应金额（亿）'] = None
        return df, dfa
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def build_product_list(dfa):
    """按固定模板排序产品类型列表"""
    available = dfa['产品类型'].unique().tolist()
    ordered = [pt for pt in PRODUCT_ORDER_TEMPLATE if pt in available]
    remaining = [pt for pt in available if pt not in PRODUCT_ORDER_TEMPLATE]
    return ordered + remaining


def build_js_data(dfa, products):
    """生成JS数据：每产品取最新有数据的月份"""
    rows = []
    for product in products:
        sub = dfa[dfa['产品类型'] == product].copy()
        if sub.empty:
            continue
        latest_month = str(sub['月份'].max())
        latest_sub = sub[sub['月份'] == sub['月份'].max()]
        for _, r in latest_sub.iterrows():
            rows.append({
                'product': product,
                'asset': r['资产类型'],
                'tenor': r['期限分类'],
                'project': str(r['项目名称']) if pd.notna(r.get('项目名称')) else '',
                'month': latest_month,
                'date': r['簿记时间'].strftime('%Y-%m-%d') if pd.notna(r['簿记时间']) else '',
                'cost': round(float(r['成本pct']), 4),
                'spread': round(float(r['基准利差']), 4),
                'inst': r['实际机构'],
                'share': round(float(r['实际份额']), 4),
                'layer': str(r['分层情况']) if pd.notna(r.get('分层情况')) else '优先A',
                'total_size': round(float(r['对应金额（亿）']), 4) if pd.notna(r.get('对应金额（亿）')) else None
            })
    return rows


# ── HTML 模板 ─────────────────────────────────────────────────
CSS = """  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "PingFang SC","Microsoft YaHei","Helvetica Neue",Arial,sans-serif;
    background: #f0f2f5; color: #1a1a2e; font-size: 13px;
  }
  .tool-banner {
    background: linear-gradient(135deg,#0d1b2e 0%,#1a3a5c 60%,#0d2a40 100%);
    color: #fff; padding: 20px 36px 18px;
  }
  .banner-tag { font-size: 10px; letter-spacing: 2px; color: #7db8e8; margin-bottom: 4px; }
  .banner-title { font-size: 18px; font-weight: 700; }
  .banner-sub { font-size: 11px; color: #a0bfd4; margin-top: 3px; }
  .container { max-width: 960px; margin: 0 auto; padding: 24px 20px 40px; }
  .ctrl-panel {
    background: #fff; border-radius: 8px; padding: 20px 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,.08); margin-bottom: 20px;
  }
  .ctrl-row { display: flex; align-items: flex-end; gap: 16px; flex-wrap: wrap; }
  .ctrl-group { display: flex; flex-direction: column; gap: 6px; }
  .ctrl-label { font-size: 11px; color: #6b7a95; letter-spacing: 1px; text-transform: uppercase; }
  select {
    height: 38px; border: 1px solid #d0d8e4; border-radius: 5px;
    padding: 0 12px; font-size: 13px; font-family: inherit;
    color: #1a1a2e; background: #fafbfc; outline: none; transition: border-color .2s;
    cursor: pointer; min-width: 170px;
  }
  select:focus { border-color: #2563a8; }
  select#tenorSelect { min-width: 130px; }
  .btn {
    height: 38px; padding: 0 24px; background: #c0392b; color: #fff;
    border: none; border-radius: 5px; font-size: 13px; font-weight: 600;
    font-family: inherit; cursor: pointer; letter-spacing: .5px; transition: background .2s;
  }
  .btn:hover { background: #a93226; }

  /* 成本微调：输入框 + 两侧按钮 */
  .cost-ctrl { display: flex; align-items: center; gap: 6px; }
  .cost-input {
    width: 72px; height: 38px; border: 1.5px solid #d0d8e4; border-radius: 5px;
    text-align: center; font-size: 14px; font-weight: 600; font-family: inherit;
    color: #1a1a2e; background: #fff; outline: none; cursor: text;
    transition: border-color .2s;
  }
  .cost-input:focus { border-color: #2563a8; }
  .cost-input::-webkit-inner-spin-button,
  .cost-input::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
  .cost-input[type=number] { -moz-appearance: textfield; }
  .cost-btn {
    width: 32px; height: 32px; border-radius: 50%;
    border: 1.5px solid #c0392b; background: #fff; color: #c0392b;
    font-size: 18px; font-weight: 600; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: background .15s, color .15s; flex-shrink: 0;
    line-height: 1;
  }
  .cost-btn:hover { background: #c0392b; color: #fff; }
  .cost-btn:active { background: #a93226; }
  .cost-val {
    min-width: 50px; text-align: center; font-size: 13px;
    font-weight: 600; color: #1a3a5c;
    padding: 5px 8px; background: #f0f4fa; border-radius: 5px;
    border: 1px solid #d0d8e4;
  }

  .result-area { display: none; }
  .result-area.show { display: block; }
  .hint-bar {
    padding: 10px 16px; background: #e8f0fc; border-radius: 8px 8px 0 0;
    font-size: 12px; color: #2a4a7c; display: flex;
    justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;
  }
  .hint-bar strong { color: #1a3a5c; font-size: 14px; }
  .res-table-wrap {
    background: #fff; border-radius: 0 0 8px 8px;
    overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.07);
  }
  .res-table { width: 100%; border-collapse: collapse; }
  .res-table thead th {
    background: #0d1b2e; color: #fff; padding: 9px 16px;
    font-size: 11px; font-weight: 600; letter-spacing: .5px; text-align: left;
  }
  .res-table thead th:last-child { text-align: right; }
  .res-table tbody td:last-child { text-align: right; font-variant-numeric: tabular-nums; }
  .res-table tbody tr:nth-child(even) { background: #f7f9fc; }
  .res-table tbody tr:hover { background: #eef3fa; }
  .res-table tbody td {
    padding: 9px 16px; font-size: 12px; border-bottom: 1px solid #eaeef4;
  }
  .inst-cell { font-weight: 500; color: #1a2a40; }
  .cost-cell { color: #2d7a4f; font-weight: 600; }
  .spread-cell { font-weight: 600; color: #1a3a5c; }
  .date-cell { color: #6b7a95; font-size: 11px; }
  .rank-num { font-size: 12px; }
  .summary-row td { background: #f0f4fa !important; border-top: 2px solid #d0d8e4; }
  .tenor-badge {
    display: inline-block; font-size: 10px; font-weight: 600;
    padding: 2px 8px; border-radius: 3px; margin-left: 8px;
    background: #dde8f4; color: #2a4a7a; border: 1px solid #aac4e0;
  }
  .empty-state {
    background: #fff; border-radius: 8px; padding: 40px;
    text-align: center; color: #8a9ab5; font-size: 13px;
    box-shadow: 0 1px 4px rgba(0,0,0,.07);
  }
  .footer-note { margin-top: 14px; font-size: 11px; color: #9aa5b5; text-align: center; }
  @keyframes fadeIn { from { opacity:0; transform:translateY(8px) } to { opacity:1; transform:translateY(0) } }
  .result-area.show { animation: fadeIn .3s ease; }"""


# ── 数据计算层（供综合看板调用）──────────────────────────────
def compute_data(xlsx_path):
    """读取台账 + 计算 products/rows + QC precheck"""
    df, dfa = load_data(xlsx_path)
    products = build_product_list(dfa)
    rows = build_js_data(dfa, products)
    data_js = json.dumps(rows, ensure_ascii=False, indent=2)
    products_js = json.dumps(products, ensure_ascii=False)

    qc_passed = run_qc(df, dfa, products, rows, output_path=None, precheck_only=True)
    if not qc_passed:
        raise RuntimeError(f'[QC] 机构比对工具预检未通过')

    # Build PROJECT_SIZES mapping for insight panel
    proj_sizes = {}
    for _, r in dfa.iterrows():
        proj = str(r['项目名称']) if pd.notna(r.get('项目名称')) else ''
        amt = r.get('对应金额（亿）')
        if proj and pd.notna(amt):
            try:
                proj_sizes[proj] = float(amt)
            except:
                pass
    proj_sizes_js = json.dumps(proj_sizes, ensure_ascii=False)

    return {
        'df': df,
        'dfa': dfa,
        'products': products,
        'rows': rows,
        'products_js': products_js,
        'data_js': data_js,
        'proj_sizes_js': proj_sizes_js,
        'xlsx_basename': os.path.basename(xlsx_path),
        'xlsx_path': xlsx_path,
    }


def render_body(data):
    """渲染 body 片段（含 <script>，不含 <!DOCTYPE>/<html>/<head>）"""
    products_js = data['products_js']
    data_js = data['data_js']
    xlsx_basename = data['xlsx_basename']

    body_template = """
<div class="tool-banner">
  <div class="banner-tag">ABS Investor Intelligence Tool · Priority A</div>
  <div class="banner-title">发行定价测试工具</div>
  <div class="banner-sub">优先A · 产品类型（资产类型+期限） · 不高于目标成本的认购机构排名</div>
</div>

<div class="container">
  <div class="ctrl-panel">
    <div class="ctrl-row">
      <div class="ctrl-group">
        <div class="ctrl-label">期限筛选</div>
        <select id="tenorSelect" onchange="onTenorChange()">
          <option value="">全部</option>
          <option value="1年期">1年期</option>
          <option value="超1年期">超1年期</option>
        </select>
      </div>
      <div class="ctrl-group">
        <div class="ctrl-label">产品类型</div>
        <select id="productSelect">
          <option value="">— 选择产品类型 —</option>
        </select>
      </div>
      <div class="ctrl-group">
        <div class="ctrl-label">目标成本上限（%）</div>
        <div class="cost-ctrl">
          <button class="cost-btn" onclick="adjCost(-0.01)" title="减0.01%">&#8722;</button>
          <input type="number" id="costInput" class="cost-input"
                 min="1.50" max="2.50" step="0.01" value="1.80"
                 placeholder="1.50~2.20" onclick="this.select()">
          <button class="cost-btn" onclick="adjCost(0.01)" title="加0.01%">+</button>
        </div>
      </div>
      <div class="ctrl-group">
        <div class="ctrl-label">&nbsp;</div>
        <button class="btn" onclick="doSearch()">查询</button>
      </div>
    </div>
  </div>

  <div class="result-area" id="resultArea">
    <div class="hint-bar">
      <span id="hintText"></span>
      <span id="metaTag" style="font-size:11px;color:#5a7aa8"></span>
    </div>
    <div class="res-table-wrap">
      <table class="res-table">
        <thead>
          <tr>
            <th style="width:36px;text-align:center">#</th>
            <th>认购机构</th>
            <th>簿记日期</th>
            <th>实际成本</th>
            <th>基准利差</th>
            <th>认购份额（亿元）</th>
          </tr>
        </thead>
        <tbody id="resultBody"></tbody>
      </table>
    </div>
  </div>

  <div class="empty-state" id="emptyState">
    选择产品类型，输入目标成本上限，点击查询
  </div>

  <div class="footer-note">
    仅统计分层情况为"优先A"的条目 ·
    产品类型 = 资产类型 + 期限分类（单一期限） ·
    基准利差 = 成本 &#8722; 国股CD ·
    数据来源：{xlsx_basename} · 分析报告员 Peizhi Wu
  </div>
</div>

<script>
const ALL_PRODUCTS = {products_js};
const ALL_DATA = {data_js};

// 初始化：填充全部产品
function populateProducts(products) {{
  const sel = document.getElementById('productSelect');
  sel.innerHTML = '<option value="">— 选择产品类型 —</option>';
  products.forEach(p => {{
    const o = document.createElement('option');
    o.value = p;
    o.textContent = p;
    sel.appendChild(o);
  }});
}}

// 期限切换：根据选中期限过滤产品下拉列表
function onTenorChange() {{
  const tenor = document.getElementById('tenorSelect').value;
  if (tenor === '') {{
    populateProducts(ALL_PRODUCTS);
  }} else {{
    const filtered = ALL_PRODUCTS.filter(p => p.startsWith(tenor));
    populateProducts(filtered);
  }}
  document.getElementById('productSelect').value = '';
}}

// 成本微调
function adjCost(delta) {{
  const inp = document.getElementById('costInput');
  let v = parseFloat(inp.value);
  if (isNaN(v)) {{ v = 1.80; }}
  v = Math.round((v + delta) * 100) / 100;
  v = Math.max(1.50, Math.min(2.50, v));
  inp.value = v.toFixed(2);
  inp.select();
}}

// 查询
function doSearch() {{
  const product = document.getElementById('productSelect').value;
  const costLimit = parseFloat(document.getElementById('costInput').value);
  const resultArea = document.getElementById('resultArea');
  const emptyState = document.getElementById('emptyState');
  const tbody = document.getElementById('resultBody');

  if (!product || isNaN(costLimit)) {{
    alert('请选择产品类型并输入目标成本');
    return;
  }}

  const filtered = ALL_DATA
    .filter(r => r.product === product && r.cost <= costLimit)
    .sort(function(a, b) {{ return a.cost - b.cost || b.share - a.share; }});

  const mergedMap = {{}};
  filtered.forEach(r => {{
    const key = r.inst + '|' + r.date + '|' + r.cost + '|' + r.spread;
    if (!mergedMap[key]) {{
      mergedMap[key] = Object.assign({{}}, r);
    }} else {{
      mergedMap[key].share = parseFloat((mergedMap[key].share + r.share).toFixed(4));
    }}
  }});
  const merged = Object.values(mergedMap).sort(function(a, b) {{ return a.cost - b.cost || b.share - a.share; }});

  const latestMonth = [...new Set(merged.map(r => r.month))].sort().reverse()[0] || '—';
  const tenorLabel = merged.length > 0 ? merged[0].tenor : '—';
  document.getElementById('hintText').innerHTML =
    '<strong>' + product + '</strong> · 不高于 <strong>' + costLimit.toFixed(2) + '%</strong> 的机构' +
    ' <span class="tenor-badge">' + tenorLabel + '</span>';
  document.getElementById('metaTag').textContent =
    '最新月份：' + latestMonth + ' · ' + merged.length + ' 家机构';

  if (merged.length === 0) {{
    resultArea.classList.remove('show');
    emptyState.style.display = 'block';
    emptyState.textContent = '该产品在最新月份暂无成本不高于 ' + costLimit.toFixed(2) + '% 的记录';
    return;
  }}

  const total = merged.reduce(function(s, r) {{ return s + r.share; }}, 0).toFixed(2);
  const rows = merged.map(function(r, i) {{
    return '<tr>' +
      '<td style="text-align:center" class="rank-num">' + (i+1) + '</td>' +
      '<td class="inst-cell">' + r.inst + '</td>' +
      '<td class="date-cell">' + r.date + '</td>' +
      '<td class="cost-cell">' + r.cost.toFixed(2) + '%</td>' +
      '<td class="spread-cell">+' + r.spread.toFixed(2) + '%</td>' +
      '<td>' + r.share.toFixed(2) + '</td>' +
    '</tr>';
  }}).join('');

  tbody.innerHTML = rows +
    '<tr class="summary-row">' +
      '<td colspan="5" style="text-align:right;font-size:11px;color:#6b7a95;padding-right:16px">' +
        merged.length + ' 家机构 合计' +
      '</td>' +
      '<td>' + total + '</td>' +
    '</tr>';

  resultArea.classList.add('show');
  emptyState.style.display = 'none';
}}

populateProducts(ALL_PRODUCTS);
</script>"""
    return body_template.format(products_js=products_js, data_js=data_js, xlsx_basename=xlsx_basename)


def render_html(data):
    """渲染完整 HTML 文档（含 <!DOCTYPE>/<html>/<head>）"""
    body = render_body(data)
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ABS机构成本比对工具</title>
<style>
{CSS}
</style>
</head>
<body>
{body}
</body>
</html>'''


def build_html(products_js, data_js, xlsx_basename):
    """已废弃，用 render_html 替代（保留向后兼容）"""
    data = {
        'products_js': products_js,
        'data_js': data_js,
        'xlsx_basename': xlsx_basename,
    }
    return render_html(data)


# ═══════════════════════════════════════════════════════════════
# §6.1  定价测试 panel（全局注释右对齐）
# ═══════════════════════════════════════════════════════════════

import re as _re

PRICING_CSS = """
  /* ── 定价测试 panel：全局注释右对齐 ── */
  .lab-global-note {
    max-width: 960px; margin: 14px auto 0; padding: 0 20px;
    font-size: 11px; color: #9aa5b5; text-align: right;
  }
"""


def render_body_pricing(data):
    """渲染定价测试 panel 的 body（成本筛选查询工具 + 全局注释右对齐）

    与 render_body 的差异：footer-note 从 container 内移到外面，右对齐
    """
    original_body = render_body(data)

    footer_note_match = _re.search(
        r'<div class="footer-note">.*?</div>',
        original_body,
        flags=_re.DOTALL
    )
    if not footer_note_match:
        return original_body

    footer_note_html = footer_note_match.group(0)
    body_no_footer = original_body.replace(footer_note_html, '', 1)

    inner_match = _re.search(r'<div class="footer-note">(.*?)</div>', footer_note_html, flags=_re.DOTALL)
    inner_text = inner_match.group(1).strip() if inner_match else ''

    global_note = f'\n<div class="lab-global-note">{inner_text}</div>'
    body = body_no_footer.replace(
        '\n\n<script>',
        f'{global_note}\n\n<script>',
        1
    )
    return body


# ═══════════════════════════════════════════════════════════════
# §6.2  投资明细 panel（机构认购明细查询）
# ═══════════════════════════════════════════════════════════════

INVEST_CSS = """
  /* ── 投资明细 panel：独立查询模块 ── */
  .invest-container {
    max-width: 1200px; margin: 0 auto; padding: 24px 20px 40px;
  }
  .invest-ctrl-panel {
    background: #fff; border-radius: 8px; padding: 20px 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,.08); margin-bottom: 20px;
  }
  .invest-ctrl-row {
    display: flex; align-items: flex-end; gap: 16px; flex-wrap: wrap;
  }
  .invest-ctrl-group { display: flex; flex-direction: column; gap: 6px; flex: 1 1 240px; }
  .invest-ctrl-label {
    font-size: 11px; color: #6b7a95; letter-spacing: 1px; text-transform: uppercase;
  }
  .invest-select {
    height: 38px; border: 1px solid #d0d8e4; border-radius: 5px;
    padding: 0 12px; font-size: 13px; font-family: inherit;
    color: #1a1a2e; background: #fafbfc; outline: none; transition: border-color .2s;
    cursor: pointer; width: 100%; box-sizing: border-box;
  }
  .invest-select:focus { border-color: #2563a8; }

  /* ── 投资明细：机构搜索下拉（自定义组件，白底黑字）── */
  .invest-search-wrap { position: relative; width: 100%; }
  .invest-search-input {
    height: 38px; border: 1px solid #d0d8e4; border-radius: 5px;
    padding: 0 12px; font-size: 13px; font-family: inherit;
    color: #1a1a2e; background: #fff; outline: none; transition: border-color .2s;
    width: 100%; box-sizing: border-box;
  }
  .invest-search-input:focus { border-color: #2563a8; }
  .invest-search-dropdown {
    display: none; position: absolute; top: 100%; left: 0; right: 0;
    max-height: 280px; overflow-y: auto;
    background: #fff; border: 1px solid #d0d8e4; border-top: none;
    border-radius: 0 0 5px 5px; z-index: 200;
    box-shadow: 0 4px 12px rgba(0,0,0,.12);
  }
  .invest-search-dropdown.show { display: block; }
  .invest-search-item {
    padding: 8px 12px; font-size: 13px; color: #1a1a2e; cursor: pointer;
    background: #fff; border-bottom: 1px solid #f0f4fa;
  }
  .invest-search-item:last-child { border-bottom: none; }
  .invest-search-item:hover, .invest-search-item.active {
    background: #eef3fa; color: #0d1b2e;
  }
  .invest-search-empty {
    padding: 12px; font-size: 12px; color: #9aa5b5; text-align: center;
  }

  /* ── 投资明细：结果区 ── */
  .invest-result-area { display: none; }
  .invest-result-area.show { display: block; animation: fadeIn .3s ease; }
  .invest-hint-bar {
    padding: 10px 16px; background: #e8f0fc; border-radius: 8px 8px 0 0;
    font-size: 14px; color: #2a4a7c; display: flex;
    justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;
  }
  .invest-hint-bar strong { color: #1a3a5c; font-size: 14px; font-weight: 700; }
  .invest-hint-bar .invest-meta { font-size: 14px; color: #1a3a5c; font-weight: 700; }
  .invest-table-wrap {
    background: #fff; border-radius: 0 0 8px 8px;
    overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.07);
  }
  .invest-table {
    width: 100%; border-collapse: collapse; table-layout: fixed;
  }
  .invest-table thead th {
    background: #0d1b2e; color: #fff; padding: 12px 8px;
    font-size: 13px; font-weight: 600; letter-spacing: .5px; text-align: center;
  }
  .invest-table tbody td {
    padding: 10px 8px; font-size: 13px; border-bottom: 1px solid #eaeef4;
    text-align: center; word-break: break-all;
  }
  .invest-table tbody tr:nth-child(even) { background: #f7f9fc; }
  .invest-table tbody tr:hover { background: #eef3fa; }
  .invest-table .inst-cell { font-weight: 500; color: #1a2a40; }
  .invest-table .cost-cell { color: #2d7a4f; font-weight: 600; }
  .invest-table .spread-cell { font-weight: 600; color: #1a3a5c; }
  .invest-table .date-cell { color: #6b7a95; }
  .invest-table .summary-row td { background: #f0f4fa !important; border-top: 2px solid #d0d8e4; }
  .invest-empty-state {
    background: #fff; border-radius: 8px; padding: 40px;
    text-align: center; color: #8a9ab5; font-size: 13px;
    box-shadow: 0 1px 4px rgba(0,0,0,.07);
  }
"""


INVEST_JS_TEMPLATE = """
// === 投资明细：机构认购明细查询 ===
const INVEST_ALL_DATA = {data_js};
const INVEST_ALL_PRODUCTS = {products_js};

// === 机构搜索下拉（自定义组件，白底黑字，随输入过滤）===
let INVEST_ALL_INSTS = [];
let INVEST_ACTIVE_IDX = -1;

function investInitInstSearch() {{
  const insts = [...new Set(INVEST_ALL_DATA.map(r => r.inst))].filter(Boolean).sort();
  INVEST_ALL_INSTS = insts;

  const input = document.getElementById('investInstSelect');
  const dropdown = document.getElementById('investInstDropdown');
  if (!input || !dropdown) return;

  input.addEventListener('focus', function() {{
    investRenderDropdown('');
    dropdown.classList.add('show');
  }});

  input.addEventListener('input', function() {{
    investRenderDropdown(this.value);
    dropdown.classList.add('show');
    INVEST_ACTIVE_IDX = -1;
  }});

  input.addEventListener('keydown', function(e) {{
    const items = dropdown.querySelectorAll('.invest-search-item');
    if (e.key === 'ArrowDown') {{
      e.preventDefault();
      INVEST_ACTIVE_IDX = Math.min(INVEST_ACTIVE_IDX + 1, items.length - 1);
      investUpdateActive(items);
    }} else if (e.key === 'ArrowUp') {{
      e.preventDefault();
      INVEST_ACTIVE_IDX = Math.max(INVEST_ACTIVE_IDX - 1, 0);
      investUpdateActive(items);
    }} else if (e.key === 'Enter') {{
      e.preventDefault();
      if (INVEST_ACTIVE_IDX >= 0 && items[INVEST_ACTIVE_IDX]) {{
        items[INVEST_ACTIVE_IDX].click();
      }}
    }} else if (e.key === 'Escape') {{
      dropdown.classList.remove('show');
    }}
  }});

  document.addEventListener('click', function(e) {{
    if (!e.target.closest('.invest-search-wrap')) {{
      dropdown.classList.remove('show');
    }}
  }});
}}

function investRenderDropdown(query) {{
  const dropdown = document.getElementById('investInstDropdown');
  if (!dropdown) return;
  const q = (query || '').trim().toLowerCase();
  let filtered = INVEST_ALL_INSTS;
  if (q) {{
    filtered = INVEST_ALL_INSTS.filter(i => i.toLowerCase().includes(q));
  }}
  if (filtered.length === 0) {{
    dropdown.innerHTML = '<div class="invest-search-empty">未找到匹配机构</div>';
    return;
  }}
  dropdown.innerHTML = filtered.map((i, idx) => {{
    return '<div class="invest-search-item" data-value="' + i + '" data-idx="' + idx + '">' + i + '</div>';
  }}).join('');
  dropdown.querySelectorAll('.invest-search-item').forEach(item => {{
    item.addEventListener('click', function() {{
      const input = document.getElementById('investInstSelect');
      input.value = this.dataset.value;
      dropdown.classList.remove('show');
      investDoSearch();
    }});
  }});
}}

function investUpdateActive(items) {{
  items.forEach((item, idx) => {{
    item.classList.toggle('active', idx === INVEST_ACTIVE_IDX);
    if (idx === INVEST_ACTIVE_IDX) {{
      item.scrollIntoView({{ block: 'nearest' }});
    }}
  }});
}}

function investPopulateProducts() {{
  const sel = document.getElementById('investProductSelect');
  if (!sel) return;
  sel.innerHTML = '<option value="">— 选择产品类型 —</option>';
  INVEST_ALL_PRODUCTS.forEach(p => {{
    const o = document.createElement('option');
    o.value = p; o.textContent = p;
    sel.appendChild(o);
  }});
}}

function investDoSearch() {{
  const inst = document.getElementById('investInstSelect').value;
  const product = document.getElementById('investProductSelect').value;
  const resultArea = document.getElementById('investResultArea');
  const emptyState = document.getElementById('investEmptyState');
  const tbody = document.getElementById('investResultBody');
  const hintText = document.getElementById('investHintText');
  const metaTag = document.getElementById('investMetaTag');

  if (!inst || !product) {{
    resultArea.classList.remove('show');
    emptyState.style.display = 'block';
    emptyState.textContent = '请选择认购机构和产品类型';
    return;
  }}

  const filtered = INVEST_ALL_DATA.filter(r => r.inst === inst && r.product === product);

  if (filtered.length === 0) {{
    resultArea.classList.remove('show');
    emptyState.style.display = 'block';
    emptyState.textContent = inst + ' 在 ' + product + ' 暂无认购记录';
    return;
  }}

  filtered.sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));

  const total = filtered.reduce((s, r) => s + r.share, 0).toFixed(2);
  hintText.innerHTML = '<strong>' + inst + '</strong> · <strong>' + product + '</strong>';
  metaTag.textContent = filtered.length + ' 笔 · 合计 ' + total + ' 亿';

  const rows = filtered.map(r => {{
    return '<tr>' +
      '<td class="date-cell">' + r.date + '</td>' +
      '<td class="inst-cell">' + r.product + '</td>' +
      '<td>' + (r.project || '—') + '</td>' +
      '<td class="cost-cell">' + r.cost.toFixed(2) + '%</td>' +
      '<td class="spread-cell">+' + r.spread.toFixed(2) + '%</td>' +
      '<td>' + r.share.toFixed(2) + '</td>' +
    '</tr>';
  }}).join('');

  tbody.innerHTML = rows +
    '<tr class="summary-row">' +
      '<td colspan="5" style="text-align:right;font-size:12px;color:#6b7a95;padding-right:16px">' +
        filtered.length + ' 笔 合计' +
      '</td>' +
      '<td>' + total + '</td>' +
    '</tr>';

  resultArea.classList.add('show');
  emptyState.style.display = 'none';
}}

investInitInstSearch();
investPopulateProducts();
"""


def render_body_invest(data):
    """渲染投资明细 panel 的 body（独立的机构认购明细查询模块）"""
    js = INVEST_JS_TEMPLATE.format(
        data_js=data['data_js'],
        products_js=data['products_js'],
    )
    xlsx_basename = data['xlsx_basename']
    return f'''
<div class="tool-banner">
  <div class="banner-tag">ABS Investment Detail Query · Priority A</div>
  <div class="banner-title">机构投资明细查询</div>
  <div class="banner-sub">机构认购利率为投标利率，基准利差 = 认购成本 − 同日国股CD</div>
</div>

<div class="invest-container">
  <div class="invest-ctrl-panel">
    <div class="invest-ctrl-row">
      <div class="invest-ctrl-group">
        <div class="invest-ctrl-label">认购机构</div>
        <div class="invest-search-wrap">
          <input type="text" id="investInstSelect" class="invest-search-input"
                 placeholder="输入关键词搜索机构" autocomplete="off">
          <div class="invest-search-dropdown" id="investInstDropdown"></div>
        </div>
      </div>
      <div class="invest-ctrl-group">
        <div class="invest-ctrl-label">产品类型</div>
        <select id="investProductSelect" class="invest-select" onchange="investDoSearch()">
          <option value="">— 选择产品类型 —</option>
        </select>
      </div>
    </div>
  </div>

  <div class="invest-result-area" id="investResultArea">
    <div class="invest-hint-bar">
      <span id="investHintText"></span>
      <span class="invest-meta" id="investMetaTag"></span>
    </div>
    <div class="invest-table-wrap">
      <table class="invest-table">
        <thead>
          <tr>
            <th>簿记日期</th>
            <th>产品类型</th>
            <th>项目名称</th>
            <th>认购利率</th>
            <th>基准利差</th>
            <th>认购规模（亿元）</th>
          </tr>
        </thead>
        <tbody id="investResultBody"></tbody>
      </table>
    </div>
  </div>

  <div class="invest-empty-state" id="investEmptyState">
    请选择认购机构和产品类型
  </div>

  <div class="footer-note">
    仅统计分层情况为"优先A"的条目 ·
    产品类型 = 资产类型 + 期限分类（单一期限） ·
    基准利差 = 成本 − 国股CD ·
    数据来源：{xlsx_basename} · 分析报告员 Peizhi Wu
  </div>
</div>

<script>
{js}
</script>'''


def _build_html_legacy(products_js, data_js, xlsx_basename):
    """构建完整HTML字符串"""
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ABS机构成本比对工具</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "PingFang SC","Microsoft YaHei","Helvetica Neue",Arial,sans-serif;
    background: #f0f2f5; color: #1a1a2e; font-size: 13px;
  }
  .tool-banner {
    background: linear-gradient(135deg,#0d1b2e 0%,#1a3a5c 60%,#0d2a40 100%);
    color: #fff; padding: 20px 36px 18px;
  }
  .banner-tag { font-size: 10px; letter-spacing: 2px; color: #7db8e8; margin-bottom: 4px; }
  .banner-title { font-size: 18px; font-weight: 700; }
  .banner-sub { font-size: 11px; color: #a0bfd4; margin-top: 3px; }
  .container { max-width: 960px; margin: 0 auto; padding: 24px 20px 40px; }
  .ctrl-panel {
    background: #fff; border-radius: 8px; padding: 20px 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,.08); margin-bottom: 20px;
  }
  .ctrl-row { display: flex; align-items: flex-end; gap: 16px; flex-wrap: wrap; }
  .ctrl-group { display: flex; flex-direction: column; gap: 6px; }
  .ctrl-label { font-size: 11px; color: #6b7a95; letter-spacing: 1px; text-transform: uppercase; }
  select {
    height: 38px; border: 1px solid #d0d8e4; border-radius: 5px;
    padding: 0 12px; font-size: 13px; font-family: inherit;
    color: #1a1a2e; background: #fafbfc; outline: none; transition: border-color .2s;
    cursor: pointer; min-width: 170px;
  }
  select:focus { border-color: #2563a8; }
  select#tenorSelect { min-width: 130px; }
  .btn {
    height: 38px; padding: 0 24px; background: #c0392b; color: #fff;
    border: none; border-radius: 5px; font-size: 13px; font-weight: 600;
    font-family: inherit; cursor: pointer; letter-spacing: .5px; transition: background .2s;
  }
  .btn:hover { background: #a93226; }

  /* 成本微调：输入框 + 两侧按钮 */
  .cost-ctrl { display: flex; align-items: center; gap: 6px; }
  .cost-input {
    width: 72px; height: 38px; border: 1.5px solid #d0d8e4; border-radius: 5px;
    text-align: center; font-size: 14px; font-weight: 600; font-family: inherit;
    color: #1a1a2e; background: #fff; outline: none; cursor: text;
    transition: border-color .2s;
  }
  .cost-input:focus { border-color: #2563a8; }
  .cost-input::-webkit-inner-spin-button,
  .cost-input::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
  .cost-input[type=number] { -moz-appearance: textfield; }
  .cost-btn {
    width: 32px; height: 32px; border-radius: 50%;
    border: 1.5px solid #c0392b; background: #fff; color: #c0392b;
    font-size: 18px; font-weight: 600; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: background .15s, color .15s; flex-shrink: 0;
    line-height: 1;
  }
  .cost-btn:hover { background: #c0392b; color: #fff; }
  .cost-btn:active { background: #a93226; }
  .cost-val {
    min-width: 50px; text-align: center; font-size: 13px;
    font-weight: 600; color: #1a3a5c;
    padding: 5px 8px; background: #f0f4fa; border-radius: 5px;
    border: 1px solid #d0d8e4;
  }

  .result-area { display: none; }
  .result-area.show { display: block; }
  .hint-bar {
    padding: 10px 16px; background: #e8f0fc; border-radius: 8px 8px 0 0;
    font-size: 12px; color: #2a4a7c; display: flex;
    justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;
  }
  .hint-bar strong { color: #1a3a5c; font-size: 14px; }
  .res-table-wrap {
    background: #fff; border-radius: 0 0 8px 8px;
    overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.07);
  }
  .res-table { width: 100%; border-collapse: collapse; }
  .res-table thead th {
    background: #0d1b2e; color: #fff; padding: 9px 16px;
    font-size: 11px; font-weight: 600; letter-spacing: .5px; text-align: left;
  }
  .res-table thead th:last-child { text-align: right; }
  .res-table tbody td:last-child { text-align: right; font-variant-numeric: tabular-nums; }
  .res-table tbody tr:nth-child(even) { background: #f7f9fc; }
  .res-table tbody tr:hover { background: #eef3fa; }
  .res-table tbody td {
    padding: 9px 16px; font-size: 12px; border-bottom: 1px solid #eaeef4;
  }
  .inst-cell { font-weight: 500; color: #1a2a40; }
  .cost-cell { color: #2d7a4f; font-weight: 600; }
  .spread-cell { font-weight: 600; color: #1a3a5c; }
  .date-cell { color: #6b7a95; font-size: 11px; }
  .rank-num { font-size: 12px; }
  .summary-row td { background: #f0f4fa !important; border-top: 2px solid #d0d8e4; }
  .tenor-badge {
    display: inline-block; font-size: 10px; font-weight: 600;
    padding: 2px 8px; border-radius: 3px; margin-left: 8px;
    background: #dde8f4; color: #2a4a7a; border: 1px solid #aac4e0;
  }
  .empty-state {
    background: #fff; border-radius: 8px; padding: 40px;
    text-align: center; color: #8a9ab5; font-size: 13px;
    box-shadow: 0 1px 4px rgba(0,0,0,.07);
  }
  .footer-note { margin-top: 14px; font-size: 11px; color: #9aa5b5; text-align: center; }
  @keyframes fadeIn { from { opacity:0; transform:translateY(8px) } to { opacity:1; transform:translateY(0) } }
  .result-area.show { animation: fadeIn .3s ease; }
</style>
</head>
<body>

<div class="tool-banner">
  <div class="banner-tag">ABS Investor Intelligence Tool · Priority A</div>
  <div class="banner-title">发行定价测试工具</div>
  <div class="banner-sub">优先A · 产品类型（资产类型+期限） · 不高于目标成本的认购机构排名</div>
</div>

<div class="container">
  <div class="ctrl-panel">
    <div class="ctrl-row">
      <div class="ctrl-group">
        <div class="ctrl-label">期限筛选</div>
        <select id="tenorSelect" onchange="onTenorChange()">
          <option value="">全部</option>
          <option value="1年期">1年期</option>
          <option value="超1年期">超1年期</option>
        </select>
      </div>
      <div class="ctrl-group">
        <div class="ctrl-label">产品类型</div>
        <select id="productSelect">
          <option value="">— 选择产品类型 —</option>
        </select>
      </div>
      <div class="ctrl-group">
        <div class="ctrl-label">目标成本上限（%）</div>
        <div class="cost-ctrl">
          <button class="cost-btn" onclick="adjCost(-0.01)" title="减0.01%">&#8722;</button>
          <input type="number" id="costInput" class="cost-input"
                 min="1.50" max="2.50" step="0.01" value="1.80"
                 placeholder="1.50~2.20" onclick="this.select()">
          <button class="cost-btn" onclick="adjCost(0.01)" title="加0.01%">+</button>
        </div>
      </div>
      <div class="ctrl-group">
        <div class="ctrl-label">&nbsp;</div>
        <button class="btn" onclick="doSearch()">查询</button>
      </div>
    </div>
  </div>

  <div class="result-area" id="resultArea">
    <div class="hint-bar">
      <span id="hintText"></span>
      <span id="metaTag" style="font-size:11px;color:#5a7aa8"></span>
    </div>
    <div class="res-table-wrap">
      <table class="res-table">
        <thead>
          <tr>
            <th style="width:36px;text-align:center">#</th>
            <th>认购机构</th>
            <th>簿记日期</th>
            <th>实际成本</th>
            <th>基准利差</th>
            <th>认购份额（亿元）</th>
          </tr>
        </thead>
        <tbody id="resultBody"></tbody>
      </table>
    </div>
  </div>

  <div class="empty-state" id="emptyState">
    选择产品类型，输入目标成本上限，点击查询
  </div>

  <div class="footer-note">
    仅统计分层情况为"优先A"的条目 ·
    产品类型 = 资产类型 + 期限分类（单一期限） ·
    基准利差 = 成本 &#8722; 国股CD ·
    数据来源：{xlsx_basename} · 分析报告员 Peizhi Wu
  </div>
</div>

<script>
const ALL_PRODUCTS = {products_js};
const ALL_DATA = {data_js};

// 初始化：填充全部产品
function populateProducts(products) {
  const sel = document.getElementById('productSelect');
  sel.innerHTML = '<option value="">— 选择产品类型 —</option>';
  products.forEach(p => {
    const o = document.createElement('option');
    o.value = p;
    o.textContent = p;
    sel.appendChild(o);
  });
}

// 期限切换：根据选中期限过滤产品下拉列表
function onTenorChange() {
  const tenor = document.getElementById('tenorSelect').value;
  if (tenor === '') {
    populateProducts(ALL_PRODUCTS);
  } else {
    const filtered = ALL_PRODUCTS.filter(p => p.startsWith(tenor));
    populateProducts(filtered);
  }
  document.getElementById('productSelect').value = '';
}

// 成本微调
function adjCost(delta) {
  const inp = document.getElementById('costInput');
  let v = parseFloat(inp.value);
  if (isNaN(v)) { v = 1.80; }
  v = Math.round((v + delta) * 100) / 100;
  v = Math.max(1.50, Math.min(2.50, v));
  inp.value = v.toFixed(2);
  inp.select();
}

// 查询
function doSearch() {
  const product = document.getElementById('productSelect').value;
  const costLimit = parseFloat(document.getElementById('costInput').value);
  const resultArea = document.getElementById('resultArea');
  const emptyState = document.getElementById('emptyState');
  const tbody = document.getElementById('resultBody');

  if (!product || isNaN(costLimit)) {
    alert('请选择产品类型并输入目标成本');
    return;
  }

  const filtered = ALL_DATA
    .filter(r => r.product === product && r.cost <= costLimit)
    .sort(function(a, b) { return a.cost - b.cost || b.share - a.share; });

  const mergedMap = {};
  filtered.forEach(r => {
    const key = r.inst + '|' + r.date + '|' + r.cost + '|' + r.spread;
    if (!mergedMap[key]) {
      mergedMap[key] = Object.assign({}, r);
    } else {
      mergedMap[key].share = parseFloat((mergedMap[key].share + r.share).toFixed(4));
    }
  });
  const merged = Object.values(mergedMap).sort(function(a, b) { return a.cost - b.cost || b.share - a.share; });

  const latestMonth = [...new Set(merged.map(r => r.month))].sort().reverse()[0] || '—';
  const tenorLabel = merged.length > 0 ? merged[0].tenor : '—';
  document.getElementById('hintText').innerHTML =
    '<strong>' + product + '</strong> · 不高于 <strong>' + costLimit.toFixed(2) + '%</strong> 的机构' +
    ' <span class="tenor-badge">' + tenorLabel + '</span>';
  document.getElementById('metaTag').textContent =
    '最新月份：' + latestMonth + ' · ' + merged.length + ' 家机构';

  if (merged.length === 0) {
    resultArea.classList.remove('show');
    emptyState.style.display = 'block';
    emptyState.textContent = '该产品在最新月份暂无成本不高于 ' + costLimit.toFixed(2) + '% 的记录';
    return;
  }

  const total = merged.reduce(function(s, r) { return s + r.share; }, 0).toFixed(2);
  const rows = merged.map(function(r, i) {
    return '<tr>' +
      '<td style="text-align:center" class="rank-num">' + (i+1) + '</td>' +
      '<td class="inst-cell">' + r.inst + '</td>' +
      '<td class="date-cell">' + r.date + '</td>' +
      '<td class="cost-cell">' + r.cost.toFixed(2) + '%</td>' +
      '<td class="spread-cell">+' + r.spread.toFixed(2) + '%</td>' +
      '<td>' + r.share.toFixed(2) + '</td>' +
    '</tr>';
  }).join('');

  tbody.innerHTML = rows +
    '<tr class="summary-row">' +
      '<td colspan="5" style="text-align:right;font-size:11px;color:#6b7a95;padding-right:16px">' +
        merged.length + ' 家机构 合计' +
      '</td>' +
      '<td>' + total + '</td>' +
    '</tr>';

  resultArea.classList.add('show');
  emptyState.style.display = 'none';
}

populateProducts(ALL_PRODUCTS);
</script>
</body>
</html>"""

    # 安全注入数据：用命名占位符替换
    html = html.replace('{products_js}', products_js)
    html = html.replace('{data_js}', data_js)
    html = html.replace('{xlsx_basename}', xlsx_basename)
    return html


# ── QC ────────────────────────────────────────────────────────
def run_qc(df, dfa, products, rows, output_path, precheck_only=False):
    qc = QCRunner('ABS机构成本比对工具（含期限维度+成本微调）')
    qc.header()
    df_raw = df.copy()
    ok, warn, fail = qc.ok, qc.warn, qc.fail

    print('\n【1】数据完整性')
    ok(f'机构数：{dfa[RESOLVED_INST_COL].nunique()}家 | 产品类型：{len(products)}种')

    raw_cnt = len(df_raw[df_raw['分层情况'].isin(PRIORITY_LAYERS)])
    if raw_cnt == len(dfa):
        ok(f'优先A记录数一致：{len(dfa)}条')
    else:
        fail(f'优先A记录数不一致：原始={raw_cnt}，处理={len(dfa)}')

    raw_total = df_raw[df_raw['分层情况'].isin(PRIORITY_LAYERS)]['认购份额'].sum()
    report_total = dfa['实际份额'].sum()
    diff = abs(raw_total - report_total)
    if diff < 0.001 or report_total > raw_total:
        ok(f'认购总额一致（resolve后）：{report_total:.4f}亿')
    else:
        fail(f'认购总额不一致：原始={raw_total:.4f}（TUV列），resolve={report_total:.4f}（WXY+TUV），差={diff:.4f}')

    unknown_tenor = (dfa['期限分类'] == '未知').sum()
    if unknown_tenor == 0:
        ok('期限分类全部分解成功，无"未知"')
    else:
        warn(f'{unknown_tenor}条记录期限分类为"未知"，请检查期限列数据')

    raw_assets = set(df_raw[df_raw['分层情况'].isin(PRIORITY_LAYERS)]['资产类型'].unique())
    ok(f'资产类型覆盖：{raw_assets} | 产品类型：{len(products)}个')

    dates = dfa['簿记时间'].dropna()
    if not dates.empty:
        min_d = pd.to_datetime(dates).min().strftime('%Y-%m-%d')
        max_d = pd.to_datetime(dates).max().strftime('%Y-%m-%d')
        ok(f'时间范围：{min_d} ~ {max_d}')
    else:
        warn('簿记时间全部缺失，无法检查时间范围')

    print('\n【2】业务逻辑')
    excluded = df_raw[df_raw['分层情况'].str.startswith('优先A', na=False) & (df_raw['分层情况'] != '优先A')]
    if excluded.empty:
        ok('无优先A1/优先A2等相似分层被误匹配')
    else:
        warn(f'以下分层已被正确排除（共{len(excluded)}条）：{excluded["分层情况"].value_counts().to_dict()}')

    tenor_dist = dfa['期限分类'].value_counts()
    ok(f'期限分类分布：{tenor_dist.to_dict()}')

    mixed = []
    for pt, sub in dfa.groupby('产品类型', dropna=False):
        tenors = sub['期限分类'].unique()
        if len(tenors) > 1:
            mixed.append(pt)
    if not mixed:
        ok(f'产品类型均为单一期限，无混合（总计{len(products)}个产品）')
    else:
        fail(f'以下产品类型混合了多种期限：{mixed}')

    ok(f'数据行：{len(rows)}条（工具前端JS按成本+日期+机构+利差合并）')

    cost_vals = [r['cost'] for r in rows]
    if cost_vals:
        min_cost, max_cost = min(cost_vals), max(cost_vals)
        if min_cost < 0.5:
            fail(f'成本值疑似未转换为百分比：最小值={min_cost}（期望应≥1%）')
        elif max_cost > 10:
            warn(f'成本值异常偏高：最大值={max_cost}%，请确认数据来源')
        else:
            ok(f'成本值范围正常：{min_cost:.4f}% ~ {max_cost:.4f}%')

    neg_shares = [r for r in rows if r['share'] <= 0]
    if not neg_shares:
        ok('所有记录认购份额均为正值')
    else:
        warn(f'{len(neg_shares)}条记录认购份额≤0')

    print('\n【3】输出质量')
    if precheck_only:
        ok(f'输出质量检查在输出文件写入后执行（预检模式跳过）')
    else:
        file_kb = os.path.getsize(output_path) / 1024
        if file_kb < 1:
            fail(f'输出文件过小（{file_kb:.1f}KB）')
        elif file_kb < 5:
            warn(f'输出文件较小（{file_kb:.1f}KB），请确认内容完整性')
        else:
            ok(f'输出文件大小正常：{file_kb:.1f}KB')

        with open(output_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        checks = [
            ('tenorSelect',   '期限筛选下拉框'),
            ('productSelect', '产品类型下拉框'),
            ('costInput',     '成本数字输入框'),
            ('adjCost',       '成本微调函数'),
            ('ALL_DATA',      'JS数据变量'),
            ('基准利差',      '基准利差列'),
        ]
        html_fail = False
        for keyword, label in checks:
            if keyword not in html_content:
                fail(f'HTML缺少关键结构：{label}（"{keyword}"未找到）')
                html_fail = True
        if not html_fail:
            ok('HTML关键结构完整')

        tenor_count = html_content.count('tenor-badge')
        ok(f'期限标签（tenor-badge）出现次数：{tenor_count}')

    return qc.summary()


# ── 主入口 ──────────────────────────────────────────────────
def generate(xlsx_path, output_path=None):
    if output_path is None:
        date_tag = pd.Timestamp('today').strftime('%Y%m%d')
        kanban_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', 'deliverables', 'dashboards', '01_latest'
        )
        os.makedirs(kanban_dir, exist_ok=True)
        output_path = os.path.join(kanban_dir, f'{date_tag}_发行定价分析工具.html')

    # 计算数据（含 QC precheck）
    try:
        data = compute_data(xlsx_path)
    except RuntimeError as e:
        print(f'\n[ERROR] {e}')
        print('[ERROR] 请修正数据或逻辑后重试')
        return

    # 渲染 + 写文件
    html_str = render_html(data)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_str)
    print(f'Done: {output_path}')
    print(f'Data rows: {len(data["rows"])} | Products: {len(data["products"])}')

    # 最终 QC
    run_qc(data['df'], data['dfa'], data['products'], data['rows'],
           output_path, precheck_only=False)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python gen_compare_tool.py <xlsx_path> [output_path]')
        sys.exit(1)

    xlsx_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        generate(xlsx_path, output_path)
    except ValueError as e:
        print(f'[INPUT ERROR] {e}')
        sys.exit(1)
    except Exception as e:
        print(f'[ERROR] 生成失败：{e}')
        sys.exit(1)
