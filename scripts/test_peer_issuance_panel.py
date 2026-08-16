"""peer_issuance_panel 单元测试（不依赖真实 Excel）。"""

from __future__ import annotations

import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from peer_issuance_panel import (  # noqa: E402
    ASSET_FAMILY_ORDER,
    UNKNOWN_ASSET_FAMILY,
    asset_family,
    build_dashboard,
    is_jd,
    is_trust_channel,
    parse_rate,
    parse_term,
    rate_sparkline,
    render_body,
    weighted_avg,
    yoy_cutoff,
)

D = Decimal


def make_record(**overrides):
    record = {
        "week": "2026.8.10-2026.8.16", "product": "测试产品", "originator": "国投信托",
        "base_asset": "网商贷", "asset_type": "小微toB", "amount": D("10"),
        "date": date(2026, 8, 14), "aaa": D("0.0175"), "term": D("1.5"),
    }
    record.update(overrides)
    return record


class TestParse(unittest.TestCase):
    def test_rate_decimal_form(self):
        self.assertEqual(parse_rate(0.0175), D("0.0175"))

    def test_rate_multi_tier_text(self):
        # 多档利率“1.89%、1.93%”取首档
        self.assertEqual(parse_rate("1.89%、1.93%"), D("0.0189"))

    def test_rate_bare_percent_number(self):
        # 裸写的 1.89 视为百分数
        self.assertEqual(parse_rate("1.89"), D("0.0189"))

    def test_rate_invalid(self):
        self.assertIsNone(parse_rate(None))
        self.assertIsNone(parse_rate("—"))

    def test_term_multi_tier(self):
        self.assertEqual(parse_term("0.91、1.19"), D("0.91"))

    def test_term_numeric(self):
        self.assertEqual(parse_term(1.54), D("1.54"))


class TestJdExclusion(unittest.TestCase):
    def test_excludes_by_originator(self):
        self.assertTrue(is_jd(make_record(originator="京东世纪贸易")))

    def test_excludes_by_base_asset(self):
        self.assertTrue(is_jd(make_record(base_asset="京东白条")))

    def test_excludes_channel_issuance(self):
        # 走外贸信托通道发行的京东资产也必须剔除
        self.assertTrue(is_jd(make_record(originator="外贸信托", base_asset="京东金条")))

    def test_keeps_non_jd(self):
        self.assertFalse(is_jd(make_record(originator="财付通小贷", base_asset="腾讯分付")))


class TestAssetFamilies(unittest.TestCase):
    def test_maps_six_families(self):
        expectations = {
            "蚂蚁花呗": "蚂蚁系", "蚂蚁借呗": "蚂蚁系", "网商贷": "网商系",
            "腾讯分付": "腾讯系", "微众银行微粒贷": "微众系",
            "抖音放心借·小微": "字节系", "美团生活费": "美团系",
        }
        for base_asset, family in expectations.items():
            self.assertEqual(asset_family(base_asset), family)
        self.assertEqual(asset_family("度小满满易贷"), UNKNOWN_ASSET_FAMILY)

    def test_trust_channel_uses_originator_only(self):
        self.assertTrue(is_trust_channel(make_record(originator="外贸信托", base_asset="网商贷")))
        self.assertFalse(is_trust_channel(make_record(originator="财付通小贷", base_asset="腾讯分付")))


