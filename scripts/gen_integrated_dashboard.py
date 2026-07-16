"""ABS 综合看板生成器（路径 C · 数据驱动版）

调 4 个原始脚本的 compute_data + render_body，一步到位生成综合看板。
不再依赖中间 HTML 文件，不再依赖 BeautifulSoup。

用法:
  python gen_integrated_dashboard.py <xlsx_path> [output_path]
  默认输出 deliverables/dashboards/01_latest/ABS综合看板_YYYYMMDD.html
"""
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# 脚本目录加入 sys.path，便于 import 4 个生成器
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import gen_institution_stats
import gen_abs_cost_report
import gen_spread_report
import gen_compare_tool
import gen_investment_ledger
import gen_pricing_insight

# 投资人分析模块(lab 实验转正:fig7_wlz_panel 调 fig4_new + fig5 同步台账)
LAB_DIR = SCRIPT_DIR / 'lab'
if str(LAB_DIR) not in sys.path:
    sys.path.insert(0, str(LAB_DIR))
import fig7_wlz_panel

# 非标额度监控模块
import fig6_credit_panel

# 总授信额度监控模块
import fig8_credit_total_panel


# ── 综合看板的 Tab 框架 CSS（独立于 4 份原始 CSS）──────────────
TAB_CSS = """
/* ── 综合看板 Tab 框架专用样式（不动原始看板样式）── */
body { background:#f4f5f7; }

.top-tabs {
  display:flex; gap:0; background:#fff;
  border-bottom:1px solid #e5e7eb;
  padding:0 24px;
  position:sticky; top:0; z-index:100;
  box-shadow:0 1px 3px rgba(0,0,0,.04);
}
.tab-button {
  padding:14px 24px;
  font-size:14px; font-weight:600;
  color:#6b7280;
  background:transparent; border:none; border-bottom:2px solid transparent;
  cursor:pointer; transition:all .15s;
  font-family:"PingFang SC","Microsoft YaHei",sans-serif;
}
.tab-button:hover { color:#1a3a5c; background:#f9fafb; }
.tab-button.active {
  color:#0d1b2e;
  border-bottom-color:#0d1b2e;
}

.sub-tabs-wrapper {
  background:#fff;
  border-bottom:1px solid #e5e7eb;
  padding:8px 24px 0;
}
.sub-tabs-pane { display:none; gap:0; }
.sub-tabs-pane.active { display:flex; }
.sub-tab-button {
  padding:8px 16px;
  font-size:12px; font-weight:500;
  color:#6b7280;
  background:#f3f4f6;
  border:1px solid transparent;
  border-radius:6px 6px 0 0;
  cursor:pointer; transition:all .15s;
  margin-right:4px;
  font-family:"PingFang SC","Microsoft YaHei",sans-serif;
}
.sub-tab-button:hover { color:#1a3a5c; background:#eef3fa; }
.sub-tab-button.active {
  color:#fff;
  background:#0d1b2e;
  border-color:#0d1b2e;
}

.panel-container { background:#f4f5f7; }
.panel { display:none; }
.panel.active { display:block; }

/* 让原始看板的 page-banner 在 Tab 框架下保持视觉占位 */
.panel .page-banner { padding-top:14px; padding-bottom:12px; }
"""


# ── Tab 框架 JS（切换逻辑）─────────────────────────────────────
TAB_JS = """
function selectModule(module) {
  document.querySelectorAll('.tab-button').forEach(b => {
    b.classList.toggle('active', b.dataset.module === module);
  });
  document.querySelectorAll('.sub-tabs-pane').forEach(p => {
    p.classList.toggle('active', p.dataset.module === module);
  });
  const firstSub = document.querySelector('.sub-tabs-pane[data-module="' + module + '"] .sub-tab-button');
  if (firstSub) {
    selectSub(firstSub.dataset.sub);
  }
}

function selectSub(sub) {
  let activeModule = null;
  document.querySelectorAll('.tab-button').forEach(b => {
    if (b.classList.contains('active')) activeModule = b.dataset.module;
  });
  if (!activeModule) return;

  document.querySelectorAll('.sub-tab-button').forEach(b => {
    b.classList.toggle('active', b.dataset.sub === sub);
  });
  document.querySelectorAll('.panel').forEach(p => {
    const match = (p.dataset.module === activeModule && p.dataset.sub === sub);
    p.classList.toggle('active', match);
  });
  window.scrollTo({top:0, behavior:'smooth'});
}

document.addEventListener('DOMContentLoaded', () => {
  selectModule('pricing');
});
"""


