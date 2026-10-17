"""Manual denominator expectations against production functions; no workbook writes."""
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
import gen_compare_tool as compare
import gen_pricing_insight as pricing
from abs_common import COLNAMES, resolve_columns


def row(**changes):
    data = dict.fromkeys(COLNAMES, None)
    data.update({'资产类型': '赊销白条', '簿记时间': pd.Timestamp('2026-10-16'),
                 '项目名称': '测试项目', '发行场所': '银行间', '分层情况': '优先A1',
                 '对应金额（亿）': 8, '规模': 10, '月份': pd.Period('2026-10'),
                 '产品类型': '1年期赊销白条', '期限分类': '1年期',
                 '成本pct': 1.8, '基准利差': 0.2, '实际机构': '测试机构', '实际份额': 1})
    data.update(changes)
    return data


def frame(*rows):
    return pd.DataFrame(rows)


class Denominators(unittest.TestCase):
    def test_manual_a1_a2_and_precision(self):
        rows = compare.build_js_data(frame(row(), row(**{'分层情况': '优先A2', '对应金额（亿）': 2})), ['1年期赊销白条'])
        self.assertEqual([r['share']/r['layer_size']*100 for r in rows], [12.5, 50])
        self.assertEqual([r['project_size'] for r in rows], [10, 10])
        precise = compare.build_js_data(frame(row(**{'对应金额（亿）': 8.123456789})), ['1年期赊销白条'])[0]
        self.assertEqual(precise['layer_size'], 8.123456789)
        self.assertEqual(precise['total_size'], precise['layer_size'])

    def test_all_dates_assets_venues_layers_and_order(self):
        records = [row(), row(**{'簿记时间': pd.Timestamp('2026-09-16'), '月份': pd.Period('2026-09'), '对应金额（亿）': 2}),
                   row(**{'发行场所': '上交所', '对应金额（亿）': 3}), row(**{'资产类型': '京企贷', '对应金额（亿）': 4}),
                   row(**{'分层情况': '优先A2', '对应金额（亿）': 5})]
        sizes = compare.build_layer_sizes(frame(*records))
        self.assertEqual(len(sizes), 5)
        self.assertEqual(sizes, compare.build_layer_sizes(frame(*reversed(records))))
        rows = compare.build_js_data(frame(*records), ['1年期赊销白条'])
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]['layer_size'], 8)
        self.assertEqual(json.loads(rows[0]['identity_key']), ['赊销白条', '2026-10-16', '测试项目', '银行间', '优先A1'])
        self.assertNotEqual(compare.pricing_identity_key(pd.Series(row(**{'项目名称': 'a|b', '发行场所': 'c'}))),
                            compare.pricing_identity_key(pd.Series(row(**{'项目名称': 'a', '发行场所': 'b|c'}))))

    def test_consistent_conflict_and_old_month_conflict(self):
        self.assertEqual(list(compare.build_layer_sizes(frame(row(), row())).values()), [8])
        for records in [(row(), row(**{'对应金额（亿）': 2})),
                        (row(**{'月份': pd.Period('2026-09')}), row(**{'月份': pd.Period('2026-09'), '对应金额（亿）': 2}), row())]:
            with self.assertRaisesRegex(ValueError, 'conflicting R'):
                compare.build_js_data(frame(*records), ['1年期赊销白条'])

    def test_missing_and_illegal(self):
        for value in [None, pd.NA, np.nan, '', '  ']:
            rows = compare.build_js_data(frame(row(**{'对应金额（亿）': value}), row()), ['1年期赊销白条'])
            self.assertIsNone(rows[0]['layer_size'])
            self.assertEqual(rows[0]['project_size'], 10)
        for value in [-1, 0, True, False, np.bool_(True), float('inf'), -float('inf'), '8', 'bad', '=J2*Q2']:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'R FAIL'):
                compare.build_js_data(frame(row(**{'对应金额（亿）': value}), row()), ['1年期赊销白条'])

    def test_compute_api_validates_all_pricing_rows_and_keeps_full_keys(self):
        df = frame(row(), row(**{'分层情况': '优先A2', '对应金额（亿）': 2}))
        with patch.object(compare, 'load_data', return_value=(df, df)), patch.object(compare, 'run_qc', return_value=True):
            data = compare.compute_data('synthetic.xlsx')
        sizes = json.loads(data['proj_sizes_js'])
        self.assertEqual(len(sizes), 2)
        self.assertNotIn('测试项目', sizes)
        df = frame(row(), row(**{'分层情况': '优先A2', '对应金额（亿）': 2}), row(**{'分层情况': '优先A2', '对应金额（亿）': 3}))
        with patch.object(compare, 'load_data', return_value=(df, df)), self.assertRaisesRegex(ValueError, 'conflicting R'):
            compare.compute_data('synthetic.xlsx')

    def test_original_share_trio(self):
        df = frame(row(**{'成本': .018, '认购机构': '表面测试', '认购份额': .5,
                          '申购利率': .019, '穿透机构': '穿透测试', '申购规模': 2}),
                   row(**{'成本': .018, '认购机构': '表面测试', '认购份额': .5,
                          '申购利率': .019, '穿透机构': None, '申购规模': 2}))
        with contextlib.redirect_stdout(io.StringIO()):
            resolved = resolve_columns(df)
        self.assertEqual(resolved['实际份额'].tolist(), [2, .5])
        self.assertEqual(resolved['实际成本'].tolist(), [.019, .018])

    def test_trimmed_identity_and_positive_project_metadata(self):
        padded = row(**{'资产类型': ' 赊销白条 ', '项目名称': ' 测试项目 ', '发行场所': ' 银行间 ', '分层情况': ' 优先A1 '})
        self.assertEqual(compare.pricing_identity_key(pd.Series(padded)), compare.pricing_identity_key(pd.Series(row())))
        rows = compare.build_js_data(frame(padded), ['1年期赊销白条'])
        self.assertEqual([rows[0][field] for field in ['asset', 'project', 'venue', 'layer']], ['赊销白条', '测试项目', '银行间', '优先A1'])
        with self.assertRaisesRegex(ValueError, 'conflicting R'):
            compare.build_layer_sizes(frame(padded, row(**{'对应金额（亿）': 2})))
        for value in [-1, 0, True, float('inf'), '10', None]:
            self.assertIsNone(compare.pricing_project_size(value))

    def test_resource_calculations_match(self):
        marker = '// ====== DEFAULT VIEW ======'
        expected = pricing._PRICING_INSIGHT_JS.split(marker)[0] + 'populateProducts(ALL_PRODUCTS);\n'
        self.assertEqual(Path(__file__).with_name('lab').joinpath('pricing_insight_js.txt').read_text(), expected)


if __name__ == '__main__':
    if '--real-panel' in sys.argv:
        target = Path(sys.argv[sys.argv.index('--real-panel') + 1])
        source = Path(__file__).resolve().parents[1] / 'deliverables/ledger/03_final/2026年ABS发行台账-1016-定稿.xlsx'
        data = compare.compute_data(str(source))
        target.write_text('<!doctype html><html><head><meta charset="utf-8"><style>' + pricing.PRICING_INSIGHT_CSS + '</style></head><body>' + pricing.render_pricing_panel(data) + '</body></html>')
        print(json.dumps({'status': 'PASS', 'realRows': len(data['rows']), 'realKeys': len(json.loads(data['proj_sizes_js'])), 'missingR': sum(r['layer_size'] is None for r in data['rows'])}))
    else:
        unittest.main()
