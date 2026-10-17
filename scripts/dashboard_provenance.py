"""综合看板全量来源门禁：局部簿记刷新不得伪装成所有台账消费者已更新。"""
from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / 'scripts'
BLOCK_ID = 'abs-ledger-provenance'
SCHEMA = 'abs-integrated-ledger/v1'
# 影响其他台账消费者的生产实现；簿记组件由自身门禁另行校验。
PRODUCERS = (
    'gen_integrated_dashboard.py', 'gen_abs_cost_report.py', 'gen_spread_report.py',
    'gen_compare_tool.py', 'gen_investment_ledger.py', 'gen_pricing_insight.py',
    'gen_institution_profile.py', 'gen_institution_stats.py', 'abs_common.py',
    'ledger_formula_tools.py',
    'entity_alias.py', 'institution_identity.py', 'dashboard_provenance.py',
    'itl_panel.js', 'itl_panel.css', 'itl_chat.js', 'itl_chat.css',
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def producer_sha256():
    digest = hashlib.sha256()
    for name in PRODUCERS:
        digest.update(name.encode())
        digest.update((SCRIPT_DIR / name).read_bytes())
    return digest.hexdigest()


def add_full_generation_provenance(document, ledger, *, source_hash):
    """仅完整生成入口调用；局部刷新不能重新签发全量来源证明。"""
    if source_hash != sha256(ledger):
        raise ValueError('完整生成期间台账已变更，请重新生成全部台账面板')
    marker = {'schema': SCHEMA, 'generation': 'full', 'source': Path(ledger).name,
              'sourceSha256': source_hash, 'producerSha256': producer_sha256()}
    encoded = json.dumps(marker, ensure_ascii=False, separators=(',', ':'))
    encoded = encoded.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    if document.count('</body>') != 1:
        raise ValueError('完整看板body边界不唯一')
    return document.replace('</body>', f'<script id="{BLOCK_ID}" type="application/json">{encoded}</script></body>', 1)


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.payloads, self.active, self.parts = [], False, []
    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('id') == BLOCK_ID:
            self.active, self.parts = True, []
    def handle_data(self, value):
        if self.active:
            self.parts.append(value)
    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.payloads.append(''.join(self.parts))
            self.active = False


def verify_full_generation(document, ledger):
    parser = _Parser(); parser.feed(document)
    if len(parser.payloads) != 1:
        raise ValueError('缺少唯一全量台账来源证明；局部刷新或旧看板不能发布，请完整重新生成')
    marker = json.loads(parser.payloads[0])
    if marker.get('schema') != SCHEMA or marker.get('generation') != 'full':
        raise ValueError('看板不是受控全量生成产物，禁止发布')
    if marker.get('source') != Path(ledger).name or marker.get('sourceSha256') != sha256(ledger):
        raise ValueError('其他台账面板来源陈旧；簿记局部更新不代表全量同步，请完整重新生成')
    if marker.get('producerSha256') != producer_sha256():
        raise ValueError('全量生成实现已更新，请重新生成所有台账面板后发布')
    return marker
