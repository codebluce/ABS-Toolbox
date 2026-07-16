"""ABS 投资台账面板生成器（综合看板第 4 个 Tab）

数据驱动：复用 abs_common.load_and_filter 取得穿透优先口径的逐条投资记录
（已剔除自持 / 黑名单机构、已做机构名归并、已纠正 2025→2026 簿记年份），
序列化为 JSON 内嵌进面板，配 itl_panel.js（vanilla）实现前端多维筛选统计，
并配 itl_chat.js 提供右下角「智能问答」悬浮球（本地语义解析·离线·数据不出内网·联动面板）。

多年份支持（2024/2025/2026）：三年台账表结构互不相同，各走独立适配路径：
  - 2026：当前业务年台账，走 load_and_filter 默认路径（含 2025→2026 日期纠错）
  - 2025：25 列表结构与 2026 完全一致，走同一 load_and_filter，但关闭日期纠错
          （否则 2025 年的真实日期会被误"纠正"成 2026 年）
  - 2024：仅 18 列，无穿透机构/份额分列（无 WXY 双轨），无国股CD（故无利差），
          走独立的轻量解析（不经过 load_and_filter/25 列校验）
三年记录统一映射到同一套字段（asset/proj/mgr/.../year），前端合并为一份语料供智能问答
跨年问答，同时按年份切成三个独立子 Tab 供筛选统计浏览。

对外接口（与其它 gen_* 模块一致）：
  compute_data(xlsx_path)        -> dict{records, xlsx_basename, count}（单年，向后兼容 CLI 预览）
  compute_data_multi_year(paths) -> dict{by_year, all_records}（paths: {'2026':path,'2025':path,'2024':path}）
  render_body(data)              -> str（单年面板 body HTML，CLI 预览用）
  render_body_multi_year(data)   -> list[(year, body_html)]（供 gen_integrated_dashboard 接三个子 Tab）
  LEDGER_CSS                     -> str（面板 + Chatbox 样式，供 gen_integrated_dashboard 拼接）

筛选字段：D资产类型 / P分层 / S评级（多选）· G管理人 / H承销商 / I托管行 / U认购机构（关键词联想多选）
          · L簿记时间（区间）· V认购份额（区间）
统计口径：字段内多选取「或」，跨字段取「且」
输出视图：分组统计（可排序排行 + 份额占比条）/ 透视表（行×列交叉）/ 明细清单，均支持导出 CSV
"""
import os
import sys
import json

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from abs_common import (
    load_and_filter,
    filter_excluded_institutions,
    normalize_investor_name,
    NON_NUMERIC_COST_VALS,
    RESOLVED_COST_COL,   # 实际成本
    RESOLVED_INST_COL,   # 实际机构
    RESOLVED_SHARE_COL,  # 实际份额
)

# ── 面板样式 / 逻辑从同目录资源文件读取（单一来源，便于维护）──────
_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_DIR, 'itl_panel.css'), encoding='utf-8') as _f:
    LEDGER_CSS = _f.read()
with open(os.path.join(_DIR, 'itl_panel.js'), encoding='utf-8') as _f:
    LEDGER_JS = _f.read()
with open(os.path.join(_DIR, 'itl_chat.css'), encoding='utf-8') as _f:
    CHAT_CSS = _f.read()
with open(os.path.join(_DIR, 'itl_chat.js'), encoding='utf-8') as _f:
    CHAT_JS = _f.read()

# 综合看板拼接时用：面板样式 + Chatbox 样式一起进全局 <style>
LEDGER_CSS = LEDGER_CSS + '\n' + CHAT_CSS


def _s(v):
    """转字符串并 strip，空 / NaN 归 None"""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    return s if s else None


def _n(v):
    """转 float，NaN / 非数值归 None"""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if pd.isna(f):
        return None
    return f


