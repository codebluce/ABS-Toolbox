"""Lab 次级/夹层速查快照与字段映射的回归用例。"""

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import secondary_allocation_quick as preview


class AllocationPreviewTests(unittest.TestCase):
    def test_april_uses_allocated_amounts_not_reported_amounts(self):
        rows = [
            ['资产类型', '序号', '项目名称', '牵头管理人', '期限', '投资人',
             '次级券报量', '分量', '价格', '溢价率', '小计（万）', '投资人',
             '中间级报量', '分量', '夹层价格', '小计（万）',
             '项目规模（亿）', '分层比例', '原始权益人', '状态'],
            ['白条', '1', '禾昱9-2', '华泰', '12+5+15+3', '中信证券（换券）',
             '4750', '1200', '4.50%', '0%', '4750', '中信证券（换券）',
             '1900', '400', '3.10%', '1900', '10', '90:3:2:5', '世纪贸易', '开放'],
        ]
        allocations = preview.parse_main('4月', rows)
        self.assertEqual([(r['level'], r['amount_wan']) for r in allocations],
                         [('次级', 1200), ('夹层', 400)])
        self.assertEqual([r['source'] for r in allocations],
                         ['4月!F2/H2', '4月!L2/N2'])
        self.assertEqual(allocations[1]['premium'], '—')

    def test_march_reported_junior_amount_does_not_count(self):
        rows = [
            ['资产类型', '序号', '项目名称', '牵头管理人', '期限', '投资人',
             '次级券报量', '价格', '溢价率', '小计（万）', '投资人',
             '分量', '夹层价格', '小计（万）', '项目规模（亿）', '分层比例',
             '原始权益人', '状态'],
            ['赊销白条', '1', '某项目', '招证', '12+12', '中信证券',
             '750', '5.05%', '0%', '5000', '中信证券', '1000',
             '3.10%', '2000', '10', '90:3:2:5', '外贸信托', '开放'],
        ]
        allocations = preview.parse_main('3月', rows)
        self.assertEqual([(r['level'], r['amount_wan']) for r in allocations], [('夹层', 1000)])

    def test_standalone_3_to_1_is_converted_from_yi_to_wan(self):
        rows = [['', '3：1结构化次级-JPM【第三期】'],
                ['', '11+13，15e'], ['', '投资人', '分量', '合计'],
                ['', '次级：3.7%'], ['', '中信证券', '1.85', '3.75']]
        allocations = preview.parse_structured('6月', rows)
        self.assertEqual(len(allocations), 1)
        self.assertEqual(allocations[0]['amount_wan'], 18500)
        self.assertEqual(allocations[0]['original_amount'], '1.85亿')
        self.assertEqual(allocations[0]['scale'], '15')

    def test_nine_months_snapshot_and_exact_september_match(self):
        data = json.loads(preview.SNAPSHOT_PATH.read_text(encoding='utf-8'))
        self.assertEqual({r['month'] for r in data['records']}, set(preview.MONTHS))
        rows = [r for r in data['records'] if r['month'] == '9月'
                and r['investor'] == '中信证券']
        self.assertEqual(len(rows), 5)
        self.assertEqual(sum(r['amount_wan'] for r in rows if r['level'] == '次级'), 3000)
        self.assertEqual(sum(r['amount_wan'] for r in rows if r['level'] == '夹层'), 2500)
        self.assertEqual(len({r['project'] for r in rows}), 4)
        self.assertEqual([r['source'] for r in rows], [
            '9月!K6/L6', '9月!K11/L11', '9月!F20/G20',
            '9月!K20/L20', '9月!F33/G33',
        ])

    def test_source_text_cannot_close_embedded_json_script(self):
        html = preview.build_preview({'records': [{'investor': '</script><img src=x onerror=alert(1)>'}]})
        self.assertNotIn('</script><img', html)
        self.assertIn('\\u003c/script\\u003e', html)


if __name__ == '__main__':
    unittest.main()
