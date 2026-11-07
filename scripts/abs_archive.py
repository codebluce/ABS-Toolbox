#!/usr/bin/env python3
"""ABS工具箱 产出归档工具

四个子命令:
  ledger     — 台账晋升: 02_processing/* → 03_final/(保守策略,不自动归档旧定稿)
  final      — 台账定稿归档(人工触发): 03_final/* → 04_archive/
  dashboards — 看板归档: 01_latest/* 旧日期 → 02_history/YYYYMMDD/(最新日期保留)
  index      — 重建 _文件索引目录.md (修复脱节)

用法:
  PYTHONUTF8=1 python abs_archive.py ledger
  PYTHONUTF8=1 python abs_archive.py final
  PYTHONUTF8=1 python abs_archive.py dashboards
  PYTHONUTF8=1 python abs_archive.py index
"""
import os
import re
import sys
import shutil
from datetime import date, datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

VAULT = Path(__file__).resolve().parent.parent
DELIVERABLES = VAULT / "deliverables"
LEDGER = DELIVERABLES / "ledger"
DASHBOARDS = DELIVERABLES / "dashboards"


# ═══════════════════════════════════════════════════════════════
# §1  台账归档
# ═══════════════════════════════════════════════════════════════

def archive_ledger():
    """台账归档(保守策略):
    1. 02_processing/* 移到 03_final/(只晋升,不自动归档旧定稿)
    2. 旧 03_final/* 的归档由人工或独立 archive-final 子命令处理
    设计理由: 自动归档旧定稿风险高(可能误归当前在用定稿),
              保守只做晋升,归档动作交人工决策。
    v2.1.0 注(2026-07-05): 簿记录入产出在 02_processing/,文件名形如
        '2026年ABS发行台账-MMDD-补充簿记vN.xlsx'。晋升前请人工确认:
        - 补充簿记是否已通过 QC(数据质量)
        - 是否已是定稿状态(还是仍需增量合并)
        未定稿的补充簿记不应晋升到 03_final/。
    """
    print("=== 台账归档(仅晋升 02_processing → 03_final) ===")
    processing = LEDGER / "02_processing"
    final = LEDGER / "03_final"

    if not processing.exists():
        print(f"⚠ 跳过: {processing.name}/ 不存在")
        return

    processing_files = list(processing.glob("*.xlsx"))
    if not processing_files:
        print("  02_processing/ 无 xlsx 文件,无需晋升")
        return

    final.mkdir(parents=True, exist_ok=True)
    print(f"  加工中 → 定稿 ({len(processing_files)} 份):")
    for f in processing_files:
        dst = final / f.name
        if dst.exists():
            # 同名文件加时间戳后缀避免覆盖
            stem, ext = f.stem, f.suffix
            dst = final / f"{stem}_{datetime.now().strftime('%H%M%S')}{ext}"
            print(f"    ⚠ 03_final 已存在同名,新文件重命名: {dst.name}")
        from update_latest_bookkeeping import validate_pending_final
        validate_pending_final(f, dst)
        shutil.move(str(f), str(dst))
        print(f"    {f.name} → {dst.name}")

    # 受控定稿晋升完成后，刷新业务日期最新定稿的簿记面板。
    from update_latest_bookkeeping import refresh_if_controlled_final
    from latest_bookkeeping_panel import find_latest_final
    if any(f.name.endswith('-定稿.xlsx') for f in processing_files):
        refresh_if_controlled_final(find_latest_final(final))

    print("✅ 台账晋升完成(旧定稿归档请人工执行: 03_final/* → 04_archive/)")


def archive_final():
    """台账定稿归档(人工触发): 03_final/* → 04_archive/
    需显式调用 abs_archive.py final,不会自动触发。
    """
    print("=== 台账定稿归档(03_final → 04_archive) ===")
    final = LEDGER / "03_final"
    archive = LEDGER / "04_archive"

    if not final.exists():
        print(f"⚠ 跳过: {final.name}/ 不存在")
        return

    finals = list(final.glob("*.xlsx"))
    if not finals:
        print("  03_final/ 无 xlsx 文件")
        return

    archive.mkdir(parents=True, exist_ok=True)
    print(f"  定稿 → 归档 ({len(finals)} 份):")
    for f in finals:
        dst = archive / f.name
        if dst.exists():
            stem, ext = f.stem, f.suffix
            dst = archive / f"{stem}_{datetime.now().strftime('%H%M%S')}{ext}"
            print(f"    ⚠ 04_archive 已存在同名,重命名: {dst.name}")
        shutil.move(str(f), str(dst))
        print(f"    {f.name} → {dst.name}")

    print("✅ 台账定稿归档完成")