def _records_from_25col_df(df, year_tag):
    """25 列标准结构（2026/2025 通用）→ 逐条投资记录列表"""
    records = []
    for _, row in df.iterrows():
        cost = _n(row.get(RESOLVED_COST_COL))
        cd = _n(row.get('国股CD'))
        date = row.get('簿记时间')
        spread = round(cost - cd, 6) if (cost is not None and cd is not None) else None
        records.append({
            'asset':       _s(row.get('资产类型')),
            'proj':        _s(row.get('项目名称')),
            'venue':       _s(row.get('发行场所')),
            'mgr':         _s(row.get('计划管理人')),
            'underwriter': _s(row.get('联席承销商')),
            'custodian':   _s(row.get('托管行')),
            'scale':       _n(row.get('规模')),
            'tenor':       _s(row.get('期限')),
            'date':        date.strftime('%Y-%m-%d') if pd.notna(date) else None,
            'layer':       _s(row.get('分层情况')),
            'rating':      _s(row.get('评级')),
            'inst':        _s(row.get(RESOLVED_INST_COL)),
            'cost':        cost,
            'share':       _n(row.get(RESOLVED_SHARE_COL)),
            'cd':          cd,
            'spread':      spread,
            'year':        year_tag,
        })
    return records


def compute_data(xlsx_path, preprocessed_path=None):
    """读取台账 → 逐条投资记录（穿透优先口径），返回可序列化 dict（单年，CLI 预览用，年份=2026）"""
    df, dfa, tmp_path, _tenor = load_and_filter(xlsx_path, preprocessed_path=preprocessed_path)
    # 共享 tmp(preprocessed_path 传入)由创建方统一删,不在此删
    if preprocessed_path is None:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    records = _records_from_25col_df(df, '2026')

    print(f'投资台账：{len(records)} 条投资记录，'
          f'认购份额合计 {sum(r["share"] or 0 for r in records):.2f} 亿')

    return {
        'records': records,
        'xlsx_basename': os.path.basename(xlsx_path),
        'count': len(records),
    }


def _compute_flat_year(xlsx_path, year_tag, mgr_col, has_underwriter, has_venue, has_cd, label):
    """2024/2025 共用解析路径：均无合并单元格（逐行数据自成一体，无需 forward-fill），
    均为单层 认购机构/认购份额（无 2026 式的表面/穿透 WXY 双轨），故不走 abs_common.load_and_filter
    （那套逻辑硬编码 25 列 A~Y 位置且假设合并单元格结构，与这两年的真实文件结构不符）。

    Args:
        mgr_col: 计划管理人列名（2024 是"计划管理人/主承"合并列，2025 是"计划管理人"）
        has_underwriter/has_venue/has_cd: 该年份是否有联席承销商/发行场所/国股CD列
    """
    df = pd.read_excel(xlsx_path, engine='openpyxl', header=0)
    # 簿记时间列存在个别单元格丢失日期格式、被读成裸数字（Excel 序列日期，如 45463）的情况；
    # 若直接丢给 pd.to_datetime，裸整数会被当成"纳秒时间戳"误判为 1970-01-01，而非真实日期或 NaT。
    # 按 Excel 1900 日期系统（起点 1899-12-30）解码这类数字，其余值仍走正常解析，无法解析的归 NaT（date 记为 None）
    def _parse_booking_date(v):
        if isinstance(v, (int, float)) and not isinstance(v, bool) and pd.notna(v):
            return pd.Timestamp('1899-12-30') + pd.Timedelta(days=v)
        return pd.to_datetime(v, errors='coerce')
    df['簿记时间'] = df['簿记时间'].apply(_parse_booking_date)

    role_cols = [c for c in [mgr_col, '联席承销商', '托管行', '认购机构'] if c in df.columns]
    df = filter_excluded_institutions(df, role_cols=role_cols, label=label)

    # 自持/不出表标记：与 2026 的 NON_NUMERIC_COST_VALS 口径一致，成本或认购机构列命中即剔除
    def _is_self_hold(row):
        for col in ('成本', '认购机构'):
            v = row.get(col)
            if v is not None and str(v).strip() in NON_NUMERIC_COST_VALS:
                return True
        return False
    df = df[~df.apply(_is_self_hold, axis=1)]

    before = df['认购机构'].nunique()
    df['认购机构'] = df['认购机构'].apply(normalize_investor_name)
    after = df['认购机构'].nunique()
    if before != after:
        print(f'[MERGE] {label}机构名归并：{before} → {after}（减少 {before - after} 个变体）')

    records = []
    for _, row in df.iterrows():
        date = row.get('簿记时间')
        cost = _n(row.get('成本'))
        cd = _n(row.get('国股CD')) if has_cd else None
        spread = round(cost - cd, 6) if (has_cd and cost is not None and cd is not None) else None
        records.append({
            'asset':       _s(row.get('资产类型')),
            'proj':        _s(row.get('项目名称')),
            'venue':       _s(row.get('发行场所')) if has_venue else None,
            'mgr':         _s(row.get(mgr_col)),
            'underwriter': _s(row.get('联席承销商')) if has_underwriter else None,
            'custodian':   _s(row.get('托管行')),
            'scale':       _n(row.get('规模')),
            'tenor':       _s(row.get('期限')),
            'date':        date.strftime('%Y-%m-%d') if pd.notna(date) else None,
            'layer':       _s(row.get('分层情况')),
            'rating':      _s(row.get('评级')),
            'inst':        _s(row.get('认购机构')),
            'cost':        cost,
            'share':       _n(row.get('认购份额')),
            'cd':          cd,
            'spread':      spread,
            'year':        year_tag,
        })

    print(f'投资台账({year_tag})：{len(records)} 条投资记录，'
          f'认购份额合计 {sum(r["share"] or 0 for r in records):.2f} 亿'
          + ('' if has_cd else '（无国股CD/无穿透分列，利差恒为空）'))

    return {
        'records': records,
        'xlsx_basename': os.path.basename(xlsx_path),
        'count': len(records),
    }


