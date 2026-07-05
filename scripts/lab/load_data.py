"""lab/load_data.py — 加载 0703 定稿台账 WXY 数据

输出 pandas DataFrame,字段:
  project, category, asset_type, book_date, layer, cost, subscriber, rate, institution, size
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import pandas as pd
from abs_common import preprocess_xlsx_for_pandas

LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      '..', '..', 'deliverables', 'ledger', '03_final',
                      '2026年ABS发行台账-0703-定稿.xlsx')


def load_wxy_df():
    # preprocess_xlsx_for_pandas 返回临时文件路径,需再用 pandas 读
    tmp = preprocess_xlsx_for_pandas(LEDGER)
    raw = pd.read_excel(tmp, header=None)
    # Row1 是表头,数据从 Row3 起(0-indexed: row 0 是表头,row 1 是示例数据行,row 2 起是真实数据)
    headers = raw.iloc[0].tolist()
    df = raw.iloc[2:].copy()
    df.columns = [str(h).strip() if h is not None and str(h).strip() else f'col{i}'
                  for i, h in enumerate(headers)]

    # 筛选有 WXY 的行
    df = df[df['申购利率'].notna() & df['穿透机构'].notna()].copy()

    # 类型转换
    df['申购利率'] = pd.to_numeric(df['申购利率'], errors='coerce')
    df['申购规模'] = pd.to_numeric(df['申购规模'], errors='coerce')
    df['成本'] = pd.to_numeric(df['成本'], errors='coerce')
    df['簿记时间'] = pd.to_datetime(df['簿记时间'], errors='coerce')

    # 过滤合理范围
    df = df[(df['申购利率'] > 0) & (df['申购利率'] < 0.05)].copy()
    df = df[(df['申购规模'] > 0) & (df['申购规模'] < 50)].copy()

    # 重命名
    df = df.rename(columns={
        '项目名称': 'project', '类别': 'category', '资产类型': 'asset_type',
        '簿记时间': 'book_date', '分层情况': 'layer', '成本': 'cost',
        '认购机构': 'subscriber', '申购利率': 'rate', '穿透机构': 'institution',
        '申购规模': 'size',
    })

    # 提取月份
    df['month'] = df['book_date'].dt.month
    df['rate_pct'] = df['rate'] * 100  # 转百分比

    return df[['project', 'category', 'asset_type', 'book_date', 'month',
               'layer', 'cost', 'subscriber', 'rate', 'rate_pct',
               'institution', 'size']].reset_index(drop=True)


if __name__ == '__main__':
    df = load_wxy_df()
    print(f'总记录数: {len(df)}')
    print(f'\n=== 类别 ===\n{df["category"].value_counts()}')
    print(f'\n=== 资产类型 top10 ===\n{df["asset_type"].value_counts().head(10)}')
    print(f'\n=== 分层 ===\n{df["layer"].value_counts()}')
    print(f'\n=== 穿透机构 top15 ===\n{df["institution"].value_counts().head(15)}')
    print(f'\n=== 利率/规模统计 ===')
    print(df[['rate_pct', 'size']].describe())
    print(f'\n=== 月份分布 ===\n{df["month"].value_counts().sort_index()}')
