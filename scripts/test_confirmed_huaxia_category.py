import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / 'lab'))
import monthly_bid_institutions_demo as panel
import monthly_bookkeeping_qc as qc


class HuaxiaCategoryTest(unittest.TestCase):
    def test_confirmed_category_matches_independent_reader(self):
        self.assertEqual(panel.fund_classification()['explicitCategoryOverrides']['华夏久盈'], '公募基金')
        self.assertEqual(panel.classify('华夏久盈', panel.category_lookup())[0], '公募基金')
        self.assertEqual(qc._classify('华夏久盈', qc._classification_lookup())[0], '公募基金')
        self.assertEqual(panel.classify('平安养老', panel.category_lookup())[0], '其他')


if __name__ == '__main__':
    unittest.main()
