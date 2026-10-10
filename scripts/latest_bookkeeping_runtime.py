"""执行真实台账快照的前端运行时对账（不依赖浏览器、不修改文件）。"""
import json
from pathlib import Path
import shutil
import subprocess


def verify_runtime(data):
    node = shutil.which('node')
    if node is None:
        raise ValueError('最新簿记运行时门禁需要node')
    result = subprocess.run([node,str(Path(__file__).with_name('verify_latest_bookkeeping_runtime.js'))],
                            input=json.dumps(data,ensure_ascii=False,allow_nan=False),text=True,capture_output=True)
    if result.returncode:
        raise ValueError('最新簿记实际明细/筛选/导出对账失败: '+result.stdout+result.stderr)
    return json.loads(result.stdout)
