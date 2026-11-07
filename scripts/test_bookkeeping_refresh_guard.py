"""簿记刷新与质控告警分级：月度看板不局部刷新，告警按级别统计。"""
import tempfile
import unittest
from pathlib import Path

import latest_bookkeeping_qc as qc
import update_latest_bookkeeping as update


class MonthlyGuardTest(unittest.TestCase):
    def test_refresh_skips_monthly_dashboard_without_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            dashboard = Path(tmp) / 'ABS综合看板_20261106.html'
            dashboard.write_text(
                '<html><body><div class="lb-monthly-root">月度簿记</div></body></html>',
                encoding='utf-8')
            # 台账路径故意不存在：只要提前返回，就不会读到它
            result = update.refresh(ledger=Path(tmp) / '不存在.xlsx', dashboard=dashboard)
        self.assertIsNone(result)

    def test_replace_panel_still_rejects_monthly_component(self):
        with self.assertRaises(ValueError):
            update.replace_panel('<div class="monthly-bookkeeping">x</div>', {})


class LevelCountTest(unittest.TestCase):
    def test_counts_and_format(self):
        report = {'issues': [{'level': 'FAIL'}, {'level': 'WARN'},
                             {'level': 'WARN'}, {'level': 'INFO'}]}
        self.assertEqual(qc.level_counts(report), {'FAIL': 1, 'WARN': 2, 'INFO': 1})
        self.assertEqual(qc.format_level_counts(report), 'FAIL 1 · WARN 2 · INFO 1')

    def test_unknown_level_does_not_crash(self):
        counts = qc.level_counts({'issues': [{'level': 'NOTICE'}]})
        self.assertEqual(counts['FAIL'], 0)
        self.assertEqual(counts['NOTICE'], 1)

    def test_known_source_gaps_are_informational(self):
        source_text = Path(qc.__file__).read_text(encoding='utf-8')
        for code in ('LAYER_SIZE_UNCACHED', 'NO_BIDS'):
            self.assertIn(f"issue('INFO', '{code}'", source_text)


if __name__ == '__main__':
    unittest.main()
