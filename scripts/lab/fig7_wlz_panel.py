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
    """生成理财子分析 panel HTML body

    regenerate=True 时,先重跑 fig4_new + fig5 同步最新台账数据
    """
    if regenerate:
        print('[fig7] 重跑 fig4_new_welizhi_matrix 同步最新台账...')
        import fig4_new_welizhi_matrix
        fig4_new_welizhi_matrix.main()
        print('[fig7] 重跑 fig5_hbr_composite 同步最新台账...')
        import fig5_hbr_composite
        fig5_hbr_composite.main()

    fig4_b64 = png_to_base64(FIG4_PATH)
    fig5_b64 = png_to_base64(FIG5_PATH)

    html_body = f'''
<div class="section">
  <div class="section-header" style="background:linear-gradient(135deg,#1a3a5c,#0d1b2e)">
    <span class="section-title">理财子投资分析(并排视图)</span>
    <span class="section-sub">21家理财子 · 左:资产类型矩阵 · 右:申购规模×平均利率 · 0703定稿台账</span>
  </div>
  <div style="display:flex;gap:12px;padding:16px;background:#FDFBF7;align-items:flex-start">
    <div style="flex:1;min-width:0">
      <div style="font-size:12px;color:#666;margin-bottom:6px;font-weight:600">理财子×资产类型投资规模矩阵</div>
      <img src="{fig4_b64}" alt="fig4 理财子矩阵" style="width:100%;display:block"/>
    </div>
    <div style="flex:1;min-width:0">
      <div style="font-size:12px;color:#666;margin-bottom:6px;font-weight:600">理财子投资画像:申购规模 × 平均申购利率</div>
      <img src="{fig5_b64}" alt="fig5 理财子投资画像" style="width:100%;display:block"/>
    </div>
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
