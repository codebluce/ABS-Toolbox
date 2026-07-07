from pathlib import Path

out_dir = Path(r"D:\wupeizhi.nolan\Documents\LikeCodeNex\skills\ABS工具箱\scripts\lab")
css = (out_dir / "pricing_insight_css.txt").read_text(encoding="utf-8")
js_logic = (out_dir / "pricing_insight_js.txt").read_text(encoding="utf-8")
html_body = (out_dir / "pricing_insight_html.txt").read_text(encoding="utf-8")

# Build the module using raw-string templates to avoid f-string {} conflicts
module = r'''"""ABS 定价测试 + 洞察面板 —— 新版双栏布局渲染器"""
import json
import os

PRICING_INSIGHT_CSS = """\
''' + css + r'''\
"""

_PRICING_INSIGHT_JS = """\
''' + js_logic + r'''\
"""

_PRICING_INSIGHT_HTML = """\
''' + html_body + r'''\
"""


def render_pricing_panel(data):
    """渲染定价测试面板（新版双栏：洞察左1/3 + 明细右2/3）"""
    products_js = data['products_js']
    data_js = data['data_js']
    proj_sizes_js = data.get('proj_sizes_js', '{}')
    xlsx_basename = data['xlsx_basename']

    body = _PRICING_INSIGHT_HTML.replace('{xlsx_basename}', xlsx_basename)

    script = (
        '<script>\n'
        'const ALL_PRODUCTS = ' + products_js + ';\n'
        'const ALL_DATA = ' + data_js + ';\n'
        'const PROJECT_SIZES = ' + proj_sizes_js + ';\n'
        '\n'
        + _PRICING_INSIGHT_JS +
        '\n</script>'
    )

    return body + script
'''

module_path = Path(r"D:\wupeizhi.nolan\Documents\LikeCodeNex\skills\ABS工具箱\scripts\gen_pricing_insight.py")
module_path.write_text(module, encoding="utf-8")
print(f"Written: {module_path} ({len(module)} chars)")

# Quick syntax check
import py_compile
try:
    py_compile.compile(str(module_path), doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print(f"Syntax error: {e}")
