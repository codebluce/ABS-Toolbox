"""投资台账明细清单排序：簿记时间倒序、同日份额降序、缺日期置底。"""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InvestmentLedgerDetailSortTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node.js unavailable')
    def test_detail_sorted_by_bookkeeping_date_desc(self):
        source = (ROOT / 'scripts/itl_panel.js').read_text(encoding='utf-8')
        js = """
const vm = require('vm');
const context = {window: {ITL_DATA: []}};
vm.runInNewContext(%s, context);
const rows = [
  {proj: 'old', date: '2026-01-08', share: 9},
  {proj: 'new', date: '2026-10-27', share: 1},
  {proj: 'same-a', date: '2026-10-27', share: 0.5},
  {proj: 'same-b', date: '2026-10-27', share: 2},
  {proj: 'missing', date: null, share: 99},
  {proj: 'prev-year', date: '2025-12-31', share: 3}
];
console.log(JSON.stringify(context.window.ITL.sortDetailRecords(rows).map(r => r.proj)));
""" % json.dumps(source, ensure_ascii=False)
        proc = subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(proc.stdout),
                         ['same-b', 'new', 'same-a', 'old', 'prev-year', 'missing'])


if __name__ == '__main__':
    unittest.main()
