#!/usr/bin/env python3
"""Build the phone-sized ABS dashboard from a generated desktop dashboard HTML.

The desktop dashboard is the single source of truth: this script re-reads its embedded
datasets (机构画像 / 投资台账 / 消金资产 / 同业发行) and emits a small self-contained
HTML tuned for a 393pt viewport. Nothing here talks to Excel — run it after
gen_integrated_dashboard.py so the two views can never drift apart.

Usage:
    python scripts/gen_mobile_dashboard.py <desktop.html> [<out.html>]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
APP_JS = SCRIPTS_DIR / "abs_mobile_app.js"

PRIORITY_LAYERS = ("优先A", "优先级", "优先A1", "优先A2", "优先A档")

CREDIT_NAME_NORMS = {
    "工商银行": "工银理财", "交通银行": "交银理财", "民生银行": "民生理财",
    "光大银行": "光大理财", "华夏银行": "华夏理财", "广发理财": "广银理财",
    "苏银理财": "江苏银行", "杭州银行": "杭银理财", "恒丰理财": "恒丰银行",
    "上海农商行": "沪农商行", "上海农商": "沪农商行", "北京银行": "北银理财",
    "东莞农商": "东莞农商业银行", "东莞银行": "东莞农商业银行",
}


# ---------------------------------------------------------------- extraction

def extract_literal(src: str, marker: str, opener: str) -> str:
    """Slice a balanced JS array/object literal that follows `marker`, string-aware."""
    i = src.find(marker)
    if i < 0:
        raise ValueError(f"未在看板中找到 {marker!r}")
    start = src.index(opener, i + len(marker) - 1)
    closer = "]" if opener == "[" else "}"
    depth = 0
    in_str = False
    quote = ""
    esc = False
    for pos in range(start, len(src)):
        ch = src[pos]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
            continue
        if ch in "\"'":
            in_str = True
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
            if depth == 0:
                return src[start:pos + 1]
    raise ValueError(f"{marker!r} 字面量未闭合")


_IDENT_START = re.compile(r"[A-Za-z_$]")
_IDENT_CHAR = re.compile(r"[A-Za-z0-9_$]")


def strip_js_noise(literal: str) -> str:
    """把 JS 对象字面量转成合法 JSON:剥注释、补裸 key 引号、去尾随逗号。

    看板里的字面量是人写的 JS 源码,直接喂给 json.loads 会失败,常见三类:
      1. 注释    —— PROG_NAME_MAP 用中文注释说明归并规则;
      2. 裸 key  —— PROG_CREDIT_DATA 写成 {total: 20.0, remain: 14.0};
      3. 尾随逗号 —— JS 合法、JSON 非法。
    按字符扫描并跳过字符串内部,避免把 "https://..." 里的 // 当注释、
    或把字符串内容当成裸 key 误加引号。
    """
    out = []
    i, n = 0, len(literal)
    in_str = False
    quote = ""
    esc = False
    prev_sig = ""      # 上一个有意义的非空白字符,用于判定"当前是否处在 key 位置"
    while i < n:
        ch = literal[i]
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
                prev_sig = ch
            i += 1
            continue
        if ch in "\"'":
            in_str = True
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n:
            nxt = literal[i + 1]
            if nxt == "/":                      # 行注释:吃到行尾(保留换行,维持行号语义)
                while i < n and literal[i] != "\n":
                    i += 1
                continue
            if nxt == "*":                      # 块注释:吃到 */
                end = literal.find("*/", i + 2)
                i = n if end < 0 else end + 2
                continue
        # 裸 key: 仅在 { 或 , 之后的位置识别标识符,且其后必须跟 : 才补引号,
        # 这样值位置的 true/false/null 与数字不会被误加引号
        if prev_sig in "{," and _IDENT_START.match(ch):
            j = i
            while j < n and _IDENT_CHAR.match(literal[j]):
                j += 1
            k = j
            while k < n and literal[k] in " \t\r\n":
                k += 1
            if k < n and literal[k] == ":":
                out.append('"' + literal[i:j] + '"')
                prev_sig = literal[j - 1]
                i = j
                continue
        out.append(ch)
        if not ch.isspace():
            prev_sig = ch
        i += 1
    cleaned = "".join(out)
    # 尾随逗号: {"a":1,} / [1,2,] —— JS 合法、JSON 非法
    cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)
    return cleaned


def load_json_literal(src: str, marker: str, opener: str):
    literal = extract_literal(src, marker, opener)
    try:
        return json.loads(literal)
    except json.JSONDecodeError:
        # 字面量含注释/尾随逗号等 JS 语法时清洗后重试;仍失败则抛原始错误位置
        return json.loads(strip_js_noise(literal))


# ---------------------------------------------------------------- 机构画像

def build_ledger_profile(itl_rows: list[dict]) -> dict:
    """{inst: {year: {asset: {share, spread_sum, spread_weight}}}} — 利差仅统计优先档。"""
    profile: dict = {}
    for row in itl_rows:
        inst = row.get("inst")
        if not inst:
            continue
        try:
            share = float(row.get("share") or 0)
        except (TypeError, ValueError):
            share = 0.0
        asset = row.get("asset") or "未知"
        year = str(row.get("year") or "未知")
        spread = None
        if row.get("layer") in PRIORITY_LAYERS and row.get("spread") is not None:
            try:
                spread = float(row["spread"])
            except (TypeError, ValueError):
                spread = None
        cell = profile.setdefault(inst, {}).setdefault(year, {}).setdefault(
            asset, {"share": 0.0, "spread_sum": 0.0, "spread_weight": 0.0}
        )
        cell["share"] += share
        if spread is not None:
            cell["spread_sum"] += spread * share
            cell["spread_weight"] += share


    return profile


def resolve_names(prog_name: str, name_map: dict, profile: dict) -> list[str]:
    """机构进展表名 → 台账机构名。与看板 progResolveLedgerNames 同口径。"""

    def resolve_single(name: str) -> list[str]:
        if name in name_map:
            return name_map[name]
        base = re.sub(r"[（(].*?[）)]", "", name.split(":")[0].split("：")[0]).strip()
        if not base:
            return []
        hits = []
        for inst in profile:
            inst_base = re.sub(r"-.*$", "", re.sub(r"[（(].*?[）)]", "", inst)).strip()
            if inst_base == base or inst == name or inst.startswith(base):
                hits.append(inst)
        return hits or [base]

    parts = [p.strip() for p in prog_name.split("/") if p.strip()]
    if len(parts) <= 1:
        return resolve_single(prog_name)
    out: list[str] = []
    for part in parts:
        for hit in resolve_single(part):
            if hit not in out:
                out.append(hit)
    return out


def match_credit(name: str, credit: dict) -> str | None:
    def match_one(candidate: str) -> str | None:
        if candidate in credit:
            return candidate
        norm = CREDIT_NAME_NORMS.get(candidate)
        if norm and norm in credit:
            return norm
        for key in credit:
            if candidate in key or key in candidate:
                return key
        return None

    hit = match_one(name)
    if hit:
        return hit
    for part in (p.strip() for p in name.split("/")):
        if not part:
            continue
        hit = match_one(part)
        if hit:
            return hit
    return None


def parse_contacts(raw: str) -> list[dict]:
    """把「部门-姓名」「姓名（部门）」「部门-甲、乙」等写法拆成结构化联系人。"""
    if not raw or raw == "—":
        return []

    def parse_one(seg: str) -> dict | None:
        seg = seg.strip().strip(";、，, ")
        if not seg:
            return None
        m = re.match(r"^([\u4e00-\u9fa5·]{2,5})[（(]([^）)]*)[）)]$", seg)
        if m:
            return {"dept": m.group(2), "name": m.group(1)}
        if "-" in seg or "—" in seg:
            parts = re.split(r"[-—]", seg)
            if len(parts) >= 2:
                left, right = parts[0].strip(), "-".join(parts[1:]).strip()
                lname = bool(re.fullmatch(r"[\u4e00-\u9fa5·]{2,5}", left))
                rname = bool(re.fullmatch(r"[\u4e00-\u9fa5·]{2,5}", right))
                if lname and not rname:
                    return {"dept": right, "name": left}
                if rname and not lname:
                    return {"dept": left, "name": right}
                if lname:
                    return {"dept": right, "name": left}
                return {"dept": left, "name": right}
        m = re.match(r"^([\u4e00-\u9fa5A-Za-z]{2,10}?)([\u4e00-\u9fa5·]{2,5})$", seg)
        if m and len(m.group(1)) >= 2:
            return {"dept": m.group(1), "name": m.group(2)}
        if re.fullmatch(r"[\u4e00-\u9fa5·]{2,5}", seg):
            return {"dept": "", "name": seg}
        return {"dept": "", "name": seg}

    out: list[dict] = []
    for seg in re.split(r"[;\n]", raw.replace("\\n", ";")):
        seg = seg.strip()
        if not seg:
            continue
        m = re.match(r"^(.+?[-—])(.+)$", seg)
        if m:
            dept = re.sub(r"[-—]$", "", m.group(1)).strip()
            names = [x.strip() for x in re.split(r"[、,，]", m.group(2)) if x.strip()]
            if len(names) > 1:
                for nm in names:
                    parsed = parse_one(nm)
                    if parsed:
                        out.append({"dept": dept, "name": parsed["name"] or nm})
                continue
        if "、" in seg and "-" not in seg and "—" not in seg and "（" not in seg:
            names = [x.strip() for x in re.split(r"[、,，]", seg) if x.strip()]
            if names and all(re.fullmatch(r"[\u4e00-\u9fa5·]{2,5}", n) for n in names):
                out.extend({"dept": "", "name": n} for n in names)
                continue
        parsed = parse_one(seg)
        if parsed:
            out.append(parsed)
    return out


def build_prog_quick(html: str) -> list[dict]:
    prog_all = load_json_literal(html, "const PROG_ALL_DATA =", "[")
    itl_rows = load_json_literal(html, "window.ITL_ALL_DATA=", "[")
    name_map = load_json_literal(html, "const PROG_NAME_MAP =", "{")
    credit = load_json_literal(html, "const PROG_CREDIT_DATA =", "{")
    profile = build_ledger_profile(itl_rows)

    def rnd(v: float, digits: int = 2) -> float:
        return round(float(v) + 0.0, digits)

    out: list[dict] = []
    for rec in prog_all:
        names = resolve_names(rec.get("name", ""), name_map, profile)
        year_agg: dict = {}
        year_tot: dict = {}
        for inst in names:
            for year, assets in profile.get(inst, {}).items():
                bucket = year_agg.setdefault(year, {})
                year_tot.setdefault(year, 0.0)
                for asset, cell in assets.items():
                    slot = bucket.setdefault(asset, {"share": 0.0, "ss": 0.0, "sw": 0.0})
                    slot["share"] += cell["share"]
                    slot["ss"] += cell["spread_sum"]
                    slot["sw"] += cell["spread_weight"]
                    year_tot[year] += cell["share"]

        years = []
        for year in sorted(year_agg, reverse=True):
            total = year_tot.get(year, 0.0)
            if total <= 0:
                continue
            ss = sw = 0.0
            rows = []
            for asset, slot in sorted(year_agg[year].items(), key=lambda kv: -kv[1]["share"]):
                ss += slot["ss"]
                sw += slot["sw"]
                rows.append({
                    "a": asset,
                    "s": rnd(slot["share"]),
                    "p": rnd(slot["share"] / total * 100, 1) if total else 0,
                    "sp": round(slot["ss"] / slot["sw"] * 10000) if slot["sw"] > 0 else None,
                })
            years.append({
                "y": year,
                "tot": rnd(total),
                "avg": round(ss / sw * 10000) if sw > 0 else None,
                "rows": rows,
            })

        credit_key = match_credit(rec.get("name", ""), credit)
        cr = None
        if credit_key:
            cr = {"t": credit[credit_key]["total"], "r": credit[credit_key]["remain"]}
        elif rec.get("approval") and rec["approval"] != "—":
            cr = {"ap": rec["approval"], "q": rec.get("quota") or ""}

        out.append({
            "n": rec.get("name", ""),
            "c": rec.get("category", ""),
            "o": rec.get("owner", ""),
            "ct": parse_contacts(rec.get("contact", "")),
            "pn": rec.get("progress_count", 0),
            "pr": [{"d": p.get("date"), "t": p.get("text")} for p in (rec.get("recent_progress") or [])[:5]],
            "cr": cr,
            "pf": years,
            "tot": rnd(sum(y["tot"] for y in years)),
        })
    return out


# ---------------------------------------------------------------- 消金资产

BAR_ROW_RE = re.compile(
    r'<div class="(?P<ns>consumer-asset|peer-issuance)-bar-row">\s*'
    r'<div class="\1-label">(?P<label>[^<]*)</div>\s*'
    r'<div class="\1-track"><span style="width:(?P<w>[\d.]+)%;background:(?P<color>#[0-9a-fA-F]{6})"></span></div>\s*'
    r'<div class="\1-value"><span>(?P<amount>[^<]*)</span>'
    r'<small class="\1-delta (?P<dir>up|down|flat)">(?P<delta>[^<]*)</small>',
    re.S,
)

DELTA_RE = re.compile(r"(?:增长|下降)\s*(-?[\d.]+)\s*亿元（(?P<pct>[+-]?[\d.]+)%）")


def parse_delta(text: str) -> tuple[float, float]:
    m = DELTA_RE.search(text)
    if not m:
        return 0.0, 0.0
    return float(m.group(1)), float(m.group("pct"))


def split_amount(text: str) -> tuple[str, str]:
    """'1,208 亿 · 86%' → ('1,208 亿', '86%')"""
    parts = [p.strip() for p in text.split("·")]
    return parts[0], (parts[1] if len(parts) > 1 else "")


def build_asset(html: str) -> dict | None:
    start = html.find('<main class="consumer-asset-root">')
    if start < 0:
        return None
    block = html[start:html.index("</main>", start) + 7]

    kpis = []
    for m in re.finditer(
        r'<article class="consumer-asset-kpi"><p>([^<]*)</p><strong>([\d,]+)<em>亿</em></strong>\s*'
        r'<span class="consumer-asset-delta (?:up|down)">([^<]*)</span>', block, re.S):
        d, p = parse_delta(m.group(3))
        label = m.group(1).replace("消金资产合计", "消金合计")
        kpis.append({"label": label, "val": m.group(2), "d": d, "p": p})

    sections = re.split(r'<h2>(消费贷资产及资金结构|现金贷资产及资金结构)</h2>', block)
    sides: dict[str, dict] = {}
    for idx in range(1, len(sections), 2):
        title, body = sections[idx], sections[idx + 1]
        key = "consume" if title.startswith("消费贷") else "cash"
        note = "白条消费 + 分分卡" if key == "consume" else "金条 + 白取"
        groups = []
        for gm in re.finditer(r'<h3>(资产类型结构|资金类型结构)</h3>(.*?)(?=<h3>|</section>)', body, re.S):
            rows = []
            for rm in BAR_ROW_RE.finditer(gm.group(2)):
                amount, share = split_amount(rm.group("amount"))
                d, p = parse_delta(rm.group("delta"))
                rows.append({
                    "label": rm.group("label"), "amount": amount, "w": float(rm.group("w")),
                    "share": share, "d": d, "p": p,
                })
            if rows:
                groups.append({"title": gm.group(1), "rows": rows})
        if groups:
            sides[key] = {"note": note, "groups": groups}

    if not kpis or "consume" not in sides or "cash" not in sides:
        return None
    expected = len(re.findall(r'<div class="consumer-asset-bar-row">', block))
    got = sum(len(g["rows"]) for s in sides.values() for g in s["groups"])
    if got != expected:
        raise RuntimeError(f"消金资产行数不匹配: 源 {expected} 行, 解析到 {got} 行")
    return {"kpis": kpis, "consume": sides["consume"], "cash": sides["cash"]}


# ---------------------------------------------------------------- 同业发行

# 电脑端同业发行图例:<i style="background:#cf6b6b"></i>京东系
# 配色的唯一真源是 peer_issuance_panel.ASSET_FAMILY_COLORS,它已渲染进图例;
# 从这里回读可以让手机端自动跟随电脑端调色,无需两边各存一份常量。
LEGEND_RE = re.compile(
    r'<span class="peer-issuance-legend-item"><i style="background:'
    r'(?P<color>#[0-9a-fA-F]{6})"></i>(?P<family>[^<]+)</span>'
)


def build_peer_colors(block: str) -> dict:
    """从图例回读资产集团配色;沿用与 label 相同的 未知资产→其他 改名。"""
    colors = {}
    for m in LEGEND_RE.finditer(block):
        family = m.group("family").strip().replace("未知资产", "其他")
        colors[family] = m.group("color")
    return colors


def build_peer(html: str) -> dict | None:
    start = html.find('<main class="peer-issuance-root">')
    if start < 0:
        return None
    block = html[start:html.index("</main>", start) + 7]

    overview_end = block.find("信托渠道分布")
    groups = []
    for m in BAR_ROW_RE.finditer(block[:overview_end]):
        d, p = parse_delta(m.group("delta"))
        ly = re.search(r"去年同期\s*([\d,.]+\s*亿)", m.group("delta"))
        groups.append({
            "label": m.group("label").replace("未知资产", "其他"),
            "w": float(m.group("w")),
            "amt": m.group("amount"),
            "ly": ly.group(1) if ly else "—",
            "d": d, "p": p,
        })

    trust = []
    for m in re.finditer(
        r'<div class="peer-issuance-trust-row">(.*?)<div class="peer-issuance-trust-value">([^<]*)</div>',
        block, re.S):
        inner, total = m.group(1), m.group(2).strip()
        name = re.search(r'trust-name">([^<]*)<', inner)
        segs = []
        for sm in re.finditer(r'<i style="background:#[0-9a-fA-F]{6}">\s*</i>([^<]*)<', inner):
            label = sm.group(1).strip()
            pm = re.match(r"^(.+?)\s([\d.]+)\s亿（(\d+)%）$", label)
            if pm:
                segs.append([pm.group(1).replace("未知资产", "其他"), float(pm.group(2)), int(pm.group(3))])
        if name and segs:
            display = name.group(1)
            if display == "其他":
                display = f"其他渠道（{total.split('·')[-1].strip()}）" if "合并" in total else "其他渠道"
                total = " · ".join(p.strip() for p in m.group(2).split("·")[:2])
            trust.append({"name": display, "total": total, "segs": segs})

    top = []
    for m in re.finditer(r'<section class="peer-issuance-card">(.*?)</section>', block, re.S):
        inner = m.group(1)
        head = re.search(
            r'<h3>([^<]*)</h3>\s*<[^>]*>([^<]*)</[^>]*>\s*<[^>]*>([^<]*)</[^>]*>', inner, re.S)
        if not head:
            continue
        amt_terms = [x.strip() for x in head.group(3).split("·")]
        rows = []
        for rm in BAR_ROW_RE.finditer(inner):
            delta = rm.group("delta")
            move = re.search(r"([+-]?\d+)\s*亿）$", delta)
            direction = 0
            if move:
                direction = 1 if int(move.group(1)) > 0 else (-1 if int(move.group(1)) < 0 else 0)
            elif "新增" in delta:
                direction = 1
            rows.append([rm.group("label"), rm.group("amount"), float(rm.group("w")), delta, direction])
        if rows:
            top.append({
                "name": head.group(1), "cat": head.group(2).strip(),
                "amt": amt_terms[0], "terms": amt_terms[1] if len(amt_terms) > 1 else "",
                "rows": rows,
            })

    if not groups or not trust or not top:
        return None
    # 面板行数必须与源 HTML 一致，防止正则漏匹配后静默发一个缺行的手机版
    expected = len(re.findall(r'<div class="peer-issuance-bar-row">', block))
    got = len(groups) + sum(len(c["rows"]) for c in top)
    if got != expected:
        raise RuntimeError(f"同业发行行数不匹配: 源 {expected} 行, 解析到 {got} 行")
    colors = build_peer_colors(block)
    if not colors:
        raise RuntimeError("同业发行图例配色解析为空,手机版会退回内置兜底色导致与电脑端不一致")
    return {"groups": groups, "trust": trust, "top": top, "colors": colors}


# ---------------------------------------------------------------- meta

def build_meta(html: str, dashboard_path: Path) -> dict:
    snapshot = "—"
    m = re.search(r"(20\d{2})(\d{2})(\d{2})", dashboard_path.stem)
    if m:
        snapshot = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    asset_date = "—"
    am = re.search(r"白条消费[^<]*统计日\s*(20\d{2})-(\d{2})-(\d{2})", html)
    if am:
        asset_date = f"{am.group(2)}-{am.group(3)}"

    peer_date = "—"
    pm = re.search(r"数据更新至\s*(20\d{2})-(\d{2})-(\d{2})", html)
    if pm:
        peer_date = f"{pm.group(2)}-{pm.group(3)}"

    # 台账年份取 ITL 数据里出现过的最大年份，回退到看板文件名年份
    prog_year = int(m.group(1)) if m else 2026
    years = {int(y) for y in re.findall(r'"year"\s*:\s*"?(20\d{2})"?', html)}
    if years:
        prog_year = max(years)

    return {"snapshot": snapshot, "assetDate": asset_date, "peerDate": peer_date, "progYear": prog_year}


# ---------------------------------------------------------------- assemble

PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="format-detection" content="telephone=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="robots" content="noindex,nofollow">
<title>ABS 综合看板 · 手机版</title>
<style>
  html, body {{ height:100%; margin:0; padding:0; overflow:hidden; background:#f2f4f8; }}
  body {{ font-family:"PingFang SC","Microsoft YaHei","Helvetica Neue",Arial,sans-serif;
         -webkit-text-size-adjust:100%; -webkit-tap-highlight-color:transparent; }}
  *, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}
  #app {{ position:fixed; inset:0; }}
  .noscroll::-webkit-scrollbar {{ display:none; }}
  .noscroll {{ scrollbar-width:none; }}
  a {{ color:#1a3a5c; text-decoration:none; }}
  @keyframes mSheetUp {{ from {{ transform:translateY(100%); }} to {{ transform:translateY(0); }} }}
  @keyframes mFadeIn {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
  @keyframes mPageIn {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
</style>
</head>
<body>
<div id="app"></div>
<script id="abs-mobile-data">window.PROG_QUICK={prog_quick};window.ABS_MOBILE_DATA={inject};</script>
<script id="abs-mobile-app">{app_js}</script>
<script>window.ABS_MOBILE_MOUNT(document.getElementById('app'));</script>
</body>
</html>
"""


