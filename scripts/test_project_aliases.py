"""项目名别名登记表：只做精确单跳映射，未登记不归并。"""
import unittest

import increment_merge
import project_aliases


class RegistryTest(unittest.TestCase):
    def test_registry_is_single_hop_and_complete(self):
        mapping = project_aliases.mapping()
        self.assertGreaterEqual(len(mapping), 30)
        self.assertTrue(all(reason for reason in [project_aliases.policy()]))

    def test_known_aliases_resolve_to_ledger_names(self):
        cases = {
            '金采玖2A': '金采9-2',
            '【26东裕ABN001】': '26东裕8号一期',
            '【东裕8-5】': '26东裕8号五期',
            '【尚乘1-4】': '尚乘1号第4期',
            '【26东裕5仲裕ABN001】': '（续发）25东裕5号仲裕ABCP',
        }
        for alias, canonical in cases.items():
            self.assertEqual(project_aliases.resolve(alias), canonical)

    def test_unregistered_name_passes_through(self):
        self.assertEqual(project_aliases.resolve('东裕9-3ABN'), '东裕9-3ABN')
        self.assertEqual(project_aliases.resolve('26东裕10号六期'), '26东裕10号六期')

    def test_validation_rejects_self_duplicate_and_chain(self):
        bad_rows = [
            [{'alias': 'A', 'canonical': 'A', 'reason': 'x'}],
            [{'alias': 'A', 'canonical': 'B', 'reason': 'x'},
             {'alias': 'A', 'canonical': 'C', 'reason': 'x'}],
            [{'alias': 'A', 'canonical': 'B', 'reason': 'x'},
             {'alias': 'B', 'canonical': 'C', 'reason': 'x'}],
            [{'alias': 'A', 'canonical': 'B'}],
        ]
        for rows in bad_rows:
            with self.assertRaises(ValueError):
                project_aliases._validate(rows)

    def test_stale_entries_detect_ledger_rename(self):
        stale = project_aliases.stale_entries({'26东裕9号一期'})
        self.assertIn('26东裕9号一期', set(project_aliases.mapping().values()))
        self.assertTrue(any(row['canonical'] == '金采9-2' for row in stale))

    def test_lookalike_hint_never_merges(self):
        hints = project_aliases.lookalikes('东裕9号一期', ['26东裕9号一期', '26东裕10号二期'])
        self.assertEqual(hints, ['26东裕9号一期'])
        self.assertFalse(project_aliases.registered('东裕9号一期'))


class MergeMappingTest(unittest.TestCase):
    def test_detail_filename_maps_through_registry(self):
        names = {'26东裕8号一期', '26东裕8号二期'}
        self.assertEqual(
            increment_merge.map_detail_to_project('【26东裕ABN001】项目簿记明细-20261016.xlsx', names),
            '26东裕8号一期')

    def test_unregistered_similar_name_keeps_original(self):
        names = {'26东裕9号一期', '26东裕9号二期'}
        self.assertEqual(
            increment_merge.map_detail_to_project('【东裕9-3ABN】项目簿记明细-20261201.xlsx', names),
            '【东裕9-3ABN】')


class ProjectSizeTest(unittest.TestCase):
    def test_missing_project_returns_none(self):
        class Empty:
            value = None

        class Sheet:
            max_row = 5
            def cell(self, row, column):
                return Empty()
        self.assertIsNone(increment_merge.project_size(Sheet(), '不存在的项目'))


if __name__ == '__main__':
    unittest.main()
