"""角色专属统计归并、投行规模和销售项目去重回归。"""
import unittest
import pandas as pd
from gen_institution_stats import compute_manager_table, compute_sales_table, normalize_stats_role
from abs_common import normalize_investor_name
from entity_alias import normalize_bank
from gen_institution_stats import compute_custodian_table

class StatsRoleAliasesTest(unittest.TestCase):
    def test_interbank_ccb_alias_and_market_subscription(self):
        from gen_institution_stats import compute_sales_markets
        projects=pd.DataFrame([
            {'项目名称':'a','联席承销商':'建行/建设银行','规模':10},
            {'项目名称':'b','联席承销商':'建设银行','规模':5},
            {'项目名称':'c','联席承销商':'中信证券','规模':20},
        ])
        df=pd.DataFrame([
            {'项目名称':'a','发行场所':'银行间','认购机构':'建行投行','认购份额':1},
            {'项目名称':'b','发行场所':'银行间','认购机构':'建设银行投行','认购份额':2},
            {'项目名称':'c','发行场所':'上交所','认购机构':'中信证券投行','认购份额':3},
        ])
        markets=compute_sales_markets(df,projects)
        bank=markets[1]['sales'].iloc[0]
        self.assertEqual(bank['机构名称'],'建设银行')
        self.assertEqual(bank['销售项目数'],2)
        self.assertEqual(bank['参与项目规模'],15)
        self.assertEqual(bank['投行认购规模'],3)
        self.assertEqual(bank['规模占比'],100)
        self.assertEqual(markets[0]['sales'].iloc[0]['投行认购规模'],3)

    def test_interbank_boc_alias_merges_without_changing_totals(self):
        from gen_institution_stats import compute_sales_markets
        projects=pd.DataFrame([
            {'项目名称':'a','联席承销商':'中行','规模':10},
            {'项目名称':'b','联席承销商':'中国银行','规模':5},
            {'项目名称':'c','联席承销商':'中行/中国银行','规模':20},
        ])
        df=pd.DataFrame([{'项目名称':name,'发行场所':'银行间','认购机构':'-','认购份额':0} for name in 'abc'])
        bank=compute_sales_markets(df,projects)[1]['sales'].set_index('机构名称')
        self.assertEqual(list(bank.index),['中国银行'])
        self.assertEqual(bank.loc['中国银行','销售项目数'],3)
        self.assertEqual(bank.loc['中国银行','参与项目规模'],35)
        self.assertEqual(bank.loc['中国银行','规模占比'],100)

    def test_exchange_cinda_alias_uses_ledger_name(self):
        from gen_institution_stats import compute_sales_markets
        projects=pd.DataFrame([
            {'项目名称':'a','联席承销商':'信达证券','规模':10},
            {'项目名称':'b','联席承销商':'信达自营','规模':5},
            {'项目名称':'c','联席承销商':'信达证券/信达自营','规模':20},
        ])
        df=pd.DataFrame([{'项目名称':name,'发行场所':'上交所','认购机构':'-','认购份额':0} for name in 'abc'])
        sales=compute_sales_markets(df,projects)[0]['sales'].set_index('机构名称')
        self.assertEqual(list(sales.index),['信达证券'])
        self.assertEqual(sales.loc['信达证券','销售项目数'],3)
        self.assertEqual(sales.loc['信达证券','参与项目规模'],35)
        self.assertEqual(sales.loc['信达证券','规模占比'],100)

    def test_sales_display_restores_ledger_names_without_merging_distinct_entities(self):
        from gen_institution_stats import compute_sales_markets
        projects=pd.DataFrame([
            {'项目名称':'a','联席承销商':'中泰证券','规模':10},
            {'项目名称':'b','联席承销商':'中泰自营','规模':5},
            {'项目名称':'c','联席承销商':'国金资管','规模':20},
            {'项目名称':'d','联席承销商':'国金证券','规模':8},
        ])
        df=pd.DataFrame([{'项目名称':name,'发行场所':'上交所','认购机构':'-','认购份额':0} for name in 'abcd'])
        sales=compute_sales_markets(df,projects)[0]['sales'].set_index('机构名称')
        self.assertEqual(sales.loc['中泰证券','销售项目数'],2)
        self.assertEqual(sales.loc['中泰证券','参与项目规模'],15)
        self.assertEqual(sales.loc['国金资管','销售项目数'],1)
        self.assertEqual(sales.loc['国金资管','参与项目规模'],20)
        self.assertEqual(sales.loc['国金证券','参与项目规模'],8)
        self.assertNotIn('中泰（自营）',sales.index)
        self.assertNotIn('国金证券资管',sales.index)

    def test_icbc_tianjin_branch_merges_in_custodian_table(self):
        self.assertEqual(normalize_bank('工行天分'), '工商银行')
        projects = pd.DataFrame([
            {'项目名称': 'a', '托管行': normalize_bank('工行天分'), '规模': 15},
            {'项目名称': 'b', '托管行': normalize_bank('工商银行'), '规模': 10},
        ])
        result = compute_custodian_table(projects, 25)
        self.assertEqual(result['托管行'].tolist(), ['工商银行'])
        self.assertEqual(result.iloc[0]['托管项目数'], 2)
        self.assertEqual(result.iloc[0]['托管规模'], 25)

    def test_manager_groups_and_ib_share_are_merged_once(self):
        projects=pd.DataFrame([
            {'项目名称':str(i),'计划管理人':n,'规模':10}
            for i,n in enumerate(['国证资管','国投证券','天风证券','天风资管','华泰证券','华泰资管'])])
        original=projects.copy(deep=True)
        ib=pd.Series([1,2,3,4,5,6],index=['国证资管','国投证券','天风证券','天风资管','华泰证券','华泰资管'])
        result=compute_manager_table(projects,ib,60).set_index('计划管理人')
        self.assertEqual(set(result.index),{'国投证券','天风资管','华泰资管'})
        self.assertEqual(result.loc['国投证券','管理项目数'],2)
        self.assertEqual(result.loc['天风资管','投行认购规模'],7)
        self.assertEqual(result.loc['华泰资管','投行认购规模'],11)
        self.assertEqual(result['管理规模'].sum(),60)
        pd.testing.assert_frame_equal(projects,original)

    def test_sales_aliases_are_deduplicated_within_project(self):
        projects=pd.DataFrame([{'项目名称':'p1','联席承销商':'建投/中信建投','规模':10},
                               {'项目名称':'p2','联席承销商':'建投','规模':5}])
        ib=pd.Series([1,2],index=['建投','中信建投'])
        result=compute_sales_table(projects,ib,15).set_index('机构名称')
        self.assertEqual(list(result.index),['中信建投'])
        self.assertEqual(result.loc['中信建投','销售项目数'],2)
        self.assertEqual(result.loc['中信建投','参与项目规模'],15)
        self.assertEqual(result.loc['中信建投','投行认购规模'],3)
        self.assertEqual(normalize_stats_role('华泰证券','sales'),'华泰证券')
        self.assertEqual(normalize_stats_role('建投','manager'),'建投')
        self.assertNotEqual(normalize_investor_name('华泰证券'),normalize_investor_name('华泰资管'))

if __name__=='__main__':unittest.main()
