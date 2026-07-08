"""ABS 投资台账面板生成器（综合看板第 4 个 Tab）

数据驱动：复用 abs_common.load_and_filter 取得穿透优先口径的逐条投资记录
（已剔除自持 / 黑名单机构、已做机构名归并、已纠正 2025→2026 簿记年份），
序列化为 JSON 内嵌进面板，配 itl_panel.js（vanilla）实现前端多维筛选统计。

对外接口（与其它 gen_* 模块一致）：
  compute_data(xlsx_path)  -> dict{records, xlsx_basename, count}
  render_body(data)        -> str（面板 body HTML，含内嵌数据 + JS）
  LEDGER_CSS               -> str（面板样式，供 gen_integrated_dashboard 拼接）

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


def compute_data(xlsx_path):
    """读取台账 → 逐条投资记录（穿透优先口径），返回可序列化 dict"""
    df, dfa, tmp_path, _tenor = load_and_filter(xlsx_path)
    try:
        os.remove(tmp_path)
    except OSError:
        pass

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
        })

    print(f'投资台账：{len(records)} 条投资记录，'
          f'认购份额合计 {sum(r["share"] or 0 for r in records):.2f} 亿')

    return {
        'records': records,
        'xlsx_basename': os.path.basename(xlsx_path),
        'count': len(records),
    }


def render_body(data):
    """返回面板 body HTML（内嵌数据 + JS，自动初始化到 #itl-root）"""
    payload = json.dumps(data['records'], ensure_ascii=False, separators=(',', ':'))
    source = json.dumps(data['xlsx_basename'], ensure_ascii=False)
    return (
        '<div id="itl-root"></div>\n'
        f'<script>window.ITL_DATA={payload};window.ITL_SOURCE={source};</script>\n'
        f'<script>{LEDGER_JS}</script>\n'
        '<script>ITL.build(document.getElementById("itl-root"));</script>'
    )


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
