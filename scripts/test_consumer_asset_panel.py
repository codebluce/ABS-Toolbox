"""消金资产实验面板的口径与环比单元测试。"""

import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from consumer_asset_panel import metric, render_body, sum_items


class ConsumerAssetPanelTest(unittest.TestCase):
    def test_consumer_and_cash_loan_totals(self):
        values = {"白条消费": Decimal("120"), "分分卡": Decimal("20"), "金条": Decimal("300"), "白取": Decimal("50")}
        consumer_loan = sum_items(values, ("白条消费", "分分卡"))
        cash_loan = sum_items(values, ("金条", "白取"))
        self.assertEqual(consumer_loan, Decimal("140"))
        self.assertEqual(cash_loan, Decimal("350"))
        self.assertEqual(consumer_loan + cash_loan, Decimal("490"))

    def test_cash_loan_funding_aggregation(self):
        values = {"金条助贷": Decimal("300"), "白取助贷100%": Decimal("20"), "白取助贷联合贷": Decimal("10")}
        self.assertEqual(sum(values.values()), Decimal("330"))

    def test_positive_and_negative_change(self):
        increased = metric("余额", Decimal("120000000"), Decimal("100000000"))
        declined = metric("余额", Decimal("80000000"), Decimal("100000000"))
        self.assertEqual(increased["status"], "增长")
        self.assertEqual(increased["change_yuan"], Decimal("20000000"))
        self.assertEqual(declined["status"], "下降")
        self.assertEqual(declined["change_pct"], Decimal("-20"))

    def test_zero_and_missing_previous(self):
        added = metric("余额", Decimal("1"), Decimal("0"))
        unavailable = metric("余额", Decimal("1"), None)
        self.assertEqual(added["status"], "新增")
        self.assertIsNone(added["change_pct"])
        self.assertEqual(unavailable["status"], "无可比上期")
        self.assertIsNone(unavailable["change_yuan"])

    def test_dates_are_independent_values(self):
        white_date = date(2026, 8, 14)
        gold_date = date(2026, 8, 13)
        self.assertGreater(white_date, gold_date)
        self.assertNotEqual(white_date, gold_date)

    def test_comparison_baseline_is_five_days_prior(self):
        self.assertEqual(date.fromordinal(date(2026, 8, 14).toordinal() - 5), date(2026, 8, 9))
        self.assertEqual(date.fromordinal(date(2026, 8, 13).toordinal() - 5), date(2026, 8, 8))

    def test_render_body_is_fragment(self):
        metric_data = metric("消费贷", Decimal("100"), Decimal("90"))
        data = {
            "dates": {"baitiao": {"current": date(2026, 8, 14), "previous": date(2026, 8, 9)},
                      "jintiao": {"current": date(2026, 8, 13), "previous": date(2026, 8, 8)}},
            "consumer_loan": {"total": metric_data, "assets": [metric_data], "funding": [metric_data]},
            "cash_loan": {"total": metric_data, "assets": [metric_data], "funding": [metric_data]},
            "consumer_finance_total": {"total": metric_data},
        }
        body = render_body(data)
        self.assertIn("消金资产面板", body)
        self.assertNotIn("<!doctype html>", body.lower())
        self.assertNotIn("<script", body.lower())


if __name__ == "__main__":
    unittest.main()
