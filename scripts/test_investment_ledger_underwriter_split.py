"""投资台账联席承销商：组合文本拆成单一机构，筛选按参与关系匹配。"""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class UnderwriterSplitTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node.js unavailable')
    def test_options_and_filter_use_single_institutions(self):
        source = (ROOT / 'scripts/itl_panel.js').read_text(encoding='utf-8')
        source = source.replace(
            'distinctCounts: distinctCounts\n  };',
            'distinctCounts: distinctCounts,\n'
            '    __test: function(f,q) { inputs[f]={value:q}; return suggestions(f); },\n'
            '    __filter: function(f,vals) { st.selKw[f]=vals.slice(); return filtered(); },\n'
            '    __apply: function(spec) { applySpec(spec); return filtered().map(r=>r.share); }\n  };')
        js = """const vm=require('vm');
const rows=[
  {underwriter:'江苏银行/南京银行/宁波银行',share:1},
  {underwriter:'宁波银行/上海银行',share:2},
  {underwriter:'南京银行',share:3},
  {underwriter:'-',share:4}
];
const context={window:{ITL_DATA:rows}};
vm.runInNewContext(%s,context);
const t=context.window.ITL;
const out={
  search:t.__test('underwriter','宁波银行').map(r=>r),
  all:t.__test('underwriter','').map(r=>r[0]).sort(),
  ningbo:t.__filter('underwriter',['宁波银行']).map(r=>r.share),
  nanjing:t.__filter('underwriter',['南京银行']).map(r=>r.share),
  jiangsu:t.__filter('underwriter',['江苏银行']).map(r=>r.share),
  dash:t.__filter('underwriter',['-']).length
  ,legacy:t.__apply({filters:{underwriter:['江苏银行/南京银行']}})
};
console.log(JSON.stringify(out));
""" % json.dumps(source, ensure_ascii=False)
        proc = subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True)
        out = json.loads(proc.stdout)
        self.assertEqual(out['search'], [['宁波银行', 2]])
        self.assertEqual(out['all'], ['上海银行', '南京银行', '宁波银行', '江苏银行'])
        self.assertEqual(out['ningbo'], [1, 2])
        self.assertEqual(out['nanjing'], [1, 3])
        self.assertEqual(out['jiangsu'], [1])
        self.assertEqual(out['dash'], 0)
        self.assertEqual(out['legacy'], [1, 3])


if __name__ == '__main__':
    unittest.main()
