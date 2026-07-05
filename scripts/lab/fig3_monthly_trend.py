"""fig3_monthly_trend.py — Top 资产类型月度利率中位数趋势 small multiples

clean-viz:每个资产类型一个小图,共享 y 轴,中位数趋势 + 散点
洞察:不同资产类型 4-6 月利率走势,看哪些资产利率上行/下行
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_data import load_wxy_df

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

CLEAN_BLACK = '#1a1a1a'
CLEAN_GRAY = '#555555'
CLEAN_LIGHT_GRAY = '#888888'
ACCENT = '#c0392b'
CLEAN_FONT_SIZE = 9

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      '..', '..', 'deliverables', 'dashboards', '02_history',
                      'lab_viz', 'fig3_monthly_trend.png')


def main():
    df = load_wxy_df()
    # 选 4 个资产类型(覆盖消金/保理/信托/金采)
    top_assets = df['asset_type'].value_counts().head(4).index.tolist()
    sub = df[df['asset_type'].isin(top_assets) & df['month'].isin([4, 5, 6])].copy()

    fig, axes = plt.subplots(2, 2, figsize=(10, 6.5), sharex=True, sharey=True)
    fig.suptitle('Top 4 资产类型月度申购利率中位数走势',
                 fontsize=12, color=CLEAN_BLACK, fontweight='bold', y=0.97)
    fig.text(0.5, 0.92, '4-6 月 ABS 一级申购利率演化,红实线为中位数,灰点为单笔申购',
             ha='center', fontsize=CLEAN_FONT_SIZE, color=CLEAN_GRAY, style='italic')

    months = [4, 5, 6]
    month_labels = ['4月', '5月', '6月']

    for idx, asset in enumerate(top_assets):
        ax = axes[idx // 2, idx % 2]
        d = sub[sub['asset_type'] == asset]
        medians = []
        for m in months:
            md = d[d['month'] == m]['rate_pct']
            medians.append(md.median() if len(md) > 0 else np.nan)

        # 散点(灰) - 抖动
        for i, m in enumerate(months):
            md = d[d['month'] == m]['rate_pct'].values
            if len(md) > 0:
                x = np.full(len(md), i + 1) + np.random.uniform(-0.15, 0.15, len(md))
                ax.scatter(x, md, color='#cccccc', s=20, alpha=0.6, zorder=2)

        # 中位数连线(红)
        valid_x = [i + 1 for i, v in enumerate(medians) if not np.isnan(v)]
        valid_y = [v for v in medians if not np.isnan(v)]
        ax.plot(valid_x, valid_y, color=ACCENT, linewidth=1.5,
                marker='o', markersize=6, zorder=3)

        # 标注中位数
        for x, y in zip(valid_x, valid_y):
            ax.text(x, y + 0.05, f'{y:.2f}%', ha='center',
                    fontsize=CLEAN_FONT_SIZE - 1, color=ACCENT, fontweight='bold')

        ax.set_title(f'{asset}', fontsize=CLEAN_FONT_SIZE,
                     color=CLEAN_BLACK, pad=4)
        # 样本数副标题
        n = len(d)
        ax.text(0.98, 0.95, f'n={n}', transform=ax.transAxes,
                ha='right', va='top', fontsize=CLEAN_FONT_SIZE - 2,
                color=CLEAN_LIGHT_GRAY)

        # 样式
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(CLEAN_GRAY)
        ax.spines['bottom'].set_color(CLEAN_GRAY)
        ax.tick_params(direction='in', colors=CLEAN_GRAY, labelsize=CLEAN_FONT_SIZE)
        ax.set_xticks([1, 2, 3])
        ax.set_xticklabels(month_labels)
        ax.set_xlim(0.5, 3.5)
        # 共享 y 范围
        ax.set_ylim(1.0, 3.0)
        ax.spines['bottom'].set_bounds(1, 3)
        ax.spines['left'].set_bounds(1.0, 3.0)
        ax.set_yticks([1.0, 1.5, 2.0, 2.5, 3.0])

    # 共享轴标签
    for ax in axes[-1]:
        ax.set_xlabel('月份', fontsize=CLEAN_FONT_SIZE, color=CLEAN_GRAY)
    for ax in axes[:, 0]:
        ax.set_ylabel('申购利率 (%)', fontsize=CLEAN_FONT_SIZE, color=CLEAN_GRAY)

    plt.tight_layout(rect=[0, 0, 1, 0.91])
    plt.savefig(OUTPUT, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'已保存: {OUTPUT}')


if __name__ == '__main__':
    main()
