"""智能问答反馈聚合脚本

背景：ABS工具箱是零依赖单文件 HTML 架构，没有服务器，每个用户的"没听懂"/主动反馈
记录只存在自己浏览器的 localStorage 里（见 itl_chat.js 的 recordFeedback/exportFeedback）。
没有自动汇总的可能，只能靠人工把各自导出的 json 丢进一个共享目录，本脚本负责离线合并。

用法：
    1. 同事在问答面板底部点"导出反馈(N条)"，下载 itl_feedback_YYYY-MM-DD.json
    2. 把这些 json 文件丢进 feedback_inbox/ 目录（自建，不进 git，见 .gitignore）
    3. python3 scripts/lab/aggregate_chat_feedback.py [feedback_inbox目录路径]

输出：audit/self_check/chat_feedback_汇总_<今天日期>.md —— 一张按频次排序的"待验证问题"表，
直接作为下一轮 itl_chat_harness.js 回归题库的候选来源。
"""
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

TYPE_LABEL = {
    'unrecognized': '没听懂（自动记录）',
    'user_flagged_wrong': '用户主动反馈答错',
    'compute_error': '计算报错',
    'exception': '解析异常',
}


def normalize_question(q):
    """归一化问题文本用于去重计数：去首尾空白、合并连续空白、统一全角空格"""
    return ' '.join(q.replace('　', ' ').split())


def load_inbox(inbox_dir):
    """扫描目录下所有 json 文件，合并成一个记录列表"""
    records = []
    inbox_dir = Path(inbox_dir)
    if not inbox_dir.exists():
        return records
    for f in sorted(inbox_dir.glob('*.json')):
        try:
            with open(f, encoding='utf-8') as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError) as e:
            print(f'[WARN] 跳过无法解析的文件 {f.name}: {e}')
            continue
        if not isinstance(data, list):
            print(f'[WARN] 跳过格式不符的文件 {f.name}（应为 json 数组）')
            continue
        for entry in data:
            entry['_source_file'] = f.name
            records.append(entry)
    return records


def aggregate(records):
    """按归一化问题文本聚合：出现次数、来源文件数（近似"多少人问过"）、类型分布"""
    groups = defaultdict(lambda: {'count': 0, 'sources': set(), 'types': defaultdict(int), 'raw_examples': []})
    for r in records:
        q = normalize_question(r.get('question', ''))
        if not q:
            continue
        g = groups[q]
        g['count'] += 1
        g['sources'].add(r.get('_source_file', '?'))
        g['types'][r.get('type', 'unknown')] += 1
        if len(g['raw_examples']) < 3:
            g['raw_examples'].append(r.get('question', ''))
    return groups


def render_report(groups, out_path):
    rows = sorted(groups.items(), key=lambda kv: (-kv[1]['count'], kv[0]))
    lines = [
        f'# 智能问答反馈汇总 — {datetime.now().strftime("%Y-%m-%d")}',
        '',
        f'共 {len(rows)} 个去重后的问题，来自反馈 inbox 聚合。按出现频次排序，'
        f'直接作为 `scripts/lab/itl_chat_harness.js` 下一轮回归题库的候选来源。',
        '',
        '| 排名 | 问题 | 出现次数 | 来源文件数 | 类型分布 |',
        '|---|---|---|---|---|',
    ]
    for i, (q, g) in enumerate(rows, 1):
        types_str = '、'.join(f'{TYPE_LABEL.get(t, t)}×{n}' for t, n in g['types'].items())
        lines.append(f'| {i} | {q} | {g["count"]} | {len(g["sources"])} | {types_str} |')
    lines.append('')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    inbox = sys.argv[1] if len(sys.argv) > 1 else 'feedback_inbox'
    records = load_inbox(inbox)
    if not records:
        print(f'[INFO] {inbox} 目录下没有找到可用的反馈 json 文件，无需汇总')
        return
    groups = aggregate(records)
    script_dir = Path(__file__).resolve().parent
    out_dir = script_dir.parent.parent / 'audit' / 'self_check'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'chat_feedback_汇总_{datetime.now().strftime("%Y%m%d")}.md'
    render_report(groups, out_path)
    print(f'[完成] 合并 {len(records)} 条原始反馈 → {len(groups)} 个去重问题 → {out_path}')


if __name__ == '__main__':
    main()
