"""冒烟测试：验证三个脚本在测试数据上能否正常完成 + QC 通过

每次修改脚本后，必须执行此脚本确保不引入回归。
兼容 Linux 和 Windows 运行环境。
"""

import subprocess
import sys
import os
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 使用 managed runtime（与SKILL.md §六一致）
PYTHON = sys.executable


def find_test_file():
    """自动查找测试数据文件

    搜索策略：
    1. 环境变量 ABS_TEST_DATA 指定的路径
    2. 台账定稿目录下最新的总表（>100KB）
    3. 台账源文件目录下最新的总表（>100KB）
    """
    # 环境变量优先
    env_path = os.environ.get('ABS_TEST_DATA')
    if env_path and os.path.exists(env_path):
        return env_path

    candidates = []

    # 台账定稿目录 (v2.2.0 改造: 路径改 deliverables/ledger/)
    ledger_dirs = [
        os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'deliverables', 'ledger', '03_final')),
        os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'deliverables', 'ledger', '01_source')),
    ]

    for ws_dir in ledger_dirs:
        if not os.path.isdir(ws_dir):
            continue
        pattern = os.path.join(ws_dir, '*.xlsx')
        try:
            big_files = [f for f in glob.glob(pattern) if os.path.getsize(f) > 100 * 1024]
        except OSError:
            continue
        xlsx_files = sorted(big_files, key=os.path.getmtime, reverse=True)
        candidates.extend(xlsx_files)

    for fp in candidates:
        if os.path.exists(fp):
            return fp
    return None


def run_script(name, script_name):
    script_path = os.path.join(SCRIPT_DIR, script_name)
    test_file = find_test_file()

    if test_file is None:
        print(f"\n--- {name} ---")
        print("SKIP: 未找到测试数据文件（设置 ABS_TEST_DATA 环境变量指定）")
        return None  # None = skip, not fail

    if not os.path.exists(script_path):
        print(f"\n--- {name} ---")
        print(f"FAIL: 脚本文件不存在 {script_path}")
        return False

    result = subprocess.run(
        [PYTHON, script_path, test_file],
        capture_output=True,
        text=True,
        cwd=SCRIPT_DIR,
        timeout=120,
    )

    combined = result.stdout + result.stderr
    exit_ok = result.returncode == 0

    # 提取 QC 汇总行
    qc_lines = [l for l in combined.split('\n') if 'QC PASSED' in l or 'QC FAILED' in l]

    print(f"\n--- {name} ---")
    print(f"  Exit: {'OK' if exit_ok else f'FAIL(code={result.returncode})'}")
    print(f"  QC:   {qc_lines[-1] if qc_lines else 'NOT FOUND'}")

    if not exit_ok:
        err_lines = combined.strip().split('\n')[-10:]
        for l in err_lines:
            print(f"  | {l}")

    if "QC FAILED" in combined:
        print("  -> FAIL")
        return False

    if "QC PASSED" in combined and exit_ok:
        print("  -> PASSED")
        return True

    print("  -> FAIL (QC未通过或异常退出)")
    return False


def main():
    results = []
    results.append(("工具一 gen_abs_cost_report", run_script("工具一", "gen_abs_cost_report.py")))
    results.append(("工具二 gen_compare_tool",   run_script("工具二", "gen_compare_tool.py")))
    results.append(("工具三 gen_spread_report",  run_script("工具三", "gen_spread_report.py")))

    print("\n" + "=" * 50)
    all_pass = True
    any_run = False
    for name, result in results:
        if result is None:
            print(f"  [SKIP] {name}")
            continue
        any_run = True
        mark = "OK" if result else "FAIL"
        if not result:
            all_pass = False
        print(f"  [{mark}] {name}")
    print("=" * 50)

    if not any_run:
        print("No tests executed. Set ABS_TEST_DATA env var or place test data in ledger directories.")
        sys.exit(2)

    if all_pass:
        print("All smoke tests passed.")
        sys.exit(0)
    else:
        print("Some tests failed. Please fix before committing.")
        sys.exit(1)


if __name__ == "__main__":
    main()
