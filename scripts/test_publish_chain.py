"""综合看板与发布链路测试(审计 P2-05 补充)。

覆盖:
- build_integrated_html 动态 Tab(模块组合一致性,含空模块不渲染)
- verify_integrated_html QC 纯函数(异常必须被检出)
- encrypt/decrypt roundtrip(正确/错误密码)
- audit_protected_site 泄露自检(明文特征必须被检出)
- ledger_date_tag / latest_by_name_date 业务日期选择(mtime 干扰防护)
- publish_to_pages 分支行为(mock git,不碰真实仓库)

不依赖真实 Excel 与网络。
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from deploy_github_pages import (  # noqa: E402
    audit_protected_site,
    encrypt_dashboard_html,
    ledger_date_tag,
    latest_by_name_date,
    verify_dashboard_artifact,
)
from gen_integrated_dashboard import (  # noqa: E402
    TAB_CSS,
    build_integrated_html,
    verify_integrated_html,
)


def _panel(module: str, sub: str) -> str:
    return f"<div class='fake'>{module}/{sub}</div>"


class DynamicTabsTest(unittest.TestCase):
    """P2-01: 一级 Tab 按实际 panels 推导,无 panel 的模块不渲染。"""

    CSS_DUMMY = ".x{color:red}"

    def _tabs(self, panels):
        html = build_integrated_html(panels, self.CSS_DUMMY + TAB_CSS)
        import re
        return re.findall(r'data-module="(\w+)"[^>]*onclick="selectModule', html)

    def test_no_optional_sources_no_empty_tabs(self):
        panels = [
            ("pricing", "compare", _panel("pricing", "compare")),
            ("pricing", "invest", _panel("pricing", "invest")),
            ("progress", "quick", _panel("progress", "quick")),
            ("ledger", "query_2026", _panel("ledger", "query_2026")),
        ]
        tabs = self._tabs(panels)
        self.assertEqual(tabs, ["progress", "ledger", "pricing"])
        self.assertNotIn("asset_overview", tabs)
        self.assertNotIn("peer_issuance", tabs)

    def test_full_sources_all_tabs_in_order(self):
        panels = [
            ("pricing", "compare", _panel("pricing", "compare")),
            ("progress", "quick", _panel("progress", "quick")),
            ("ledger", "query_2026", _panel("ledger", "query_2026")),
            ("asset_overview", "consumer_asset", _panel("asset_overview", "consumer_asset")),
            ("peer_issuance", "overview", _panel("peer_issuance", "overview")),
        ]
        tabs = self._tabs(panels)
        self.assertEqual(tabs, ["progress", "ledger", "asset_overview", "pricing", "peer_issuance"])

    def test_every_module_has_matching_pane(self):
        panels = [
            ("pricing", "compare", _panel("pricing", "compare")),
            ("progress", "quick", _panel("progress", "quick")),
        ]
        html = build_integrated_html(panels, self.CSS_DUMMY + TAB_CSS)
        for module in ("progress", "pricing"):
            self.assertIn(f'data-module="{module}"', html)
        # 每个 tab 都有对应的 sub-tabs-pane
        import re
        panes = re.findall(r'class="sub-tabs-pane" data-module="(\w+)"', html)
        self.assertEqual(sorted(panes), ["pricing", "progress"])


class VerifyHtmlTest(unittest.TestCase):
    """P1-01: verify_integrated_html 必须能检出结构异常。"""

    def test_ok_content_passes(self):
        content = '<div class="panel" x></div>' * 3 + "function selectModule(){} function selectSub(){}"
        self.assertEqual(verify_integrated_html(content, 3), [])

    def test_panel_count_mismatch_detected(self):
        content = '<div class="panel"></div>' + "function selectModule(){} function selectSub(){}"
        problems = verify_integrated_html(content, 3)
        self.assertTrue(any("panel" in p for p in problems))

    def test_missing_switch_js_detected(self):
        content = '<div class="panel"></div>' * 2
        problems = verify_integrated_html(content, 2)
        self.assertTrue(any("selectModule" in p for p in problems))
        self.assertTrue(any("selectSub" in p for p in problems))

    def test_verify_dashboard_artifact_raises_on_bad(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
            f.write("<html>empty</html>")
            path = Path(f.name)
        try:
            with self.assertRaises(RuntimeError):
                verify_dashboard_artifact(path)
        finally:
            path.unlink()


class CryptoRoundTripTest(unittest.TestCase):
    """正确/错误密码解密验证。"""

    def _roundtrip(self, password: str, guess: str, should_pass: bool):
        import tempfile
        html = "<!DOCTYPE html><html><body>测试看板内容 ABC</body></html>"
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
            f.write(html)
            path = Path(f.name)
        try:
            payload = encrypt_dashboard_html(path, password, 1000)
            key = hashlib.pbkdf2_hmac(
                "sha256", guess.encode(), base64.b64decode(payload["salt"]), 1000, dklen=32
            )
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            try:
                cipher = base64.b64decode(payload["ciphertext"])
                plain = AESGCM(key).decrypt(base64.b64decode(payload["iv"]), cipher, None)
                text = gzip.decompress(plain).decode("utf-8")
                self.assertTrue(should_pass, "错误密码不应解密成功")
                self.assertEqual(text, html)
            except Exception:
                self.assertFalse(should_pass, "正确密码必须解密成功")
        finally:
            path.unlink()

    def test_correct_password(self):
        self._roundtrip("right-pass", "right-pass", True)

    def test_wrong_password(self):
        self._roundtrip("right-pass", "wrong-pass", False)

    def test_payload_has_no_plaintext(self):
        import tempfile
        html = "<!DOCTYPE html><html><body>机密内容XYZ</body></html>"
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
            f.write(html)
            path = Path(f.name)
        try:
            payload = encrypt_dashboard_html(path, "pw", 1000)
            blob = payload["ciphertext"] + payload["salt"] + payload["iv"]
            self.assertNotIn("机密内容XYZ", blob)
            self.assertNotIn("<!DOCTYPE", blob)
        finally:
            path.unlink()


class AuditProtectedSiteTest(unittest.TestCase):
    """A3: protected 站点包泄露自检。"""

    def test_clean_shell_passes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            site = Path(root) / "site"
            site.mkdir()
            (site / "index.html").write_text("<!doctype html>加密壳" + "A" * 500, encoding="utf-8")
            src = Path(root) / "src.html"
            src.write_text("<!DOCTYPE html>" + "不同内容" * 100, encoding="utf-8")
            audit_protected_site(site, src)  # 不应抛异常

    def test_xlsx_leak_detected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            site = Path(root) / "site"
            site.mkdir()
            (site / "index.html").write_text("<!doctype html>壳", encoding="utf-8")
            (site / "data.xlsx").write_bytes(b"fake")
            src = Path(root) / "src.html"
            src.write_text("<!DOCTYPE html>源", encoding="utf-8")
            with self.assertRaises(RuntimeError) as ctx:
                audit_protected_site(site, src)
            self.assertIn("敏感文件", str(ctx.exception))

    def test_plaintext_dashboard_leak_detected(self):
        import tempfile
        src_content = "<!DOCTYPE html><html>明文看板全部内容" + "B" * 3000
        with tempfile.TemporaryDirectory() as root:
            site = Path(root) / "site"
            site.mkdir()
            src = Path(root) / "src.html"
            src.write_text(src_content, encoding="utf-8")
            # 站点内某文件包含源 HTML 的头部 2048 字节片段 → 疑似明文泄露
            (site / "leaked.html").write_text(src_content, encoding="utf-8")
            (site / "index.html").write_text("<!doctype html>壳", encoding="utf-8")
            with self.assertRaises(RuntimeError) as ctx:
                audit_protected_site(site, src)
            self.assertIn("明文看板", str(ctx.exception))


class LedgerSelectionTest(unittest.TestCase):
    """P2-02: 文件名业务日期优先,mtime 干扰防护。"""

    def test_ledger_date_tag_variants(self):
        self.assertEqual(ledger_date_tag(Path("2026年ABS发行台账-0807-定稿.xlsx")), "20260807")
        self.assertEqual(ledger_date_tag(Path("2026年ABS发行台账-20260807-定稿.xlsx")), "20260807")

    def test_touched_old_file_not_selected(self):
        import os
        import tempfile
        import time
        with tempfile.TemporaryDirectory() as d:
            old = Path(d) / "2026年ABS发行台账-0801-定稿.xlsx"
            new = Path(d) / "2026年ABS发行台账-0807-定稿.xlsx"
            old.write_text("a")
            new.write_text("b")
            os.utime(old, (time.time() + 500, time.time() + 500))  # 旧文件 mtime 更大
            self.assertEqual(latest_by_name_date([old, new]), new)


class PublishToPagesTest(unittest.TestCase):
    """P1-02/P2-04: publish_to_pages 分支行为(mock git)。"""

    def _patch_capture(self, returns):
        """按命令前缀返回预设 stdout。"""
        seq = list(returns)

        def fake_capture(cmd, cwd=None, check=True):
            for i, (prefix, out) in enumerate(seq):
                if " ".join(cmd).startswith(prefix):
                    seq.pop(i)
                    return out
            return ""

        return fake_capture

    def test_diverged_local_aborts(self):
        import tempfile
        from deploy_github_pages import publish_to_pages
        with tempfile.TemporaryDirectory() as d:
            site = Path(d) / "site"
            site.mkdir()
            (site / "index.html").write_text("x", encoding="utf-8")
            with mock.patch("deploy_github_pages.run"), mock.patch(
                "deploy_github_pages.capture",
                side_effect=self._patch_capture([
                    ("git rev-parse refs/heads/gh-pages", "aaa111"),
                    ("git rev-parse refs/remotes/origin/gh-pages", "bbb222"),
                    ("git merge-base", "ccc333"),  # 分叉: base 既非 local 也非 remote
                ]),
            ), mock.patch("subprocess.run") as fake_sub:
                fake_sub.return_value.returncode = 0
                with self.assertRaises(RuntimeError) as ctx:
                    publish_to_pages(site, "origin", "gh-pages", "m", no_push=True)
                self.assertIn("分叉", str(ctx.exception))

    def test_no_push_no_git_push_called(self):
        import tempfile
        from deploy_github_pages import publish_to_pages
        with tempfile.TemporaryDirectory() as d:
            site = Path(d) / "site"
            site.mkdir()
            (site / "index.html").write_text("x", encoding="utf-8")
            pushes = []

            def fake_run(cmd, cwd=None, check=True):
                if "push" in cmd:
                    pushes.append(cmd)

            with mock.patch("deploy_github_pages.run", side_effect=fake_run), mock.patch(
                "subprocess.run"
            ) as fake_sub, mock.patch("shutil.copytree"), mock.patch(
                "shutil.copy2"
            ), mock.patch("deploy_github_pages.remove_worktree_contents"):
                fake_sub.return_value.returncode = 0
                # diff_status 非空 → 走 commit 分支,但 no_push=True 不得 push
                with mock.patch("deploy_github_pages.capture",
                                side_effect=lambda cmd, cwd=None, check=True:
                                 "M index.html" if "status" in cmd else
                                 ("aaa111" if "rev-parse" in cmd or "merge-base" in cmd else "")):
                    changed = publish_to_pages(site, "origin", "gh-pages", "msg", no_push=True)
                self.assertTrue(changed)
                self.assertEqual(pushes, [])

    def _run_no_change_publish(self, local_sha, remote_sha, has_local=True):
        """辅助:构造"无文件变化"场景并返回 (pushes, changed)。"""
        import tempfile
        from deploy_github_pages import publish_to_pages
        with tempfile.TemporaryDirectory() as d:
            site = Path(d) / "site"
            site.mkdir()
            (site / "index.html").write_text("x", encoding="utf-8")
            pushes = []

            def fake_run(cmd, cwd=None, check=True):
                if "push" in cmd:
                    pushes.append(cmd)

            def fake_capture(cmd, cwd=None, check=True):
                cmd_str = " ".join(cmd)
                if "status" in cmd_str:
                    return ""  # 无文件变化
                if "rev-parse" in cmd_str and "refs/heads/gh-pages" in cmd_str:
                    return local_sha
                if "rev-parse" in cmd_str and "refs/remotes/origin/gh-pages" in cmd_str:
                    return remote_sha
                if "merge-base" in cmd_str:
                    # fast-forward 关系: base 取两端之一(local 领先→base=remote,反之亦然)
                    return local_sha if local_sha != remote_sha and len(local_sha) <= len(remote_sha) else remote_sha
                if "rev-parse" in cmd_str and cmd_str.endswith("HEAD"):
                    return "new000"
                return ""

            with mock.patch("deploy_github_pages.run", side_effect=fake_run), mock.patch(
                "deploy_github_pages.capture", side_effect=fake_capture
            ), mock.patch("subprocess.run") as fake_sub, mock.patch(
                "shutil.copytree"
            ), mock.patch("shutil.copy2"), mock.patch(
                "deploy_github_pages.remove_worktree_contents"
            ):
                fake_sub.return_value.returncode = 0
                changed = publish_to_pages(site, "origin", "gh-pages", "msg", no_push=False)
            return pushes, changed

    def test_no_change_refs_equal_skips_push(self):
        # REV-04 场景1: 无变化 + 本地/远端引用一致 → 跳过 push
        pushes, changed = self._run_no_change_publish("same111", "same111", has_local=True)
        self.assertFalse(changed)
        self.assertEqual(pushes, [])

    def test_no_change_local_ahead_pushes(self):
        # REV-04 场景2: 无变化 + 本地领先(引用不等但 merge-base=local) → 执行 push
        pushes, changed = self._run_no_change_publish("ahead11", "behind2", has_local=True)
        self.assertFalse(changed)
        self.assertEqual(len(pushes), 1)

    def test_no_change_no_local_branch(self):
        # REV-04 场景3: 无变化 + 无本地分支(引用比对 local_sha='') → 触发 push(方向安全,真实环境无本地分支时 push 会报错中止而非错误发布)
        pushes, changed = self._run_no_change_publish("", "remote1", has_local=False)
        self.assertFalse(changed)
        self.assertEqual(len(pushes), 1)


if __name__ == "__main__":
    unittest.main()