class TestAggregation(unittest.TestCase):
    def setUp(self):
        self.r2026 = [
            make_record(originator="国投信托", base_asset="网商贷", asset_type="小微toB",
                        amount=D("100"), date=date(2026, 8, 14), aaa=D("0.0160"), term=D("1")),
            make_record(originator="中信信托", base_asset="蚂蚁花呗", asset_type="消金分期类",
                        amount=D("50"), date=date(2026, 8, 13), aaa=D("0.0180"), term=D("2")),
            # 京东通道资产应被剔除
            make_record(originator="外贸信托", base_asset="京东金条", asset_type="消金提现类",
                        amount=D("30"), date=date(2026, 8, 12), aaa=D("0.0170"), term=D("1")),
            # 早期记录扩大同比差异
            make_record(originator="国投信托", base_asset="网商贷", asset_type="小微toB",
                        amount=D("40"), date=date(2026, 2, 10), aaa=D("0.0200"), term=D("1"),
                        week="2026.2.9-2026.2.15"),
        ]
        self.r2025 = [
            # 同期窗口内（≤ 2025-08-14）
            make_record(originator="国投信托", base_asset="网商贷", asset_type="小微toB",
                        amount=D("60"), date=date(2025, 5, 20), week="2025.5.19-2025.5.25"),
            # 同期窗口外（2025-09，不计入同比）
            make_record(originator="中信信托", base_asset="蚂蚁花呗", asset_type="消金分期类",
                        amount=D("999"), date=date(2025, 9, 10), week="2025.9.8-2025.9.14"),
            # 2025 的京东资产不计入同比
            make_record(originator="京东世纪贸易", base_asset="京东白条", asset_type="消金分期类",
                        amount=D("80"), date=date(2025, 3, 10), week="2025.3.9-2025.3.15"),
        ]
        self.data, self.qc = build_dashboard(self.r2026, self.r2025)

    def test_total_excludes_jd(self):
        # 100 + 50 + 40 = 190，京东 30 已剔除
        self.assertEqual(self.data["kpis"]["total_2026"]["amount"], D("190"))
        self.assertEqual(self.data["kpis"]["total_2026"]["count"], 3)

    def test_yoy_window(self):
        # 2025 同期仅国投信托 60 亿；窗口外 999 与京东 80 不计
        self.assertEqual(self.data["kpis"]["yoy"]["amount"], D("60"))
        yoy_pct = self.data["kpis"]["yoy"]["pct"]
        self.assertEqual(yoy_pct, (D("190") - D("60")) / D("60") * 100)

    def test_yoy_cutoff(self):
        self.assertEqual(self.data["meta"]["yoy_cutoff"], date(2025, 8, 14))

    def test_latest_week_weighted(self):
        # 最新簿记周 8.10-8.16 两笔：10 亿价 1.60% + 50 亿价 1.80%，加权 = (0.016*100+0.018*50)/150
        aaa = self.data["kpis"]["latest_week"]["aaa"]
        expected = (D("0.016") * D("100") + D("0.018") * D("50")) / D("150")
        self.assertEqual(aaa["wavg"], expected)
        self.assertEqual(aaa["min"], D("0.016"))
        self.assertEqual(aaa["max"], D("0.018"))

    def test_top_cards_order(self):
        names = [card["name"] for card in self.data["cards"]]
        self.assertEqual(names[0], "网商贷")  # 140 亿 > 蚂蚁花呗 50 亿
        self.assertNotIn("京东金条", names)

    def test_card_monthly_sum(self):
        card = self.data["cards"][0]
        self.assertEqual(sum(card["monthly"].values(), D("0")), card["amount"])

    def test_card_mom_rows(self):
        card = self.data["cards"][0]
        rows = {row["name"]: row for row in card["mom"]["rows"]}
        self.assertEqual(rows["国投信托"]["cur"], D("100"))
        self.assertEqual(rows["国投信托"]["prev"], D("0"))
        self.assertEqual(rows["国投信托"]["status"], "新增")

    def test_family_overview_aggregation(self):
        overview = {row["name"]: row for row in self.data["kpis"]["by_family"]}
        self.assertEqual(overview["网商系"]["amount_2026"], D("140"))
        self.assertEqual(overview["网商系"]["amount_2025"], D("60"))
        self.assertEqual(overview["蚂蚁系"]["amount_2026"], D("50"))
        self.assertEqual(
            sum((row["amount_2026"] for row in overview.values()), D("0")),
            self.data["kpis"]["total_2026"]["amount"],
        )

    def test_trust_channel_aggregation(self):
        channels = self.data["kpis"]["trust_channels"]
        self.assertEqual(channels["total"], D("190"))
        self.assertEqual([row["name"] for row in channels["rows"]], ["国投信托", "中信信托"])
        self.assertEqual(channels["rows"][0]["segments"]["网商系"], D("140"))
        self.assertEqual(channels["rows"][1]["segments"]["蚂蚁系"], D("50"))
        self.assertNotIn("京东金条", channels["unmapped_assets"])

    def test_no_warn_qc(self):
        warnings = [item for item in self.qc if item["level"] == "WARN"]
        self.assertEqual(warnings, [])


