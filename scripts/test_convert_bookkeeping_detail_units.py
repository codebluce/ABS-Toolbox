import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

import openpyxl

from convert_bookkeeping_detail_units import convert_detail_amounts


class ConvertDetailUnitsTest(unittest.TestCase):
    def test_wan_to_yi_and_original_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp) / 'src.xlsx'
            out = Path(temp) / 'out.xlsx'
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(['项目名称', None])
            ws.append(['簿记日期', None])
            ws.append(['管理人', None])
            ws.append([None, None])
            ws.append(['优先A申购利率', '穿透机构', '申购规模（亿元）'])
            ws.append([0.017, '甲', 12400])
            ws.append([0.017, '乙', 5000])
            ws.append([None, None, None])
            ws.append(['优先B申购利率', '穿透机构', '申购规模（亿元）'])
            ws.append([0.018, '丙', 3500])
            wb.save(src)
            wb.close()
            count = convert_detail_amounts(src, out, Decimal('10000'), '启赢3-4', '2026-10-26', '光大证券')
            self.assertEqual(count, 3)
            original = openpyxl.load_workbook(src).active
            self.assertEqual(original['C6'].value, 12400)
            converted = openpyxl.load_workbook(out).active
            self.assertEqual(converted['C6'].value, 1.24)
            self.assertEqual(converted['C7'].value, 0.5)
            self.assertEqual(converted['C10'].value, 0.35)
            self.assertEqual(converted['C5'].value, '申购规模（亿元）')
            self.assertEqual(converted['B1'].value, '启赢3-4')


if __name__ == '__main__':
    unittest.main()
