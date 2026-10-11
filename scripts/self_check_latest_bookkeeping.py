"""最新簿记自检：回归测试 + 原始定稿逐笔对账 + 实际HTML校验，失败非零退出。

可独立检查台账；--dashboard核对指定面板；--skip-tests供同一次更新的第二次复核。
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys

import latest_bookkeeping_panel as panel
import latest_bookkeeping_qc as qc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path)
    parser.add_argument('--dashboard', type=Path)
    parser.add_argument('--report', type=Path, help='可选JSON检查报告，不包含机构明细')
    parser.add_argument('--skip-tests', action='store_true')
    args = parser.parse_args()
    report = {'checkedAt':datetime.now().astimezone().isoformat(timespec='seconds'), 'status':'FAIL', 'tests':[]}
    try:
        ledger = args.ledger or panel.find_latest_final()
        if not args.skip_tests:
            folder = Path(__file__).resolve().parent
            commands = [[sys.executable,'-m','unittest','discover','-s',str(folder),'-p','test_latest_bookkeeping*.py','-v'],
                        [sys.executable,'-m','unittest','discover','-s',str(folder),'-p','test_mobile_bookkeeping_panel.py','-v']]
            node = shutil.which('node')
            if not node:
                raise ValueError('自检需要node执行真实面板交互及CSV回归，未找到node')
            commands.append([node,str(folder/'test_latest_bookkeeping_panel.js')])
            for command in commands:
                result = subprocess.run(command, text=True, capture_output=True)
                report['tests'].append({'command':command,'returncode':result.returncode})
                print(result.stdout, end='')
                print(result.stderr, end='', file=sys.stderr)
                if result.returncode:
                    raise ValueError('回归测试失败')
        data = panel.compute_data(ledger)
        report.update(data['qc'])
        report['provenance'] = data['provenance']
        from latest_bookkeeping_runtime import verify_runtime
        report['runtime'] = verify_runtime(data)
        from latest_bookkeeping_runtime import verify_mobile_runtime
        report['mobileRuntime'] = verify_mobile_runtime(data)
        if args.dashboard:
            report.update(qc.verify_html(args.dashboard.read_text(encoding='utf-8'),ledger))
            report['dashboard'] = args.dashboard.name
            report['dashboardSha256'] = qc.file_sha256(args.dashboard)
        report['status']='PASS'
    except (ValueError, OSError) as error:
        report['status']='FAIL'
        report['error']=str(error)
        if isinstance(error,qc.BookkeepingGateError):
            report['issues']=error.report['issues']
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':
    raise SystemExit(main())
