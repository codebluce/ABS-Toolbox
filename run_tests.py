"""统一测试入口:从仓库根目录一条命令运行全部测试。

用法:
  python run_tests.py            # 全部单元测试(不含冒烟)
  python run_tests.py --smoke    # 全部单元测试 + 冒烟测试

修复审计 P2-06:
- 原先需 cd scripts 后才能运行(顶层导入依赖当前目录);
- `python -m unittest scripts.test_xxx` 会静默收集 0 个测试形成假绿。
本入口显式把 scripts/ 加入 sys.path 后用 unittest.defaultTestLoader
按文件路径发现测试,发现 0 个测试时以非零退出,杜绝假绿。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


def main() -> int:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))

    test_files = sorted(SCRIPTS_DIR.glob("test_*.py"))
    suite = unittest.TestSuite()
    for tf in test_files:
        module_name = tf.stem
        if module_name == "test_smoke":
            # test_smoke.py 是脚本式冒烟测试(main 形式),由 --smoke 分支子进程运行
            continue
        try:
            tests = unittest.defaultTestLoader.loadTestsFromName(module_name)
        except Exception as exc:  # 导入失败必须暴露,不能静默跳过
            print(f"[load-failed] {module_name}: {exc}")
            return 2
        count = tests.countTestCases()
        if count == 0:
            print(f"[empty] {module_name} 未发现任何测试,请检查")
            return 2
        print(f"[discover] {module_name}: {count} tests")
        suite.addTests(tests)

    total = suite.countTestCases()
    if total == 0:
        print("[error] 未发现任何测试")
        return 2

    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if not result.wasSuccessful():
        return 1

    if "--smoke" in sys.argv:
        import subprocess
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "test_smoke.py")],
            cwd=str(REPO_ROOT),
        )
        if proc.returncode != 0:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
