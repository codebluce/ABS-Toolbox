"""风险表现定稿内容与快照门禁。"""
import json
import unittest
import risk_performance_panel as panel
from gen_integrated_dashboard import build_integrated_html

class RiskPerformanceTest(unittest.TestCase):
    def test_confirmed_periods_and_disclosure_scope(self):
        data=panel.compute_data()
        self.assertEqual(len(data['periods']['dynamic']),9)
        self.assertEqual(len(data['periods']['static']),5)
        self.assertEqual(data['periods']['dynamic'][-1]['date'],'2026-06-01')
        self.assertEqual(data['periods']['static'][-1]['date'],'2025-12-31')
        dynamic=data['pages']['dynamic']
        self.assertNotIn('<div class="balance">',dynamic)
        static=data['pages']['static']
        self.assertNotIn('白条取现\\n（不披露）',static)
        marker='<script id="static-data" type="application/json">'
        values=json.loads(static.split(marker)[1].split('</script>')[0])
        self.assertEqual([r['name'] for r in values['periods'][-1]['records']],['赊销白条','信托白条','金条','现金贷整体'])
        self.assertNotIn('0.0225',static)
        self.assertIn("if(!index)return ''",static)
        self.assertIn("change.toFixed(2)+' 个百分点'",static)

    def test_roundtrip_and_modified_document_fails(self):
        document=panel.extract_document(panel.render_body())
        panel.verify_document(document)
        with self.assertRaisesRegex(ValueError,'陈旧'):
            panel.verify_document(document.replace('风险表现','旧面板',1))
        with self.assertRaisesRegex(ValueError,'缺失或重复'):
            panel.extract_document(panel.render_body()+panel.render_body())

    def test_asset_overview_subtab(self):
        html=build_integrated_html([('asset_overview','risk_performance',panel.render_body())],'')
        self.assertIn('>风险表现</button>',html)
        self.assertEqual(panel.extract_document(html),panel.render_document(panel.compute_data()))

if __name__=='__main__':unittest.main()
