"""明细录入前预检：单位、利率、分层、项目名四类历史事故必须被检出。"""
import tempfile
import unittest
from pathlib import Path

import openpyxl

import detail_precheck


def build_detail(path, rows, *, header='优先A级申购利率（%）', note=None):
    book = openpyxl.Workbook()
    sheet = book.active
    if note:
        sheet['E1'] = note
        start = 2
    else:
        start = 1
    sheet.cell(row=start, column=1, value=header)
    sheet.cell(row=start, column=2, value='投资者名称')
    sheet.cell(row=start, column=3, value='申购规模（亿元）')
    for offset, (rate, name, amount) in enumerate(rows, start=start + 1):
        sheet.cell(row=offset, column=1, value=rate)
        sheet.cell(row=offset, column=2, value=name)
        sheet.cell(row=offset, column=3, value=amount)
    book.save(path)
    return path


class PrecheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.names = ['26东裕9号一期', '金采9-2']

    def tearDown(self):
        self.tmp.cleanup()

    def codes(self, report):
        return [item['code'] for item in report['findings']]

    def test_clean_detail_is_recordable(self):
        path = build_detail(self.dir / '金采玖2A项目簿记明细-20261103.xlsx',
                            [(0.025, '甲银行', 3.0), (0.026, '乙银行', 2.0)])
        report = detail_precheck.inspect(path, project_names=self.names, expected_size=10)
        self.assertEqual(report['verdict'], '可录', report['findings'])
        self.assertEqual(report['project']['canonical'], '金采9-2')
        self.assertTrue(report['project']['viaAlias'])
        self.assertAlmostEqual(report['total'], 5.0)

    def test_wan_yuan_amounts_block_recording(self):
        path = build_detail(self.dir / '金采玖2A项目簿记明细-20261103.xlsx',
                            [(0.025, '甲银行', 8000), (0.026, '乙银行', 12400)])
        report = detail_precheck.inspect(path, project_names=self.names, expected_size=10)
        self.assertEqual(report['verdict'], '不可录')
        self.assertIn('AMOUNT_UNIT', self.codes(report))

    def test_declared_wan_unit_blocks_recording(self):
        path = build_detail(self.dir / '金采玖2A项目簿记明细-20261103.xlsx',
                            [(0.025, '甲银行', 3.0)],
                            note='金额单位：万元')
        report = detail_precheck.inspect(path, project_names=self.names, expected_size=10)
        self.assertIn('UNIT_DECLARED_WAN', self.codes(report))

    def test_converted_note_is_not_flagged(self):
        path = build_detail(self.dir / '金采玖2A项目簿记明细-20261103.xlsx',
                            [(0.025, '甲银行', 3.0)],
                            note='金额单位：原始表为万元，已除以10000换算为亿元')
        report = detail_precheck.inspect(path, project_names=self.names, expected_size=10)
        self.assertNotIn('UNIT_DECLARED_WAN', self.codes(report))
        self.assertEqual(report['verdict'], '可录')

    def test_multi_price_cell_needs_confirmation(self):
        path = build_detail(self.dir / '金采玖2A项目簿记明细-20261103.xlsx',
                            [('2.50/2.60', '甲银行', 3.0), (0.026, '乙银行', 2.0)])
        report = detail_precheck.inspect(path, project_names=self.names, expected_size=10)
        self.assertEqual(report['verdict'], '需确认')
        self.assertIn('RATE_MULTI', self.codes(report))

    def test_truncated_layer_name_needs_confirmation(self):
        path = self.dir / '金采玖2A项目簿记明细-20261103.xlsx'
        book = openpyxl.Workbook()
        sheet = book.active
        sheet.append(['优先申购利率（%）', '投资者名称', '申购规模（亿元）'])
        sheet.append([0.025, '甲银行', 3.0])
        sheet.append(['优先B级申购利率（%）', '投资者名称', '申购规模（亿元）'])
        sheet.append([0.030, '乙银行', 2.0])
        book.save(path)
        report = detail_precheck.inspect(path, project_names=self.names, expected_size=10)
        self.assertIn('LAYER_AMBIGUOUS', self.codes(report))

    def test_unregistered_project_name_blocks_with_hint(self):
        path = build_detail(self.dir / '东裕9号一期项目簿记明细-20261201.xlsx',
                            [(0.025, '甲银行', 3.0)])
        report = detail_precheck.inspect(path, project_names=self.names, expected_size=10)
        self.assertEqual(report['verdict'], '不可录')
        self.assertIn('PROJECT_UNMATCHED', self.codes(report))
        self.assertEqual(report['project']['lookalikes'], ['26东裕9号一期'])

    def test_missing_file_and_empty_sheet(self):
        missing = detail_precheck.inspect(self.dir / '不存在.xlsx', project_names=self.names)
        self.assertIn('FILE_MISSING', self.codes(missing))

        empty = self.dir / '金采玖2A项目簿记明细-20261103.xlsx'
        openpyxl.Workbook().save(empty)
        report = detail_precheck.inspect(empty, project_names=self.names)
        self.assertIn('NO_SECTION', self.codes(report))
        self.assertEqual(report['verdict'], '不可录')

    def test_summary_counts_verdicts(self):
        reports = [{'verdict': '可录'}, {'verdict': '需确认'}, {'verdict': '不可录'}]
        self.assertEqual(detail_precheck.summarize(reports), '可录 1 · 需确认 1 · 不可录 1')


if __name__ == '__main__':
    unittest.main()
