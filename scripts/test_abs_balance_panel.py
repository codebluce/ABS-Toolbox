"""消金ABS余额的季度过滤、明细守恒及整合来源验证。"""
import json
import unittest
import abs_balance_panel
import asset_issuance_panel


class AbsBalancePanelTest(unittest.TestCase):
    def test_quarter_dates_and_conservation(self):
        data = abs_balance_panel.compute_data()
        self.assertEqual(len(data['periods']), 10)
        self.assertTrue(all(int(p['date'][5:7]) in (3, 6, 9, 12) for p in data['periods']))
        for period in data['periods']:
            self.assertAlmostEqual(sum(r['total'] for r in period['records']), period['total'])
            self.assertAlmostEqual(sum(period['channels'].values()), period['total'], places=2)
        self.assertAlmostEqual(data['periods'][-1]['total'], 2240.6)
        self.assertNotIn('2024-08', abs_balance_panel.render_document())

    def test_balance_tampering_rejected(self):
        data = asset_issuance_panel.compute_data(asset_issuance_panel.SOURCES['2026'])
        document = asset_issuance_panel.render_document(data)
        marker = '<script id="consumer-abs-data" type="application/json">'
        encoded = document.split(marker, 1)[1].split('</script>', 1)[0]
        pages = json.loads(encoded)
        self.assertNotIn('Demo', pages['balance'])
        self.assertNotIn('新增发行口径', pages['balance'])
        pages['balance'] = pages['balance'].replace('存续余额合计', '错误合计')
        bad = document.replace(encoded, json.dumps(pages, ensure_ascii=False).replace('<', '\\u003c'))
        with self.assertRaisesRegex(ValueError, '陈旧或内容不一致'):
            asset_issuance_panel.verify_document(bad, asset_issuance_panel.SOURCES['2026'])
