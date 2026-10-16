"""机构统计别名与证券/资管隔离回归。"""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from abs_common import investor_search_aliases, normalize_investor_name
from entity_alias import normalize_entity
from fig6_credit_panel import approximate_match as fig6_match
from fig8_credit_total_panel import approximate_match as fig8_match
from institution_identity import aliases, registry
from generate_institution_alias_audit import audit_rows

ROOT = Path(__file__).resolve().parents[1]


class InstitutionIdentityTest(unittest.TestCase):
    def test_approved_aliases_and_distinct(self):
        self.assertEqual(normalize_investor_name('中信证券（换券）'), '中信证券（自营）')
        self.assertEqual(normalize_investor_name('中信自营（换券）'), '中信证券（自营）')
        self.assertEqual(normalize_investor_name('粤财信托（协助展期）'), '粤财信托')
        self.assertEqual(normalize_investor_name('青岸投资'), '青岸资本')
        self.assertEqual(normalize_investor_name('广发证券资管'), '广发资管')
        self.assertEqual(normalize_entity('申万资管'), '申万宏源资管')
        self.assertNotEqual(normalize_investor_name('广发证券'), normalize_investor_name('广发资管'))
        self.assertNotEqual(normalize_entity('申万宏源'), normalize_entity('申万宏源资管'))
        self.assertNotEqual(normalize_investor_name('中信证券'), normalize_investor_name('中信证券（投顾）'))
        self.assertEqual(normalize_investor_name('广发证券（资管）'), '广发资管')
        self.assertNotEqual(normalize_investor_name('广发证券'), normalize_investor_name('广发证券（资管）'))
        self.assertEqual(len(aliases()), len(registry()['aliases']))
        self.assertEqual(investor_search_aliases()['青岸投资'], '青岸资本')
        self.assertEqual(normalize_investor_name('中泰证券自营'), '中泰（自营）')
        self.assertEqual(normalize_investor_name('中金自营（非标）'), '中金公司（自营）')
        self.assertEqual(normalize_entity('国联资管'), '国联证券')

    def test_ledger_roles_share_global_mapping(self):
        from gen_investment_ledger import _org_name, _underwriters, _bank_name
        self.assertEqual(_org_name('信达证券'), '信达（自营）')
        self.assertEqual(_underwriters('中泰证券/广发证券（资管）'), '中泰（自营）/广发资管')
        self.assertEqual(_bank_name('广发证券（资管）'), '广发资管')
        self.assertEqual(_underwriters('广发证券/广发证券（资管）'), '广发证券/广发资管')

    def test_citic_investor_groups_preserve_roles_and_boundaries(self):
        from gen_investment_ledger import _org_name
        groups = {
            '中信证券（自营）': ['中信证券', '中信证券自营', '中信自营', '中信证券（换券）', '中信自营（换券）', '中信证券股份有限公司', '中信证券固收'],
            '中信证券（投顾）': ['中信投顾', '中信（投顾）', '中信证券投顾', '中信投顾财富'],
            '中信证券（财富）': ['中信财富', '中信证券财富'],
            '中信证券（资管）': ['中信证券资管', '中信资管'],
        }
        for target, originals in groups.items():
            self.assertEqual(normalize_investor_name(target), target)
            for original in originals:
                self.assertEqual(normalize_investor_name(original), target)
                self.assertEqual(investor_search_aliases().get(original, normalize_investor_name(original)), target)
        self.assertEqual(_org_name('中信证券'), '中信证券')
        for original in ['中信银行', '中信信托', '中信建投', '中信财富投顾', '中信证券（投行）']:
            self.assertNotIn(normalize_investor_name(original), groups)

    def test_credit_does_not_confuse_legal_entities(self):
        for match in (fig6_match, fig8_match):
            self.assertTrue(match('青岸投资', '青岸资本'))
            self.assertTrue(match('中信证券（换券）', '中信证券'))
            self.assertTrue(match('中信自营', '中信证券'))
            self.assertTrue(match('广发证券（资管）', '广发资管'))
            self.assertFalse(match('广发证券', '广发资管'))
            self.assertFalse(match('申万宏源', '申万宏源资管'))
            self.assertFalse(match('中信证券', '中信证券（投顾）'))
            self.assertFalse(match('中信证券', '中信'))

    def test_confirmed_investor_short_names_and_corrections(self):
        expected = {
            '信达自营': '信达证券（自营）', '信达证券': '信达证券（自营）',
            '西部自营': '西部证券（自营）', '华兴证券': '华兴证券（自营）',
            '德邦自营': '德邦证券（自营）', '广发自营': '广发证券（自营）',
            '首创自营': '首创证券（自营）', '国信自营': '国信证券（自营）',
            '申万自营': '申万宏源（自营）', '申万投顾': '申万宏源（投顾）',
            '中信建投机构部': '中信建投（机构部）', '建投投顾': '中信建投（投顾）',
            '建投衍生品': '中信建投衍生品', '宝武财务': '宝物财务',
            '朗姿韩雅': '朗姿韩亚', '建新信托': '建信信托',
            '淅商银行': '浙商银行', '中金投颜': '中金公司（投顾）',
        }
        for original, target in expected.items():
            self.assertEqual(normalize_investor_name(original), target)
            self.assertEqual(normalize_investor_name(target), target)
        self.assertNotEqual(normalize_investor_name('建投投顾'), normalize_investor_name('建投衍生品'))
        for original in ['首创证券', '国信证券', '申万宏源', '广发证券', '华兴银行']:
            self.assertEqual(normalize_investor_name(original), original)

    def test_confirmed_groups_one_to_seven(self):
        groups = {
            '东方财富证券（自营）': ['东方财富证券', '东方财富（自营）', '东方财富自营', '东方财富证券自营', '东方财富'],
            '中信建投（投顾）': ['中信建投固收投顾', '中信建投固收（投顾）', '建投投顾'],
            '中信建投衍生品': ['中信建投固收', '建投衍生品'],
            '中金公司（自营）': ['中金公司', '中金固收', '中金证券自营', '中金证券（自营）', '中金'],
            '中金财富': ['中金财富自营', '中金财富（自营）'],
            '中金公司（投顾）': ['中金资管投顾', '中金资管（投顾）'],
            '银河证券FICC': ['银河FICC', '银河证券FICC'],
            '银河证券（自营）': ['银河固收', '银河证券固收', '银河证券金市', '银河证券', '银河证券自营'],
        }
        for target, originals in groups.items():
            for original in originals:
                self.assertEqual(normalize_investor_name(original), target)
            self.assertEqual(normalize_investor_name(target), target)
        self.assertNotEqual(normalize_investor_name('银河FICC'), normalize_investor_name('银河证券'))
        self.assertNotEqual(normalize_investor_name('中金财富'), normalize_investor_name('中金投顾'))
        self.assertEqual(normalize_investor_name('中信建投资管'), '中信建投资管')
        self.assertEqual(normalize_investor_name('银河证券投行'), '银河证券（自营）')

    def test_audit_covers_originals_and_keeps_secondary_local(self):
        rows = audit_rows()
        self.assertGreater(len(rows), 100)
        self.assertTrue(any(r[2] == '青岸投资' and r[3] == '青岸资本' for r in rows))
        self.assertTrue(any(r[2] == '广发资管' and r[3] == '广发资管' for r in rows))
        self.assertEqual(aliases()['信达证券'], '信达（自营）')
        self.assertTrue(any(r[1] == '次级投资人' and r[2] == '信达证券' and r[3] == '信达（自营）' for r in rows))

    def test_confirmed_groups_eight_to_sixteen(self):
        expected = {
            '国泰君安自营': '国泰海通（自营）', '海通证券固收': '国泰海通（自营）',
            '海通证券自营': '国泰海通（自营）', '国泰海通固收': '国泰海通（自营）',
            '国泰君安投行': '国泰海通（投行）', '海通证券投行': '国泰海通（投行）',
            '国泰海通投': '国泰海通（投行）', '国泰证券投行': '国泰海通（投行）',
            '国泰海通资管': '国泰海通（资管）',
            '国联证券投行': '国联民生（投行）', '国联证券': '国联民生（资管）',
            '国联资管': '国联民生（资管）', '国联证券自营': '国联证券（自营）',
            '平安资管': '平安资产', '宁波通商行': '宁波通商银行', '沪农商': '上海农商行',
            '重庆农商行': '重庆农商银行', '重庆农商行金市': '重庆农商银行',
            '重庆农商理财': '渝农商理财', '渝农商资源': '渝农商理财',
            '兴业理财': '兴银理财', '平银理财': '平安理财', '交易理财': '交银理财',
        }
        for original, target in expected.items():
            self.assertEqual(normalize_investor_name(original), target)
            self.assertEqual(normalize_investor_name(target), target)
        self.assertNotEqual(normalize_investor_name('重庆农商行'), normalize_investor_name('渝农商理财'))
        from gen_investment_ledger import _org_name
        self.assertEqual(_org_name('国联证券'), '国联证券')

    @unittest.skipUnless(shutil.which('node'), 'Node.js unavailable')
    def test_ledger_suggestions_search_alias_without_blending_results(self):
        source = (ROOT / 'scripts/itl_panel.js').read_text(encoding='utf-8')
        source = source.replace('distinctCounts: distinctCounts\n  };',
                                'distinctCounts: distinctCounts, __test: function(f,q) { inputs[f]={value:q}; return suggestions(f); }\n  };')
        js = """const vm=require('vm');const context={window:{ITL_DATA:[
          {inst:'广发证券'},{inst:'广发资管'},{inst:'青岸资本'},{inst:'信达证券（自营）'},
          {inst:'中信证券（自营）'},{inst:'中信证券（投顾）'},{inst:'中信证券（财富）'},
          {inst:'中信证券（资管）'},{inst:'中信建投（投顾）'}],ITL_ALIAS:%s}};
          vm.runInNewContext(%s,context);console.log(JSON.stringify(
            ['广发证券','广发资管','广发证券（资管）','青岸投资','信达证券',
            '中信证券','中信（投顾）','中信财富','中信证券资管'].map(q=>context.window.ITL.__test('inst',q).map(r=>r[0]))));""" % (
            json.dumps(investor_search_aliases(), ensure_ascii=False), json.dumps(source, ensure_ascii=False))
        proc = subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(proc.stdout), [['广发证券'], ['广发资管'], ['广发资管'], ['青岸资本'], ['信达证券（自营）'],
                                                ['中信证券（自营）'], ['中信证券（投顾）'], ['中信证券（财富）'], ['中信证券（资管）']])

    @unittest.skipUnless(shutil.which('node'), 'Node.js unavailable')
    def test_profile_excludes_legacy_cross_entity_credit_and_prefix(self):
        from gen_institution_profile import _PROFILE_JS_TEMPLATE
        js = _PROFILE_JS_TEMPLATE.replace('__PROG_ALL_DATA__', '[]').replace(
            '__PROG_ALIASES__', json.dumps(investor_search_aliases(), ensure_ascii=False))
        probe = """const vm=require('vm'); const ctx={setTimeout:()=>{},window:{}};
          vm.runInNewContext(%s,ctx);console.log(JSON.stringify(vm.runInNewContext(
          "[progResolveSingle('广发证券',{'广发证券':{},'广发资管':{}}),"+
          "progResolveSingle('青岸投资',{'青岸资本':{}}),"+
          "progMatchCreditSingle('工商银行'),progMatchCreditSingle('工银理财')]",ctx)));""" % json.dumps(js, ensure_ascii=False)
        proc = subprocess.run(['node', '-e', probe], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(proc.stdout), [['广发证券'], ['青岸资本'], None, '工银理财'])

    @unittest.skipUnless(shutil.which('node'), 'Node.js unavailable')
    def test_chat_search_exact_alias_and_no_prefix_merge(self):
        source = (ROOT / 'scripts/itl_chat.js').read_text(encoding='utf-8')
        source = source.replace('window.ITLChat = { init: init };',
                                'window.ITLChat = { init: init, __test: { initVocab: initVocab, matchEntities: matchEntities } };')
        records = [
            {'inst': name, 'mgr': '', 'underwriter': '', 'custodian': '', 'asset': '', 'rating': '', 'layer': ''}
            for name in ('广发证券', '广发资管', '中信证券（自营）', '中信证券（投顾）', '青岸资本', '信达证券（自营）')
        ]
        js = '''const vm=require('vm'); const context={window:{ITL_ALL_DATA:%s,ITL_ALIAS:%s},
          document:{readyState:'loading',addEventListener:()=>{}}};
          vm.runInNewContext(%s,context);let t=context.window.ITLChat.__test;t.initVocab();
          console.log(JSON.stringify(['广发证券','广发资管','广发证券（资管）','中信证券','中信证券（投顾）','中信自营','青岸投资','信达证券']
            .map(n=>t.matchEntities(n+'认购多少','share','inst').inst||[])));''' % (
            json.dumps(records, ensure_ascii=False), json.dumps(investor_search_aliases(), ensure_ascii=False),
            json.dumps(source, ensure_ascii=False))
        proc = subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True)
        result = json.loads(proc.stdout)
        self.assertEqual(result, [['广发证券'], ['广发资管'], ['广发资管'], ['中信证券（自营）'], ['中信证券（投顾）'], ['中信证券（自营）'], ['青岸资本'], ['信达证券（自营）']])


if __name__ == '__main__':
    unittest.main()
