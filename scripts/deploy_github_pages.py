#!/usr/bin/env python3
"""Generate and publish ABS dashboard static site to GitHub Pages.

Workflow:
  1. Optionally generate the latest integrated dashboard from a ledger workbook.
  2. Build a static site package from deliverables/dashboards/01_latest.
  3. Sync the package to the gh-pages branch via a temporary git worktree.
  4. Commit and push to GitHub.

This script never uploads source Excel files or scripts to Pages; only the static HTML
site package is copied to gh-pages.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
LATEST_DIR = REPO_ROOT / "deliverables" / "dashboards" / "01_latest"
SITE_STAGING_DIR = REPO_ROOT / "deliverables" / "dashboard_site"
FINAL_LEDGER_DIR = REPO_ROOT / "deliverables" / "ledger" / "03_final"
DASHBOARD_PREFIX = "ABS综合看板_"
DASHBOARD_SUFFIX = ".html"

# Cloudflare Pages 国内加速镜像。指向 gh-pages 分支自动同步,与 GitHub Pages 内容一致。
# 创建项目后回填实际 URL(形如 https://abs-toolbox-xxxx.pages.dev);留空则不提示。
# 详见 docs/cloudflare_pages_部署.md。
CF_PAGES_URL = os.environ.get("ABS_CF_PAGES_URL", "")


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(cmd))
    return subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        check=check,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def capture(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        check=check,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.strip()


def latest_by_mtime(paths: Iterable[Path]) -> Path:
    items = [p for p in paths if p.exists()]
    if not items:
        raise FileNotFoundError("没有找到可用文件")
    return max(items, key=lambda p: p.stat().st_mtime)


def find_latest_ledger() -> Path:
    candidates = sorted(FINAL_LEDGER_DIR.glob("2026年ABS发行台账-*-定稿.xlsx"))
    if not candidates:
        raise FileNotFoundError(f"未找到定稿台账: {FINAL_LEDGER_DIR}")
    # Prefer newest by modification time so manually refreshed files are picked up.
    return latest_by_mtime(candidates)


def find_dashboard_files() -> list[Path]:
    files = sorted(LATEST_DIR.glob(f"{DASHBOARD_PREFIX}*{DASHBOARD_SUFFIX}"))
    if not files:
        raise FileNotFoundError(f"未找到综合看板 HTML: {LATEST_DIR}")
    return files


def dashboard_date(path: Path) -> str:
    name = path.name
    if name.startswith(DASHBOARD_PREFIX) and name.endswith(DASHBOARD_SUFFIX):
        return name[len(DASHBOARD_PREFIX):-len(DASHBOARD_SUFFIX)]
    return path.stem


def generate_dashboard(ledger_path: Path, baitiao_path: Path | None = None, jintiao_path: Path | None = None) -> Path:
    print(f"\n[1/4] 生成最新综合看板: {ledger_path}")
    command = [sys.executable, str(SCRIPTS_DIR / "gen_integrated_dashboard.py"), str(ledger_path)]
    if baitiao_path and jintiao_path:
        command.extend(["--baitiao-xlsx", str(baitiao_path), "--jintiao-xlsx", str(jintiao_path)])
    run(command)
    return latest_by_mtime(find_dashboard_files())


def encrypt_dashboard_html(dashboard_path: Path, password: str, iterations: int) -> dict:
    """Return encrypted payload metadata for static password-gated Pages.

    The deployed page contains only gzip(html) encrypted by AES-GCM. The password is
    never written to disk; it is used to derive a 256-bit key through PBKDF2-SHA256.
    """
    if not password:
        raise ValueError("protected mode requires a non-empty password")
    raw = dashboard_path.read_bytes()
    compressed = gzip.compress(raw, compresslevel=6, mtime=0)
    salt = secrets.token_bytes(16)
    iv = secrets.token_bytes(12)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
    cipher = AESGCM(key).encrypt(iv, compressed, None)
    return {
        "algorithm": "PBKDF2-SHA256 + AES-256-GCM + gzip",
        "iterations": iterations,
        "salt": base64.b64encode(salt).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii"),
        "ciphertext": base64.b64encode(cipher).decode("ascii"),
        "plainBytes": len(raw),
        "gzipBytes": len(compressed),
        "cipherBytes": len(cipher),
    }


def protected_shell_html(latest_dashboard: Path, payload: dict) -> str:
    latest_name = latest_dashboard.name
    latest_date = dashboard_date(latest_dashboard)
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>ABS 综合看板 · 访问验证</title>
  <style>
    :root{{color-scheme:light;--ink:#111827;--muted:#667085;--line:#e5e7eb;--bg:#f6f7f9;--card:#fff;--brand:#172033;--danger:#b42318;--ok:#067647;}}
    *{{box-sizing:border-box}} body{{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at 20% 20%,#eef4ff,transparent 30%),var(--bg);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;color:var(--ink)}}
    .card{{width:min(560px,calc(100vw - 32px));background:rgba(255,255,255,.92);border:1px solid rgba(229,231,235,.9);border-radius:24px;padding:30px;box-shadow:0 24px 80px rgba(15,23,42,.12);backdrop-filter:blur(14px)}}
    .eyebrow{{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:700}} h1{{margin:10px 0 8px;font-size:30px;line-height:1.12}} p{{margin:0;color:var(--muted);line-height:1.7;font-size:14px}} .meta{{margin:18px 0;padding:14px;border:1px solid var(--line);border-radius:14px;background:#fbfcfe;font-size:13px;color:#475467;display:grid;gap:6px}}
    label{{display:block;margin:22px 0 8px;font-weight:700;font-size:14px}} .row{{display:flex;gap:10px}} input{{flex:1;border:1px solid #cfd4dc;border-radius:12px;padding:13px 14px;font-size:16px;outline:none}} input:focus{{border-color:#344054;box-shadow:0 0 0 4px rgba(52,64,84,.08)}} button{{border:0;border-radius:12px;background:var(--brand);color:white;font-weight:800;padding:0 18px;font-size:15px;cursor:pointer}} button:disabled{{opacity:.6;cursor:not-allowed}} .msg{{min-height:22px;margin-top:12px;font-size:14px}} .err{{color:var(--danger)}} .ok{{color:var(--ok)}} .hint{{margin-top:18px;font-size:12px;color:#98a2b3}}
    #viewer{{display:none;position:fixed;inset:0;border:0;width:100vw;height:100vh;background:white}}
  </style>
</head>
<body>
  <main class="card" id="gate">
    <div class="eyebrow">ABS Dashboard Protected</div>
    <h1>ABS 综合看板</h1>
    <p>请输入访问密码。看板数据已在发布前加密,密码只在本机浏览器中用于解密,不会发送到服务器。</p>
    <div class="meta">
      <div><strong>版本</strong>：{latest_date}</div>
      <div><strong>来源</strong>：{latest_name}</div>
      <div><strong>加密</strong>：PBKDF2-SHA256 / AES-GCM / gzip</div>
    </div>
    <label for="password">访问密码</label>
    <div class="row"><input id="password" type="password" autocomplete="current-password" placeholder="输入密码后按 Enter"><button id="unlock">解锁</button></div>
    <div class="msg" id="msg"></div>
    <div class="hint">提示：首次解锁会在浏览器本地完成密钥派生、解密和解压；请使用强密码并避免在公共设备保存。</div>
  </main>
  <iframe id="viewer" sandbox="allow-scripts allow-same-origin allow-downloads allow-popups allow-forms"></iframe>
  <script>
    const PAYLOAD = {payload_json};
    const $ = (id) => document.getElementById(id);
    const msg = (text, cls='') => {{ $('msg').className = 'msg ' + cls; $('msg').textContent = text; }};
    const b64 = (s) => Uint8Array.from(atob(s), c => c.charCodeAt(0));
    async function deriveKey(password) {{
      const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveKey']);
      return crypto.subtle.deriveKey({{name:'PBKDF2', salt:b64(PAYLOAD.salt), iterations:PAYLOAD.iterations, hash:'SHA-256'}}, base, {{name:'AES-GCM', length:256}}, false, ['decrypt']);
    }}
    async function ungzip(bytes) {{
      if (!('DecompressionStream' in window)) throw new Error('当前浏览器不支持 DecompressionStream,请升级浏览器。');
      const ds = new DecompressionStream('gzip');
      const stream = new Blob([bytes]).stream().pipeThrough(ds);
      const buf = await new Response(stream).arrayBuffer();
      return new TextDecoder('utf-8').decode(buf);
    }}
    async function unlock() {{
      const password = $('password').value;
      if (!password) {{ msg('请输入密码。', 'err'); return; }}
      $('unlock').disabled = true;
      const t0 = performance.now();
      try {{
        msg('正在解密看板...', '');
        const key = await deriveKey(password);
        const plain = await crypto.subtle.decrypt({{name:'AES-GCM', iv:b64(PAYLOAD.iv)}}, key, b64(PAYLOAD.ciphertext));
        const html = await ungzip(new Uint8Array(plain));
        const elapsed = Math.round(performance.now() - t0);
        msg('解锁成功,正在打开看板... ' + elapsed + 'ms', 'ok');
        const viewer = $('viewer');
        viewer.srcdoc = html;
        viewer.style.display = 'block';
        $('gate').style.display = 'none';
      }} catch (err) {{
        console.error(err);
        msg('密码错误或浏览器不支持解密。', 'err');
      }} finally {{
        $('unlock').disabled = false;
      }}
    }}
    $('unlock').addEventListener('click', unlock);
    $('password').addEventListener('keydown', e => {{ if (e.key === 'Enter') unlock(); }});
    $('password').focus();
  </script>
</body>
</html>
"""


