from pathlib import Path

# Read the current module
module_path = Path(r"D:\wupeizhi.nolan\Documents\LikeCodeNex\skills\ABS工具箱\scripts\gen_pricing_insight.py")
content = module_path.read_text(encoding="utf-8")

# The issue is that we used f"""...""" for the body which contains JS with {} 
# Fix: the body part should use .format() or % instead of f-string
# But actually, the body already has {xlsx_basename} which needs f-string
# The script part has NO Python variables, so we can use plain string

# Let me rewrite the render function to avoid f-string conflicts
# The key fix: use string concatenation instead of f-string for the JS part

# Find and replace the problematic section
old_render_start = '    body = f"""\\'
new_render_start = '    body = f"""'

# Actually let me just rewrite the whole file properly
# Read the parts
out_dir = Path(r"D:\wupeizhi.nolan\Documents\LikeCodeNex\skills\ABS工具箱\scripts\lab")
css = (out_dir / "pricing_insight_css.txt").read_text(encoding="utf-8")
js_logic = (out_dir / "pricing_insight_js.txt").read_text(encoding="utf-8")
html_body = (out_dir / "pricing_insight_html.txt").read_text(encoding="utf-8")

# Escape { and } in JS for Python format strings
# But we CANNOT use f-string for the JS part. Instead, use .format() or %s
# Cleanest approach: use triple-quoted raw strings + .replace() for variables

# The HTML body needs {xlsx_basename}
html_body_escaped = html_body.replace("{xlsx_basename}", "{{xlsx_basename}}")

# Build module with proper escaping
module = f'''"""ABS 定价测试 + 洞察面板 —— 新版双栏布局渲染器

替代 gen_compare_tool.py 中 render_body / render_body_pricing。
提供 CSS、HTML 模板、JS 逻辑三部分，由 gen_integrated_dashboard.py 组装。
"""
import json
import os

# ====== CSS ======
PRICING_INSIGHT_CSS = """\\
{css}
"""

# ====== JS ======
_PRICING_INSIGHT_JS_TEMPLATE = """\\
{js_logic}
"""

# ====== HTML ======
_PRICING_INSIGHT_HTML_TEMPLATE = """\\
{html_body_escaped}
"""


def render_pricing_panel(data):
    """渲染定价测试面板（新版双栏：洞察左 1/3 + 明细右 2/3）"""
    products_js = data['products_js']
    data_js = data['data_js']
    proj_sizes_js = data.get('proj_sizes_js', '{{}}')
    xlsx_basename = data['xlsx_basename']

    body = _PRICING_INSIGHT_HTML_TEMPLATE.format(xlsx_basename=xlsx_basename)

    script = f"""\\
  <script>
  const ALL_PRODUCTS = {{products_js}};
  const ALL_DATA = {{data_js}};
  const PROJECT_SIZES = {{proj_sizes_js}};

{{_PRICING_INSIGHT_JS_TEMPLATE}}
  </script>"""

    return body + script
'''

# But wait - the JS in the template ALSO has {{ and }} which will conflict with f-string
# Let me use a different approach: triple-quoted raw string for the JS template, 
# and .replace() for variables

# Actually, let me look at what's in the JS that needs escaping
js_sample = js_logic[:200]
print("JS sample:", js_sample[:100])

# The JS has lots of {} - but since we're using a regular string (not f-string) it should be fine
# The problem was in the original module where we used f"""..."""

# Let me rewrite clean
