"""JoySpace 数据源登记表与新鲜度检查的回归测试。"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import joyspace_sources as js


class RegistryTest(unittest.TestCase):
    def test_registry_is_valid_and_covers_four_panels(self) -> None:
        data = js.load_registry()
        keys = [d["key"] for d in data["datasets"]]
        self.assertEqual(sorted(keys), ["asset_distribution", "institution_profile",
                                        "risk_performance", "secondary_allocation"])
        for item in data["datasets"]:
            self.assertTrue(item["page_url"].startswith("https://joyspace.jd.com/sheets/"))
            self.assertTrue(item["sheets"])

    def test_read_url_carries_sheet_id(self) -> None:
        data = js.load_registry()
        item = next(d for d in data["datasets"] if d["key"] == "secondary_allocation")
        url = js.read_url(item, {"name": "11月", "sheet_id": 25})
        self.assertEqual(url, "https://joyspace.jd.com/sheets/89PMGlBmUHUueYQ6Cl7L?sheetId=25")

    def test_duplicate_key_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reg.json"
            item = {"key": "a", "label": "A", "page_url": "u", "page_id": "p",
                    "sheets": [{"name": "s", "sheet_id": 1}], "target": "t",
                    "date_field": "d", "refresh": "r"}
            path.write_text(json.dumps({"datasets": [item, dict(item)]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                js.load_registry(path)


class FreshnessTest(unittest.TestCase):
    def test_stale_datasets_flags_lagging_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            (root / "data" / "snap.json").write_text(
                json.dumps({"sources": {"dynamic": {"retrievedAt": "2026-10-01"}}}), encoding="utf-8")
            reg = {"datasets": [{
                "key": "risk_performance", "label": "风险表现", "page_url": "u", "page_id": "p",
                "sheets": [{"name": "s", "sheet_id": 1}], "target": "data/snap.json",
                "date_field": "sources.dynamic.retrievedAt", "refresh": "range_data"}]}
            (root / "data" / "joyspace_sources.json").write_text(json.dumps(reg), encoding="utf-8")
            with mock.patch.object(js, "ROOT", root), mock.patch.object(js, "REGISTRY", root / "data" / "joyspace_sources.json"):
                stale = js.stale_datasets("2026-11-13", max_lag=7)
            self.assertEqual(stale, [("风险表现", "2026-10-01", 43)])


class ApplyTest(unittest.TestCase):
    def test_apply_asset_distribution_writes_cells_and_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            snapshot = {"source": "old", "sheet": "old", "sheetId": 0, "range": "A1:A1",
                        "retrievedAt": "2026-11-05", "cells": []}
            (root / "data" / "asset_distribution_snapshot.json").write_text(
                json.dumps(snapshot), encoding="utf-8")
            reg = {"datasets": [{
                "key": "asset_distribution", "label": "消金资产",
                "page_url": "https://joyspace.jd.com/sheets/6DsPlXNgFeEBf7G2ghLx",
                "page_id": "6DsPlXNgFeEBf7G2ghLx",
                "sheets": [{"name": "资产余额", "sheet_id": 2}],
                "range": {"row_from": 3, "row_to": 21, "col_from": 2, "col_to": 23},
                "target": "data/asset_distribution_snapshot.json",
                "date_field": "retrievedAt", "refresh": "range_data"}]}
            (root / "data" / "joyspace_sources.json").write_text(json.dumps(reg), encoding="utf-8")
            payload = Path(tmp) / "range.json"
            payload.write_text(json.dumps([{"rowFrom": 3, "colFrom": 2, "cellText": "占比"}]),
                               encoding="utf-8")
            args = mock.Mock(dataset="asset_distribution", input=payload, xlsx=None, date="2026-11-14")
            with mock.patch.object(js, "ROOT", root), mock.patch.object(js, "REGISTRY", root / "data" / "joyspace_sources.json"):
                code = js.cmd_apply(args)
            self.assertEqual(code, 0)
            written = json.loads((root / "data" / "asset_distribution_snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(written["retrievedAt"], "2026-11-14")
            self.assertEqual(written["range"], "C4:X22")
            self.assertEqual(written["cells"][0]["cellText"], "占比")


if __name__ == "__main__":
    unittest.main()
