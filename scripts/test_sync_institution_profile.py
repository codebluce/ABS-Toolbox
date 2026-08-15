"""机构画像同步的权威负责人归并测试。"""

import unittest

from sync_institution_profile import merge_records_by_assignment, normalize_contact


class InstitutionProfileSyncTest(unittest.TestCase):
    def test_assignment_owner_overrides_source_owner_and_merges_history(self):
        assignments = {
            "招商银行/招银理财": {"person": "姜守园", "category": "国股行"},
        }
        records = [
            {
                "name": "招银理财/招商银行", "owner": "刘啸飞", "category": "待分类",
                "contact": "张杰", "approval": "批复A", "quota": "额度A",
                "recent_progress": [{"date": "0803-0807", "text": "进展1"}], "progress_count": 1,
            },
            {
                "name": "招商银行/招银理财", "owner": "姜守园", "category": "待分类",
                "contact": "李四", "approval": "", "quota": "",
                "recent_progress": [{"date": "0803-0807", "text": "进展1"}, {"date": "0726-0731", "text": "进展2"}], "progress_count": 2,
            },
        ]
        merged, warnings = merge_records_by_assignment(records, assignments)
        self.assertEqual(warnings, [])
        self.assertEqual(len(merged), 1)
        result = merged[0]
        self.assertEqual(result["name"], "招商银行/招银理财")
        self.assertEqual(result["owner"], "姜守园")
        self.assertEqual(result["category"], "国股行")
        self.assertIn("张杰", result["contact"])
        self.assertIn("李四", result["contact"])
        self.assertEqual(result["approval"], "批复A")
        self.assertEqual(result["quota"], "额度A")
        self.assertEqual(result["progress_count"], 2)

    def test_contact_cleanup_removes_placeholders_and_business_tail(self):
        cleaned, actions, review = normalize_contact(
            "赵伊异-高级投资经理; 安奕霖-产品经理白条、金条、保理总额度140亿，上限60亿; 赵伊异-高级投资经理",
            "白条、金条、保理", "总额度140亿，上限60亿",
        )
        self.assertIn("赵伊异-高级投资经理", cleaned)
        self.assertIn("安奕霖-产品经理", cleaned)
        self.assertNotIn("总额度", cleaned)
        self.assertIn("business_tail_removed", actions)
        self.assertEqual(review, [])
        self.assertEqual(normalize_contact("暂无联系人")[0], "")

    def test_contact_role_conflict_is_preserved_for_review(self):
        cleaned, _, review = normalize_contact("张杰-总助; 张杰-项目投资一部负责人")
        self.assertIn("张杰-总助", cleaned)
        self.assertIn("张杰-项目投资一部负责人", cleaned)
        self.assertIn("possible_role_conflict:张杰", review)

    def test_unmapped_owner_is_preserved(self):
        records = [{
            "name": "未分配机构", "owner": "高雅", "category": "其他",
            "contact": "", "approval": "", "quota": "", "recent_progress": [], "progress_count": 0,
        }]
        merged, _ = merge_records_by_assignment(records, {})
        self.assertEqual(merged[0]["owner"], "高雅")
        self.assertEqual(merged[0]["name"], "未分配机构")


if __name__ == "__main__":
    unittest.main()
