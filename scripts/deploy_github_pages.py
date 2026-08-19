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
# 手机版生成器与本脚本同目录,导入前先把 scripts/ 挂进 sys.path
sys.path.insert(0, str(SCRIPTS_DIR))

from gen_mobile_dashboard import build_mobile_html  # noqa: E402  (需在 sys.path 配置之后导入)
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


def latest_by_name_date(paths: Iterable[Path], fallback_mtime: bool = True) -> Path:
    """优先按受控文件名中的业务日期(YYYYMMDD)选择,避免 mtime 被复制/解压/触碰干扰。

    支持「2026年...-0807-定稿」(年份+4位月日拼合)与「...-20260807-...」(完整8位)两种命名。
    无可解析日期时回退 mtime;日期与 mtime 结论冲突时打印提示并以文件名为准。
    """
    import re

    def name_date(p: Path) -> str | None:
        # 优先完整 8 位日期;再尝试「YYYY年...-MMDD-」拼合
        m = re.search(r"(20\d{6})", p.name)
        if m:
            return m.group(1)
        m2 = re.search(r"^(20\d{2})\S*?-(\d{4})(?!\d)", p.name)
        if m2:
            return f"{m2.group(1)}{m2.group(2)}"
        return None

    dated: list[tuple[str, Path]] = []
    undated: list[Path] = []
    for p in paths:
        if not p.exists():
            continue
        d = name_date(p)
        if d:
            dated.append((d, p))
        else:
            undated.append(p)
    if dated:
        dated.sort(key=lambda x: x[0], reverse=True)
        best_date, best = dated[0]
        mtime_pick = latest_by_mtime([p for _, p in dated] or undated)
        if mtime_pick != best:
            print(f"[select] 文件名业务日期({best_date})与 mtime({mtime_pick.name})不一致,以文件名为准: {best.name}")
        return best
    if undated:
        if not fallback_mtime:
            # 严格语义(v26-B1):禁用回退时,无可解析业务日期必须明确失败
            raise FileNotFoundError(
                "所有候选文件均无可解析的业务日期,且 fallback_mtime=False 禁用了 mtime 回退。"
                f"候选清单: {[str(p) for p in undated]}"
            )
        return latest_by_mtime(undated)
    raise FileNotFoundError("没有找到可用文件")


def find_latest_ledger() -> Path:
    candidates = sorted(FINAL_LEDGER_DIR.glob("2026年ABS发行台账-*-定稿.xlsx"))
    if not candidates:
        raise FileNotFoundError(f"未找到定稿台账: {FINAL_LEDGER_DIR}")
    # 优先按文件名业务日期(如 0807)选择,人工复制/触碰旧文件不会改变业务日期
    try:
        return latest_by_name_date(candidates)
    except FileNotFoundError:
        raise FileNotFoundError(f"未找到定稿台账: {FINAL_LEDGER_DIR}")


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


def ledger_date_tag(ledger_path: Path) -> str:
    """从受控台账文件名提取业务日期标签(YYYYMMDD)。

    例: 2026年ABS发行台账-0807-定稿.xlsx -> 20260807;
        2026年ABS发行台账-20260807-定稿.xlsx -> 20260807。
    无法解析时回退当天日期,保证输出文件名始终可控。
    """
    import re

    m = re.search(r"^(20\d{2})年ABS发行台账-(\d{4})(?!\d)", ledger_path.name)
    if m:
        return f"{m.group(1)}{m.group(2)}"
    m2 = re.search(r"(20\d{6})", ledger_path.name)
    if m2:
        return m2.group(1)
    print(f"[select] 台账文件名无法解析业务日期,回退当天: {ledger_path.name}")
    return datetime.now().strftime("%Y%m%d")