def compute_data_2025(xlsx_path):
    """2025 年历史台账：24 个有效列（+2 个空列），无合并单元格、单层 认购机构/认购份额（无穿透分列），
    但有国股CD/发行场所/联席承销商，可正常计算利差。列结构与 2026 的 25 列 A~Y 布局并不一致，
    独立解析，不走 abs_common.load_and_filter。"""
    return _compute_flat_year(xlsx_path, '2025', mgr_col='计划管理人',
                               has_underwriter=True, has_venue=True, has_cd=True, label='2025台账')


def compute_data_2024(xlsx_path):
    """2024 年历史台账：仅 18 列，无合并单元格、单层 认购机构/认购份额、无国股CD（利差恒为空）、
    无发行场所、无独立联席承销商列（计划管理人与主承合并为一列，整体映射进 mgr）。"""
    return _compute_flat_year(xlsx_path, '2024', mgr_col='计划管理人/主承',
                               has_underwriter=False, has_venue=False, has_cd=False, label='2024台账')


_YEAR_COMPUTE = {
    '2026': compute_data,
    '2025': compute_data_2025,
    '2024': compute_data_2024,
}


def compute_data_multi_year(year_paths, preprocessed_path=None):
    """paths: {'2026': path, '2025': path, '2024': path}（可只传部分年份，缺失年份 WARN 后跳过）

    preprocessed_path: 2026 台账的共享预处理产物(可选)。2025/2024 走 _compute_flat_year,
        不经 preprocess,不受影响。

    返回 {'by_year': {year: {records,xlsx_basename,count}}, 'all_records': [...三年合并，供智能问答跨年语料]}
    """
    by_year = {}
    for year in ('2026', '2025', '2024'):
        path = year_paths.get(year)
        if not path or not os.path.exists(path):
            print(f'[WARN] 投资台账 {year} 年源文件缺失，已跳过: {path or "<未配置>"}')
            continue
        basename = os.path.basename(path)
        if year not in basename:
            print(f'[WARN] 投资台账 {year} 年源文件名未包含年份 {year}，请确认是否错配: {basename}')
        # 2026 走 compute_data(支持 preprocessed_path 注入);2025/2024 走 flat 解析,无需注入
        if year == '2026':
            by_year[year] = compute_data(path, preprocessed_path=preprocessed_path)
        else:
            by_year[year] = _YEAR_COMPUTE[year](path)

    all_records = []
    for year in ('2026', '2025', '2024'):
        if year in by_year:
            all_records.extend(by_year[year]['records'])

    summary = ', '.join(f'{y}年{by_year[y]["count"]}条' for y in ('2026', '2025', '2024') if y in by_year)
    print(f'投资台账(全年份汇总)：{len(all_records)} 条投资记录（{summary}）')

    return {'by_year': by_year, 'all_records': all_records}