# ── 主流程 ────────────────────────────────────────────────────
def build_integrated_html(panels, all_css):
    """构建综合看板完整 HTML

    panels: List[(module, sub, body_html)]
    all_css: 4 份原始 CSS + TAB_CSS 拼接的字符串

    4 个 top tab: 发行定价 / 机构统计 / 投资人分析 / 投资台账
    投资人分析 > 理财子分析 (fig4 矩阵 + fig5 画像 并排)
    投资台账 > 2026年/2025年/2024年 三个年份子 Tab (各自独立筛选状态，多维筛选 + 分组/透视/明细 + 导出 CSV)
              智能问答悬浮球语料覆盖全部年份，不受当前激活子 Tab 限制
    """
    MODULES = [('pricing', '发行定价'), ('institution', '机构统计'),
               ('investor', '投资人分析'), ('ledger', '投资台账')]
    # 第一层 Tab 标签
    top_buttons = []
    for module, label in MODULES:
        top_buttons.append(
            f'<button class="tab-button" data-module="{module}" '
            f'onclick="selectModule(\'{module}\')">{label}</button>'
        )
    top_tabs_html = "\n      ".join(top_buttons)

    # 第二层 Tab 标签 + panel 容器
    sub_tabs_panes = []
    panel_divs = []
    for module, label in MODULES:
        # 该模块下的子 Tab 按钮
        sub_buttons = []
        module_panels = [p for p in panels if p[0] == module]
        for m, sub, body in module_panels:
            # 从 body 提取子 Tab 显示名（用 section-title 或 banner-title）
            # 机构统计的 3 个 panel 用 section 名，发行定价用看板名
            if module == 'institution':
                # 从 body 里找 section-title
                import re
                title_match = re.search(r'<span class="section-title">(.*?)</span>', body)
                sub_label = title_match.group(1).replace('表一：', '').replace('表二：', '').replace('表三：', '') if title_match else sub
            elif module == 'investor':
                sub_label_map = {'wlz': '理财子分析', 'credit': '非标额度', 'credit_total': '授信总额度'}
                sub_label = sub_label_map.get(sub, sub)
            elif module == 'ledger':
                sub_label_map = {'query_2026': '2026年', 'query_2025': '2025年', 'query_2024': '2024年'}
                sub_label = sub_label_map.get(sub, sub)
            else:
                # 发行定价的子 Tab 名固定
                sub_label_map = {'compare': '定价测试', 'invest': '投资明细', 'cost': '成本分布', 'spread': '利差分析'}
                sub_label = sub_label_map.get(sub, sub)
            sub_buttons.append(
                f'<button class="sub-tab-button" data-sub="{sub}" '
                f'onclick="selectSub(\'{sub}\')">{sub_label}</button>'
            )
        sub_tabs_panes.append(
            f'<div class="sub-tabs-pane" data-module="{module}">\n        '
            + "\n        ".join(sub_buttons) +
            "\n      </div>"
        )

        # 该模块下的 panel div
        for m, sub, body in module_panels:
            panel_divs.append(
                f'<div class="panel" data-module="{m}" data-sub="{sub}">\n'
                f'{body}\n      </div>'
            )

    sub_tabs_html = "\n      ".join(sub_tabs_panes)
    panels_html = "\n      ".join(panel_divs)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ABS 综合看板</title>
<style>
{all_css}

{TAB_CSS}
</style>
</head>
<body>
  <div class="top-tabs">
      {top_tabs_html}
  </div>
  <div class="sub-tabs-wrapper">
      {sub_tabs_html}
  </div>
  <div class="panel-container">
      {panels_html}
  </div>

