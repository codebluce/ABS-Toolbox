from pathlib import Path

# Read parts
out_dir = Path(r"D:\wupeizhi.nolan\Documents\LikeCodeNex\skills\ABS工具箱\scripts\lab")
css = (out_dir / "pricing_insight_css.txt").read_text(encoding="utf-8")
js_logic = (out_dir / "pricing_insight_js.txt").read_text(encoding="utf-8")
html_body = (out_dir / "pricing_insight_html.txt").read_text(encoding="utf-8")

# Build the Python module
module = f'''"""ABS 定价测试 + 洞察面板 —— 新版双栏布局渲染器

替代 gen_compare_tool.py 中 render_body / render_body_pricing。
提供 CSS、HTML 模板、JS 逻辑三部分，由 gen_integrated_dashboard.py 组装。
"""
import json
import os

# ====== CSS (same for all) ======
PRICING_INSIGHT_CSS = """\\
{css}
"""

# ====== RENDER ======
def render_pricing_panel(data):
    """渲染定价测试面板（新版双栏：洞察左 1/3 + 明细右 2/3）

    data 字段：
      - products_js: JS 产品列表
      - data_js: JS 数据数组
      - proj_sizes_js: JS 项目-总规模映射
      - xlsx_basename: 台账文件名
    """
    products_js = data['products_js']
    data_js = data['data_js']
    proj_sizes_js = data.get('proj_sizes_js', '{{}}')
    xlsx_basename = data['xlsx_basename']

    body = f"""\\
{html_body}
"""

    script = f"""\\
  <script>
  const ALL_PRODUCTS = {{products_js}};
  const ALL_DATA = {{data_js}};
  const PROJECT_SIZES = {{proj_sizes_js}};

{js_logic}
  </script>"""

    return body + script


def compute_pricing_data(xlsx_path):
    """读取台账 + 计算数据（复用 gen_compare_tool 逻辑，但追加 proj_sizes）

    注意：需要先 import gen_compare_tool，打 monkey-patch 再调用。
    推荐做法：在 gen_integrated_dashboard.py 中直接调用 gen_compare_tool.compute_data
    然后用本模块的 render_pricing_panel 渲染。
    """
    from . import gen_compare_tool
    data = gen_compare_tool.compute_data(xlsx_path)

    # Ensure proj_sizes_js exists (added by our patch)
    if 'proj_sizes_js' not in data:
        # Fallback: build from dfa
        dfa = data['dfa']
        proj_sizes = {{}}
        import pandas as pd
        for _, r in dfa.iterrows():
            proj = str(r['项目名称']) if pd.notna(r.get('项目名称')) else ''
            amt = r.get('对应金额（亿）')
            if proj and pd.notna(amt):
                try:
                    proj_sizes[proj] = float(amt)
                except:
                    pass
        data['proj_sizes_js'] = json.dumps(proj_sizes, ensure_ascii=False)

    return data
'''

# Write
module_path = Path(r"D:\wupeizhi.nolan\Documents\LikeCodeNex\skills\ABS工具箱\scripts\gen_pricing_insight.py")
module_path.write_text(module, encoding="utf-8")
print(f"Written: {module_path} ({len(module)} chars)")
