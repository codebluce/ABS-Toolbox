"""fig4_hbr_matrix.py — HBR风格:资产类型 × Top机构矩阵热图

HBR 样式:Slab Serif 标题,Cream 背景,Crimson 强调色,sidebar 关键洞察
洞察:看机构偏好哪些资产,谁专一谁多元
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_data import load_wxy_df

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle

# Windows 字体回退
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# HBR 色板
HBR_CREAM = '#FDFBF7'
HBR_CHARCOAL = '#333333'
HBR_CRIMSON = '#A6192E'
HBR_GRAY = '#666666'
HBR_LIGHT_GRAY = '#D9D9D9'

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      '..', '..', 'deliverables', 'dashboards', '02_history',
                      'lab_viz', 'fig4_hbr_matrix.png')


def main():
    df = load_wxy_df()
    # Top 8 机构 × Top 6 资产类型
    top_inst = df['institution'].value_counts().head(8).index.tolist()
    top_assets = df['asset_type'].value_counts().head(6).index.tolist()
    sub = df[df['institution'].isin(top_inst) & df['asset_type'].isin(top_assets)].copy()

    # 透视:每个 cell = 该机构在该资产的申购规模合计(亿)
    pivot = sub.groupby(['institution', 'asset_type'])['size'].sum().unstack(fill_value=0)
    pivot = pivot.reindex(index=top_inst, columns=top_assets, fill_value=0)

    # 布局:左侧主图 + 右侧 sidebar
    fig = plt.figure(figsize=(13, 7), facecolor=HBR_CREAM)
    gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1.1], wspace=0.18)
    ax = fig.add_subplot(gs[0, 0])
    ax_sidebar = fig.add_subplot(gs[0, 1])
    ax_sidebar.axis('off')

    # 热图(灰阶 + Crimson 强调大值)
    data = pivot.values
    vmax = data.max()
    # 自定义 colormap:白→浅灰→深灰,大值用 Crimson
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        'hbr_gray_crimson',
        [(0, '#FFFFFF'), (0.3, '#E8E8E8'), (0.7, '#888888'),
         (0.85, '#444444'), (1, HBR_CRIMSON)]
    )

    im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=0, vmax=vmax)

    # 标注每个 cell 的数值
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            if v > 0:
                color = 'white' if v > vmax * 0.5 else HBR_CHARCOAL
                ax.text(j, i, f'{v:.1f}', ha='center', va='center',
                        fontsize=9, color=color, fontweight='bold' if v > vmax * 0.7 else 'normal')

    # 轴标签
    ax.set_xticks(np.arange(len(top_assets)))
    ax.set_yticks(np.arange(len(top_inst)))
    ax.set_xticklabels(top_assets, fontsize=9, color=HBR_CHARCOAL, rotation=0)
    ax.set_yticklabels(top_inst, fontsize=9, color=HBR_CHARCOAL)
    ax.tick_params(axis='both', length=0)

    # 移除 spine
    for spine in ax.spines.values():
        spine.set_visible(False)

    # 标题
    ax.set_title('Top 8 机构 × Top 6 资产类型申购规模矩阵',
                 fontsize=13, color=HBR_CHARCOAL, fontweight='bold',
                 pad=12, loc='left')

    # colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
    cbar.set_label('申购规模合计 (亿元)', fontsize=9, color=HBR_GRAY)
    cbar.ax.tick_params(labelsize=8, colors=HBR_GRAY, length=0)
    cbar.outline.set_visible(False)

    # Sidebar:关键洞察
    ax_sidebar.text(0, 0.95, '关键洞察', fontsize=12, color=HBR_CHARCOAL,
                    fontweight='bold', transform=ax_sidebar.transAxes)
    ax_sidebar.plot([0, 0.85], [0.92, 0.92], color=HBR_CRIMSON,
                    linewidth=2, transform=ax_sidebar.transAxes)

    # 计算洞察
    inst_total = pivot.sum(axis=1)
    inst_diversity = (pivot > 0).sum(axis=1)
    most_diverse = inst_diversity.idxmax()
    most_diverse_n = inst_diversity.max()
    biggest_inst = inst_total.idxmax()
    biggest_amt = inst_total.max()

    insights = [
        f'• {biggest_inst} 申购规模最大',
        f'  合计 {biggest_amt:.1f} 亿元',
        f'',
        f'• {most_diverse} 资产覆盖最广',
        f'  跨 {most_diverse_n} 个资产类型',
        f'',
        f'• 矩阵稀疏度:{(data == 0).sum() / data.size * 100:.0f}%',
        f'  反映机构资产偏好分化',
        f'',
        f'• Crimson 单元 = 高集中度',
        f'  规模 > {vmax * 0.7:.1f} 亿的强参与',
    ]
    for i, line in enumerate(insights):
        ax_sidebar.text(0, 0.85 - i * 0.085, line,
                        fontsize=9, color=HBR_CHARCOAL,
                        transform=ax_sidebar.transAxes,
                        family='sans-serif')

    plt.figtext(0.5, 0.02,
                '数据来源:0703 定稿台账 957 笔申购 | HBR 风格可视化',
                ha='center', fontsize=8, color=HBR_GRAY, style='italic')

    plt.savefig(OUTPUT, dpi=150, bbox_inches='tight', facecolor=HBR_CREAM)
    print(f'已保存: {OUTPUT}')


if __name__ == '__main__':
    main()
