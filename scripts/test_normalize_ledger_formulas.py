import tempfile
import unittest
from pathlib import Path

import openpyxl

from normalize_ledger_formulas import normalize_formula_cells


class NormalizeLedgerFormulasTest(unittest.TestCase):
    def test_arithmetic_refs_percent_and_original_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'x.xlsx'
            wb = openpyxl.Workbook()
            ws = wb.active
            ws['A1'] = 10
            ws['B1'] = 0.2
            ws['C1'] = '=A1*B1'
            ws['D1'] = '=2.28%+0.6%'
            ws['E1'] = '=-A1'
            wb.save(path)
            wb.close()
            wb = openpyxl.load_workbook(path)
            ws = wb.active
            self.assertEqual(normalize_formula_cells(ws), 3)
            self.assertAlmostEqual(ws['C1'].value, 2.0)
            self.assertAlmostEqual(ws['D1'].value, 0.0288)
            self.assertAlmostEqual(ws['E1'].value, -10.0)
            wb.close()
            original = openpyxl.load_workbook(path).active
            self.assertEqual(original['C1'].value, '=A1*B1')


if __name__ == '__main__':
    unittest.main()
