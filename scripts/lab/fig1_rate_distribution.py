"""fig1_rate_distribution.py — 利率分布直方图(按资产类型 small multiples)

clean-viz 风格:Tufte 原则,range frame,无 chartjunk
洞察:不同资产类型的利率分布形状差异,看哪些资产定价集中、哪些分散
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_data import load_wxy_df

import matplotlib.pyplot as plt
import numpy as np

# === clean-viz 全局常量 ===
# Windows 中文字体回退:Microsoft YaHei + SimHei
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

CLEAN_BLACK = '#1a1a1a'
CLEAN_GRAY = '#555555'
CLEAN_LIGHT_GRAY = '#888888'
ACCENT = '#c0392b'  # 强调色
CLEAN_FONT_SIZE = 9
CLEAN_TITLE_SIZE = 11

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      '..', '..', 'deliverables', 'dashboards', '02_history',
                      'lab_viz', 'fig1_rate_distribution.png')


def apply_range_frame(ax):
    """去除上/右 spine,左/下 spine bound 到数据范围,tick 朝内"""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(CLEAN_GRAY)
    ax.spines['bottom'].set_color(CLEAN_GRAY)
    ax.tick_params(direction='in', colors=CLEAN_GRAY, labelsize=CLEAN_FONT_SIZE)


def main():
    df = load_wxy_df()
    # 选 top 6 资产类型
    top_assets = df['asset_type'].value_counts().head(6).index.tolist()
    df = df[df['asset_type'].isin(top_assets)].copy()

    fig, axes = plt.subplots(2, 3, figsize=(11, 6.5), sharex=True, sharey=True)
    fig.suptitle('申购利率分布按资产类型分层',
                 fontsize=CLEAN_TITLE_SIZE + 2, color=CLEAN_BLACK,
                 fontweight='bold', y=0.98)
    fig.text(0.5, 0.93, '理财子/信托/保险等机构在 2026 年 4-6 月 ABS 一级申购的利率报价分布',
             ha='center', fontsize=CLEAN_FONT_SIZE, color=CLEAN_GRAY, style='italic')

    bins = np.arange(1.0, 3.05, 0.05)

    for idx, asset in enumerate(top_assets):
        ax = axes[idx // 3, idx % 3]
        sub = df[df['asset_type'] == asset]
        rates = sub['rate_pct'].values
        median = np.median(rates)

        # 灰色柱
        ax.hist(rates, bins=bins, color='#cccccc', edgecolor='white',
                linewidth=0.5)
        # 中位数竖线(强调色)
        ax.axvline(median, color=ACCENT, linewidth=1.2, alpha=0.85)
        # 中位数标注
        ax.text(median, ax.get_ylim()[1] * 0.92,
                f'中位 {median:.2f}%', ha='center',
                fontsize=CLEAN_FONT_SIZE - 1, color=ACCENT, fontweight='bold')

        ax.set_title(f'{asset}  (n={len(rates)})',
                     fontsize=CLEAN_FONT_SIZE, color=CLEAN_BLACK,
                     pad=4)
        apply_range_frame(ax)

        # range frame
        ax.set_xlim(1.0, 3.0)
        ax.spines['bottom'].set_bounds(1.0, 3.0)
        ax.set_xticks([1.0, 1.5, 2.0, 2.5, 3.0])

    # 共享轴标签
    for ax in axes[-1]:
        ax.set_xlabel('申购利率 (%)', fontsize=CLEAN_FONT_SIZE, color=CLEAN_GRAY)
    for ax in axes[:, 0]:
        ax.set_ylabel('申购笔数', fontsize=CLEAN_FONT_SIZE, color=CLEAN_GRAY)

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    plt.savefig(OUTPUT, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'已保存: {OUTPUT}')


if __name__ == '__main__':
    main()