def build_mobile_html(dashboard_path: Path, out_path: Path | None = None) -> Path:
    dashboard_path = Path(dashboard_path).resolve()
    html = dashboard_path.read_text(encoding="utf-8")
    if not APP_JS.exists():
        raise FileNotFoundError(f"缺少手机端应用脚本: {APP_JS}")

    prog_quick = build_prog_quick(html)
    if not prog_quick:
        raise RuntimeError("机构画像数据为空,手机版生成中止")

    inject = {"meta": build_meta(html, dashboard_path)}
    asset = build_asset(html)
    peer = build_peer(html)
    missing = [name for name, val in (("消金资产", asset), ("同业发行", peer)) if val is None]
    if missing:
        raise RuntimeError("以下面板未能从看板中解析,手机版生成中止: " + "、".join(missing))
    inject["asset"] = asset
    inject["peer"] = peer

    page = PAGE.format(
        prog_quick=json.dumps(prog_quick, ensure_ascii=False, separators=(",", ":")),
        inject=json.dumps(inject, ensure_ascii=False, separators=(",", ":")),
        app_js=APP_JS.read_text(encoding="utf-8"),
    )

    out_path = Path(out_path) if out_path else dashboard_path.with_name(dashboard_path.stem + "_手机版.html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")

    print(f"[mobile] 机构 {len(prog_quick)} 家 · 消金 KPI {len(asset['kpis'])} 项 · "
          f"同业集团 {len(peer['groups'])} 个 / 渠道 {len(peer['trust'])} 家 / Top {len(peer['top'])} · "
          f"配色 {len(peer['colors'])} 组(取自电脑端图例)")
    print(f"[mobile] 产物: {out_path}  ({out_path.stat().st_size / 1024:.0f} KB)")
    return out_path


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    src = Path(sys.argv[1])
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    build_mobile_html(src, dest)


if __name__ == "__main__":
    main()
