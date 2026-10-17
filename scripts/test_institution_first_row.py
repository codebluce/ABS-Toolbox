from pathlib import Path
import tempfile
import unittest

from openpyxl import Workbook

import gen_institution_stats as stats
from abs_common import COLNAMES


class InstitutionFirstRowTests(unittest.TestCase):
    def test_real_second_row_allocation_kept(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'ledger.xlsx'
            book=Workbook()
            sheet=book.active
            sheet.title='总表'
            sheet.append(COLNAMES)
            for institution,amount in [('首行机构',2),('后行机构',3)]:
                values={'资产类型':'赊销白条','项目名称':'测试项目','发行场所':'上交所',
                        '计划管理人':'中信证券','联席承销商':'招商证券','托管行':'建设银行',
                        '规模':5,'期限':'12','簿记时间':'2026-01-08','国股CD':.01,
                        '分层情况':'优先A','分层占比':1,'对应金额（亿）':5,
                        '成本':.02,'认购机构':institution,'认购份额':amount}
                sheet.append([values.get(name) for name in COLNAMES])
            book.save(path);book.close()
            frame,projects=stats.load_data(path,preprocessed_path=path)
            self.assertEqual(list(frame['认购机构']),['首行机构','后行机构'])
            self.assertEqual(frame['认购份额'].sum(),5)
            self.assertEqual(len(projects),1)


if __name__=='__main__':
    unittest.main()