<script>
{TAB_JS}
</script>
</body>
</html>"""


# 共享 tmp 结构断言:fig4/fig5 按列名读 + iloc[2:] 跳前2行,结构不符会静默错数。
# 此断言在 main 创建共享 tmp 后注入前执行,不符立即 fail,杜绝静默错数风险。
SHARED_TMP_REQUIRED_COLS = {
    '月份', '资产类型', '项目名称', '发行场所', '认购机构', '认购份额',   # fig4 load_all_rows
    '申购利率', '穿透机构', '申购规模', '成本', '簿记时间', '分层情况',     # fig5 load_wxy_df
    '规模', '国股CD', '计划管理人', '联席承销商', '托管行',                # load_and_filter
}


def _assert_shared_tmp_structure(tmp_path):
    """断言共享 tmp 满足所有消费方的结构依赖,不符立即 fail。"""
    import pandas as _pd
    raw = _pd.read_excel(tmp_path, header=None)
    headers = [str(h).strip() if h is not None else '' for h in raw.iloc[0].tolist()]
    missing = SHARED_TMP_REQUIRED_COLS - set(headers)
    if missing:
        raise ValueError(
            f'[shared_tmp] 列名缺失,共享 tmp 结构不满足消费方依赖: {sorted(missing)}\n'
            f'  现有列: {headers}'
        )
    if raw.shape[1] < 25:
        raise ValueError(f'[shared_tmp] 列数 {raw.shape[1]} < 25,定稿台账应为 25 列')
    if len(raw) < 3:
        raise ValueError(f'[shared_tmp] 行数 {len(raw)} < 3,无有效数据行')
    print(f'[shared_tmp] 结构断言通过: {raw.shape[1]} 列 / {len(raw)} 行 / 关键列名齐全')


def main():
    parser = argparse.ArgumentParser(description='ABS 综合看板生成器（路径 C · 数据驱动）')
    parser.add_argument('xlsx_path', help='台账文件路径（.xlsx）')
    parser.add_argument('output_path', nargs='?', default=None, help='输出 HTML 路径（默认 01_latest/ABS综合看板_YYYYMMDD.html）')
    args = parser.parse_args()

    xlsx_path = args.xlsx_path
    if args.output_path:
        out_path = args.output_path
    else:
        date_tag = datetime.now().strftime('%Y%m%d')
        kanban_dir = SCRIPT_DIR.parent / 'deliverables' / 'dashboards' / '01_latest'
        kanban_dir.mkdir(parents=True, exist_ok=True)
        out_path = str(kanban_dir / f'ABS综合看板_{date_tag}.html')

    print('=' * 60)
    print('  ABS 综合看板生成器（数据驱动）')
    print('=' * 60)

    # 1. 单次预处理:产出共享 tmp,注入各子模块(原 8 次 preprocess → 1 次,预期省 ~80s)
    #    shared_tmp 创建移入 try,preprocess 自身异常时 finally 兜底删除
    from abs_common import preprocess_xlsx_for_pandas
    shared_tmp = None
    try:
        print('\n[1/4] 单次预处理(共享 tmp)...')
        shared_tmp = preprocess_xlsx_for_pandas(xlsx_path)
        print(f'[preprocess] 共享预处理产物: {shared_tmp}')
        _assert_shared_tmp_structure(shared_tmp)   # 结构断言:不符立即 fail,防 fig4/fig5 静默错数

        # 各 compute_data(注入 shared_tmp;gen_institution_stats 综合看板场景不 preprocess,不注入)
        print('\n[1.5/4] 计算数据...')
        cmp_data = gen_compare_tool.compute_data(xlsx_path, preprocessed_path=shared_tmp)
        cost_data = gen_abs_cost_report.compute_data(xlsx_path, preprocessed_path=shared_tmp)
        spread_data = gen_spread_report.compute_data(xlsx_path, preprocessed_path=shared_tmp)
        inst_data = gen_institution_stats.compute_data(xlsx_path)
        # 投资台账：2026 用当前入参台账(注入 shared_tmp)，2025/2024 走固定的历史台账路径（缺失则该年份跳过，不报错）
        source_dir = SCRIPT_DIR.parent / 'deliverables' / 'ledger' / '01_source'
        ledger_year_paths = {
            '2026': xlsx_path,
            '2025': str(source_dir / '2025年ABS发行台账.xlsx'),
            '2024': str(source_dir / '2024年ABS发行台账.xlsx'),
        }
        led_data = gen_investment_ledger.compute_data_multi_year(
            ledger_year_paths, preprocessed_path=shared_tmp)   # 只 2026 用
    except RuntimeError as e:
        print(f'\n[ERROR] {e}')
        print('[ERROR] 请修正数据或逻辑后重试')
        if shared_tmp:
            try:
                os.remove(shared_tmp)
            except OSError:
                pass
        sys.exit(1)

    # 2. 各 render_body（institution 3 次调用，传 section_key）
    print('\n[2/4] 渲染 body...')
    panels = [
        ('pricing',     'compare',    gen_pricing_insight.render_pricing_panel(cmp_data)),
        ('pricing',     'invest',     gen_compare_tool.render_body_invest(cmp_data)),
        ('pricing',     'cost',       gen_abs_cost_report.render_body(cost_data)),
        ('pricing',     'spread',     gen_spread_report.render_body(spread_data)),
        ('institution', 'manager',    gen_institution_stats.render_body(inst_data, section_key='manager')),
        ('institution', 'sales',      gen_institution_stats.render_body(inst_data, section_key='sales')),
        ('institution', 'custodian',  gen_institution_stats.render_body(inst_data, section_key='custodian')),
    ]

    # 投资人分析模块:理财子分析 panel(fig4 矩阵 + fig5 画像 并排,同步最新台账)
    print('\n[3/4] 生成投资人分析 > 理财子分析 panel...')
    wlz_body = fig7_wlz_panel.render_wlz_panel(regenerate=True, preprocessed_path=shared_tmp)
    panels.append(('investor', 'wlz', wlz_body))

    # 投资人分析模块:非标额度 panel
    print('\n[3.5/4] 生成投资人分析 > 非标额度 panel...')
    try:
        credit_body = fig6_credit_panel.render_credit_panel(
            ledger_path=xlsx_path, preprocessed_path=shared_tmp)
        panels.append(('investor', 'credit', credit_body))
    except Exception as e:
        print(f'[WARN] 非标额度面板跳过: {e}')
        panels.append(('investor', 'credit', '<div style="padding:40px;text-align:center;color:#9aa5b5;">非标额度数据暂不可用</div>'))

    # 投资人分析模块:总授信额度 panel
    print('\n[3.6/4] 生成投资人分析 > 授信总额度 panel...')
    credit_total_body = fig8_credit_total_panel.render_credit_total_panel(
        ledger_path=xlsx_path, preprocessed_path=shared_tmp)
    panels.append(('investor', 'credit_total', credit_total_body))

    # 共享 tmp 生命周期结束(所有 read 已完成,进入 HTML 拼接),统一删除杜绝泄漏
    if shared_tmp:
        try:
            os.remove(shared_tmp)
        except OSError:
            pass
        shared_tmp = None

    # 投资台账模块：按年份拆分的多维筛选统计 panel（2026/2025/2024 各一个子 Tab，
    # 智能问答悬浮球随第一个年份 panel 一起挂载，语料覆盖全部年份，不受当前子 Tab 限制）
    print('\n[3.7/4] 生成投资台账 > 分年份筛选统计 panel...')
    for year, body in gen_investment_ledger.render_body_multi_year(led_data):
        panels.append(('ledger', f'query_{year}', body))

    # 4. CSS 拼接 + 套 Tab 框架 + 写文件
    print('\n[4/4] 拼接 HTML...')
    all_css = '\n'.join([
        gen_institution_stats.CSS,
        gen_abs_cost_report.CSS,
        gen_spread_report.CSS,
        gen_compare_tool.CSS,
        gen_pricing_insight.PRICING_INSIGHT_CSS,
        gen_compare_tool.INVEST_CSS,
        fig6_credit_panel.CREDIT_CSS,
        fig8_credit_total_panel.CREDIT_TOTAL_CSS,
        gen_investment_ledger.LEDGER_CSS,
    ])
    html = build_integrated_html(panels, all_css)

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = os.path.getsize(out_path) / 1024
    print(f'\n[完成] {out_path} ({size_kb:.1f} KB)')
    print(f'\n默认显示: 发行定价 / 定价测试')

    # 轻量级最终检查
    with open(out_path, 'r', encoding='utf-8') as f:
        content = f.read()
    panel_count = content.count('<div class="panel"')
    expected_panel_count = 10 + len(led_data['by_year'])  # 7 主 + 理财子/非标额度/授信总额度 3 个 + 各年份投资台账
    has_select_module = 'function selectModule' in content
    has_select_sub = 'function selectSub' in content
    ledger_years_str = '+'.join(sorted(led_data['by_year'].keys(), reverse=True))
    if panel_count == expected_panel_count and has_select_module and has_select_sub:
        print(f'[QC] 综合看板结构检查通过：{panel_count} 个 panel(7 主 + 理财子分析 + 非标额度 + 授信总额度 + 投资台账[{ledger_years_str}]) + Tab 切换 JS 齐全')
    else:
        print(f'[QC WARN] 结构异常：panel={panel_count}(预期{expected_panel_count}), selectModule={has_select_module}, selectSub={has_select_sub}')


if __name__ == '__main__':
    main()
