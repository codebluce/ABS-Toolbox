"""簿记明细录入前的格式预检：先给“可录 / 需确认”清单，再决定要不要录。

为什么要这一步
--------------
历史踩过的坑都不是“表格打不开”，而是打开后静默读错：

* 启赢3-4 明细表头写的是万元，程序按亿元录入，规模整体放大 1 万倍；
* 有些明细把两个价格写在同一个单元格（“2.30/2.35”），读出来是文本，
  后续求和直接把它当 0 或报错；
* 分层表头被截成“优先”“优先A”，A1/A2 两档数据混进同一层；
* 明细文件名与台账项目名对不上（“金采玖2A” / “金采9-2”），
  明细被记到别的期次上。

这些错误都能在录入前从表格本身看出来，所以本模块只做体检、不改数据：
返回“可录 / 需确认 / 不可录”，把需要人看的点逐条列出来。
"""
from __future__ import annotations

import re
from pathlib import Path

import openpyxl

import project_aliases

BLOCK = 'BLOCK'
CONFIRM = 'CONFIRM'
INFO = 'INFO'

# 单笔认购金额达到该量级只可能是“万元”被当成“亿元”
SINGLE_AMOUNT_CEILING = 1000.0
# 认购合计 / 项目规模 的倍数：申购倍数常见 3–5 倍，20 倍以上先看单位
SUM_RATIO_BLOCK = 50.0
SUM_RATIO_CONFIRM = 10.0


def _text(value) -> str:
    return str(value).strip() if value is not None else ''


def _rate_state(value) -> str:
    """判断利率单元格是否可被当作单一价格读取。"""
    if value is None:
        return 'missing'
    if isinstance(value, bool):
        return 'text'
    if isinstance(value, (int, float)):
        return 'ok'
    text = str(value).strip()
    if not text:
        return 'missing'
    numbers = re.findall(r'\d+(?:\.\d+)?', text)
    if len(numbers) > 1:
        return 'multi'
    if len(numbers) == 1 and re.fullmatch(r'[\d.]+[%％]?', text):
        return 'ok'
    return 'text'


def _sheet_unit_note(ws) -> tuple[str, str]:
    """返回 (单位声明, 原文)。识别"金额单位：万元"及换算说明。"""
    for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 6)):
        for cell in row:
            text = _text(cell.value)
            if '万元' not in text and '亿元' not in text:
                continue
            if '已' in text and '换算' in text or '已除以' in text:
                return 'converted', text
            if '万元' in text:
                return 'wan', text
            return 'yi', text
    return 'unknown', ''


def _scan_sheet(ws) -> dict:
    """按“表头分段”扫描一张工作表，统计分层与金额。"""
    sections = []
    current = None
    for row in range(1, ws.max_row + 1):
        c1 = _text(ws.cell(row=row, column=1).value)
        c2 = _text(ws.cell(row=row, column=2).value)
        c3 = ws.cell(row=row, column=3).value
        if c1 and ('申购利率' in c1 or '投标利率' in c1):
            layer = c1.split('申购利率')[0].split('投标利率')[0].strip()
            layer = layer.replace('级', '').strip()
            if layer == '优先' and '优先级' in c1:
                layer = '优先级'
            current = {'sheet': ws.title, 'layer': layer or '优先A', 'header': c1,
                       'rows': 0, 'total': 0.0, 'largest': 0.0,
                       'rates': {'ok': 0, 'missing': 0, 'multi': 0, 'text': 0}}
            sections.append(current)
            continue
        if current is None:
            continue
        if not c2 or c2 in ('投资者', '投资者名称', '机构', '穿透机构'):
            continue
        if c1 in ('项目名称', '簿记日期', '管理人'):
            continue
        try:
            amount = float(c3) if c3 not in (None, '') else 0.0
        except (TypeError, ValueError):
            current['rates']['text'] += 1
            continue
        if amount <= 0:
            continue
        current['rows'] += 1
        current['total'] += amount
        current['largest'] = max(current['largest'], amount)
        current['rates'][_rate_state(ws.cell(row=row, column=1).value)] += 1
    unit, unit_text = _sheet_unit_note(ws)
    return {'sheet': ws.title, 'sections': sections,
            'unit': unit, 'unitText': unit_text}


