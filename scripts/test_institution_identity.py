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
        self.assertEqual(normalize_investor_name('中信证券（换券）'), '中信证券')
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

    def test_audit_covers_originals_and_keeps_secondary_local(self):
        rows = audit_rows()
        self.assertGreater(len(rows), 100)
        self.assertTrue(any(r[2] == '青岸投资' and r[3] == '青岸资本' for r in rows))
        self.assertTrue(any(r[2] == '广发资管' and r[3] == '广发资管' for r in rows))
        self.assertEqual(aliases()['信达证券'], '信达（自营）')
        self.assertTrue(any(r[1] == '次级投资人' and r[2] == '信达证券' and r[3] == '信达（自营）' for r in rows))

    @unittest.skipUnless(shutil.which('node'), 'Node.js unavailable')
    def test_ledger_suggestions_search_alias_without_blending_results(self):
        source = (ROOT / 'scripts/itl_panel.js').read_text(encoding='utf-8')
        source = source.replace('distinctCounts: distinctCounts\n  };',
                                'distinctCounts: distinctCounts, __test: function(f,q) { inputs[f]={value:q}; return suggestions(f); }\n  };')
        js = """const vm=require('vm');const context={window:{ITL_DATA:[
          {inst:'广发证券'},{inst:'广发资管'},{inst:'青岸资本'},{inst:'信达（自营）'}],ITL_ALIAS:%s}};
          vm.runInNewContext(%s,context);console.log(JSON.stringify(
            ['广发证券','广发资管','广发证券（资管）','青岸投资','信达证券'].map(q=>context.window.ITL.__test('inst',q).map(r=>r[0]))));""" % (
            json.dumps(investor_search_aliases(), ensure_ascii=False), json.dumps(source, ensure_ascii=False))
        proc = subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(proc.stdout), [['广发证券'], ['广发资管'], ['广发资管'], ['青岸资本'], ['信达（自营）']])

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
            for name in ('广发证券', '广发资管', '中信证券', '中信证券（投顾）', '青岸资本', '信达（自营）')
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
        self.assertEqual(result, [['广发证券'], ['广发资管'], ['广发资管'], ['中信证券'], ['中信证券（投顾）'], ['中信证券'], ['青岸资本'], ['信达（自营）']])


if __name__ == '__main__':
    unittest.main()
