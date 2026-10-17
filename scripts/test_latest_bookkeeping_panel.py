"""最新簿记 Demo：选择规则、双口径、字段缺失和集成路由回归。"""
import json
from pathlib import Path
import re
import tempfile
import unittest

import pandas as pd

import latest_bookkeeping_panel as panel
from gen_integrated_dashboard import build_integrated_html, verify_integrated_html


def row(**changes):
    record = {'资产类型':'白条','项目名称':'项目一','簿记时间':'2026-09-21','分层情况':'优先A',
              '成本':0.0177,'认购机构':'获配机构','认购份额':1.3,'申购利率':0.018,
              '穿透机构':'不同报价机构','申购规模':2.0,'规模':10,'计划管理人':'管理人','发行场所':'银行间','期限':'21+3'}
    record.update(changes)
    return record


class LatestBookkeepingTest(unittest.TestCase):
    def test_latest_by_asset_and_same_day_projects(self):
        frame = pd.DataFrame([row(项目名称='历史项目',簿记时间='2026-09-01'), row(),
            row(项目名称='同日项目'), row(资产类型='保理',项目名称='保理最近',簿记时间='2026-08-05')])
        data = panel.compute_frame(frame, 'source.xlsx')
        white = next(a for a in data['assets'] if a['name'] == '白条')
        factoring = next(a for a in data['assets'] if a['name'] == '保理')
        self.assertEqual([p['name'] for p in white['projects']], ['项目一','同日项目','历史项目'])
        self.assertEqual(factoring['date'], '2026-08-05')

    def test_dual_tracks_never_pair_same_excel_row(self):
        tier = panel.compute_frame(pd.DataFrame([row()]), 'source')['assets'][0]['projects'][0]['tiers'][0]
        self.assertEqual(tier['allocations'][0]['institution'], '获配机构')
        self.assertEqual(tier['allocations'][0]['share'], 1.3)
        self.assertIsNone(tier['allocations'][0]['rate'])
        self.assertEqual(tier['bids'][0]['institution'], '不同报价机构')
        self.assertEqual(tier['bids'][0]['bidSize'], 2.0)
        self.assertIsNone(tier['bids'][0]['share'])

    def test_latest_missing_bids_does_not_fallback(self):
        data = panel.compute_frame(pd.DataFrame([row(簿记时间='2026-09-01'),
            row(簿记时间='2026-09-24',穿透机构=None,申购利率=None,申购规模=None)]), 'source')
        self.assertEqual(data['assets'][0]['date'],'2026-09-24')
        self.assertEqual(data['assets'][0]['projects'][0]['tiers'][0]['bids'],[])

    def test_headers_zero_rates_and_non_numeric_cost(self):
        rows = [row(穿透机构='穿透机构',申购利率='申购利率'),
                row(成本='自持',申购利率=0,申购规模=0), row(成本=0.02,认购份额=None)]
        tier = panel.compute_frame(pd.DataFrame(rows), 'source')['assets'][0]['projects'][0]['tiers'][0]
        self.assertEqual(len(tier['bids']),2)
        self.assertEqual(tier['bids'][0]['rate'],0)
        self.assertEqual(tier['bids'][0]['bidSize'],0)
        self.assertEqual(tier['costs'],[0.0177,'自持',0.02])
        self.assertIsNone(tier['allocations'][2]['share'])

    def test_excel_date_and_invalid_date(self):
        data = panel.compute_frame(pd.DataFrame([row(簿记时间=46289),row(簿记时间='错误日期')]), 'source')
        self.assertEqual(data['invalidDateRows'],1)
        self.assertRegex(data['asOf'],r'^2026-')
        with self.assertRaises(ValueError):
            panel.compute_frame(pd.DataFrame([row(簿记时间=None)]), 'source')

    def test_find_latest_final_ignores_mtime_and_backups(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ['2026年ABS发行台账-0918-定稿.xlsx','2026年ABS发行台账-0924-定稿.xlsx',
                         '2026年ABS发行台账-1009-定稿-备份.xlsx','2026年ABS发行台账-1332-定稿.xlsx']:
                (root/name).touch()
            self.assertEqual(panel.find_latest_final(root).name,'2026年ABS发行台账-0924-定稿.xlsx')

    def test_embedding_and_panel_registration(self):
        data=panel.compute_frame(pd.DataFrame([row(项目名称='</script><b>项目</b>')]), 'source')
        body=panel.render_body(data)
        embedded=re.search(r'<script id="lb-data" type="application/json">(.*?)</script>',body,re.S).group(1)
        self.assertNotIn('<',embedded)
        self.assertEqual(json.loads(embedded),data)
        html=build_integrated_html([('pricing','bookkeeping',body)],panel.BOOKKEEPING_CSS)
        self.assertIn('>最新簿记</button>',html)
        self.assertEqual(verify_integrated_html(html,1),[])

    def test_venue_filter_runs_before_latest_selection(self):
        records = [row(项目名称='交易所旧期',发行场所='深交所',簿记时间='2026-09-01'),
                   row(项目名称='非标最新',发行场所='非标',簿记时间='2026-09-24'),
                   row(项目名称='保登最新',发行场所='保登',簿记时间='2026-09-25'),
                   row(资产类型='保理',项目名称='保理交易所',发行场所='上交所'),
                   row(资产类型='仅非标资产',发行场所='非标'),
                   row(资产类型='未知场所资产',发行场所=None)]
        data = panel.compute_frame(pd.DataFrame(records), 'source')
        self.assertEqual([a['name'] for a in data['assets']], ['保理', '白条'])
        white = next(a for a in data['assets'] if a['name'] == '白条')
        self.assertEqual(white['projects'][0]['name'], '交易所旧期')
        self.assertEqual(white['date'], '2026-09-01')
        self.assertEqual(data['asOf'], '2026-09-25')
        for asset in data['assets']:
            for project in asset['projects']:
                self.assertIn(project['venue'], panel.ALLOWED_VENUES)

    def test_no_eligible_venue_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError, '发行场所'):
            panel.compute_frame(pd.DataFrame([row(发行场所='非标')]), 'source')

    def test_quote_first_placement_second_and_default_quote(self):
        body = panel.render_body(panel.compute_frame(pd.DataFrame([row()]), 'source'))
        labels = re.findall(r'<button type="button" data-view="[^"]+">([^<]+)</button>', body)
        self.assertEqual(labels, ['申购明细', '最终配售'])
        self.assertIn("view = 'bids'", body)
        self.assertNotIn('最终认购', body)
        self.assertIn('剔除非标、保登', body)

    def test_asset_order_alias_merge_and_other_assets_follow(self):
        records = [row(资产类型='额外资产甲'), row(资产类型='信托白取',项目名称='取现最近',簿记时间='2026-09-22'),
                   row(资产类型='白条取现',项目名称='取现旧期',簿记时间='2026-09-01'),
                   row(资产类型='金条&白取混发'), row(资产类型='额外资产乙')]
        records += [row(资产类型=asset) for asset in reversed(panel.ASSET_ORDER) if asset != '白条取现']
        data = panel.compute_frame(pd.DataFrame(records), 'source')
        self.assertEqual([a['name'] for a in data['assets']], list(panel.ASSET_ORDER) + ['额外资产甲', '额外资产乙'])
        cash = next(a for a in data['assets'] if a['name'] == '白条取现')
        self.assertEqual(cash['date'], '2026-09-22')
        self.assertEqual([p['name'] for p in cash['projects']], ['取现最近','取现旧期'])
        self.assertEqual(sum(a['name'] == '金条白取混发' for a in data['assets']), 1)

    def test_cash_merge_preserves_same_day_projects(self):
        data = panel.compute_frame(pd.DataFrame([row(资产类型='白条取现',项目名称='取现项目'),
                                                row(资产类型='信托白取',项目名称='信托取现项目')]), 'source')
        self.assertEqual(len(data['assets']), 1)
        self.assertEqual(len(data['assets'][0]['projects']), 2)

    def test_detail_title_and_removed_view_note(self):
        body = panel.render_body(panel.compute_frame(pd.DataFrame([row()]), 'source'))
        self.assertIn('<h2>簿记明细</h2>', body)
        self.assertNotIn('机构簿记明细', body)
        self.assertNotIn('lb-view-note', body)
        self.assertNotIn('申购明细（W/X/Y）：逐笔保留报价及申购规模，不表示最终获配。', body)

    def test_recent_three_dates_not_three_projects_and_stable_ties(self):
        records = [row(项目名称='旧第四期',簿记时间='2026-09-01'),
                   row(项目名称='第三期',簿记时间='2026-09-10'),
                   row(项目名称='第二期',簿记时间='2026-09-18'),
                   row(项目名称='第一期甲',簿记时间='2026-09-21 09:00:00'),
                   row(项目名称='第一期乙',簿记时间='2026-09-21 15:00:00'),
                   row(项目名称='较新非标',簿记时间='2026-09-24',发行场所='非标')]
        asset = panel.compute_frame(pd.DataFrame(records), 'source')['assets'][0]
        self.assertEqual(asset['dates'],['2026-09-21','2026-09-18','2026-09-10'])
        self.assertEqual([p['name'] for p in asset['projects']],['第一期甲','第一期乙','第二期','第三期'])
        self.assertEqual([p['date'] for p in asset['projects']],['2026-09-21','2026-09-21','2026-09-18','2026-09-10'])

    def test_reused_project_name_different_periods_not_merged(self):
        records = [row(项目名称='同名项目',簿记时间='2026-09-21'),
                   row(项目名称='同名项目',簿记时间='2026-09-18')]
        projects=panel.compute_frame(pd.DataFrame(records), 'source')['assets'][0]['projects']
        self.assertEqual(len(projects),2)
        self.assertEqual([p['date'] for p in projects],['2026-09-21','2026-09-18'])
        self.assertTrue(all(len(p['tiers'][0]['allocations'])==1 for p in projects))

    def test_desktop_pricing_bookkeeping_first_preserves_other_order(self):
        panels = [('pricing', name, '<section>'+name+'</section>')
                  for name in ['compare','invest','cost','spread','bookkeeping']]
        html=build_integrated_html(panels,'')
        labels=re.findall(r'<button class="sub-tab-button"[^>]*>([^<]+)</button>',html)
        self.assertEqual(labels,['最新簿记','定价测试','投资明细','成本分布','利差分析'])
        routes=re.findall(r'<div class="panel" data-module="pricing" data-sub="([^"]+)"',html)
        self.assertEqual(routes,['bookkeeping','compare','invest','cost','spread'])
        self.assertEqual([item[1] for item in panels],['compare','invest','cost','spread','bookkeeping'])

    def test_real_final_latest_project_and_exact_values(self):
        # 固定0924业务样本用于精确数值回归，不让每周新增定稿改变测试预期。
        data=panel.compute_data(panel.SCRIPT_DIR.parent / 'deliverables/ledger/03_final/2026年ABS发行台账-0924-定稿.xlsx')
        self.assertTrue(all(p['venue'] in panel.ALLOWED_VENUES for a in data['assets'] for p in a['projects']))
        white=next(a for a in data['assets'] if a['name']=='赊销白条')
        self.assertEqual(white['date'],'2026-09-21')
        p=next(p for p in white['projects'] if p['name']=='26东裕10号四期')
        tier=next(t for t in p['tiers'] if t['name']=='优先A')
        self.assertEqual(tier['costs'],[0.0177])
        self.assertEqual(p['tenor'],'21+3')
        bank=next(r for r in tier['allocations'] if r['institution']=='建设银行')
        self.assertEqual(bank['share'],1.3)
        bid=next(r for r in tier['bids'] if r['institution']=='建设银行（投行上报）')
        self.assertEqual(bid['bidSize'],1.74)


if __name__=='__main__':
    unittest.main()
