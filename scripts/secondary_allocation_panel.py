"""机构画像 > 次级速查：JoySpace 次级/夹层获配的本地快照面板。

快照来自《终版-26年次级分配》，由 lab/secondary_allocation_quick.py
按各月 sheet 导入；综合看板生成时嵌入快照，并不在线读取 JoySpace。
"""

from __future__ import annotations

import json
from pathlib import Path

from abs_common import normalize_investor_name
from institution_identity import aliases as global_aliases

SCRIPT_DIR = Path(__file__).resolve().parent
SNAPSHOT_PATH = SCRIPT_DIR.parent / 'data' / 'secondary_allocation_snapshot.json'
ALIASES_PATH = SCRIPT_DIR.parent / 'data' / 'secondary_allocation_aliases.json'
ALLOCATION_CSS = (SCRIPT_DIR / 'secondary_allocation_panel.css').read_text(encoding='utf-8')
_BODY_HTML = (SCRIPT_DIR / 'secondary_allocation_panel_body.html').read_text(encoding='utf-8')
_JS = (SCRIPT_DIR / 'secondary_allocation_panel.js').read_text(encoding='utf-8')


def load_snapshot() -> dict:
    """缺失或损坏的快照要使生成失败，不能输出貌似正常的空数据面板。"""
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding='utf-8'))
    if not isinstance(snapshot.get('records'), list) or not snapshot['records']:
        raise ValueError(f'次级配售快照无有效明细: {SNAPSHOT_PATH}')
    return snapshot


def load_aliases() -> dict[str, str]:
    """全局登记表是唯一执行来源；原次级文件作为历史批准清单校验完整性。"""
    historical = json.loads(ALIASES_PATH.read_text(encoding='utf-8'))
    mapped = global_aliases()
    if not isinstance(historical, dict) or any(
        not isinstance(source, str) or not isinstance(target, str)
        or not source or not target or mapped.get(source) != normalize_investor_name(target)
        for source, target in historical.items()
    ):
        raise ValueError(f'次级速查原有映射未完整推广至全局: {ALIASES_PATH}')
    return mapped



def render_body(snapshot: dict | None = None, *, preview: bool = False) -> str:
    snapshot = load_snapshot() if snapshot is None else snapshot
    # 不改快照原名；只在渲染时附加查询层映射。
    embedded = {**snapshot, 'investor_aliases': load_aliases()}
    # 内嵌 JSON 中的 HTML 特殊字符必须转义，避免源表文本闭合 script。
    data = json.dumps(embedded, ensure_ascii=False, separators=(',', ':'))
    data = (data.replace('&', '\\u0026').replace('<', '\\u003c')
                .replace('>', '\\u003e').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))
    preview_bar = (
        '<div class="preview-bar"><span><strong>ABS 综合台账</strong> / 机构画像 / '
        '次级与夹层配售速查</span><span class="preview-pill">LAB · 独立预览</span></div>'
        if preview else ''
    )
    return (f'<div id="alloc-quick">\n{preview_bar}\n{_BODY_HTML}\n'
            f'<script id="alloc-snapshot" type="application/json">{data}</script>\n'
            f'</div>\n<script>\n{_JS}\n</script>')