def _resolve_project(filename, project_names) -> dict:
    base = Path(filename).name.replace('.xlsx', '').replace('.xls', '')
    name = re.sub(r'[_-]?簿记.*$', '', base)
    name = re.sub(r'[_-]?明细.*$', '', name)
    name = re.sub(r'项目$', '', name).strip()
    mapped = bool(project_aliases.registered(name))
    canonical = project_aliases.resolve(name)
    matched = canonical in set(project_names)
    return {
        'sourceName': name,
        'canonical': canonical,
        'viaAlias': mapped,
        'matched': matched,
        'lookalikes': [] if matched else project_aliases.lookalikes(name, project_names),
    }


def inspect(path, *, project_names=(), expected_size=None) -> dict:
    """体检单个明细文件。expected_size 为该期项目发行规模（亿元，可选）。"""
    path = Path(path)
    findings = []

    def add(level, code, message):
        findings.append({'level': level, 'code': code, 'message': message})

    if not path.is_file():
        add(BLOCK, 'FILE_MISSING', '文件不存在，请核对路径。')
        return {
            'file': path.name, 'path': str(path),
            'project': {'sourceName': path.stem, 'canonical': path.stem,
                        'viaAlias': False, 'matched': False, 'lookalikes': []},
            'expectedSize': expected_size, 'total': 0.0, 'largest': 0.0,
            'sections': [], 'findings': findings, 'verdict': '不可录',
        }

    project = _resolve_project(path.name, list(project_names))
    if not project['matched']:
        hint = ''
        if project['lookalikes']:
            hint = '；台账中形似的项目：' + '、'.join(project['lookalikes'][:3]) + '（需人工确认是否为同一期）'
        add(BLOCK, 'PROJECT_UNMATCHED',
            f"文件名“{project['sourceName']}”对不上台账项目名{hint}。"
            '请先在项目名别名表登记，再录入。')

    book = openpyxl.load_workbook(path, data_only=True)
    try:
        scanned = [_scan_sheet(ws) for ws in book.worksheets]
    finally:
        book.close()

    sections = [section for sheet in scanned for section in sheet['sections']]
    if not sections:
        add(BLOCK, 'NO_SECTION', '未识别到“XX申购利率”分层表头，无法按分层录入。')
    if not any(section['rows'] for section in sections):
        add(BLOCK, 'NO_ROWS', '分层表头下没有任何有效认购行（机构+金额）。')

    # 单位：先看表内声明，再看金额量级
    declared = [(sheet['sheet'], sheet['unitText']) for sheet in scanned if sheet['unit'] == 'wan']
    if declared:
        add(BLOCK, 'UNIT_DECLARED_WAN',
            '表内注明金额单位为万元（未换算），需先换算为亿元再录入：'
            + '；'.join(f'{sheet}：{text}' for sheet, text in declared[:2]))
    total = sum(section['total'] for section in sections)
    largest = max((section['largest'] for section in sections), default=0.0)
    if largest >= SINGLE_AMOUNT_CEILING:
        add(BLOCK, 'AMOUNT_UNIT',
            f'存在单笔认购 {largest:,.2f} 的金额，亿元口径下不可能出现，'
            '几乎可以确定原始单位为万元，需先换算再录入。')
    if expected_size and total > 0:
        ratio = total / expected_size
        if ratio >= SUM_RATIO_BLOCK:
            add(BLOCK, 'AMOUNT_UNIT',
                f'认购合计 {total:,.2f} 是项目规模 {expected_size:,.2f} 的 {ratio:,.0f} 倍，'
                '量级不合理，需先确认金额单位。')
        elif ratio >= SUM_RATIO_CONFIRM:
            add(CONFIRM, 'AMOUNT_RATIO',
                f'认购合计 {total:,.2f} 是项目规模 {expected_size:,.2f} 的 {ratio:,.1f} 倍，'
                '高于常见申购倍数，请核对金额与规模口径。')
    elif expected_size is None:
        add(INFO, 'NO_EXPECTED_SIZE', '台账中找不到该项目的发行规模，跳过金额倍数校验。')

    # 利率：多值拼接、缺失、纯文本
    multi = [(section['sheet'], section['layer']) for section in sections if section['rates']['multi']]
    text = [(section['sheet'], section['layer']) for section in sections if section['rates']['text']]
    missing = [section['layer'] for section in sections
               if section['rows'] and section['rates']['missing'] == section['rows']]
    if multi:
        add(CONFIRM, 'RATE_MULTI',
            '这些分层的利率单元格里写了多个价格，需先确认按哪个价格录入：'
            + '、'.join(f'{sheet}/{layer}' for sheet, layer in multi[:4]))
    if text:
        add(CONFIRM, 'RATE_TEXT',
            '这些分层的利率不是数字（含文字或备注），需先清洗：'
            + '、'.join(f'{sheet}/{layer}' for sheet, layer in text[:4]))
    if missing:
        add(CONFIRM, 'RATE_MISSING',
            '这些分层所有认购行都没有利率，可能是价格写在别处或未披露：'
            + '、'.join(missing[:4]))

    # 分层命名：多档位却用泛化层名
    layers = [section['layer'] for section in sections]
    generic = {'优先', '优先级', '优先A级', '优先B级'}
    ambiguous = {layer for layer in layers if layer in generic}
    # “优先A”与“优先A1/A2”并存时，前者太粗，A1/A2 会被合并进同一层
    for layer in layers:
        for other in layers:
            if other != layer and other.startswith(layer) and other[len(layer):].isdigit():
                ambiguous.add(layer)
    ambiguous = sorted(ambiguous)
    if len(set(layers)) > 1 and ambiguous:
        add(CONFIRM, 'LAYER_AMBIGUOUS',
            '文件里有多个档位，但部分表头只写了“' + '、'.join(ambiguous)
            + '”，A1/A2 可能混在一起，需确认档位名称。')
    if len(set(layers)) < len(layers):
        duplicated = sorted({layer for layer in layers if layers.count(layer) > 1})
        add(INFO, 'LAYER_REPEATED',
            '同一档位在多个位置重复出现，录入时会按“机构+价格+档位”合并：'
            + '、'.join(duplicated))

    for sheet in scanned:
        if len(sheet['sections']) > 1:
            add(INFO, 'MULTI_SECTION',
                f"工作表“{sheet['sheet']}”含 {len(sheet['sections'])} 个分层段，将逐段读取。")

    if project['viaAlias']:
        add(INFO, 'ALIAS_REGISTERED',
            f"文件名经别名表映射为“{project['canonical']}”。")

    levels = {item['level'] for item in findings}
    verdict = '不可录' if BLOCK in levels else ('需确认' if CONFIRM in levels else '可录')
    return {
        'file': path.name,
        'path': str(path),
        'project': project,
        'expectedSize': expected_size,
        'total': total,
        'largest': largest,
        'sections': sections,
        'findings': findings,
        'verdict': verdict,
    }


def format_report(report: dict) -> list[str]:
    """控制台可读清单：先结论，再逐条提示。"""
    lines = [f"[预检] {report['file']} → {report['verdict']}"]
    project = report['project']
    target = project['canonical']
    if report['sections']:
        sizes = '、'.join(f"{section['layer']} {section['rows']} 行" for section in report['sections'])
        lines.append(f"       项目：{target}｜分层：{sizes}｜认购合计 {report['total']:,.4f}")
    for item in report['findings']:
        if item['level'] == INFO:
            continue
        lines.append(f"       [{item['level']}] {item['message']}")
    return lines


def summarize(reports) -> str:
    ok = sum(1 for report in reports if report['verdict'] == '可录')
    confirm = sum(1 for report in reports if report['verdict'] == '需确认')
    blocked = sum(1 for report in reports if report['verdict'] == '不可录')
    return f'可录 {ok} · 需确认 {confirm} · 不可录 {blocked}'
