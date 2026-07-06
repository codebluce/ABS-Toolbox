"""fig5_hbr_composite.py — HBR风格:理财子投资画像

HBR 样式:主图(散点+规模编码),纵轴=理财子(以"理财"结尾的机构)
洞察:理财子申购规模 × 平均申购利率
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_data import load_wxy_df

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

HBR_CREAM = '#FDFBF7'
HBR_CHARCOAL = '#333333'
HBR_CRIMSON = '#A6192E'
HBR_GRAY = '#666666'
HBR_LIGHT_GRAY = '#D9D9D9'

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      '..', '..', 'deliverables', 'dashboards', '02_history',
                      'lab_viz', 'fig5_hbr_composite.png')


def main():
    df = load_wxy_df()
    # 筛选理财子(以"理财"结尾的机构)
    df_wlz = df[df['institution'].str.endswith('理财')].copy()

    # 机构汇总
    summary = df_wlz.groupby('institution').agg(
        total_size=('size', 'sum'),
        mean_rate=('rate_pct', 'mean'),
        n=('size', 'count'),
    ).reset_index()
    summary = summary.sort_values('total_size', ascending=True)

    # 高度与 fig4 矩阵实际产出对齐(21 家机构 → ~13 英寸,fig4 实际高度)
    # 宽度 9 英寸(并排时缩小,留间距)
    fig_height = max(7, len(summary) * 0.62 + 1)
    fig = plt.figure(figsize=(9, fig_height), facecolor=HBR_CREAM)
    ax = fig.add_subplot(111)

    # 散点:横轴=平均利率,纵轴=机构(按规模升序),点大小=总规模
    sizes = (summary['total_size'] / summary['total_size'].max() * 800 + 80).values
    colors = []
    for _, r in summary.iterrows():
        # 量大价低 = Crimson(划算)
        # 量小价高 = 灰(贵)
        if r['total_size'] >= summary['total_size'].median() and r['mean_rate'] <= summary['mean_rate'].median():
            colors.append(HBR_CRIMSON)
        elif r['total_size'] < summary['total_size'].median() and r['mean_rate'] > summary['mean_rate'].median():
            colors.append(HBR_LIGHT_GRAY)
        else:
            colors.append(HBR_GRAY)

    scatter = ax.scatter(summary['mean_rate'], range(len(summary)),
                         s=sizes, c=colors, alpha=0.75,
                         edgecolors=HBR_CHARCOAL, linewidth=0.8, zorder=3)

    # 标注每个点的规模
    for i, (_, r) in enumerate(summary.iterrows()):
        ax.text(r['mean_rate'] + 0.02, i, f'{r["total_size"]:.1f}亿',
                va='center', fontsize=8, color=HBR_CHARCOAL)

    # 中位线
    median_rate = summary['mean_rate'].median()
    ax.axvline(median_rate, color=HBR_CRIMSON, linestyle='--',
               linewidth=1, alpha=0.5)
    ax.text(median_rate, len(summary) - 0.5,
            f' 利率中位数 {median_rate:.2f}%',
            fontsize=8, color=HBR_CRIMSON, va='top', style='italic')

    ax.set_yticks(range(len(summary)))
    ax.set_yticklabels(summary['institution'].values,
                       fontsize=11, color=HBR_CHARCOAL)
    ax.set_xlabel('平均申购利率 (%)', fontsize=12, color=HBR_CHARCOAL)
    ax.set_title('理财子投资画像:申购规模 × 平均申购利率',
                 fontsize=14, color=HBR_CHARCOAL, fontweight='bold',
                 pad=12, loc='left')

    # 虚线网格(主+次,加密)
    ax.grid(True, which='major', linestyle='--', linewidth=0.6,
            color=HBR_LIGHT_GRAY, alpha=0.8, zorder=1)
    ax.grid(True, which='minor', linestyle=':', linewidth=0.4,
            color=HBR_LIGHT_GRAY, alpha=0.5, zorder=1)
    ax.set_axisbelow(True)
    ax.minorticks_on()

    # 样式
    for spine_name in ['top', 'right']:
        ax.spines[spine_name].set_visible(False)
    ax.spines['left'].set_color(HBR_GRAY)
    ax.spines['bottom'].set_color(HBR_GRAY)
    ax.tick_params(direction='in', colors=HBR_GRAY, labelsize=11, length=3)

    # range frame + 横轴步长 0.05
    import matplotlib.ticker as mticker
    x_min, x_max = summary['mean_rate'].min(), summary['mean_rate'].max()
    ax.set_xlim(x_min - 0.05, x_max + 0.15)
    ax.spines['bottom'].set_bounds(x_min, x_max)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(0.05))

    # 图例(点大小说明)
    legend_sizes = [2, 5, 10, 20]
    for i, s in enumerate(legend_sizes):
        ax.scatter([], [], s=s / summary['total_size'].max() * 800 + 80,
                   c=HBR_GRAY, edgecolors=HBR_CHARCOAL, linewidth=0.5,
                   label=f'{s}亿')
    leg = ax.legend(loc='lower right', title='申购总规模', frameon=False,
                    fontsize=8, title_fontsize=8, labelspacing=1.2,
                    borderpad=1, scatterpoints=1)
    leg.get_title().set_color(HBR_CHARCOAL)

    plt.figtext(0.5, 0.02,
                f'数据来源:0703 定稿台账 · {len(df_wlz)} 笔理财子申购 · {len(summary)} 家理财子 | HBR 风格可视化',
                ha='center', fontsize=8, color=HBR_GRAY, style='italic')

    plt.savefig(OUTPUT, dpi=150, bbox_inches='tight', facecolor=HBR_CREAM)
    print(f'已保存: {OUTPUT}')
    print(f'理财子数量: {len(summary)} 家, 总申购笔数: {len(df_wlz)}')


if __name__ == '__main__':
    main()