def write_archive_index(archive_dir: Path, dashboards: list[Path]) -> None:
    rows = []
    for p in sorted(dashboards, key=dashboard_date, reverse=True):
        size_mb = p.stat().st_size / 1024 / 1024
        date = dashboard_date(p)
        rows.append(
            f'<tr><td>{date}</td><td><a href="{p.name}">{p.name}</a></td><td>{size_mb:.2f} MB</td></tr>'
        )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ABS综合看板历史归档</title>
  <style>
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;margin:32px;background:#f6f7f9;color:#172033;}}
    .wrap{{max-width:960px;margin:auto;background:white;border-radius:18px;padding:28px;box-shadow:0 12px 40px rgba(15,23,42,.08);}}
    h1{{margin:0 0 8px;font-size:28px;}}
    p{{color:#667085;}}
    table{{width:100%;border-collapse:collapse;margin-top:20px;}}
    th,td{{padding:12px 10px;border-bottom:1px solid #e5e7eb;text-align:left;font-size:14px;}}
    th{{color:#475467;background:#f9fafb;}}
    a{{color:#175cd3;text-decoration:none;font-weight:600;}}
    .top{{display:flex;justify-content:space-between;gap:16px;align-items:center;}}
    .btn{{display:inline-block;padding:10px 14px;border-radius:10px;background:#172033;color:white;}}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <div>
        <h1>ABS综合看板历史归档</h1>
        <p>最新版本请访问 <a href="../index.html">主入口 index.html</a>。</p>
      </div>
      <a class="btn" href="../index.html">返回最新看板</a>
    </div>
    <table>
      <thead><tr><th>日期</th><th>文件</th><th>大小</th></tr></thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
</body>
</html>
"""
    (archive_dir / "index.html").write_text(html, encoding="utf-8")


def build_site(
    latest_dashboard: Path | None = None,
    *,
    protected: bool = False,
    password: str | None = None,
    iterations: int = 310_000,
) -> Path:
    print("\n[2/4] 组装静态站点包...")
    dashboards = find_dashboard_files()
    latest_dashboard = latest_dashboard or latest_by_mtime(dashboards)

    if SITE_STAGING_DIR.exists():
        shutil.rmtree(SITE_STAGING_DIR)
    SITE_STAGING_DIR.mkdir(parents=True, exist_ok=True)

    protected_payload = None
    if protected:
        if not password:
            raise RuntimeError("--protected 需要通过环境变量提供密码")
        print("[site] protected 模式: gzip(html) + AES-GCM, 不发布明文 archive")
        protected_payload = encrypt_dashboard_html(latest_dashboard, password, iterations)
        (SITE_STAGING_DIR / "index.html").write_text(
            protected_shell_html(latest_dashboard, protected_payload), encoding="utf-8"
        )
    else:
        archive_dir = SITE_STAGING_DIR / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(latest_dashboard, SITE_STAGING_DIR / "index.html")
        for p in dashboards:
            shutil.copy2(p, archive_dir / p.name)
        write_archive_index(archive_dir, dashboards)

    (SITE_STAGING_DIR / ".nojekyll").write_text("", encoding="utf-8")

    # Keep the site package deterministic for the same dashboard HTML.
    # Otherwise every dry run changes manifest/README timestamps and creates noisy gh-pages commits.
    packaged_at = datetime.fromtimestamp(latest_dashboard.stat().st_mtime).isoformat(timespec="seconds")
    manifest = {
        "generatedAt": packaged_at,
        "latest": latest_dashboard.name,
        "latestDate": dashboard_date(latest_dashboard),
        "dashboardCount": 1 if protected else len(dashboards),
        "archive": [] if protected else [p.name for p in sorted(dashboards, key=dashboard_date, reverse=True)],
        "protected": protected,
        "source": "scripts/deploy_github_pages.py",
    }
    if protected_payload:
        manifest["encryption"] = {
            "algorithm": protected_payload["algorithm"],
            "iterations": protected_payload["iterations"],
            "plainBytes": protected_payload["plainBytes"],
            "gzipBytes": protected_payload["gzipBytes"],
            "cipherBytes": protected_payload["cipherBytes"],
        }
    (SITE_STAGING_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    archive_line = "- 历史归档：已下线（protected 模式不发布明文历史版本）" if protected else "- 历史归档：`archive/index.html`"
    security_line = "安全说明：站点包为加密门禁版本，`index.html` 只包含密文和本地解密逻辑，不包含明文看板。" if protected else "安全说明：站点包只包含静态 HTML，不包含源 Excel、簿记明细、脚本、`.env` 等文件。"
    readme = f"""# ABS综合看板静态站点包

本目录由 `scripts/deploy_github_pages.py` 自动生成，用于发布到 GitHub Pages。

- 最新入口：`index.html`
- 最新来源：`{latest_dashboard.relative_to(REPO_ROOT)}`
{archive_line}
- 生成时间：`{manifest['generatedAt']}`
- 加密模式：`{protected}`

{security_line}
"""
    (SITE_STAGING_DIR / "README.md").write_text(readme, encoding="utf-8")

    print(f"[site] 最新: {latest_dashboard.name}")
    if protected_payload:
        print(
            f"[site] 加密体积: raw={protected_payload['plainBytes']} "
            f"gzip={protected_payload['gzipBytes']} cipher={protected_payload['cipherBytes']}"
        )
    print(f"[site] 文件数: {len(list(SITE_STAGING_DIR.rglob('*')))}")
    return SITE_STAGING_DIR


def ensure_clean_main() -> None:
    status = capture(["git", "status", "--short"])
    if status:
        raise RuntimeError(
            "main 工作树不干净。为避免部署夹带未提交改动,请先处理以下文件:\n" + status
        )


def remove_worktree_contents(worktree: Path) -> None:
    for child in worktree.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def publish_to_pages(site_dir: Path, remote: str, branch: str, message: str, no_push: bool) -> bool:
    print("\n[3/4] 同步到 gh-pages worktree...")
    tmp_parent = Path(tempfile.mkdtemp(prefix="abs_pages_"))
    worktree = tmp_parent / "worktree"
    changed = False
    try:
        # Ensure local branch exists. If not, create it from remote branch.
        has_local = subprocess.run(["git", "show-ref", "--verify", f"refs/heads/{branch}"], cwd=REPO_ROOT).returncode == 0
        if not has_local:
            run(["git", "fetch", remote, f"{branch}:{branch}"])
        run(["git", "worktree", "add", str(worktree), branch])

        remove_worktree_contents(worktree)
        for item in site_dir.iterdir():
            dest = worktree / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        run(["git", "add", "-A"], cwd=worktree)
        diff_status = capture(["git", "status", "--short"], cwd=worktree)
        if not diff_status:
            print("[pages] gh-pages 无文件变化")
            if no_push:
                print("[pages] --no-push 已设置,跳过推送")
            else:
                print("[pages] 仍执行 git push,确保本地 gh-pages 已同步到远端")
                run(["git", "push", remote, f"{branch}:{branch}"], cwd=worktree)
            return False
        changed = True
        print(diff_status)
        run(["git", "commit", "-m", message], cwd=worktree)
        if no_push:
            print("[pages] --no-push 已设置,未推送远端")
        else:
            print("\n[4/4] 推送到 GitHub Pages...")
            run(["git", "push", remote, f"{branch}:{branch}"], cwd=worktree)
        return True
    finally:
        try:
            run(["git", "worktree", "remove", "--force", str(worktree)], check=False)
        finally:
            shutil.rmtree(tmp_parent, ignore_errors=True)
        if changed:
            print("[pages] 临时 worktree 已清理")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成并发布 ABS 综合看板到 GitHub Pages")
    parser.add_argument("--ledger", type=Path, default=None, help="定稿台账路径。默认使用 03_final 下最新 2026 定稿")
    parser.add_argument("--baitiao-xlsx", type=Path, default=None, help="白条大盘余额原始 Excel（需与金条源成对传入）")
    parser.add_argument("--jintiao-xlsx", type=Path, default=None, help="金条大盘余额原始 Excel（需与白条源成对传入）")
    parser.add_argument("--skip-generate", action="store_true", help="跳过综合看板生成,直接用 01_latest 最新 HTML 组装站点")
    parser.add_argument("--no-push", action="store_true", help="只在本地更新 gh-pages worktree commit,不推送")
    parser.add_argument("--remote", default="github", help="Pages 远端名,默认 github")
    parser.add_argument("--branch", default="gh-pages", help="Pages 分支名,默认 gh-pages")
    parser.add_argument("--message", default=None, help="gh-pages commit message")
    parser.add_argument("--allow-dirty", action="store_true", help="允许 main 工作树有未提交改动(不推荐)")
    parser.add_argument("--protected", action="store_true", help="发布加密门禁版: gzip(html)+AES-GCM,不发布明文archive")
    parser.add_argument("--password-env", default="ABS_DASHBOARD_PASSWORD", help="protected模式读取密码的环境变量名")
    parser.add_argument("--pbkdf2-iterations", type=int, default=310_000, help="PBKDF2-SHA256迭代次数,默认310000")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if bool(args.baitiao_xlsx) != bool(args.jintiao_xlsx):
        raise ValueError("--baitiao-xlsx 与 --jintiao-xlsx 必须成对传入")
    if args.skip_generate and args.baitiao_xlsx:
        raise ValueError("--skip-generate 不能与消金源 Excel 参数同时使用")
    if not args.allow_dirty:
        ensure_clean_main()

    latest_dashboard = None
    if args.skip_generate:
        print("[1/4] 跳过生成综合看板,使用现有 01_latest 最新 HTML")
    else:
        ledger = args.ledger or find_latest_ledger()
        latest_dashboard = generate_dashboard(ledger, args.baitiao_xlsx, args.jintiao_xlsx)

    password = os.environ.get(args.password_env) if args.protected else None
    site_dir = build_site(
        latest_dashboard,
        protected=args.protected,
        password=password,
        iterations=args.pbkdf2_iterations,
    )
    date_tag = dashboard_date(latest_by_mtime(find_dashboard_files()))
    mode = "protected" if args.protected else "site"
    message = args.message or f"deploy: update ABS dashboard {mode} {date_tag}"
    changed = publish_to_pages(site_dir, args.remote, args.branch, message, args.no_push)

    print("\n[完成] GitHub Pages 更新流程结束")
    print(f"站点包: {site_dir}")
    print("海外/备用入口(GitHub Pages): https://codebluce.github.io/ABS-Toolbox/")
    if CF_PAGES_URL:
        print(f"国内主入口(Cloudflare Pages,免代理): {CF_PAGES_URL}")
        if changed:
            print("  ↑ gh-pages 已更新,CF Pages 将在 1~2 分钟内自动同步该镜像")
        else:
            print("  ↑ 本次无 gh-pages 变更,CF 镜像保持不变")
    else:
        print("国内主入口(Cloudflare Pages): 未配置 ABS_CF_PAGES_URL,详见 docs/cloudflare_pages_部署.md")
    if args.protected:
        print("归档页: protected 模式已下线明文 archive")
    else:
        print("归档页: https://codebluce.github.io/ABS-Toolbox/archive/index.html")
    print(f"是否产生 gh-pages 更新: {'是' if changed else '否'}")


if __name__ == "__main__":
    main()
