from pathlib import Path

# Read lab CSS and JS for reference
lab_path = Path(r"D:\wupeizhi.nolan\Documents\LikeCodeNex\skills\ABS工具箱\deliverables\dashboards\03_test\lab_pricing_insight.html")
lab = lab_path.read_text(encoding="utf-8")

# Extract full CSS
css_start = lab.index("<style>") + 7
css_end = lab.index("</style>")
css = lab[css_start:css_end]

# Strip body/head wrapper - we just need the styles
print(f"CSS extracted: {len(css)} chars")

# Extract JS logic (after data, to end)
js_start = lab.index("// ====== HELPERS =====")
js_end = lab.index("populateProducts(ALL_PRODUCTS);") + len("populateProducts(ALL_PRODUCTS);")
js_logic = lab[js_start:js_end]
print(f"JS logic extracted: {len(js_logic)} chars")

# Extract HTML body (between <body> and <script>)
body_start = lab.index("<body>") + 6
script_start = lab.index("<script>")
html_body = lab[body_start:script_start].strip()
print(f"HTML body extracted: {len(html_body)} chars")

# Save the parts for building
out_dir = Path(r"D:\wupeizhi.nolan\Documents\LikeCodeNex\skills\ABS工具箱\scripts\lab")
out_dir.mkdir(parents=True, exist_ok=True)

with open(out_dir / "pricing_insight_css.txt", "w", encoding="utf-8") as f:
    f.write(css)
with open(out_dir / "pricing_insight_js.txt", "w", encoding="utf-8") as f:
    f.write(js_logic)
with open(out_dir / "pricing_insight_html.txt", "w", encoding="utf-8") as f:
    f.write(html_body)

print("Parts saved to scripts/lab/")
