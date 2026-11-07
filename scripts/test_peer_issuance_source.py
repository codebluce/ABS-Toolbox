"""同业底稿来源校验：只认完整已录底稿，且期数/规模不得回退。"""
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

import peer_issuance_source as source


class NamingTest(unittest.TestCase):
    def test_working_paper_name_carries_business_date(self):
        self.assertEqual(
            source.working_paper_date(Path('同业发行完整已录底稿_20261106.xlsx')), '20261106')

    def test_raw_weekly_report_is_rejected(self):
        with self.assertRaises(source.PeerIssuanceSourceError):
            source.working_paper_date(Path('互联网金融ABS内部信息共享-更新至20261106.xlsx'))
        with self.assertRaises(source.PeerIssuanceSourceError):
            source.working_paper_date(Path('同业发行完整已录底稿-20261106.xlsx'))


class ResolutionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)
        for name in ('同业发行完整已录底稿_20261030.xlsx',
                     '同业发行完整已录底稿_20261106.xlsx',
                     '互联网金融ABS内部信息共享-更新至20261106.xlsx'):
            (self.folder / name).touch()

    def tearDown(self):
        self.tmp.cleanup()

    def test_latest_working_paper_skips_raw_reports(self):
        latest = source.resolve_latest_working_paper(self.folder)
        self.assertEqual(latest.name, '同业发行完整已录底稿_20261106.xlsx')

    def test_source_must_live_in_fixed_folder(self):
        outside = self.folder / '同业发行完整已录底稿_20261106.xlsx'
        with self.assertRaises(source.PeerIssuanceSourceError):
            source.verify_source(outside, folder=self.folder / 'other')

    def test_empty_folder_is_an_error(self):
        empty = self.folder / 'empty'
        empty.mkdir()
        with self.assertRaises(source.PeerIssuanceSourceError):
            source.resolve_latest_working_paper(empty)

    def _fake_summarize(self, records, amounts):
        def summarize(path):
            date_text = source.working_paper_date(Path(path))
            return {'path': Path(path), 'date': date_text,
                    'records': records[date_text],
                    'amount': Decimal(amounts[date_text])}
        return summarize

    def test_regression_blocks_by_default(self):
        fake = self._fake_summarize({'20261030': 623, '20261106': 600},
                                    {'20261030': '5282.23', '20261106': '5165.00'})
        with mock.patch.object(source, 'summarize', side_effect=fake):
            with self.assertRaises(source.PeerIssuanceSourceError):
                source.verify_not_regressing(
                    self.folder / '同业发行完整已录底稿_20261106.xlsx', self.folder)

    def test_regression_can_be_allowed_explicitly(self):
        fake = self._fake_summarize({'20261030': 623, '20261106': 600},
                                    {'20261030': '5282.23', '20261106': '5165.00'})
        with mock.patch.object(source, 'summarize', side_effect=fake):
            result = source.verify_not_regressing(
                self.folder / '同业发行完整已录底稿_20261106.xlsx', self.folder,
                allow_fewer=True)
        self.assertEqual(len(result['problems']), 2)
        self.assertEqual(result['previous']['date'], '20261030')

    def test_growth_passes(self):
        fake = self._fake_summarize({'20261030': 594, '20261106': 623},
                                    {'20261030': '5031.05', '20261106': '5282.23'})
        with mock.patch.object(source, 'summarize', side_effect=fake):
            result = source.verify_not_regressing(
                self.folder / '同业发行完整已录底稿_20261106.xlsx', self.folder)
        self.assertEqual(result['problems'], [])
        self.assertIsNotNone(result['previous'])

    def test_first_working_paper_has_no_baseline(self):
        fake = self._fake_summarize({'20261030': 594}, {'20261030': '5031.05'})
        with mock.patch.object(source, 'summarize', side_effect=fake):
            result = source.verify_not_regressing(
                self.folder / '同业发行完整已录底稿_20261030.xlsx', self.folder)
        self.assertIsNone(result['previous'])


if __name__ == '__main__':
    unittest.main()