class TestTrustTopN(unittest.TestCase):
    def test_top_five_and_other_reconcile(self):
        records = []
        families = ["蚂蚁花呗", "网商贷", "腾讯分付", "微粒贷", "抖音放心借", "美团月付"]
        for index, base_asset in enumerate(families, 1):
            records.append(make_record(
                originator=f"渠道{index}信托", base_asset=base_asset,
                amount=D(str(70 - index * 10)), date=date(2026, 8, 14),
            ))
        # 未映射资产归入未知资产分段，并在 QC 数据中留痕。
        records.append(make_record(originator="渠道7信托", base_asset="度小满满易贷", amount=D("5"), date=date(2026, 8, 14)))
        data, qc = build_dashboard(records, [make_record(date=date(2025, 8, 1))])
        channels = data["kpis"]["trust_channels"]
        self.assertEqual(len(channels["rows"]), 6)
        self.assertEqual(channels["rows"][-1]["name"], "其他")
        self.assertEqual(channels["rows"][-1]["amount"], D("15"))
        self.assertEqual(channels["rows"][-1]["segments"][UNKNOWN_ASSET_FAMILY], D("5"))
        self.assertEqual(sum((row["amount"] for row in channels["rows"]), D("0")), channels["total"])
        self.assertEqual(channels["unmapped_assets"]["度小满满易贷"], D("5"))
        self.assertIn("TRUST_UNKNOWN_ASSETS", [item["code"] for item in qc])


class TestHelpers(unittest.TestCase):
    def test_weighted_avg_none_when_empty(self):
        self.assertIsNone(weighted_avg([]))
        self.assertIsNone(weighted_avg([(None, D("10"))]))

    def test_weighted_avg(self):
        self.assertEqual(weighted_avg([(D("0.02"), D("1")), (D("0.04"), D("1"))]), D("0.03"))

    def test_yoy_cutoff_leap(self):
        self.assertEqual(yoy_cutoff(date(2028, 2, 29)), date(2027, 2, 28))

    def test_sparkline_single_point(self):
        svg = rate_sparkline([{"week": "w", "avg": D("0.0175")}])
        self.assertIn("<svg", svg)
        self.assertNotIn("<polyline", svg)
        # 坐标轴与网格线存在
        self.assertEqual(svg.count("<line"), 7)  # 5 网格 + 2 轴

    def test_sparkline_multi_points(self):
        svg = rate_sparkline([{"week": "w1", "avg": D("0.02")}, {"week": "w2", "avg": D("0.018")}])
        self.assertIn("<polyline", svg)
        self.assertIn("2.00%", svg)  # 0.02 → 2.00%
        self.assertIn("1.80%", svg)
        # 每个数据点都有标记圆点
        self.assertEqual(svg.count("<circle"), 2)


class TestRender(unittest.TestCase):
    def test_body_fragment(self):
        data, _ = build_dashboard([make_record()], [make_record(date=date(2025, 4, 1), week="w25")])
        html = render_body(data)
        self.assertIn("同业发行面板", html)
        self.assertNotIn("<!doctype", html)
        self.assertNotIn("<script", html)
        # 顶部 KPI 卡已删除
        self.assertNotIn("peer-issuance-kpi", html)
        self.assertIn("同业发行概览", html)
        self.assertNotIn("资产类型同比", html)
        self.assertIn("信托渠道分布", html)
        self.assertIn("按具体基础资产归并至资产集团", html)
        self.assertIn("蚂蚁系", html)
        self.assertIn("美团系", html)
        self.assertIn("未知资产", html)
        self.assertIn("网商系 10 亿（100%）", html)
        self.assertIn("peer-issuance-trust-segment-label", html)
        self.assertIn("peer-issuance-stack-track", html)
        # 权益人区块已合并（不再有独立月度变化区块标题）
        self.assertIn("原始权益人发行规模与月度变化", html)
        self.assertNotIn("权益人月度变化（", html)

    def test_css_namespaced(self):
        from peer_issuance_panel import PEER_ISSUANCE_CSS
        self.assertIn(".peer-issuance-root", PEER_ISSUANCE_CSS)
        self.assertIn("#2a78d6", PEER_ISSUANCE_CSS)
        from peer_issuance_panel import PEER_ISSUANCE_EXTRA_CSS
        self.assertIn("peer-issuance-stack-track", PEER_ISSUANCE_EXTRA_CSS)
        self.assertIn("peer-issuance-cards{gap:22px", PEER_ISSUANCE_EXTRA_CSS)


if __name__ == "__main__":
    unittest.main()
