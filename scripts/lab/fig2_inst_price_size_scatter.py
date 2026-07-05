"""fig2_inst_price_size_scatter.py — Top 机构申购规模 vs 利率散点图

clean-viz:每个机构用不同 marker shape + 灰阶,直接标注
洞察:看机构"价格-量"博弈——谁要量大价低,谁接受高价小量
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_data import load_wxy_df

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

CLEAN_BLACK = '#1a1a1a'
CLEAN_GRAY = '#555555'
CLEAN_LIGHT_GRAY = '#888888'
ACCENT = '#c0392b'
CLEAN_FONT_SIZE = 9

# Paul Tol 高对比度前 6 色
PALETTE = ['#332288', '#CC6677', '#117733', '#882255', '#44AA99', '#AA4499']
MARKERS = ['o', 's', '^', 'D', 'v', 'P']

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      '..', '..', 'deliverables', 'dashboards', '02_history',
                      'lab_viz', 'fig2_inst_price_size_scatter.png')


def main():
    df = load_wxy_df()
    # Top 6 机构(按申购笔数)
    top_inst = df['institution'].value_counts().head(6).index.tolist()
    sub = df[df['institution'].isin(top_inst)].copy()

    fig, ax = plt.subplots(figsize=(10, 6.5))

    for idx, inst in enumerate(top_inst):
        d = sub[sub['institution'] == inst]
        # 抖动避免点重叠
        x = d['rate_pct'].values + np.random.uniform(-0.01, 0.01, len(d))
        y = d['size'].values + np.random.uniform(-0.05, 0.05, len(d))
        ax.scatter(x, y,
                   s=40, alpha=0.55,
                   c=PALETTE[idx], marker=MARKERS[idx],
                   edgecolors='white', linewidth=0.5,
                   label=inst)

    # 标注 Top 3 机构的均值点
    for idx, inst in enumerate(top_inst[:3]):
        d = sub[sub['institution'] == inst]
        mean_x = d['rate_pct'].mean()
        mean_y = d['size'].mean()
        ax.scatter([mean_x], [mean_y], s=180, marker='X',
                   c=ACCENT, edgecolors='black', linewidth=1.2, zorder=5)
        ax.annotate(f'{inst}\n均值 ({mean_x:.2f}%, {mean_y:.2f}亿)',
                    xy=(mean_x, mean_y),
                    xytext=(15, -25), textcoords='offset points',
                    fontsize=CLEAN_FONT_SIZE - 1, color=CLEAN_BLACK,
                    arrowprops=dict(arrowstyle='->', color=ACCENT, lw=0.8))

    ax.set_title('Top 6 机构申购"价格-量"博弈(2026年4-6月 ABS 一级申购)',
                 fontsize=12, color=CLEAN_BLACK, pad=10)
    ax.set_xlabel('申购利率 (%)', fontsize=CLEAN_FONT_SIZE, color=CLEAN_GRAY)
    ax.set_ylabel('申购规模 (亿元)', fontsize=CLEAN_FONT_SIZE, color=CLEAN_GRAY)

    # 去除上右 spine,tick 朝内
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(CLEAN_GRAY)
    ax.spines['bottom'].set_color(CLEAN_GRAY)
    ax.tick_params(direction='in', colors=CLEAN_GRAY, labelsize=CLEAN_FONT_SIZE)

    # range frame
    x_min, x_max = sub['rate_pct'].min(), sub['rate_pct'].max()
    y_min, y_max = sub['size'].min(), sub['size'].max()
    ax.set_xlim(x_min - 0.1, x_max + 0.2)
    ax.set_ylim(0, y_max + 0.5)
    ax.spines['bottom'].set_bounds(x_min, x_max)
    ax.spines['left'].set_bounds(0, y_max)

    # 图例(无框,放右上)
    legend = ax.legend(loc='upper right', frameon=False,
                       fontsize=CLEAN_FONT_SIZE, title='机构',
                       title_fontsize=CLEAN_FONT_SIZE)
    legend.get_title().set_color(CLEAN_BLACK)

    plt.figtext(0.5, 0.01,
                '注:红色 X 为机构均值;点抖动处理避免重叠;n=679 笔申购',
                ha='center', fontsize=CLEAN_FONT_SIZE - 1,
                color=CLEAN_LIGHT_GRAY, style='italic')

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    plt.savefig(OUTPUT, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'已保存: {OUTPUT}')


if __name__ == '__main__':
    main()
