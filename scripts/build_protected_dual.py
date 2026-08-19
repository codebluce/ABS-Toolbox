#!/usr/bin/env python3
"""构建「单密码 + 双端分发」的加密站点包。

与 scripts/deploy_github_pages.py 的 --protected 模式对齐（同样的
PBKDF2-SHA256 + AES-256-GCM + gzip、同样的泄露自检思路），区别只有一点：
密文有两份——桌面看板和手机看板，共用同一份 salt 与派生密钥，各自独立 IV。

解锁后的行为：
  1. 只解密当前终端需要的那一份（手机端不会去解 5.6MB 的桌面密文）；
  2. 右下角提供手动切换，切换时密钥已在内存中，无需二次输入密码；
  3. ?view=mobile / ?view=desktop 可强制指定，选择记在 localStorage。

用法：
    export ABS_DASHBOARD_PASSWORD='...'
    python scripts/build_protected_dual.py \
        --desktop deliverables/dashboards/01_latest/ABS综合看板_20260816.html \
        --mobile  deliverables/dashboards/01_latest/mobile.html

产物写入 deliverables/dashboard_site/，随后照常用
    python scripts/deploy_github_pages.py --skip-generate ...
的 publish_to_pages 步骤推送，或直接把该目录同步到 gh-pages。
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
import sys
from datetime import datetime
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

REPO_ROOT = Path(__file__).resolve().parents[1]
LATEST_DIR = REPO_ROOT / "deliverables" / "dashboards" / "01_latest"
SITE_STAGING_DIR = REPO_ROOT / "deliverables" / "dashboard_site"
DASHBOARD_PREFIX = "ABS综合看板_"
DASHBOARD_SUFFIX = ".html"


def dashboard_date(path: Path) -> str:
    name = path.name
    if name.startswith(DASHBOARD_PREFIX) and name.endswith(DASHBOARD_SUFFIX):
        return name[len(DASHBOARD_PREFIX):-len(DASHBOARD_SUFFIX)]
    return path.stem


def find_latest_desktop() -> Path:
    files = sorted(LATEST_DIR.glob(f"{DASHBOARD_PREFIX}*{DASHBOARD_SUFFIX}"))
    if not files:
        raise FileNotFoundError(f"未找到综合看板 HTML: {LATEST_DIR}")
    files.sort(key=dashboard_date, reverse=True)
    return files[0]


def encrypt_pair(desktop: Path, mobile: Path, password: str, iterations: int) -> dict:
    """两份密文共用 salt 与密钥，各自独立 IV（IV 绝不复用）。"""
    if not password:
        raise ValueError("protected 模式需要非空密码")

    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
    aead = AESGCM(key)

    def one(path: Path) -> dict:
        raw = path.read_bytes()
        packed = gzip.compress(raw, compresslevel=6, mtime=0)
        iv = secrets.token_bytes(12)
        cipher = aead.encrypt(iv, packed, None)
        return {
            "iv": base64.b64encode(iv).decode("ascii"),
            "ciphertext": base64.b64encode(cipher).decode("ascii"),
            "plainBytes": len(raw),
            "gzipBytes": len(packed),
            "cipherBytes": len(cipher),
            "source": path.name,
        }

    return {
        "algorithm": "PBKDF2-SHA256 + AES-256-GCM + gzip",
        "iterations": iterations,
        "salt": base64.b64encode(salt).decode("ascii"),
        "desktop": one(desktop),
        "mobile": one(mobile),
    }


def shell_html(desktop: Path, payload: dict) -> str:
    latest_date = dashboard_date(desktop)
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    mb = lambda n: f"{n / 1024 / 1024:.2f} MB"
    size_line = (
        f"桌面 {mb(payload['desktop']['cipherBytes'])} · "
        f"手机 {mb(payload['mobile']['cipherBytes'])}"
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="robots" content="noindex,nofollow">
  <title>ABS 综合看板 · 访问验证</title>
  <style>
    :root{{color-scheme:light;--ink:#111827;--muted:#667085;--line:#e5e7eb;--bg:#f6f7f9;--brand:#172033;--danger:#b42318;--ok:#067647;}}
    *{{box-sizing:border-box}}
    body{{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at 20% 20%,#eef4ff,transparent 30%),var(--bg);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;color:var(--ink)}}
    .card{{width:min(560px,calc(100vw - 32px));background:rgba(255,255,255,.92);border:1px solid rgba(229,231,235,.9);border-radius:24px;padding:30px;box-shadow:0 24px 80px rgba(15,23,42,.12);backdrop-filter:blur(14px)}}
    .eyebrow{{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:700}}
    h1{{margin:10px 0 8px;font-size:30px;line-height:1.12}}
    p{{margin:0;color:var(--muted);line-height:1.7;font-size:14px}}
    .meta{{margin:18px 0;padding:14px;border:1px solid var(--line);border-radius:14px;background:#fbfcfe;font-size:13px;color:#475467;display:grid;gap:6px}}
    label{{display:block;margin:22px 0 8px;font-weight:700;font-size:14px}}
    .row{{display:flex;gap:10px}}
    input{{flex:1;border:1px solid #cfd4dc;border-radius:12px;padding:13px 14px;font-size:16px;outline:none}}
    input:focus{{border-color:#344054;box-shadow:0 0 0 4px rgba(52,64,84,.08)}}
    button{{border:0;border-radius:12px;background:var(--brand);color:white;font-weight:800;padding:0 18px;font-size:15px;cursor:pointer}}
    button:disabled{{opacity:.6;cursor:not-allowed}}
    .msg{{min-height:22px;margin-top:12px;font-size:14px}}
    .err{{color:var(--danger)}} .ok{{color:var(--ok)}}
    .hint{{margin-top:18px;font-size:12px;color:#98a2b3;line-height:1.6}}
    #viewer{{display:none;position:fixed;inset:0;border:0;width:100vw;height:100vh;background:white}}
    #flip{{display:none;position:fixed;z-index:20;right:14px;bottom:14px;padding:8px 14px;border:1px solid #d8dee8;border-radius:18px;background:rgba(255,255,255,.94);color:#1a3a5c;font:600 12px/1 'PingFang SC',Helvetica,Arial,sans-serif;box-shadow:0 4px 14px rgba(15,23,42,.12)}}
  </style>
</head>
<body>
  <main class="card" id="gate">
    <div class="eyebrow">ABS Dashboard Protected</div>
    <h1>ABS 综合看板</h1>
    <p>请输入访问密码。看板数据已在发布前加密，密码只在本机浏览器中用于解密，不会发送到服务器。</p>
    <div class="meta">
      <div><strong>版本</strong>：{latest_date}</div>
      <div><strong>终端</strong>：解锁后自动识别电脑 / 手机，按需解密</div>
      <div><strong>密文</strong>：{size_line}</div>
      <div><strong>加密</strong>：PBKDF2-SHA256 / AES-GCM / gzip</div>
    </div>
    <label for="password">访问密码</label>
    <div class="row"><input id="password" type="password" autocomplete="current-password" placeholder="输入密码后按 Enter"><button id="unlock">解锁</button></div>
    <div class="msg" id="msg"></div>
    <div class="hint">提示：首次解锁会在浏览器本地完成密钥派生、解密和解压。手机端只解密手机版密文，不会下载解压桌面看板。</div>
  </main>
  <iframe id="viewer" sandbox="allow-scripts allow-same-origin allow-downloads allow-popups allow-forms"></iframe>
  <button id="flip" type="button"></button>
  <script>
    const PAYLOAD = {payload_json};
    const KEY_VIEW = 'abs_dash_view';
    const $ = (id) => document.getElementById(id);
    const msg = (text, cls='') => {{ $('msg').className = 'msg ' + cls; $('msg').textContent = text; }};
    const b64 = (s) => Uint8Array.from(atob(s), c => c.charCodeAt(0));

    function detect() {{
      const ua = navigator.userAgent || '';
      if (/iPad|Android(?!.*Mobile)|Tablet/i.test(ua)) return 'desktop';
      if (/iPhone|iPod|Android.*Mobile|Windows Phone|HarmonyOS/i.test(ua)) return 'mobile';
      const coarse = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;
      const narrow = Math.min(window.innerWidth, window.innerHeight) <= 520;
      if (coarse && narrow) return 'mobile';
      return window.innerWidth <= 768 ? 'mobile' : 'desktop';
    }}
    function resolveView() {{
      const q = (location.search.match(/[?&]view=(mobile|desktop)/i) || [])[1];
      if (q) {{ try {{ localStorage.setItem(KEY_VIEW, q.toLowerCase()); }} catch (e) {{}} return q.toLowerCase(); }}
      let saved = null;
      try {{ saved = localStorage.getItem(KEY_VIEW); }} catch (e) {{}}
      if (saved === 'mobile' || saved === 'desktop') return saved;
      return detect();
    }}

    let KEY = null, MODE = null;

    async function deriveKey(password) {{
      const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveKey']);
      return crypto.subtle.deriveKey(
        {{name:'PBKDF2', salt:b64(PAYLOAD.salt), iterations:PAYLOAD.iterations, hash:'SHA-256'}},
        base, {{name:'AES-GCM', length:256}}, false, ['decrypt']
      );
    }}
    async function ungzip(bytes) {{
      if (!('DecompressionStream' in window)) {{
        const e = new Error('unsupported'); e.unsupported = true; throw e;
      }}
      const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
      const buf = await new Response(stream).arrayBuffer();
      return new TextDecoder('utf-8').decode(buf);
    }}
    async function open(view) {{
      const part = PAYLOAD[view];
      const plain = await crypto.subtle.decrypt({{name:'AES-GCM', iv:b64(part.iv)}}, KEY, b64(part.ciphertext));
      const html = await ungzip(new Uint8Array(plain));
      const viewer = $('viewer');
      viewer.srcdoc = html;
      viewer.style.display = 'block';
      $('gate').style.display = 'none';
      MODE = view;
      const auto = detect();
      // 判断被覆盖过、或窗口很宽时给出手动切换入口
      if (view !== auto || window.innerWidth > 900) {{
        $('flip').style.display = 'block';
        $('flip').textContent = view === 'mobile' ? '切换到电脑版' : '切换到手机版';
      }} else {{
        $('flip').style.display = 'none';
      }}
    }}
    async function unlock() {{
      const password = $('password').value;
      if (!password) {{ msg('请输入密码。', 'err'); return; }}
      $('unlock').disabled = true;
      const t0 = performance.now();
      try {{
        msg('正在解密看板...', '');
        KEY = await deriveKey(password);
        await open(resolveView());
        msg('解锁成功，正在打开看板... ' + Math.round(performance.now() - t0) + 'ms', 'ok');
      }} catch (err) {{
        console.error(err);
        KEY = null;
        if (err && err.unsupported) {{
          msg('当前浏览器不支持解压(DecompressionStream)，请使用 Chrome 80+/Edge 80+/Safari 16.4+ 或更新浏览器。', 'err');
        }} else {{
          msg('密码错误，解密失败。', 'err');
        }}
      }} finally {{
        $('unlock').disabled = false;
      }}
    }}
    $('unlock').addEventListener('click', unlock);
    $('password').addEventListener('keydown', e => {{ if (e.key === 'Enter') unlock(); }});
    $('flip').addEventListener('click', async () => {{
      const next = MODE === 'mobile' ? 'desktop' : 'mobile';
      try {{ localStorage.setItem(KEY_VIEW, next); }} catch (e) {{}}
      // 密钥已在内存，切换无需重新输入密码
      $('flip').disabled = true;
      try {{ await open(next); }} finally {{ $('flip').disabled = false; }}
    }});
    $('password').focus();
  </script>
</body>
</html>
"""


