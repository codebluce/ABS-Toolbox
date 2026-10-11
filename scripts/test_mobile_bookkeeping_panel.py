"""手机版紧凑簿记生产组件：布局约束、无导出、双端一致性和实际运行时回归。"""
import copy
import json
from pathlib import Path
import re
import unittest

import latest_bookkeeping_panel as desktop
import latest_bookkeeping_qc as qc
import mobile_bookkeeping_panel as mobile
from latest_bookkeeping_runtime import verify_mobile_runtime, verify_runtime


def snapshot():
    return {'source':'测试定稿.xlsx','asOf':'2026-09-21', 'assets':[
        {'name':'赊销白条','date':'2026-09-21','dates':['2026-09-21'], 'projects':[
            {'name':'项目一','date':'2026-09-21','size':1,'manager':'管理人', 'venue':'上交所','tenor':'21+3',
             'tiers':[{'name':'优先A','costs':[0.0177],
                       'allocations':[{'institution':'配售机构','share':1,'cost':0.0177,'rate':None,'bidSize':None}],
                       'bids':[{'institution':'申购机构','share':None,'rate':0.0176,'bidSize':2}]}]}]}]}


class MobileBookkeepingPanelTest(unittest.TestCase):
    def test_data_kept_and_desktop_not_changed(self):
        data=snapshot();before=copy.deepcopy(data)
        html=mobile.render_html(data)
        self.assertEqual(qc.extract_data(html),data)
        self.assertEqual(data,before)
        self.assertIn('<header class="lb-banner">',desktop.render_body(data))
        self.assertIn('id="lb-export"',desktop.render_body(data))
        self.assertNotIn('<header class="lb-banner">',html)
        self.assertIn('<header class="lb-mobile-freeze"><h1>最新项目簿记明细</h1>',html)

    def test_no_export_no_record_counters_and_single_row_controls(self):
        html=mobile.render_html(snapshot())
        self.assertNotIn('id="lb-export"',html)
        self.assertNotIn("$('lb-export')",html)
        self.assertNotIn('URL.createObjectURL',html)
        self.assertNotIn('id="lb-row-count"',html)
        self.assertNotIn('class="lb-tier-note"',html)
        self.assertIn('id="lb-layer" class="lb-filter-layer" aria-label="档位"',html)
        self.assertIn('flex-wrap:nowrap',mobile.CSS)

    def test_equal_six_column_buttons_and_four_font_levels(self):
        self.assertIn('repeat(6,minmax(0,1fr))',mobile.CSS)
        self.assertIn('height:46px;min-height:46px',mobile.CSS)
        for token in ('--m-title:18px','--m-heading:14px','--m-body:11px','--m-caption:10px'):
            self.assertIn(token,mobile.CSS)
        self.assertIn('aria-label="${esc(item.name)}"',mobile.runtime_script(snapshot()))

    def test_balanced_names_no_single_character_second_line(self):
        data=snapshot()
        data['assets'][0]['name']='信托企业主贷'
        for name in ('赊销白条','金条白取混发','信托金条','京企贷','汽车融资租赁'):
            item=copy.deepcopy(data['assets'][0]);item['name']=name;data['assets'].append(item)
        result=verify_mobile_runtime(data)
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['exports'],0)

    def test_real_mobile_and_desktop_runtime_have_same_details(self):
        data=qc.extract_data((Path(__file__).resolve().parents[1]/'deliverables/dashboards/01_latest/ABS综合看板_20260924.html').read_text())
        result=verify_mobile_runtime(data)
        desktop_result=verify_runtime(data)
        self.assertEqual(result['projects'],desktop_result['projects'])
        self.assertEqual(result['details'],desktop_result['details'])
        self.assertEqual(result['filters'],desktop_result['filters'])
        self.assertEqual(result['exports'],0)
        self.assertGreater(desktop_result['exports'],0)

    def test_actual_script_style_data_tampering_rejected(self):
        data=snapshot();html=mobile.render_html(data)
        self.assertEqual(mobile.verify_html(html,data)['status'],'PASS')
        for original,replacement in [("view = 'bids'","view = 'allocations'"),
                                      ('height:46px','height:96px'),('项目一','旧项目')]:
            with self.subTest(original=original):
                with self.assertRaises(ValueError):mobile.verify_html(html.replace(original,replacement),data)

    def test_mobile_navigation_order_and_default(self):
        script=Path(__file__).with_name('abs_mobile_app.js').read_text()
        self.assertIn("tab: 'bookkeeping'",script)
        self.assertIn("['bookkeeping','peer','asset','progress']",script)
        self.assertIn("if (!INJ.bookkeepingHtml) S.tab = 'progress'",script)

    def test_both_views_and_empty_search_work_without_export(self):
        result=verify_mobile_runtime(snapshot())
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['details'],2)
        self.assertGreater(result['filters'],0)


if __name__=='__main__':
    unittest.main()
