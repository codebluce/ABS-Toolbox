"""资产分布快照、缺失及来源验证。"""
import unittest
from unittest.mock import patch

import asset_distribution_panel as panel
from gen_integrated_dashboard import build_integrated_html


class AssetDistributionTest(unittest.TestCase):
    def test_latest_source_amounts_and_missing_values(self):
        data = panel.compute_data()
        self.assertEqual(len(data['periods']), 12)
        self.assertTrue(all(p['date'] >= '2023-01-01' for p in data['periods']))
        self.assertEqual(data['periods'][-1]['date'], '2026-06-01')
        self.assertEqual([a['totals'][-1] for a in data['assets']], [1470, 3700, 515])
        self.assertEqual(sum(a['totals'][-1] for a in data['assets']), 5685)
        self.assertEqual([p['values'][-1] for p in data['assets'][0]['parts']], [746, 268, 64, 52, 340])
        self.assertIsNone(data['assets'][0]['parts'][2]['values'][0])

    def test_component_roundtrip_and_stale_data_blocked(self):
        data = panel.compute_data()
        document = panel.extract_document(panel.render_body(data))
        panel.verify_document(document)
        self.assertNotIn('未披露差额', document)
        self.assertNotIn('历史资金结构', document)
        self.assertNotIn('DEMO', document)
        self.assertIn('四舍五入后可能与合计有最多2亿元差', document)
        data['assets'][0]['totals'][-1] = 1
        with self.assertRaisesRegex(ValueError, '陈旧'):
            panel.verify_document(panel.render_document(data))
        with self.assertRaisesRegex(ValueError, '缺失或重复'):
            panel.extract_document(panel.render_body() + panel.render_body())

    def test_subtab_order_and_replacement(self):
        html = build_integrated_html([
            ('asset_overview', 'asset_distribution', panel.render_body()),
            ('asset_overview', 'issuance_statistics', '<p>发行统计</p>')], '')
        self.assertLess(html.index('>发行统计</button>'), html.index('>消金资产</button>'))
        self.assertNotIn('data-sub="consumer_asset"', html)


if __name__ == '__main__':
    unittest.main()
