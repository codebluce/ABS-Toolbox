"""fig5_interactive.py — 理财子投资画像交互版(lab实验)

输出 ECharts + Plotly.js 两版散点图,上下排列,含月份滑块。
默认显示"全部月份",滑块 1-8 切换具体月。

数据:load_wxy_df() 已含 month 列
预计算:8 个月 + 全部,共 9 份散点数据
横轴=平均申购利率,纵轴=理财子(按规模升序),点大小=总规模
"""
import os, sys, json
_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _SCRIPTS_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from load_data import load_wxy_df

LAB_DIR = os.path.dirname(os.path.abspath(__file__))
LAB_VIZ_DIR = os.path.join(LAB_DIR, '..', '..', 'deliverables', 'dashboards', '02_history', 'lab_viz')


def is_wealth_management_sub(inst_name):
    """判断是否为理财子(以'理财'结尾)"""
    return str(inst_name).strip().endswith('理财')


def compute_scatter_by_month(df, month=None):
    """按月聚合散点数据。month=None 表示全部"""
    if month is not None:
        df = df[df['month'] == month].copy()
    df = df[df['institution'].apply(is_wealth_management_sub)].copy()
    if len(df) == 0:
        return None, []
    summary = df.groupby('institution').agg(
        total_size=('size', 'sum'),
        mean_rate=('rate_pct', 'mean'),
        n=('size', 'count'),
    ).reset_index()
    summary = summary.sort_values('total_size', ascending=True)
    # 返回机构列表 + 每个机构的 [mean_rate, total_size, n]
    return summary, list(zip(summary['institution'], summary['mean_rate'], summary['total_size'], summary['n']))


def precompute_all_months():
    """预计算全部 + 1-8 月的散点数据"""
    df = load_wxy_df()
    result = {}
    # 全部
    summary, data = compute_scatter_by_month(df, None)
    result['all'] = {
        'institutions': summary['institution'].tolist() if summary is not None else [],
        'points': [
            {'inst': inst, 'rate': float(rate), 'size': float(size), 'n': int(n)}
            for inst, rate, size, n in data
        ] if data else [],
    }
    # 1-8 月
    for m in range(1, 9):
        summary, data = compute_scatter_by_month(df, m)
        result[str(m)] = {
            'institutions': summary['institution'].tolist() if summary is not None else [],
            'points': [
                {'inst': inst, 'rate': float(rate), 'size': float(size), 'n': int(n)}
                for inst, rate, size, n in data
            ] if data else [],
        }
    return result




def build_plotly_html(data_by_month):
    """Plotly.js 散点图 + 月份滑块"""
    return f'''
<div style="margin-bottom:32px">
  <div style="font-size:14px;font-weight:600;color:#0d1b2e;margin-bottom:8px">
    Plotly 版 — 理财子投资画像(申购规模 × 平均申购利率)
  </div>
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;padding:8px 12px;background:#f8f9fa;border-radius:6px">
    <span style="font-size:12px;color:#666">月份:</span>
    <input type="range" min="0" max="8" value="0" id="fig5_plotly_slider" style="flex:1;max-width:400px">
    <span id="fig5_plotly_label" style="font-size:13px;font-weight:600;color:#0d1b2e;min-width:80px">全部</span>
  </div>
  <div id="fig5_plotly" style="width:100%;height:700px"></div>
</div>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<script>
const fig5DataPlotly = {json.dumps(data_by_month, ensure_ascii=False)};
const fig5MonthLabelsPlotly = {{0: '全部', 1: '1月', 2: '2月', 3: '3月', 4: '4月', 5: '5月', 6: '6月', 7: '7月', 8: '8月'}};

function renderFig5Plotly(monthKey) {{
  const d = fig5DataPlotly[monthKey];
  const div = document.getElementById('fig5_plotly');
  if (!d || !d.points || d.points.length === 0) {{
    Plotly.purge(div);
    div.innerHTML = '<div style="text-align:center;padding-top:200px;color:#999;font-size:16px">无数据</div>';
    return;
  }}
  const maxSize = Math.max(...d.points.map(p => p.size), 1);
  const medianRate = d.points.reduce((s, p) => s + p.rate, 0) / d.points.length;
  const medianSize = maxSize / 2;
  // 点颜色:量大价低=红,量小价高=浅灰,均衡=深灰
  const colors = d.points.map(p => {{
    if (p.size >= medianSize && p.rate <= medianRate) return '#A6192E';
    if (p.size < medianSize && p.rate > medianRate) return '#D9D9D9';
    return '#666';
  }});
  const trace = {{
    x: d.points.map(p => p.rate),
    y: d.points.map(p => p.inst),
    mode: 'markers+text',
    text: d.points.map(p => p.size.toFixed(1) + '亿'),
    textposition: 'right',
    textfont: {{ size: 9, color: '#333' }},
    marker: {{
      size: d.points.map(p => 80 + (p.size / maxSize) * 720) / 8,
      color: colors,
      opacity: 0.75,
      line: {{ color: '#333', width: 0.8 }}
    }},
    hovertemplate: '<b>%{{y}}</b><br>平均利率: %{{x:.3f}}%<br>总规模: %{{customdata}}亿<extra></extra>',
    customdata: d.points.map(p => p.size.toFixed(2)),
    type: 'scatter'
  }};
  const layout = {{
    margin: {{ l: 140, r: 80, t: 20, b: 60 }},
    xaxis: {{
      title: '平均申购利率 (%)',
      tickfont: {{ size: 11, color: '#333' }},
      gridcolor: '#D9D9D9', griddash: 'dash',
      zeroline: false
    }},
    yaxis: {{
      tickfont: {{ size: 11, color: '#333' }},
      autorange: 'reversed',
      gridcolor: '#D9D9D9', griddash: 'dash'
    }},
    paper_bgcolor: '#FDFBF7',
    plot_bgcolor: '#FDFBF7',
    showlegend: false,
    shapes: [{{
      type: 'line', xref: 'x', yref: 'paper',
      x0: medianRate, x1: medianRate, y0: 0, y1: 1,
      line: {{ color: '#A6192E', width: 1, dash: 'dash' }}
    }}]
  }};
  Plotly.react(div, [trace], layout, {{ responsive: true, displayModeBar: false }});
}}

document.getElementById('fig5_plotly_slider').addEventListener('input', e => {{
  const v = parseInt(e.target.value);
  document.getElementById('fig5_plotly_label').textContent = fig5MonthLabelsPlotly[v];
  renderFig5Plotly(v === 0 ? 'all' : String(v));
}});

renderFig5Plotly('all');
</script>
'''


def render_fig5_interactive():
    """生成 fig5 交互版 HTML body(Plotly 版)"""
    data_by_month = precompute_all_months()
    plotly_html = build_plotly_html(data_by_month)
    return plotly_html


if __name__ == '__main__':
    html_body = render_fig5_interactive()
    standalone = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>fig5 交互版 - 独立预览</title>
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
    out = os.path.join(LAB_VIZ_DIR, 'fig5_interactive_preview.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(standalone)
    print(f'[fig5-interactive] 独立预览 HTML: {out}')