def audit_site(site_dir: Path, sources: list[Path]) -> None:
    """泄露自检：站点包内不得出现源 Excel / 脚本 / 明文看板特征。"""
    problems: list[str] = []
    banned = {".xlsx", ".xls", ".csv", ".env", ".py"}
    probes = [p.read_bytes()[:2048] for p in sources]
    for p in sorted(site_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() in banned:
            problems.append(f"敏感文件泄露: {p.relative_to(site_dir)}")
            continue
        if p.name in {"manifest.json", "README.md", ".nojekyll"}:
            continue
        blob = p.read_bytes()
        for probe in probes:
            if probe and probe in blob:
                problems.append(f"疑似明文看板泄露: {p.relative_to(site_dir)}")
                break
    if problems:
        raise RuntimeError("泄露自检失败:\n  " + "\n  ".join(problems))
    print("[site] 泄露自检通过: 无源 Excel/明文看板特征")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="构建单密码双端加密站点包")
    ap.add_argument("--desktop", type=Path, default=None, help="桌面综合看板 HTML，默认取 01_latest 中业务日期最新的一份")
    ap.add_argument("--mobile", type=Path, default=None, help="手机版 HTML，默认 01_latest/mobile.html")
    ap.add_argument("--password-env", default="ABS_DASHBOARD_PASSWORD", help="读取密码的环境变量名")
    ap.add_argument("--pbkdf2-iterations", type=int, default=310_000, help="PBKDF2-SHA256 迭代次数")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    desktop = (args.desktop or find_latest_desktop()).resolve()
    mobile = (args.mobile or (LATEST_DIR / "mobile.html")).resolve()
    for p in (desktop, mobile):
        if not p.exists():
            raise FileNotFoundError(f"未找到输入文件: {p}")

    password = os.environ.get(args.password_env)
    if not password:
        raise RuntimeError(f"未设置密码环境变量 {args.password_env}")

    print(f"[1/3] 输入: 桌面={desktop.name} 手机={mobile.name}")
    payload = encrypt_pair(desktop, mobile, password, args.pbkdf2_iterations)

    print("[2/3] 组装站点包...")
    if SITE_STAGING_DIR.exists():
        shutil.rmtree(SITE_STAGING_DIR)
    SITE_STAGING_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_STAGING_DIR / "index.html").write_text(shell_html(desktop, payload), encoding="utf-8")
    (SITE_STAGING_DIR / ".nojekyll").write_text("", encoding="utf-8")

    manifest = {
        "generatedAt": datetime.fromtimestamp(desktop.stat().st_mtime).isoformat(timespec="seconds"),
        "latest": desktop.name,
        "latestDate": dashboard_date(desktop),
        "protected": True,
        "dual": True,
        "views": {
            "desktop": {k: payload["desktop"][k] for k in ("source", "plainBytes", "gzipBytes", "cipherBytes")},
            "mobile": {k: payload["mobile"][k] for k in ("source", "plainBytes", "gzipBytes", "cipherBytes")},
        },
        "encryption": {"algorithm": payload["algorithm"], "iterations": payload["iterations"]},
        "source": "scripts/build_protected_dual.py",
    }
    (SITE_STAGING_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (SITE_STAGING_DIR / "README.md").write_text(
        f"""# ABS综合看板静态站点包（单密码 · 双端）

由 `scripts/build_protected_dual.py` 生成。

- 入口：`index.html`（密码门禁，解锁后按终端自动分发）
- 桌面来源：`{desktop.name}`
- 手机来源：`{mobile.name}`
- 加密：PBKDF2-SHA256 / AES-256-GCM / gzip，两份密文共用 salt 与派生密钥、各自独立 IV

安全说明：客户端加密而非服务端鉴权——密文、salt、IV 均随页面下发，访问者可离线尝试口令，
无身份校验、撤销与审计能力。请使用高熵口令并定期轮换；需身份级管控请迁移至 Cloudflare Access。
""",
        encoding="utf-8",
    )

    print("[3/3] 自检...")
    audit_site(SITE_STAGING_DIR, [desktop, mobile])

    d, m = payload["desktop"], payload["mobile"]
    print(f"[site] 桌面 raw={d['plainBytes']} gzip={d['gzipBytes']} cipher={d['cipherBytes']}")
    print(f"[site] 手机 raw={m['plainBytes']} gzip={m['gzipBytes']} cipher={m['cipherBytes']}")
    print(f"\n[完成] 站点包: {SITE_STAGING_DIR}")
    print("接下来推送 gh-pages（复用现有发布链的同步步骤）：")
    print("  python scripts/deploy_github_pages.py --skip-generate --protected --build-only  # 先预览差异")
    print("或直接把 deliverables/dashboard_site/ 同步到 gh-pages 分支。")


if __name__ == "__main__":
    main()