def generate_dashboard(
    ledger_path: Path,
    baitiao_path: Path | None = None,
    jintiao_path: Path | None = None,
    peer_issuance_path: Path | None = None,
    peer_issuance_baseline_path: Path | None = None,
) -> Path:
    print(f"\n[1/4] 生成最新综合看板: {ledger_path}")
    # 显式指定输出路径,生成后直接使用该产物,不再按 mtime 重扫目录(避免误选旧文件)
    ledger_date = ledger_date_tag(ledger_path)
    out_path = LATEST_DIR / f"{DASHBOARD_PREFIX}{ledger_date}{DASHBOARD_SUFFIX}"
    command = [sys.executable, str(SCRIPTS_DIR / "gen_integrated_dashboard.py"), str(ledger_path), str(out_path)]
    if baitiao_path and jintiao_path:
        command.extend(["--baitiao-xlsx", str(baitiao_path), "--jintiao-xlsx", str(jintiao_path)])
    if peer_issuance_path:
        command.extend(["--peer-issuance-xlsx", str(peer_issuance_path)])
        if peer_issuance_baseline_path:
            command.extend(["--peer-issuance-baseline-xlsx", str(peer_issuance_baseline_path)])
    run(command)
    if not out_path.exists():
        raise RuntimeError(f"生成器已退出但未找到产物: {out_path}")
    # 产物结构验证:QC 失败时生成器非零退出,这里再校验一次关键结构双保险
    verify_dashboard_artifact(out_path)
    return out_path


def verify_dashboard_artifact(dashboard_path: Path) -> None:
    """部署侧产物验证:关键结构缺失即中止发布(P1-01 双保险)。"""
    content = dashboard_path.read_text(encoding="utf-8")
    problems = []
    if '<div class="panel"' not in content:
        problems.append("缺少 panel 容器")
    if "function selectModule" not in content:
        problems.append("缺少 selectModule")
    if "function selectSub" not in content:
        problems.append("缺少 selectSub")
    if problems:
        raise RuntimeError(f"综合看板产物结构异常: {'; '.join(problems)}")


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


