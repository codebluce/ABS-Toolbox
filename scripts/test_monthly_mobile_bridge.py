"""Monthly desktop source bridge: controlled temp ledgers, real gate and mobile compatibility."""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from openpyxl import Workbook

import gen_mobile_dashboard as mobile
import latest_bookkeeping_panel as panel
import latest_bookkeeping_qc as qc
from lab import monthly_bid_institutions_demo as renderer
from lab import monthly_bookkeeping_qc as gate
from test_monthly_bookkeeping_integration import HEADERS, source_row


class MonthlyMobileBridgeTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='monthly-mobile-bridge-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.controlled = self.root / 'deliverables/ledger/03_final'
        self.controlled.mkdir(parents=True)
        self.ledger = self.controlled / '2026年ABS发行台账-1016-定稿.xlsx'
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = '总表'
        sheet.append(HEADERS)
        sheet.append(source_row())
        workbook.save(self.ledger)
        workbook.close()
        self.latest = panel.compute_data(self.ledger)
        self.monthly = renderer.compute_monthly(self.ledger)
        self.html = renderer.build_document(self.latest, self.monthly)
        patch = mock.patch.object(mobile, 'MONTHLY_LEDGER_DIR', self.controlled)
        patch.start()
        self.addCleanup(patch.stop)

    def changed_html(self, change):
        monthly = copy.deepcopy(self.monthly)
        latest = copy.deepcopy(self.latest)
        change(latest, monthly)
        return renderer.build_document(latest, monthly)

    def test_real_gate_receives_controlled_source(self):
        with mock.patch.object(gate, 'verify_html', wraps=gate.verify_html) as verify:
            self.assertEqual(mobile.verify_desktop_bookkeeping_source(self.html)['status'], 'PASS')
            verify.assert_called_once_with(self.html, self.ledger.resolve(), raise_on_fail=True)

    def test_missing_source_and_arbitrary_paths_fail_before_gate(self):
        for source in (None, '', '../' + self.ledger.name, str(self.ledger),
                       '2025年ABS发行台账-1016-定稿.xlsx',
                       '2026年ABS发行台账-1016-定稿Xxlsx'):
            with self.subTest(source=source):
                html = self.changed_html(lambda latest, monthly: monthly['provenance'].update(source=source))
                with mock.patch.object(qc, 'verify_html', side_effect=AssertionError('unsafe gate call')):
                    with self.assertRaisesRegex(ValueError, '来源缺失或非法'):
                        mobile.verify_desktop_bookkeeping_source(html)

    def test_missing_controlled_file_fails(self):
        self.ledger.unlink()
        with self.assertRaisesRegex(ValueError, '源台账缺失'):
            mobile.verify_desktop_bookkeeping_source(self.html)

    def test_symlink_escape_fails(self):
        outside = self.root / self.ledger.name
        self.ledger.rename(outside)
        self.ledger.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, '受控03_final'):
            mobile.verify_desktop_bookkeeping_source(self.html)

    def test_source_and_hash_mismatch_fail(self):
        changes = (
            lambda latest, monthly: latest.update(source='different.xlsx'),
            lambda latest, monthly: monthly.update(source='different.xlsx'),
            lambda latest, monthly: monthly['provenance'].update(sourceSha256='0' * 64),
            lambda latest, monthly: monthly.update(sourceSha256='0' * 64),
            lambda latest, monthly: latest['provenance'].update(sourceSha256='0' * 64),
        )
        for change in changes:
            with self.subTest(change=change):
                with self.assertRaisesRegex(ValueError, 'sourceSha256不一致'):
                    mobile.verify_desktop_bookkeeping_source(self.changed_html(change))

    def test_changed_ledger_fails(self):
        self.ledger.write_bytes(self.ledger.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'sourceSha256不一致'):
            mobile.verify_desktop_bookkeeping_source(self.html)

    def test_monthly_gate_failure_and_actual_html_tamper_fail(self):
        with mock.patch.object(gate, 'verify_html', return_value={'status': 'FAIL', 'issues': []}):
            with self.assertRaisesRegex(ValueError, '门禁未通过'):
                mobile.verify_desktop_bookkeeping_source(self.html)
        with self.assertRaises(ValueError):
            mobile.verify_desktop_bookkeeping_source(self.html.replace('id="lb-monthly-head"', 'id="removed"'))

    def test_orphan_duplicate_and_encoded_markers_fail(self):
        for content in ('<div class="lb-monthly-unknown"></div>',
                        "<div class='lb&#45;monthly-unknown'></div>",
                        self.html + '<script id="lb-monthly-data" type="application/json">{}</script>'):
            with self.subTest(content=content[-100:]):
                with self.assertRaises(ValueError):
                    mobile.verify_desktop_bookkeeping_source(content)
                with self.assertRaises(ValueError):
                    mobile.verify_mobile_bookkeeping(content, '')

    def test_legacy_default_does_not_load_monthly_or_require_source(self):
        html = '<html><style>' + panel.BOOKKEEPING_CSS + '</style>' + panel.render_body(self.latest) + '</html>'
        self.ledger.unlink()
        with mock.patch.object(qc, '_load_monthly_qc', side_effect=AssertionError('monthly default')):
            self.assertEqual(mobile.verify_desktop_bookkeeping_source(html), qc.verify_html(html))

    def build(self, html, name):
        desktop = self.root / (name + '.html')
        desktop.write_text(html, encoding='utf-8')
        with mock.patch.object(mobile, 'build_prog_quick', return_value=[{'name': '机构'}]), \
                mock.patch.object(mobile, 'build_meta', return_value={'same': True}), \
                mock.patch.object(mobile, 'build_asset', return_value={'kpis': [1]}), \
                mock.patch.object(mobile, 'build_peer', return_value={'groups': [], 'trust': [], 'top': [], 'colors': []}), \
                mock.patch.object(mobile, 'build_inst_stats', return_value=None), redirect_stdout(io.StringIO()):
            return mobile.build_mobile_html(desktop)

    def test_monthly_and_legacy_produce_identical_mobile_and_default_path(self):
        legacy = '<html><style>' + panel.BOOKKEEPING_CSS + '</style>' + panel.render_body(self.latest) + '</html>'
        monthly_path = self.build(self.html, 'monthly')
        legacy_path = self.build(legacy, 'legacy')
        self.assertEqual(monthly_path.name, 'monthly_手机版.html')
        self.assertEqual(monthly_path.read_bytes(), legacy_path.read_bytes())
        page = monthly_path.read_text(encoding='utf-8')
        marker = 'window.ABS_MOBILE_DATA='
        data, _ = json.JSONDecoder().raw_decode(page.split(marker, 1)[1])
        self.assertEqual(qc.extract_data(data['bookkeepingHtml']), self.latest)
        self.assertNotIn('lb-monthly', data['bookkeepingHtml'])
        mobile.verify_mobile_bookkeeping(self.html, page)
        with self.assertRaisesRegex(ValueError, '导航应用脚本'):
            mobile.verify_mobile_bookkeeping(self.html, page.replace("tab: 'bookkeeping'", "tab: 'peer'"))


if __name__ == '__main__':
    unittest.main()
