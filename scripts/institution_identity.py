"""跨面板机构身份映射：仅显式、单跳、可审计的业务统计别名。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / 'data' / 'institution_alias_registry.json'


@lru_cache(maxsize=1)
def registry() -> dict:
    data = json.loads(REGISTRY.read_text(encoding='utf-8'))
    aliases = data['aliases']
    pairs = [(row['alias'], row['canonical']) for row in aliases]
    if (len(set(src for src, _ in pairs)) != len(pairs) or
            any(not src or not dst or src == dst for src, dst in pairs) or
            set(src for src, _ in pairs) & set(dst for _, dst in pairs)):
        raise ValueError('机构映射须为唯一的单跳精确映射')
    mapping = dict(pairs)
    for row in data['distinct']:
        left, right = row['left'], row['right']
        if mapping.get(left, left) == mapping.get(right, right):
            raise ValueError(f'独立机构被错误归并：{left} / {right}')
    return data


def aliases() -> dict[str, str]:
    return {row['alias']: row['canonical'] for row in registry()['aliases']}


def canonical(name: str) -> str:
    """没有明确映射时原样保留，绝不用前缀/包含/去资管后缀推断。"""
    return aliases().get(name, name)
