"""fig4_new: 理财子 × 资产类型 投资规模矩阵(HBR风格)

新设计:
- 筛选:发行场所 ∈ {上交所, 深交所, 银行间}
- 纵轴:所有理财子(U列含"理财"关键词)
- 横轴:6类资产(赊销白条/现金贷/企业主贷/保理/金采/其他)
- 金额:V列认购份额合计(亿元)
- 标题:理财子×资产类型投资规模矩阵
"""
import os, sys
# 同时把 scripts/ 和 lab/ 加入 path
_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _SCRIPTS_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from abs_common import preprocess_xlsx_for_pandas

# Windows 中文字体
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# HBR 色板
HBR_CREAM = '#FDFBF7'
HBR_CHARCOAL = '#333333'
HBR_CRIMSON = '#A6192E'
HBR_GRAY = '#666666'
HBR_LIGHT_GRAY = '#D9D9D9'

LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      '..', '..', 'deliverables', 'ledger', '03_final',
                      '2026年ABS发行台账-0703-定稿.xlsx')
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      '..', '..', 'deliverables', 'dashboards', '02_history',
                      'lab_viz', 'fig4_new_welizhi_matrix.png')


def load_all_rows():
    """加载全行数据(不只WXY),含发行场所/资产类型/认购机构/认购份额"""
    tmp = preprocess_xlsx_for_pandas(LEDGER)
    raw = pd.read_excel(tmp, header=None)
    headers = raw.iloc[0].tolist()
    df = raw.iloc[2:].copy()
    df.columns = [str(h).strip() if h is not None and str(h).strip() else f'col{i}'
                  for i, h in enumerate(headers)]

    # 类型转换
    df['认购份额'] = pd.to_numeric(df['认购份额'], errors='coerce')
    df = df[df['发行场所'].notna() & df['资产类型'].notna() & df['认购机构'].notna()].copy()
    df = df[df['认购份额'].notna() & (df['认购份额'] > 0) & (df['认购份额'] < 100)].copy()

    return df[['发行场所', '资产类型', '认购机构', '认购份额']].reset_index(drop=True)


def classify_asset(asset_name):
    """资产类型分类映射"""
    name = str(asset_name).strip()
    # 现金贷:含金条/白取/金条&白取混发
    if any(kw in name for kw in ['金条', '白取', '金条&白取混发', '现金贷']):
        return '现金贷'
    # 企业主贷:信托企业主贷/小贷企业主贷
    if '企业主贷' in name:
        return '企业主贷'
    # 保理
    if '保理' in name:
        return '保理'
    # 金采
    if '金采' in name:
        return '金采'
    # 赊销白条
    if '赊销白条' in name or '白条' in name:
        return '赊销白条'
    # 其他
    return '其他'


def is_wealth_management_sub(inst_name):
    """判断是否为理财子(含'理财'关键词,排除银行/信托/证券/基金/资管/保险等)"""
    name = str(inst_name).strip()
    if '理财' not in name:
        return False
    # 排除:银行本部、信托、证券、基金、资管、保险、私募、自营等
    exclude_kw = ['银行', '信托', '证券', '基金', '资管', '保险', '私募', '自营',
                  '资产', '财富', '理财有限责任公司']
    # 理财子通常命名包含 "XX理财" 且不含上述排除词
    for kw in exclude_kw:
        if kw in name and kw != '理财':
            return False
    return True


def main():
    df = load_all_rows()
    print(f'总行数: {len(df)}')

    # 1. 筛选发行场所
    df = df[df['发行场所'].isin(['上交所', '深交所', '银行间'])].copy()
    print(f'筛选发行场所(上交所/深交所/银行间)后: {len(df)}')

    # 2. 资产类型分类
    df['资产分类'] = df['资产类型'].apply(classify_asset)

    # 3. 筛选理财子
    df = df[df['认购机构'].apply(is_wealth_management_sub)].copy()
    print(f'筛选理财子后: {len(df)}')

    # 理财子列表(按总规模降序)
    inst_total = df.groupby('认购机构')['认购份额'].sum().sort_values(ascending=False)
    print(f'\n理财子数量: {len(inst_total)}')
    print(f'理财子列表:\n{inst_total}')

    # 资产分类顺序(用户指定)
    asset_order = ['保理', '赊销白条', '现金贷', '金采', '企业主贷', '其他']

    # 透视表:行=理财子,列=资产分类,值=认购份额合计
    pivot = df.groupby(['认购机构', '资产分类'])['认购份额'].sum().unstack(fill_value=0)
    pivot = pivot.reindex(index=inst_total.index, columns=asset_order, fill_value=0)

    print(f'\n=== 透视表 ===')
    print(pivot)

    # 绘图:单栏全宽主图(无 sidebar)
    fig, ax = plt.subplots(figsize=(11, max(7, len(pivot) * 0.45 + 2)),
                           facecolor=HBR_CREAM)

    data = pivot.values
    vmax = data.max()

    # HBR colormap: 白→浅灰→深灰→Crimson
    cmap = LinearSegmentedColormap.from_list(
        'hbr_gray_crimson',
        [(0, '#FFFFFF'), (0.3, '#E8E8E8'), (0.7, '#888888'),
         (0.85, '#444444'), (1, HBR_CRIMSON)]
    )

    im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=0, vmax=vmax)

    # 标注数值
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            if v > 0:
                color = 'white' if v > vmax * 0.5 else HBR_CHARCOAL
                weight = 'bold' if v > vmax * 0.7 else 'normal'
                ax.text(j, i, f'{v:.1f}', ha='center', va='center',
                        fontsize=9, color=color, fontweight=weight)

    # 轴
    ax.set_xticks(np.arange(len(asset_order)))
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_xticklabels(asset_order, fontsize=10, color=HBR_CHARCOAL, rotation=0)
    ax.set_yticklabels(pivot.index, fontsize=9, color=HBR_CHARCOAL)
    ax.tick_params(axis='both', length=0)

    for spine in ax.spines.values():
        spine.set_visible(False)

    # 标题(纯标题,无副标题,避免与图像重叠)
    ax.set_title('理财子×资产类型投资规模矩阵',
                 fontsize=14, color=HBR_CHARCOAL, fontweight='bold',
                 pad=12, loc='left')

    # colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
    cbar.set_label('认购份额合计 (亿元)', fontsize=9, color=HBR_GRAY)
    cbar.ax.tick_params(labelsize=8, colors=HBR_GRAY, length=0)
    cbar.outline.set_visible(False)

    # 底部备注(发行场所 + 数据来源)
    plt.figtext(0.5, 0.02,
                '发行场所:上交所 / 深交所 / 银行间  |  金额单位:亿元(V列认购份额合计)  |  '
                '数据来源:0703 定稿台账',
                ha='center', fontsize=8.5, color=HBR_GRAY, style='italic')

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(OUTPUT, dpi=150, bbox_inches='tight', facecolor=HBR_CREAM)
    print(f'\n已保存: {OUTPUT}')


if __name__ == '__main__':
    main()
