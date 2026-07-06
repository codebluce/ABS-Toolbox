"""fig7_wlz_panel.py — 理财子分析 panel 生成器(lab实验)

为综合看板"投资人分析"模块生成"理财子分析"子模块的 panel HTML body。
内容:fig4(理财子×资产类型投资规模矩阵) + fig5(理财子投资画像) 并排显示。

设计:
  - 调用 fig4_new_welizhi_matrix.main() 和 fig5_hbr_composite.main() 重跑 PNG(同步最新台账)
  - 把两张 PNG 以 base64 嵌入 HTML(避免外部图片依赖)
  - 并排布局(响应式 flex)
  - 风格与综合看板一致(section-header + section-title)

输出: panel body HTML 字符串(供 gen_investor_module_demo.py 注入综合看板)
"""
import os, sys, base64
_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _SCRIPTS_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LAB_DIR = os.path.dirname(os.path.abspath(__file__))
LAB_VIZ_DIR = os.path.join(LAB_DIR, '..', '..', 'deliverables', 'dashboards', '02_history', 'lab_viz')

FIG4_PATH = os.path.join(LAB_VIZ_DIR, 'fig4_new_welizhi_matrix.png')
FIG5_PATH = os.path.join(LAB_VIZ_DIR, 'fig5_hbr_composite.png')


def png_to_base64(png_path):
    """把 PNG 文件转 base64 data URL"""
    with open(png_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    return f'data:image/png;base64,{b64}'


def render_wlz_panel(regenerate=True):
    """生成理财子分析 panel HTML body(交互版)

    交互版:fig4 矩阵 + fig5 画像,各出 ECharts + Plotly 两版,上下排列
    每个图含月份滑块(0=全部,1-8=具体月),默认显示全部月份
    regenerate 参数保留兼容性(交互版直接从台账读数据,无需重跑 PNG)
    """
    import fig4_interactive
    import fig5_interactive

    fig4_html = fig4_interactive.render_fig4_interactive()
    fig5_html = fig5_interactive.render_fig5_interactive()

    html_body = f'''
<div class="section">
  <div class="section-header" style="background:linear-gradient(135deg,#1a3a5c,#0d1b2e)">
    <span class="section-title">理财子投资分析(交互版 · 月份滑块)</span>
    <span class="section-sub">21家理财子 · Plotly 交互图 · 0703定稿台账</span>
  </div>
  <div style="padding:16px;background:#FDFBF7">
    {fig4_html}
    <hr style="border:none;border-top:2px dashed #e0e0e0;margin:24px 0"/>
    {fig5_html}
  </div>
</div>
'''
    return html_body


if __name__ == '__main__':
    # 独立运行时,生成独立 HTML 文件供预览
    html_body = render_wlz_panel(regenerate=True)
    standalone = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>理财子分析 - 独立预览</title>
<style>
  body {{ font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif; background:#f4f5f7; margin:0; padding:20px; }}
  .section {{ max-width:1400px; margin:0 auto 24px; border-radius:8px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.07); }}
  .section-header {{ padding:12px 16px 10px; color:#fff; display:flex; justify-content:space-between; align-items:center; }}
  .section-title {{ font-size:16px; font-weight:700; letter-spacing:.5px; }}
  .section-sub {{ font-size:11px; color:rgba(255,255,255,.75); text-align:right; line-height:1.5; }}
</style>
</head>
<body>
{html_body}
</body>
</html>'''
    out = os.path.join(LAB_VIZ_DIR, 'fig7_wlz_panel_preview.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(standalone)
    print(f'\n[fig7] 独立预览 HTML: {out}')
