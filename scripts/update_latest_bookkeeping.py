"""同步定稿台账的最新簿记面板，保留综合看板其他模块，门禁通过后原子替换。"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import tempfile
import os

import latest_bookkeeping_panel as panel
import latest_bookkeeping_qc as qc

ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT / 'deliverables' / 'dashboards' / '01_latest'
CSS_BEGIN = '/* latest-bookkeeping:begin */'
CSS_END = '/* latest-bookkeeping:end */'


def latest_dashboard(directory=LATEST):
    candidates = [p for p in Path(directory).glob('ABS综合看板_*.html') if re.fullmatch(r'ABS综合看板_\d{8}\.html', p.name)]
    if not candidates:
        raise FileNotFoundError('没有综合看板可保留其他模块，请先运行gen_integrated_dashboard.py')
    return max(candidates, key=lambda path: path.name)


def replace_panel(document, data):
    if qc.has_monthly_markers(document):
        raise ValueError('月度簿记组件不能局部刷新；请显式使用gen_integrated_dashboard.py '
                         '--monthly-bookkeeping和本地output完整生成对应renderer')
    body = panel.render_body(data)
    current = r'<div id="latest-bookkeeping">.*?</script></div>\s*<script>.*?</script>'
    if 'id="latest-bookkeeping"' in document:
        document, count = re.subn(current, lambda match: body, document, flags=re.S)
        if count != 1:
            raise ValueError('最新簿记面板边界不唯一，停止替换')
    else:
        anchor = '<div class="sub-tabs-pane" data-module="pricing">'
        if anchor not in document or document.count('<div class="panel-container">') != 1:
            raise ValueError('缺少唯一发行定价导航/面板容器')
        button = '<button class="sub-tab-button" data-sub="bookkeeping" onclick="selectSub(\'bookkeeping\')">最新簿记</button>'
        document = document.replace(anchor, anchor + button, 1)
        document = document.replace('<div class="panel-container">',
            '<div class="panel-container"><div class="panel" data-module="pricing" data-sub="bookkeeping">' + body + '</div>', 1)
    # 带边界的CSS只替换本模块。历史Demo无边界时追加当前规则，其他CSS保持原样。
    css = CSS_BEGIN + '\n' + panel.BOOKKEEPING_CSS + '\n' + CSS_END
    if CSS_BEGIN in document:
        document, count = re.subn(re.escape(CSS_BEGIN) + r'.*?' + re.escape(CSS_END), lambda match: css, document, flags=re.S)
        if count != 1:
            raise ValueError('簿记样式边界不唯一')
    else:
        document = document.replace('</style>', css + '\n</style>', 1)
    return document


def atomic_write(path, document, ledger):
    """读回实际待替换文件对账，失败清理临时文件，上一版内容不变。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.bookkeeping-', suffix='.html', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(document)
        report = qc.verify_html(Path(temporary).read_text(encoding='utf-8'), ledger)
        os.replace(temporary, path)
        return report
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()


def refresh(ledger=None, dashboard=None, output=None):
    ledger = Path(ledger) if ledger else panel.find_latest_final()
    dashboard = Path(dashboard) if dashboard else latest_dashboard()
    source = dashboard.read_text(encoding='utf-8')
    qc.component_self_check()
    data = panel.compute_data(ledger)
    from latest_bookkeeping_runtime import verify_runtime
    verify_runtime(data)
    document = replace_panel(source, data)
    if output is None:
        match = re.fullmatch(r'(\d{4})年ABS发行台账-(\d{4})-定稿.xlsx', ledger.name)
        if not match:
            raise ValueError('无法解析定稿业务日期，请显式提供--output')
        output = LATEST / f"ABS综合看板_{''.join(match.groups())}.html"
    report = atomic_write(output, document, ledger)
    print("[发布约束] 本次仅局部刷新簿记；源台账变更后须完整生成综合看板再发布")
    print(f"[簿记同步] {output} · {report['checks']} · WARN {len(report['issues'])}")
    return Path(output), report


def validate_pending_final(temporary, target):
    """最新定稿落盘前验证临时xlsx；失败时目标旧文件不变。"""
    target = Path(target).resolve()
    final_dir = (ROOT / 'deliverables' / 'ledger' / '03_final').resolve()
    if target.parent == final_dir and re.fullmatch(r'\d{4}年ABS发行台账-\d{4}-定稿.xlsx', target.name):
        panel.compute_data(temporary, source_name=target.name)


def refresh_if_controlled_final(path):
    path = Path(path).resolve()
    final_dir = (ROOT / 'deliverables' / 'ledger' / '03_final').resolve()
    if path.parent == final_dir and re.fullmatch(r'\d{4}年ABS发行台账-\d{4}-定稿.xlsx', path.name):
        # 仅当本次写入的是业务日期最新定稿才刷新，历史定稿修改不会降级面板。
        if panel.find_latest_final() == path:
            return refresh(path)
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path)
    parser.add_argument('--dashboard', type=Path, help='保留其他面板的基础综合看板，默认最新业务日期')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    refresh(args.ledger, args.dashboard, args.output)


if __name__ == '__main__':
    main()