def protected_shell_html(latest_dashboard: Path, payload: dict, mobile_payload: dict) -> str:
    latest_name = latest_dashboard.name
    latest_date = dashboard_date(latest_dashboard)
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    mobile_json = json.dumps(mobile_payload, ensure_ascii=False, separators=(",", ":"))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="robots" content="noindex,nofollow">
  <title>ABS 综合看板 · 访问验证</title>
  <style>
    :root{{color-scheme:light;--ink:#111827;--muted:#667085;--line:#e5e7eb;--bg:#f6f7f9;--card:#fff;--brand:#172033;--danger:#b42318;--ok:#067647;}}
    *{{box-sizing:border-box}} body{{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(circle at 20% 20%,#eef4ff,transparent 30%),var(--bg);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;color:var(--ink)}}
    .card{{width:min(560px,calc(100vw - 32px));background:rgba(255,255,255,.92);border:1px solid rgba(229,231,235,.9);border-radius:24px;padding:30px;box-shadow:0 24px 80px rgba(15,23,42,.12);backdrop-filter:blur(14px)}}
    .eyebrow{{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:700}} h1{{margin:10px 0 8px;font-size:30px;line-height:1.12}} p{{margin:0;color:var(--muted);line-height:1.7;font-size:14px}} .meta{{margin:18px 0;padding:14px;border:1px solid var(--line);border-radius:14px;background:#fbfcfe;font-size:13px;color:#475467;display:grid;gap:6px}}
    label{{display:block;margin:22px 0 8px;font-weight:700;font-size:14px}} .row{{display:flex;gap:10px}} input{{flex:1;border:1px solid #cfd4dc;border-radius:12px;padding:13px 14px;font-size:16px;outline:none}} input:focus{{border-color:#344054;box-shadow:0 0 0 4px rgba(52,64,84,.08)}} button{{border:0;border-radius:12px;background:var(--brand);color:white;font-weight:800;padding:0 18px;font-size:15px;cursor:pointer}} button:disabled{{opacity:.6;cursor:not-allowed}} .msg{{min-height:22px;margin-top:12px;font-size:14px}} .err{{color:var(--danger)}} .ok{{color:var(--ok)}} .hint{{margin-top:18px;font-size:12px;color:#98a2b3}}
    #viewer{{display:none;position:fixed;inset:0;border:0;width:100vw;height:100vh;background:white}}
    #flip{{display:none;position:fixed;z-index:9;right:14px;bottom:14px;padding:8px 14px;border:1px solid #d8dee8;border-radius:18px;background:rgba(255,255,255,.94);color:#1a3a5c;font:600 12px/1 'PingFang SC',Helvetica,Arial,sans-serif;box-shadow:0 4px 14px rgba(15,23,42,.12);cursor:pointer}}
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
      <div><strong>终端</strong>：<span id="term">识别中…</span></div>
    </div>
    <label for="password">访问密码</label>
    <div class="row"><input id="password" type="password" autocomplete="current-password" placeholder="输入密码后按 Enter"><button id="unlock">解锁</button></div>
    <div class="msg" id="msg"></div>
    <div class="hint">提示：首次解锁会在浏览器本地完成密钥派生、解密和解压；请使用强密码并避免在公共设备保存。</div>
  </main>
  <iframe id="viewer" sandbox="allow-scripts allow-same-origin allow-downloads allow-popups allow-forms"></iframe>
  <button id="flip" type="button"></button>
  <script>
    const PAYLOADS = {{ desktop: {payload_json}, mobile: {mobile_json} }};
    const VIEW_KEY = 'abs_dash_view';
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
      if (q) {{ try {{ localStorage.setItem(VIEW_KEY, q.toLowerCase()); }} catch (e) {{}} return q.toLowerCase(); }}
      let saved = null;
      try {{ saved = localStorage.getItem(VIEW_KEY); }} catch (e) {{}}
      return (saved === 'mobile' || saved === 'desktop') ? saved : detect();
    }}

    let VIEW = resolveView();
    const AUTO = detect();
    let KEYS = {{}};   // 每份密文的 salt 不同,派生出的 key 分开缓存
    let PASSWORD = null;
    $('term').textContent = VIEW === 'mobile' ? '手机版' : '电脑版';

    async function deriveKey(password, p) {{
      const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveKey']);
      return crypto.subtle.deriveKey({{name:'PBKDF2', salt:b64(p.salt), iterations:p.iterations, hash:'SHA-256'}}, base, {{name:'AES-GCM', length:256}}, false, ['decrypt']);
    }}
    async function ungzip(bytes) {{
      if (!('DecompressionStream' in window)) {{
        const e = new Error('unsupported');
        e.unsupported = true;
        throw e;
      }}
      const ds = new DecompressionStream('gzip');
      const stream = new Blob([bytes]).stream().pipeThrough(ds);
      const buf = await new Response(stream).arrayBuffer();
      return new TextDecoder('utf-8').decode(buf);
    }}
    async function decryptView(view, password) {{
      const p = PAYLOADS[view];
      if (!KEYS[view]) KEYS[view] = await deriveKey(password, p);
      const plain = await crypto.subtle.decrypt({{name:'AES-GCM', iv:b64(p.iv)}}, KEYS[view], b64(p.ciphertext));
      return ungzip(new Uint8Array(plain));
    }}
    function showFlip() {{
      // 判断可能不合适时才给手动开关:被覆盖过,或窗口很宽却在手机版
      if (VIEW !== AUTO || window.innerWidth > 900) {{
        flip.textContent = VIEW === 'mobile' ? '切换到电脑版' : '切换到手机版';
        flip.style.display = 'block';
      }} else {{
        flip.style.display = 'none';
      }}
    }}
    async function render(view) {{
      const html = await decryptView(view, PASSWORD);
      $('viewer').srcdoc = html;
      $('viewer').style.display = 'block';
      $('gate').style.display = 'none';
      VIEW = view;
      showFlip();
    }}
    async function unlock() {{
      const password = $('password').value;
      if (!password) {{ msg('请输入密码。', 'err'); return; }}
      $('unlock').disabled = true;
      const t0 = performance.now();
      try {{
        msg('正在解密看板...', '');
        PASSWORD = password;
        await render(VIEW);
        msg('解锁成功,正在打开看板... ' + Math.round(performance.now() - t0) + 'ms', 'ok');
      }} catch (err) {{
        console.error(err);
        PASSWORD = null; KEYS = {{}};
        if (err && err.unsupported) {{
          msg('当前浏览器不支持解压(DecompressionStream),请使用 Chrome 80+/Edge 80+/Safari 16.4+ 或更新浏览器。', 'err');
        }} else {{
          msg('密码错误,解密失败。', 'err');
        }}
      }} finally {{
        $('unlock').disabled = false;
      }}
    }}
    const flip = $('flip');
    flip.addEventListener('click', async () => {{
      const next = VIEW === 'mobile' ? 'desktop' : 'mobile';
      try {{ localStorage.setItem(VIEW_KEY, next); }} catch (e) {{}}
      if (!PASSWORD) {{ location.replace(location.pathname + '?view=' + next); return; }}
      flip.disabled = true;
      try {{ await render(next); }} finally {{ flip.disabled = false; }}
    }});
    $('unlock').addEventListener('click', unlock);
    $('password').addEventListener('keydown', e => {{ if (e.key === 'Enter') unlock(); }});
    $('password').focus();
  </script>
</body>
</html>
"""


def write_archive_index(archive_dir: Path, dashboards: list[Path]) -> None:
    import html as _html
    from urllib.parse import quote as _urlquote

    rows = []
    for p in sorted(dashboards, key=dashboard_date, reverse=True):
        size_mb = p.stat().st_size / 1024 / 1024
        date = dashboard_date(p)
        # 文件名同时做 HTML 转义(显示)与 URL 编码(href),防注入(P3-3)
        safe_name = _html.escape(p.name)
        safe_href = _urlquote(p.name)
        rows.append(
            f'<tr><td>{_html.escape(date)}</td><td><a href="{safe_href}">{safe_name}</a></td><td>{size_mb:.2f} MB</td></tr>'
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


def audit_protected_site(
    site_dir: Path, latest_dashboard: Path, mobile_probe: bytes | None = None
) -> None:
    """protected 站点包泄露自检:发现明文特征立即失败,阻断发布。

    检查项:
    1. 站点包不含源 Excel/簿记明细等敏感文件;
    2. 站点包内任何文件都不含明文看板 HTML 的特征串(取源文件头部长片段);
       双端模式下同时校验手机版明文特征串;
    3. manifest 中不得出现明文 HTML 文件本体。
    """
    problems: list[str] = []
    banned_suffixes = {".xlsx", ".xls", ".csv", ".env", ".py"}
    for p in sorted(site_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() in banned_suffixes:
            problems.append(f"敏感文件泄露: {p.relative_to(site_dir)}")
            continue
        # manifest.json / README.md 是受控生成的文本,允许存在;二进制与 HTML 需检查明文特征
        try:
            blob = p.read_bytes()
        except OSError as exc:
            problems.append(f"读取失败: {p.relative_to(site_dir)} ({exc})")
            continue
        # 明文看板特征片段:源 HTML 中必然存在且唯一的 UTF-8 字节串
        probe = "<!DOCTYPE html>".encode("utf-8")
        if p.name not in {"manifest.json", "README.md", ".nojekyll"} and probe in blob:
            # index.html 解锁壳本身也是 HTML,需进一步用源文件特征串区分
            src_probe = latest_dashboard.read_bytes()[:2048]
            if src_probe and src_probe in blob:
                problems.append(f"疑似明文看板泄露: {p.relative_to(site_dir)}")
            if mobile_probe and mobile_probe in blob:
                problems.append(f"疑似明文手机版泄露: {p.relative_to(site_dir)}")
    if problems:
        raise RuntimeError("protected 站点包泄露自检失败:\n  " + "\n  ".join(problems))
    print("[site] protected 泄露自检通过: 无源 Excel/明文看板特征")


def build_site(
    latest_dashboard: Path | None = None,
    *,
    protected: bool = False,
    password: str | None = None,
    iterations: int = 310_000,
) -> Path:
    print("\n[2/4] 组装静态站点包...")
    dashboards = find_dashboard_files()
    # 按文件名业务日期选择(与 find_latest_ledger 同一套逻辑)，不用 mtime——
    # git checkout/pull 会把签出文件的 mtime 统一盖成拉取时刻，与文件名里的
    # 真实业务日期无关；--skip-generate 场景下这会导致误选到"刚拉下来但业务
    # 日期更早"的文件而不是真正最新的看板(实测复现:0814 因刚被 pull 签出、
    # mtime 是今天，反而排在 0816 之前)。
    latest_dashboard = latest_dashboard or latest_by_name_date(dashboards)
    # 统一解析为绝对路径(v26-B3):调用方传相对路径时 relative_to(REPO_ROOT) 会抛 ValueError
    latest_dashboard = latest_dashboard.resolve()
    if not latest_dashboard.is_absolute():  # resolve 后必为绝对,防御性断言
        raise ValueError(f"看板路径解析失败: {latest_dashboard}")

    if SITE_STAGING_DIR.exists():
        shutil.rmtree(SITE_STAGING_DIR)
    SITE_STAGING_DIR.mkdir(parents=True, exist_ok=True)

    protected_payload = None
    mobile_payload = None
    mobile_probe = None
    if protected:
        if not password:
            raise RuntimeError("--protected 需要通过环境变量提供密码")
        print("[site] protected 模式: gzip(html) + AES-GCM, 不发布明文 archive")
        # 手机版明文只落在站点包之外的临时目录,用完即删——泄露自检与站点包都不会碰到它
        mobile_tmp = Path(tempfile.mkdtemp(prefix="abs_mobile_"))
        try:
            mobile_path = build_mobile_html(latest_dashboard, mobile_tmp / "mobile.html")
            protected_payload = encrypt_dashboard_html(latest_dashboard, password, iterations)
            mobile_payload = encrypt_dashboard_html(mobile_path, password, iterations)
            (SITE_STAGING_DIR / "index.html").write_text(
                protected_shell_html(latest_dashboard, protected_payload, mobile_payload),
                encoding="utf-8",
            )
            mobile_probe = mobile_path.read_bytes()[:2048]
        finally:
            shutil.rmtree(mobile_tmp, ignore_errors=True)
    else:
        archive_dir = SITE_STAGING_DIR / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(latest_dashboard, SITE_STAGING_DIR / "index.html")
        for p in dashboards:
            shutil.copy2(p, archive_dir / p.name)
        write_archive_index(archive_dir, dashboards)

    (SITE_STAGING_DIR / ".nojekyll").write_text("", encoding="utf-8")

    if protected:
        audit_protected_site(SITE_STAGING_DIR, latest_dashboard, mobile_probe)

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
        if mobile_payload:
            manifest["encryption"]["mobileCipherBytes"] = mobile_payload["cipherBytes"]
    (SITE_STAGING_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    archive_line = "- 历史归档：已下线（protected 模式不发布明文历史版本）" if protected else "- 历史归档：`archive/index.html`"
    security_line = (
        "安全说明：站点包为**客户端加密**门禁版本，`index.html` 只包含密文和本地解密逻辑，不包含明文看板。\n"
        "注意：这是客户端加密而非服务端鉴权——密文、salt、IV 均随页面下发，访问者可离线尝试口令，无身份校验、撤销与审计能力。请使用高熵口令并定期轮换；若需身份级管控请迁移至 Cloudflare Access 等方案。"
        if protected
        else "安全说明：站点包只包含静态 HTML，不包含源 Excel、簿记明细、脚本、`.env` 等文件。"
    )
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
    # .venv/ 是常驻本地虚拟环境(不入库),不构成部署夹带风险,放行
    lines = [ln for ln in status.split("\n") if ln.strip() and not ln.strip().endswith(".venv/")]
    if lines:
        raise RuntimeError(
            "main 工作树不干净。为避免部署夹带未提交改动,请先处理以下文件:\n" + "\n".join(lines)
        )


def remove_worktree_contents(worktree: Path) -> None:
    for child in worktree.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def publish_to_pages(site_dir: Path, remote: str, branch: str, message: str, no_push: bool, build_only: bool = False) -> bool:
    """同步站点包到发布分支。

    build_only=True: 真正的无副作用预览——只组装并对比,不创建提交、不更新任何本地引用、不推送(v26-A2)。
    no_push=True:    在临时 worktree 提交但不推送;不移动本地分支引用(引用同步仅在真实 push 成功后执行)。
    """
    print("\n[3/4] 同步到 gh-pages worktree...")
    tmp_parent = Path(tempfile.mkdtemp(prefix="abs_pages_"))
    worktree = tmp_parent / "worktree"
    changed = False
    try:
        # 始终 fetch 并从 remote/gh-pages 创建一次性 detached worktree,
        # 避免本地陈旧分支导致非快进失败或基于过期历史发布(P1-02)。
        run(["git", "fetch", remote, branch])
        remote_ref = f"refs/remotes/{remote}/{branch}"
        has_remote = subprocess.run(
            ["git", "show-ref", "--verify", remote_ref], cwd=REPO_ROOT
        ).returncode == 0
        if not has_remote:
            raise RuntimeError(
                f"远端 {remote} 不存在分支 {branch},请先确认发布仓库与分支配置"
            )
        # 本地分支若与远端分叉,明确中止,不自动覆盖
        has_local = subprocess.run(
            ["git", "show-ref", "--verify", f"refs/heads/{branch}"], cwd=REPO_ROOT
        ).returncode == 0
        if has_local:
            local_sha = capture(["git", "rev-parse", f"refs/heads/{branch}"]).strip()
            remote_sha = capture(["git", "rev-parse", remote_ref]).strip()
            base_sha = capture(["git", "merge-base", f"refs/heads/{branch}", remote_ref]).strip()
            if local_sha != remote_sha and base_sha not in (local_sha, remote_sha):
                raise RuntimeError(
                    f"本地 {branch} 与远端已分叉(local={local_sha[:8]} remote={remote_sha[:8]}),"
                    "请人工确认后处理,发布中止"
                )
        run(["git", "worktree", "add", "--detach", str(worktree), remote_ref])

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
            if build_only:
                print("[pages] build-only 预览:无文件变化,未创建提交/未动引用/未推送")
                return False
            if no_push:
                print("[pages] --no-push 已设置,跳过推送")
                return False
            # 无变化:比较远端跟踪引用与 detached HEAD,一致即成功退出,
            # 不再执行 gh-pages:gh-pages(无本地分支时 src refspec 不存在,v26-A3)
            head_sha = capture(["git", "rev-parse", "HEAD"], cwd=worktree).strip()
            remote_sha_now = capture(["git", "rev-parse", remote_ref]).strip()
            if head_sha == remote_sha_now:
                print("[pages] 远端 gh-pages 与本次产物一致,无需推送")
            else:
                print("[pages] 本地引用落后于远端,执行同步推送")
                run(["git", "push", remote, f"HEAD:refs/heads/{branch}"], cwd=worktree)
            return False
        if build_only:
            print("[pages] build-only 预览:检测到文件变化(如正式发布将提交以下内容),未创建提交/未动引用/未推送")
            print(diff_status)
            return False
        changed = True
        print(diff_status)
        run(["git", "commit", "-m", message], cwd=worktree)
        if no_push:
            print("[pages] --no-push 已设置,未推送远端,本地引用保持不变")
        else:
            print("\n[4/4] 推送到 GitHub Pages...")
            run(
                ["git", "push", remote, f"HEAD:refs/heads/{branch}"],
                cwd=worktree,
            )
            # 仅在真实推送成功后,才把本地分支指针对齐到刚发布的基线(v26-A2:
            # no-push 不移动本地引用)
            committed_sha = capture(["git", "rev-parse", "HEAD"], cwd=worktree).strip()
            run(["git", "update-ref", f"refs/heads/{branch}", committed_sha])
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
    parser.add_argument("--peer-issuance-xlsx", type=Path, default=None, help="当期同业发行动态 Excel")
    parser.add_argument("--peer-issuance-baseline-xlsx", type=Path, default=None, help="同业发行同比基准 Excel（默认使用受控 2025 基准）")
    parser.add_argument("--skip-generate", action="store_true", help="跳过综合看板生成,直接用 01_latest 最新 HTML 组装站点")
    parser.add_argument("--no-push", action="store_true", help="在临时 worktree 创建提交但不推送远端,且不移动本地分支引用")
    parser.add_argument("--build-only", action="store_true", help="纯预览:只组装站点包并对比差异,不创建提交/不更新引用/不推送(与 --no-push 互斥)")
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
    if args.skip_generate and (args.baitiao_xlsx or args.peer_issuance_xlsx or args.peer_issuance_baseline_xlsx):
        raise ValueError("--skip-generate 不能与消金或同业源 Excel 参数同时使用")
    if args.build_only and args.no_push:
        raise ValueError("--build-only 与 --no-push 互斥:纯预览请用 --build-only")
    if not args.allow_dirty:
        ensure_clean_main()

    latest_dashboard = None
    if args.skip_generate:
        print("[1/4] 跳过生成综合看板,使用现有 01_latest 最新 HTML")
    else:
        ledger = args.ledger or find_latest_ledger()
        latest_dashboard = generate_dashboard(
            ledger,
            args.baitiao_xlsx,
            args.jintiao_xlsx,
            args.peer_issuance_xlsx,
            args.peer_issuance_baseline_xlsx,
        )

    password = os.environ.get(args.password_env) if args.protected else None
    site_dir = build_site(
        latest_dashboard,
        protected=args.protected,
        password=password,
        iterations=args.pbkdf2_iterations,
    )
    # 提交消息日期直接取自本次实际发布的产物(v26-B2),不再二次 mtime 扫描,
    # 避免"构建用 A 产物、消息记 B 日期"的错配
    if latest_dashboard is not None:
        date_tag = dashboard_date(latest_dashboard)
    else:
        # 与 build_site() 内部选择逻辑保持一致(同用 latest_by_name_date)，
        # 否则 commit message 里的日期可能和实际打包进站点包的文件对不上。
        date_tag = dashboard_date(latest_by_name_date(find_dashboard_files()))
    mode = "protected" if args.protected else "site"
    message = args.message or f"deploy: update ABS dashboard {mode} {date_tag}"
    changed = publish_to_pages(site_dir, args.remote, args.branch, message, args.no_push, getattr(args, "build_only", False))

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