# ═══════════════════════════════════════════════════════════════
# §2  看板归档
# ═══════════════════════════════════════════════════════════════

def archive_dashboards():
    """看板归档: 委托给 tidy_dashboard_archive(唯一实现)。

    旧版按文件名前缀取日期(`YYYYMMDD_看板名.html`)，而现行看板命名是
    `ABS综合看板_YYYYMMDD.html`，日期在中间。旧版因此把所有文件都归入
    undated 分组，dated 为空后直接返回，归档动作从未真正生效——这也是
    01_latest 长期堆积 9 份历史看板的直接原因。

    统一走 scripts/tidy_dashboard_archive.py:
      最新月份的最新一份  → 01_latest/
      其余月份各一份      → 02_history/YYYY-MM/
      同月多余版本        → 仓库之外的备份目录

    参数透传，例如:
      python scripts/abs_archive.py dashboards --plan
      python scripts/abs_archive.py dashboards --apply --superseded-dir <仓库外目录>
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from tidy_dashboard_archive import main as tidy_main

    sys.argv = [sys.argv[0]] + sys.argv[2:]
    tidy_main()



# ═══════════════════════════════════════════════════════════════
# §3  重建文件索引
# ═══════════════════════════════════════════════════════════════

def file_mtime_str(p):
    """文件修改日期字符串"""
    try:
        dt = datetime.fromtimestamp(p.stat().st_mtime)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return "-"


def file_size_str(p):
    """文件大小人类可读"""
    try:
        size = p.stat().st_size
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f}KB"
        else:
            return f"{size/1024/1024:.1f}M"
    except Exception:
        return "-"


def scan_dir(d):
    """扫描目录下所有文件(递归),返回 [(rel_path, mtime, size), ...]"""
    files = []
    if not d.exists():
        return files
    for p in sorted(d.rglob("*")):
        if p.is_file() and p.name != ".gitkeep":
            rel = p.relative_to(d).as_posix()
            files.append((rel, file_mtime_str(p), file_size_str(p)))
    return files


def rebuild_index():
    """重建 _文件索引目录.md"""
    print("=== 重建文件索引 ===")
    today = date.today().isoformat()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    ledger_files = scan_dir(LEDGER)
    dashboard_files = scan_dir(DASHBOARDS)

    lines = [
        "---",
        "type: index",
        f"updated: {now}",
        "---",
        "",
        "# ABS工具箱 产出文件索引",
        "",
        f"> 由 `scripts/abs_archive.py index` 自动生成,禁止手改。",
        f"> Last scan: {now}",
        f"> Total: ledger {len(ledger_files)} 文件 / dashboards {len(dashboard_files)} 文件",
        "",
        "## ledger/ (台账)",
        "",
        "| # | 路径 | 修改日期 | 大小 |",
        "|---|---|---|---|",
    ]
    for i, (rel, mt, sz) in enumerate(ledger_files, 1):
        lines.append(f"| {i} | {rel} | {mt} | {sz} |")

    lines += [
        "",
        "## dashboards/ (看板)",
        "",
        "| # | 路径 | 修改日期 | 大小 |",
        "|---|---|---|---|",
    ]
    for i, (rel, mt, sz) in enumerate(dashboard_files, 1):
        lines.append(f"| {i} | {rel} | {mt} | {sz} |")

    index_path = DELIVERABLES / "_文件索引目录.md"
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✅ 索引重建: {index_path.relative_to(VAULT)}")
    print(f"   ledger {len(ledger_files)} 文件 / dashboards {len(dashboard_files)} 文件")


# ═══════════════════════════════════════════════════════════════
# §4  主入口
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("ledger", "final", "dashboards", "index"):
        print(__doc__)
        print("错误: 未指定子命令或子命令无效")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "ledger":
        archive_ledger()
    elif cmd == "final":
        archive_final()
    elif cmd == "dashboards":
        archive_dashboards()
    elif cmd == "index":
        rebuild_index()


if __name__ == "__main__":
    main()
