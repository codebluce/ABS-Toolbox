"""月度opt-in接入回归；仅临时台账/HTML与mock，不生成正式综合看板。"""
from __future__ import annotations

import argparse
from contextlib import ExitStack, redirect_stdout, redirect_stderr
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from openpyxl import Workbook

import gen_integrated_dashboard as generator
import latest_bookkeeping_panel as panel
import latest_bookkeeping_qc as qc
import update_latest_bookkeeping as updater
from lab import monthly_bid_institutions_demo as renderer
from lab import monthly_bookkeeping_qc as gate

HEADERS = ['序号', '月份', '类别', '资产类型', '项目名称', '发行场所', '计划管理人',
           '联席承销商', '托管行', '规模', '期限', '簿记时间', '国股CD', 'ALL-IN成本',
           '认购倍数', '分层情况', '分层占比', '对应金额（亿）', '评级', '成本',
           '认购机构', '认购份额', '申购利率', '穿透机构', '申购规模']


def source_row(project='测试项目', date='2026-05-06', allocation=2, project_size=20, layer_size=None):
    fields = {'资产类型': '赊销白条', '项目名称': project, '发行场所': '上交所',
              '计划管理人': '管理人', '规模': project_size, '期限': '21+3', '簿记时间': date,
              '分层情况': '优先A', '对应金额（亿）': layer_size, '成本': 0.02,
              '认购机构': '建设银行', '认购份额': allocation,
              '申购利率': 0.02, '穿透机构': '建设银行', '申购规模': 3}
    return [fields.get(name) for name in HEADERS]


class MonthlyIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='abs-monthly-integration-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ledger = self.root / '2026年ABS发行台账-1016-定稿.xlsx'
        self.write_source()

    def write_source(self, rows=None):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = '总表'
        sheet.append(HEADERS)
        for row in rows or [source_row()]:
            sheet.append(row)
        workbook.save(self.ledger)
        workbook.close()

    def legacy(self):
        data = panel.compute_data(self.ledger)
        return data, '<html><style>' + panel.BOOKKEEPING_CSS + '</style>' + panel.render_body(data) + '</html>'

    def test_default_contract_passes_without_loading_monthly(self):
        _, html = self.legacy()
        with mock.patch.object(qc, '_load_monthly_qc', side_effect=AssertionError('默认路径加载了月度QC')):
            self.assertEqual(qc.verify_html(html, self.ledger)['status'], 'PASS')
            self.assertEqual(qc.verify_html(html)['status'], 'PASS')

    def test_orphan_payload_and_unsupported_markers_fail(self):
        data, html = self.legacy()
        payloads = ('{bad JSON', json.dumps({'year': 2040, 'assets': {}}),
                    json.dumps({'provenance': {'schema': 'monthly-bookkeeping/unsupported'}}))
        candidates = [html + '<script id="lb-monthly-data" type="application/json">' + value + '</script>'
                      for value in payloads]
        candidates += [html + '<section class="lb-monthly-unsupported"></section>',
                       html + "<script id='lb&#45;monthly-data' type='application/json'>{}</script>",
                       html + '<div data-renderer="monthly-bookkeeping/v999"></div>']
        for candidate in candidates:
            with self.subTest(candidate=candidate[-130:]):
                with self.assertRaises(ValueError):
                    qc.verify_html(candidate, self.ledger)
                with mock.patch.object(panel, 'render_body', side_effect=AssertionError('已进入替换')):
                    with self.assertRaisesRegex(ValueError, '完整生成'):
                        updater.replace_panel(candidate, data)

    def test_valid_monthly_routes_to_gate_and_requires_ledger(self):
        data = panel.compute_data(self.ledger)
        monthly = renderer.compute_monthly(self.ledger)
        html = renderer.build_document(data, monthly)
        with mock.patch.object(qc, '_load_monthly_qc', return_value=gate), \
                mock.patch.object(gate, 'verify_html', wraps=gate.verify_html) as routed, \
                mock.patch.object(qc, 'check_data', wraps=qc.check_data) as recent:
            self.assertEqual(qc.verify_html(html, self.ledger)['status'], 'PASS')
            routed.assert_called_once_with(html, self.ledger, raise_on_fail=True)
            self.assertEqual(recent.call_count, 1)
        with self.assertRaisesRegex(ValueError, '源台账'):
            qc.verify_html(html)

    def test_legacy_updater_rejects_valid_monthly_before_rendering(self):
        data = panel.compute_data(self.ledger)
        html = renderer.build_document(data, renderer.compute_monthly(self.ledger))
        with mock.patch.object(panel, 'render_body', side_effect=AssertionError('已进入替换')):
            with self.assertRaisesRegex(ValueError, '--monthly-bookkeeping'):
                updater.replace_panel(html, data)

    def test_recursive_gate_callback_fails_and_context_is_reset(self):
        _, legacy = self.legacy()
        html = legacy + '<script id="lb-monthly-data" type="application/json">' + json.dumps(
            {'provenance': {'schema': gate.SCHEMA_VERSION}}) + '</script>'
        def callback(content, ledger, **kwargs):
            return qc.verify_html(content, ledger)
        with mock.patch.object(qc, '_load_monthly_qc', return_value=gate), \
                mock.patch.object(gate, 'verify_html', side_effect=callback) as routed:
            with self.assertRaisesRegex(ValueError, '避免递归'):
                qc.verify_html(html, self.ledger)
            self.assertEqual(routed.call_count, 1)
        self.assertEqual(qc.verify_html(legacy, self.ledger)['status'], 'PASS')

    def test_monthly_output_requires_new_local_html_outside_latest(self):
        parser = argparse.ArgumentParser()
        existing = self.root / 'previous.html'
        existing.write_text('上一版', encoding='utf-8')
        rejected = [None, 'https://example.com/test.html', str(existing), str(self.ledger),
                    str(self.root / 'nested/missing.html'), str(self.root / 'wrong.txt'),
                    str(generator.SCRIPT_DIR.parent / 'deliverables/dashboards/01_latest/monthly.html')]
        for value in rejected:
            with self.subTest(value=value), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    generator._monthly_output_path(parser, value, self.ledger)
        self.assertEqual(generator._monthly_output_path(parser, str(self.root / 'new.html'), self.ledger),
                         str((self.root / 'new.html').resolve()))
        self.assertEqual(existing.read_text(encoding='utf-8'), '上一版')

    def test_release_output_paths_allow_latest_and_reject_unsafe_targets(self):
        parser = argparse.ArgumentParser()
        latest = self.root / 'deliverables/dashboards/01_latest'
        latest.mkdir(parents=True)
        existing = latest / 'current.html'
        existing.write_text('上一版', encoding='utf-8')
        link = self.root / 'linked.html'
        link.symlink_to(existing)
        dangling = self.root / 'dangling.html'
        dangling.symlink_to(self.root / 'absent.html')
        hardlink = self.root / 'ledger.html'
        hardlink.hardlink_to(self.ledger)
        directory = self.root / 'directory.html'
        directory.mkdir()
        before = qc.file_sha256(self.ledger)
        with mock.patch.object(generator, 'SCRIPT_DIR', self.root / 'scripts'):
            for value in [str(existing), str(latest / 'new.html')]:
                self.assertEqual(generator._monthly_output_path(parser, value, self.ledger, release=True),
                                 str(Path(value).resolve()))
            default = generator._monthly_output_path(parser, None, self.ledger, release=True)
            self.assertEqual(Path(default).parent, latest.resolve())
            self.assertEqual(Path(default).suffix, '.html')
            for value in ['', 'https://example.com/page.html', str(self.ledger), str(link),
                          str(dangling), str(hardlink), str(directory),
                          str(self.root / 'missing/page.html'), str(self.root / 'wrong.txt')]:
                with self.subTest(value=value), redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        generator._monthly_output_path(parser, value, self.ledger, release=True)
        self.assertEqual(existing.read_text(encoding='utf-8'), '上一版')
        self.assertEqual(qc.file_sha256(self.ledger), before)

    def test_release_source_fail_preserves_previous_output_before_preprocess(self):
        self.write_source([source_row('一月冲突', '2026-01-06', 12.7, 10, 9),
                           source_row('五月项目', '2026-05-06'), source_row('六月项目', '2026-06-06'),
                           source_row('七月项目', '2026-07-06')])
        latest = self.root / 'deliverables/dashboards/01_latest'
        latest.mkdir(parents=True)
        target = latest / 'current.html'
        target.write_text('上一版', encoding='utf-8')
        before = qc.file_sha256(target)
        with mock.patch.object(generator, 'SCRIPT_DIR', self.root / 'scripts'), \
                mock.patch.object(sys, 'argv', ['generate', str(self.ledger), str(target), '--monthly-bookkeeping-release']), \
                mock.patch.object(panel, 'compute_data') as recent, \
                mock.patch('abs_common.preprocess_xlsx_for_pandas') as preprocess, \
                redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, 'MONTHLY_ALLOCATION_PROJECT_OVER'):
                generator.main()
        recent.assert_not_called()
        preprocess.assert_not_called()
        self.assertEqual(qc.file_sha256(target), before)
        self.assertEqual(list(latest.glob('*.qc-tmp')), [])

    def test_strict_opt_in_blocks_older_source_conflict_before_other_modules(self):
        self.write_source([source_row('一月冲突', '2026-01-06', 12.7, 10, 9),
                           source_row('五月项目', '2026-05-06'), source_row('六月项目', '2026-06-06'),
                           source_row('七月项目', '2026-07-06')])
        # 原最近三期合同不覆盖一月；全年门禁必须覆盖并阻断，不能warningpass。
        self.assertEqual(panel.compute_data(self.ledger)['qc']['status'], 'PASS')
        target = self.root / 'strict.html'
        before = qc.file_sha256(self.ledger)
        with mock.patch.object(sys, 'argv', ['generate', str(self.ledger), str(target), '--monthly-bookkeeping']), \
                mock.patch.object(panel, 'compute_data', side_effect=AssertionError('未先阻断月度源冲突')) as recent, \
                mock.patch('abs_common.preprocess_xlsx_for_pandas', side_effect=AssertionError('进入全量预处理')) as preprocess, \
                redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError) as caught:
                generator.main()
        self.assertIn('MONTHLY_ALLOCATION_PROJECT_OVER', str(caught.exception))
        self.assertIn('MONTHLY_ALLOCATION_LAYER_OVER', str(caught.exception))
        recent.assert_not_called()
        preprocess.assert_not_called()
        self.assertFalse(target.exists())
        self.assertFalse(Path(str(target) + '.qc-tmp').exists())
        self.assertEqual(qc.file_sha256(self.ledger), before)

    def test_prepare_rejects_changed_provenance_and_fail_return_value(self):
        monthly = renderer.compute_monthly(self.ledger)
        changed = copy.deepcopy(monthly)
        changed['provenance']['rulesSha256'] = 'changed-during-compute'
        with mock.patch.object(renderer, 'compute_monthly', return_value=changed):
            with self.assertRaisesRegex(ValueError, '计算期间变化'):
                generator._prepare_monthly_bookkeeping(self.ledger)
        with mock.patch.object(renderer, 'compute_monthly', return_value=monthly), \
                mock.patch.object(gate, 'verify_data', return_value={
                    'status': 'FAIL', 'issues': [{'level': 'FAIL', 'code': 'DATA03', 'message': '冲突'}]}):
            with self.assertRaisesRegex(ValueError, 'DATA03'):
                generator._prepare_monthly_bookkeeping(self.ledger)

    def test_strict_renderer_css_and_actual_html_gate_for_valid_source(self):
        module, monthly_qc, monthly = generator._prepare_monthly_bookkeeping(self.ledger)
        self.assertEqual(monthly['auditQc']['status'], 'PASS')
        self.assertFalse(monthly['auditQc']['releaseBlocked'])
        body = module.render_component(panel.compute_data(self.ledger), monthly, preview=True)
        html = generator.build_integrated_html([('pricing', 'bookkeeping', body)], module.component_css())
        self.assertEqual(monthly_qc.verify_html(html, self.ledger)['status'], 'PASS')
        self.assertEqual(qc.verify_html(html, self.ledger)['status'], 'PASS')
        self.assertNotIn('data-qc-status="FAIL"', body)

    def test_release_preserves_uncached_r_warning_and_project_fail(self):
        valid=source_row(layer_size='=J2*Q2')
        valid[HEADERS.index('分层占比')]=0.9
        self.write_source([valid])
        module, monthly_qc, monthly = generator._prepare_monthly_bookkeeping(self.ledger)
        self.assertTrue(any(item['code'] == 'MONTHLY_LAYER_SIZE_UNCACHED' and item['level'] == 'WARN'
                            for item in monthly['auditQc']['issues']))
        body = module.render_component(panel.compute_data(self.ledger), monthly, preview=False)
        html = generator.build_integrated_html([('pricing', 'bookkeeping', body)], module.component_css())
        self.assertEqual(monthly_qc.verify_html(html, self.ledger)['status'], 'PASS')
        invalid=source_row(allocation=21, project_size=20, layer_size='=J2*Q2')
        invalid[HEADERS.index('分层占比')]=0.9
        self.write_source([invalid])
        with self.assertRaisesRegex(ValueError, 'MONTHLY_ALLOCATION_PROJECT_OVER'):
            generator._prepare_monthly_bookkeeping(self.ledger)

    def test_block_cannot_be_disguised_as_pass(self):
        _, legacy = self.legacy()
        html = legacy + '<script id="lb-monthly-data" type="application/json">' + json.dumps(
            {'provenance': {'schema': gate.SCHEMA_VERSION}}) + '</script>'
        reports = [{'status': 'PASS', 'releaseStatus': 'BLOCK', 'issues': []},
                   {'status': 'PASS', 'issues': [{'level': 'FAIL', 'code': 'DATA03'}]}]
        for report in reports:
            with self.subTest(report=report):
                with self.assertRaises(ValueError):
                    generator._require_monthly_pass(report)
                with mock.patch.object(qc, '_load_monthly_qc', return_value=gate), \
                        mock.patch.object(gate, 'verify_html', return_value=report):
                    with self.assertRaises(ValueError):
                        qc.verify_html(html, self.ledger)

    def test_mocked_full_generator_pass_and_html_failure_cleanup(self):
        # 只mock其它面板；月度compute、真实组件/CSS、两阶段QC及原子输出均运行。
        import abs_common
        mocks = [(generator.gen_compare_tool, 'compute_data', {}),
                 (generator.gen_abs_cost_report, 'compute_data', {}),
                 (generator.gen_spread_report, 'compute_data', {}),
                 (generator.gen_investment_ledger, 'compute_data_multi_year', {'by_year': {}}),
                 (generator.gen_pricing_insight, 'render_pricing_panel', '<p>定价</p>'),
                 (generator.gen_compare_tool, 'render_body_invest', '<p>投资</p>'),
                 (generator.gen_abs_cost_report, 'render_body', '<p>成本</p>'),
                 (generator.gen_spread_report, 'render_body', '<p>利差</p>'),
                 (generator.secondary_allocation_panel, 'render_body', '<p>次级</p>'),
                 (generator.gen_institution_profile, 'render_body', '<p>机构</p>'),
                 (generator.gen_institution_stats, 'compute_data', {}),
                 (generator.gen_institution_stats, 'render_body', '<p>统计</p>'),
                 (generator.fig8_credit_total_panel, 'render_credit_total_panel', '<p>授信</p>'),
                 (generator.gen_investment_ledger, 'render_body_multi_year', [])]
        cases = [(False, False, False, False), (False, True, False, False),
                 (True, False, False, False), (True, True, False, False),
                 (True, 'producer', False, False),
                 (True, False, True, True), (True, False, False, True)]
        for release, tamper, default_output, demo in cases:
            latest = self.root / 'deliverables/dashboards/01_latest'
            latest.mkdir(parents=True, exist_ok=True)
            target = (latest / (f'ABS综合看板_{generator.datetime.now():%Y%m%d}.html' if default_output
                                else 'release.html')) if release else self.root / ('bad.html' if tamper else 'good.html')
            previous = b'previous release'
            if release:
                target.write_bytes(previous)
            # 相邻旧临时文件不得被正式流程截断或删除。
            old_tmp = Path(str(target) + '.qc-tmp')
            if release:
                old_tmp.write_bytes(b'other generation')
            preprocessed = self.root / 'shared-temp.xlsx'
            preprocessed.write_bytes(b'mocked preprocess')
            original_builder = generator.build_integrated_html
            def build(panels, css):
                html = original_builder(panels, css)
                return html.replace('id="lb-monthly-head"', 'id="missing-month-head"') if tamper is True else html
            with ExitStack() as stack:
                for module, name, result in mocks:
                    stack.enter_context(mock.patch.object(module, name, return_value=result))
                stack.enter_context(mock.patch.object(abs_common, 'preprocess_xlsx_for_pandas', return_value=str(preprocessed)))
                stack.enter_context(mock.patch.object(generator, '_assert_shared_tmp_structure'))
                stack.enter_context(mock.patch.object(generator, 'build_integrated_html', side_effect=build))
                flags = ['--monthly-bookkeeping-release'] if release else ['--monthly-bookkeeping']
                if release and not demo:
                    flags.append('--monthly-bookkeeping')
                if demo:
                    flags.append('--bookkeeping-demo')
                argv = ['generate', str(self.ledger)] + ([] if default_output else [str(target)]) + flags
                stack.enter_context(mock.patch.object(sys, 'argv', argv))
                stack.enter_context(mock.patch.object(generator, 'SCRIPT_DIR', self.root / 'scripts'))
                rendered = stack.enter_context(mock.patch.object(renderer, 'render_component', wraps=renderer.render_component))
                if tamper == 'producer':
                    import dashboard_provenance
                    original_provenance = dashboard_provenance.add_full_generation_provenance
                    def stale_producer(*args, **kwargs):
                        html = original_provenance(*args, **kwargs)
                        return html.replace(dashboard_provenance.producer_sha256(), '0' * 64)
                    stack.enter_context(mock.patch.object(dashboard_provenance, 'add_full_generation_provenance',
                                                         side_effect=stale_producer))
                stack.enter_context(redirect_stdout(io.StringIO()))
                if tamper:
                    with self.assertRaises(SystemExit) as failure:
                        generator.main()
                    self.assertEqual(failure.exception.code, 1)
                else:
                    generator.main()
            self.assertEqual(target.exists(), release or not tamper)
            self.assertEqual(rendered.call_args_list[0].kwargs['preview'], not release)
            if release:
                self.assertEqual(old_tmp.read_bytes(), b'other generation')
                self.assertEqual(list(latest.glob(target.name + '.*.qc-tmp')), [])
                if tamper:
                    self.assertEqual(target.read_bytes(), previous)
            else:
                self.assertFalse(old_tmp.exists())
            self.assertFalse(preprocessed.exists())
            if not tamper:
                html = target.read_text(encoding='utf-8')
                if release:
                    self.assertNotIn('Demo 仅供本地评审', html)
                    self.assertIn('随台账生成更新', html)
                    self.assertNotIn('class="lb-monthly-qc-banner"', html)
                    self.assertIn('"auditQc": {', html)
                else:
                    self.assertIn('Demo 仅供本地评审', html)
                self.assertEqual(qc.verify_html(html, self.ledger)['status'], 'PASS')
                from dashboard_provenance import verify_full_generation
                self.assertEqual(verify_full_generation(html, self.ledger)['generation'], 'full')

    def test_default_main_still_uses_original_gate_before_preprocess(self):
        target = self.root / 'default.html'
        with mock.patch.object(sys, 'argv', ['generate', str(self.ledger), str(target)]), \
                mock.patch.object(generator, '_prepare_monthly_bookkeeping', side_effect=AssertionError('默认启用月表')) as monthly, \
                mock.patch.object(panel.qc, 'component_self_check'), \
                mock.patch.object(panel, 'compute_data', side_effect=ValueError('原必选门禁')) as recent, \
                mock.patch('abs_common.preprocess_xlsx_for_pandas') as preprocess, \
                redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, '原必选门禁'):
                generator.main()
        recent.assert_called_once_with(str(self.ledger))
        monthly.assert_not_called()
        preprocess.assert_not_called()
        self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
