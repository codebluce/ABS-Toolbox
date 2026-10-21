"""用户示例日期、休市跨期及跨年补录规则回归。"""
import unittest
from datetime import date
from supplement_peer_huatai import infer_booking

class BookingInferenceTest(unittest.TestCase):
    def test_user_example(self):
        self.assertEqual(infer_booking(date(2026,10,16)),date(2026,10,13))
    def test_holiday_and_year_boundary(self):
        self.assertEqual(infer_booking(date(2026,9,29)),date(2026,9,23))
        self.assertEqual(infer_booking(date(2026,9,30)),date(2026,9,24))
        self.assertEqual(infer_booking(date(2026,1,5)),date(2025,12,29))
    def test_closed_establishment_rejected(self):
        with self.assertRaises(ValueError):infer_booking(date(2026,9,25))

if __name__=='__main__':unittest.main()