def render_body(data):
    """返回面板 body HTML（内嵌数据 + JS，自动初始化到 #itl-root）"""
    payload = json.dumps(data['records'], ensure_ascii=False, separators=(',', ':'))
    source = json.dumps(data['xlsx_basename'], ensure_ascii=False)
    return (
        '<div id="itl-root"></div>\n'
        f'<script>window.ITL_DATA={payload};window.ITL_SOURCE={source};</script>\n'
        f'<script>{LEDGER_JS}</script>\n'
        '<script>ITL.build(document.getElementById("itl-root"));</script>\n'
        f'<script>{CHAT_JS}</script>'
    )


def render_body_multi_year(data):
    """返回 [(year, body_html), ...]，每个年份一个独立面板 body，供接三个子 Tab

    每年一份独立命名空间的 ITL 实例（ITL_2026/ITL_2025/ITL_2024，互不干扰，各自的筛选状态独立），
    注册进全局 window.ITL_REG 供智能问答按年份联动；window.ITL_ALL_DATA 为三年合并语料，
    智能问答据此跨年份回答，不受当前激活的年份子 Tab 限制。
    """
    by_year = data['by_year']
    years_present = [y for y in ('2026', '2025', '2024') if y in by_year]
    all_payload = json.dumps(data['all_records'], ensure_ascii=False, separators=(',', ':'))

    chunks = []
    for i, year in enumerate(years_present):
        yd = by_year[year]
        payload = json.dumps(yd['records'], ensure_ascii=False, separators=(',', ':'))
        source = json.dumps(yd['xlsx_basename'], ensure_ascii=False)
        ns_js = (
            LEDGER_JS
            .replace('window.ITL_DATA', f'window.ITL_DATA_{year}')
            .replace('window.ITL_SOURCE', f'window.ITL_SOURCE_{year}')
            .replace('window.ITL =', f'window.ITL_{year} =')
        )
        parts = []
        if i == 0:
            parts.append(f'<script>window.ITL_ALL_DATA={all_payload};</script>')
        parts.append(f'<div id="itl-root-{year}"></div>')
        parts.append(f'<script>window.ITL_DATA_{year}={payload};window.ITL_SOURCE_{year}={source};</script>')
        parts.append(f'<script>{ns_js}</script>')
        parts.append(
            f'<script>ITL_{year}.build(document.getElementById("itl-root-{year}"));'
            f'window.ITL_REG=window.ITL_REG||{{}};window.ITL_REG["{year}"]=ITL_{year};</script>'
        )
        if i == 0:
            parts.append(f'<script>{CHAT_JS}</script>')
        chunks.append((year, '\n'.join(parts)))
    return chunks


# ── 独立预览（不进综合看板时，单独生成一个可打开的 HTML）──────────
def main():
    import argparse
    from datetime import datetime
    p = argparse.ArgumentParser(description='ABS 投资台账面板（独立预览）')
    p.add_argument('xlsx_path')
    p.add_argument('output_path', nargs='?', default=None)
    args = p.parse_args()

    data = compute_data(args.xlsx_path)
    out = args.output_path
    if not out:
        date_tag = datetime.now().strftime('%Y%m%d')
        d = os.path.join(_DIR, '..', 'deliverables', 'dashboards', '01_latest')
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, f'{date_tag}_投资台账.html')

    html = (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        '<title>ABS 投资台账</title><style>body{margin:0;background:#eef1f5;}\n'
        f'{LEDGER_CSS}</style></head><body>\n'
        f'{render_body(data)}\n</body></html>'
    )
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'[完成] {out} ({os.path.getsize(out) / 1024:.1f} KB)')


if __name__ == '__main__':
    main()
