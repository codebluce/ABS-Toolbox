"""fig4_interactive.py — 理财子×资产类型矩阵交互版(lab实验)

输出 ECharts + Plotly.js 两版热力图,上下排列,含月份滑块。
默认显示"全部月份",滑块 1-8 切换具体月。

数据:fig4_new_welizhi_matrix.load_all_rows() + 月份列
预计算:8 个月 + 全部,共 9 份 pivot
"""
import os, sys, json
_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _SCRIPTS_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import fig4_new_welizhi_matrix as fig4_mod

LAB_DIR = os.path.dirname(os.path.abspath(__file__))
LAB_VIZ_DIR = os.path.join(LAB_DIR, '..', '..', 'deliverables', 'dashboards', '02_history', 'lab_viz')

ASSET_ORDER = ['保理', '赊销白条', '现金贷', '金采', '企业主贷', '其他']


def compute_pivot_by_month(df, month=None):
    """按月聚合 pivot。month=None 表示全部"""
    if month is not None:
        df = df[df['month'] == month].copy()
    # 筛选发行场所
    df = df[df['发行场所'].isin(['上交所', '深交所', '银行间'])].copy()
    # 资产分类
    df['资产分类'] = df['资产类型'].apply(fig4_mod.classify_asset)
    # 筛选理财子
    df = df[df['认购机构'].apply(fig4_mod.is_wealth_management_sub)].copy()
    if len(df) == 0:
        return None, [], []
    # 理财子列表(按总规模降序)
    inst_total = df.groupby('认购机构')['认购份额'].sum().sort_values(ascending=False)
    pivot = df.groupby(['认购机构', '资产分类'])['认购份额'].sum().unstack(fill_value=0)
    pivot = pivot.reindex(index=inst_total.index, columns=ASSET_ORDER, fill_value=0)
    return pivot, list(pivot.index), list(pivot.columns)


def precompute_all_months():
    """预计算全部 + 1-8 月的 pivot"""
    df = fig4_mod.load_all_rows()
    result = {}
    # 全部
    pivot, insts, cols = compute_pivot_by_month(df, None)
    result['all'] = {
        'institutions': insts,
        'assets': cols,
        'data': pivot.values.tolist() if pivot is not None else [],
    }
    # 1-8 月
    for m in range(1, 9):
        pivot, insts, cols = compute_pivot_by_month(df, m)
        result[str(m)] = {
            'institutions': insts,
            'assets': cols,
            'data': pivot.values.tolist() if pivot is not None else [],
        }
    return result


def build_plotly_html(data_by_month):
    """Plotly.js 热力图 + 月份滑块"""
    return f'''
<div style="margin-bottom:32px">
  <div style="font-size:14px;font-weight:600;color:#0d1b2e;margin-bottom:8px">
    Plotly 版 — 理财子×资产类型投资规模矩阵
  </div>
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;padding:8px 12px;background:#f8f9fa;border-radius:6px">
    <span style="font-size:12px;color:#666">月份:</span>
    <input type="range" min="0" max="8" value="0" id="fig4_plotly_slider" style="flex:1;max-width:400px">
    <span id="fig4_plotly_label" style="font-size:13px;font-weight:600;color:#0d1b2e;min-width:80px">全部</span>
  </div>
  <div id="fig4_plotly" style="width:100%;height:600px"></div>
</div>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<script>
const fig4DataPlotly = {json.dumps(data_by_month, ensure_ascii=False)};
const fig4MonthLabelsPlotly = {{0: '全部', 1: '1月', 2: '2月', 3: '3月', 4: '4月', 5: '5月', 6: '6月', 7: '7月', 8: '8月'}};

function renderFig4Plotly(monthKey) {{
  const d = fig4DataPlotly[monthKey];
  const div = document.getElementById('fig4_plotly');
  if (!d || !d.data || d.data.length === 0) {{
    Plotly.purge(div);
    div.innerHTML = '<div style="text-align:center;padding-top:200px;color:#999;font-size:16px">无数据</div>';
    return;
  }}
  // Plotly heatmap: z=数据矩阵, x=资产, y=机构
  const trace = {{
    z: d.data,
    x: d.assets,
    y: d.institutions,
    type: 'heatmap',
    colorscale: [[0, '#FDFBF7'], [1, '#A6192E']],
    showscale: true,
    colorbar: {{ title: '亿元', thickness: 15 }},
    text: d.data.map(row => row.map(v => v > 0 ? v.toFixed(1) : '')),
    texttemplate: '%{{text}}',
    textfont: {{ size: 10 }}
  }};
  const layout = {{
    margin: {{ l: 140, r: 80, t: 20, b: 60 }},
    xaxis: {{ tickfont: {{ size: 12, color: '#333' }} }},
    yaxis: {{ tickfont: {{ size: 11, color: '#333' }}, autorange: 'reversed' }},
    paper_bgcolor: '#FDFBF7',
    plot_bgcolor: '#FDFBF7'
  }};
  Plotly.react(div, [trace], layout, {{ responsive: true, displayModeBar: false }});
}}

document.getElementById('fig4_plotly_slider').addEventListener('input', e => {{
  const v = parseInt(e.target.value);
  document.getElementById('fig4_plotly_label').textContent = fig4MonthLabelsPlotly[v];
  renderFig4Plotly(v === 0 ? 'all' : String(v));
}});

// 初始渲染:全部
renderFig4Plotly('all');
</script>
'''


def render_fig4_interactive():
    """生成 fig4 交互版 HTML body(Plotly 版)"""
    data_by_month = precompute_all_months()
    plotly_html = build_plotly_html(data_by_month)
    return plotly_html


if __name__ == '__main__':
    html_body = render_fig4_interactive()
    standalone = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>fig4 交互版 - 独立预览</title>
<style>
  body {{ font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif; background:#f4f5f7; margin:0; padding:20px; }}
  .container {{ max-width:1200px; margin:0 auto; background:#fff; padding:24px; border-radius:8px; box-shadow:0 1px 3px rgba(0,0,0,.07); }}
</style>
</head>
<body>
<div class="container">
{html_body}
</div>
</body>
</html>'''
    out = os.path.join(LAB_VIZ_DIR, 'fig4_interactive_preview.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(standalone)
    print(f'[fig4-interactive] 独立预览 HTML: {out}')
