"""次级速查在综合看板中的注册、样式隔离和数据嵌入回归测试。"""

import json
from pathlib import Path
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import secondary_allocation_panel as allocation
from gen_integrated_dashboard import build_integrated_html, verify_integrated_html


class SecondaryAllocationIntegrationTest(unittest.TestCase):
    def test_progress_subtabs_and_panel_route(self):
        panels = [
            ('progress', 'allocation_quick', allocation.render_body()),
            ('progress', 'quick', '<div>机构速查</div>'),
            ('progress', 'inst_stats', '<div>机构统计</div>'),
            ('progress', 'credit_total', '<div>授信数据</div>'),
        ]
        html = build_integrated_html(panels, allocation.ALLOCATION_CSS)
        labels = re.findall(r'<button class="sub-tab-button"[^>]+>([^<]+)</button>', html)
        self.assertEqual(labels, ['次级速查', '机构速查', '机构统计', '授信速查'])
        self.assertIn('class="panel" data-module="progress" data-sub="allocation_quick"', html)
        self.assertIn('function selectSub(sub)', html)
        self.assertEqual(verify_integrated_html(html, 4), [])
        self.assertNotIn('LAB · 独立预览', html)
        self.assertIn('本地快照，不实时同步', html)

    def test_embedded_snapshot_keeps_raw_records_and_groups_approved_names(self):
        html = allocation.render_body()
        match = re.search(r'<script id="alloc-snapshot" type="application/json">(.*?)</script>', html, re.S)
        self.assertIsNotNone(match)
        data = json.loads(match.group(1))
        rows = [r for r in data['records'] if r['month'] == '9月' and r['investor'] == '中信证券']
        self.assertEqual(len(rows), 5)
        self.assertEqual(sum(r['amount_wan'] for r in rows if r['level'] == '次级'), 3000)
        self.assertEqual(sum(r['amount_wan'] for r in rows if r['level'] == '夹层'), 2500)
        aliases = data['investor_aliases']
        self.assertEqual(aliases, allocation.load_aliases())
        self.assertIn('canonical(r.investor) === selected && r.month === month.value', html)
        grouped = [r for r in data['records'] if r['month'] == '9月'
                   and aliases.get(r['investor'], r['investor']) == '中信证券']
        self.assertEqual(len(grouped), 6)
        self.assertEqual(sum(r['amount_wan'] for r in grouped), 6500)
        self.assertEqual({r['investor'] for r in grouped}, {'中信证券', '中信自营'})

    def test_confirmed_mapping_boundaries_and_conservation(self):
        aliases = allocation.load_aliases()
        from abs_common import normalize_investor_name
        from institution_identity import aliases as global_aliases
        historical = json.loads(allocation.ALIASES_PATH.read_text(encoding='utf-8'))
        self.assertEqual(aliases, global_aliases())
        self.assertEqual(len(historical), 18)
        for old, target in historical.items():
            self.assertEqual(aliases[old], normalize_investor_name(target))
        self.assertEqual(aliases['广发证券（资管）'], '广发资管')
        self.assertNotIn('广发证券', aliases)
        for independent in (
            '广发资管', '中信投顾', '中信财富', '中金投顾', '中金财富',
            '建投投顾', '建投机构部', '建投衍生品', '中建投信托',
        ):
            self.assertNotIn(independent, aliases)
        rows = allocation.load_snapshot()['records']
        original_names = {r['investor'] for r in rows}
        grouped_names = {aliases.get(r['investor'], r['investor']) for r in rows}
        self.assertEqual((len(rows), len(original_names), len(grouped_names)), (989, 70, 52))
        self.assertEqual(sum(r['amount_wan'] for r in rows), 1492845)
        self.assertTrue(set(historical).issubset(original_names))
        self.assertEqual(aliases['中泰自营'], aliases['中泰证券'])

    def test_search_alias_points_to_canonical_without_changing_detail_name(self):
        html = allocation.render_body()
        self.assertIn("originalsByName.get(name).add(r.investor)", html)
        self.assertIn("name.toLocaleLowerCase('zh-CN').includes(query)", html)
        self.assertIn("canonical(r.investor) === name && r.month === month.value", html)
        self.assertIn("td(tr,record.investor,'investor')", html)

    def test_search_caption_and_source_coordinates_not_displayed(self):
        body = allocation._BODY_HTML
        script = allocation._JS
        self.assertNotIn('与「机构速查」一致', body)
        self.assertNotIn('中信证券 / 中信投顾', body)
        self.assertNotIn('项目名称 / 来源', body)
        self.assertIn('<th>项目名称</th>', body)
        self.assertNotIn('project-sub', script)
        self.assertNotIn('record.source', script)
        self.assertNotIn('record.section', script)
        # 快照仍保留原表坐标，方便后续核对，前端明细不展示。
        self.assertIn('source', allocation.load_snapshot()['records'][0])

    def test_css_is_scoped_and_script_uses_panel_root(self):
        for line in allocation.ALLOCATION_CSS.splitlines():
            if '{' in line and not line.strip().startswith(('/*', '@')):
                self.assertTrue(line.strip().startswith('#alloc-quick'), line)
        self.assertIn("const get = id => root.querySelector('#' + id);", allocation.render_body())

    def test_untrusted_snapshot_text_cannot_close_script(self):
        html = allocation.render_body({'records': [{'investor': '</script><svg onload=alert(1)>'}]})
        self.assertNotIn('</script><svg', html)
        self.assertIn('\\u003c/script\\u003e', html)

    def test_missing_snapshot_fails_build(self):
        with mock.patch.object(allocation, 'SNAPSHOT_PATH', Path('/nonexistent/allocation_snapshot.json')):
            with self.assertRaises(FileNotFoundError):
                allocation.render_body()


if __name__ == '__main__':
    unittest.main()
