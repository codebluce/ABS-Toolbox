"""fig5_hbr_composite.py — HBR风格:机构申购画像综合视图

HBR 样式:主图(散点+规模编码) + sidebar(机构画像洞察)
洞察:机构分层——量大价低型 / 量小价高型 / 均衡型
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_data import load_wxy_df

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.gridspec as gridspec

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
    # Top 10 机构
    top_inst = df['institution'].value_counts().head(10).index.tolist()
    sub = df[df['institution'].isin(top_inst)].copy()

    # 机构汇总
    summary = sub.groupby('institution').agg(
        total_size=('size', 'sum'),
        mean_rate=('rate_pct', 'mean'),
        n=('size', 'count'),
    ).reset_index()
    summary = summary.sort_values('total_size', ascending=True)

    fig = plt.figure(figsize=(12, 7), facecolor=HBR_CREAM)
    gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1.1], wspace=0.18)
    ax = fig.add_subplot(gs[0, 0])
    ax_sidebar = fig.add_subplot(gs[0, 1])
    ax_sidebar.axis('off')

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
                       fontsize=9, color=HBR_CHARCOAL)
    ax.set_xlabel('平均申购利率 (%)', fontsize=10, color=HBR_CHARCOAL)
    ax.set_title('Top 10 机构申购画像:规模 vs 价格定位',
                 fontsize=13, color=HBR_CHARCOAL, fontweight='bold',
                 pad=12, loc='left')

    # 样式
    for spine_name in ['top', 'right']:
        ax.spines[spine_name].set_visible(False)
    ax.spines['left'].set_color(HBR_GRAY)
    ax.spines['bottom'].set_color(HBR_GRAY)
    ax.tick_params(direction='in', colors=HBR_GRAY, labelsize=9, length=3)

    # range frame
    x_min, x_max = summary['mean_rate'].min(), summary['mean_rate'].max()
    ax.set_xlim(x_min - 0.05, x_max + 0.15)
    ax.spines['bottom'].set_bounds(x_min, x_max)

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

    # Sidebar
    ax_sidebar.text(0, 0.95, '机构画像', fontsize=12, color=HBR_CHARCOAL,
                    fontweight='bold', transform=ax_sidebar.transAxes)
    ax_sidebar.plot([0, 0.85], [0.92, 0.92], color=HBR_CRIMSON,
                    linewidth=2, transform=ax_sidebar.transAxes)

    # 分类统计
    big_cheap = ((summary['total_size'] >= summary['total_size'].median()) &
                 (summary['mean_rate'] <= summary['mean_rate'].median())).sum()
    small_expensive = ((summary['total_size'] < summary['total_size'].median()) &
                       (summary['mean_rate'] > summary['mean_rate'].median())).sum()
    balanced = len(summary) - big_cheap - small_expensive

    insights = [
        f'■ 红点 = 量大价低型',
        f'  {big_cheap} 家机构,核心买方',
        f'',
        f'■ 灰点 = 均衡型',
        f'  {balanced} 家机构,中位参与',
        f'',
        f'■ 浅灰点 = 量小价高型',
        f'  {small_expensive} 家机构,边缘参与',
        f'',
        f'■ 规模符号编码',
        f'  点大小 ∝ 申购总规模',
        f'',
        f'■ 风险提示',
        f'  红点机构利率下行可能',
        f'  意味着 ABS 一级需求',
        f'  竞争加剧',
    ]
    for i, line in enumerate(insights):
        color = HBR_CRIMSON if line.startswith('■ 红点') else HBR_CHARCOAL
        weight = 'bold' if line.startswith('■') else 'normal'
        ax_sidebar.text(0, 0.87 - i * 0.06, line,
                        fontsize=8.5, color=color, fontweight=weight,
                        transform=ax_sidebar.transAxes,
                        family='sans-serif')

    plt.figtext(0.5, 0.02,
                '数据来源:0703 定稿台账 957 笔申购 | HBR 风格可视化',
                ha='center', fontsize=8, color=HBR_GRAY, style='italic')

    plt.savefig(OUTPUT, dpi=150, bbox_inches='tight', facecolor=HBR_CREAM)
    print(f'已保存: {OUTPUT}')


if __name__ == '__main__':
    main()
