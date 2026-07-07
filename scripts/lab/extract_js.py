from pathlib import Path

lab_path = Path(r"D:\wupeizhi.nolan\Documents\LikeCodeNex\skills\ABS工具箱\deliverables\dashboards\03_test\lab_pricing_insight.html")
lab = lab_path.read_text(encoding="utf-8")

# The JS starts after "const PROJECT_SIZES" and goes all way to the end of script
# Find the function section
js_start = lab.index("// ====== HELPERS =====")
js_end = lab.index("</script>", js_start)
js = lab[js_start:js_end]
print(f"Full JS: {len(js)} chars")

# Save
out_dir = Path(r"D:\wupeizhi.nolan\Documents\LikeCodeNex\skills\ABS工具箱\scripts\lab")
with open(out_dir / "pricing_insight_js.txt", "w", encoding="utf-8") as f:
    f.write(js)
print("JS saved!")
