"""跨面板机构身份映射：仅显式、单跳、可审计的业务统计别名。"""
from __future__ import annotations

import json
import hashlib
from functools import lru_cache
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / 'data' / 'institution_alias_registry.json'


@lru_cache(maxsize=1)
def _registry_snapshot(path: str, sha256: str, content: bytes) -> dict:
    # 指纹与解析使用同一次读取的字节，避免再次读取时文件变化。
    data = json.loads(content.decode('utf-8'))
    aliases = data['aliases']
    pairs = [(row['alias'], row['canonical']) for row in aliases]
    if (len(set(src for src, _ in pairs)) != len(pairs) or
            any(not src or not dst or src == dst for src, dst in pairs) or
            set(src for src, _ in pairs) & set(dst for _, dst in pairs)):
        raise ValueError('机构映射须为唯一的单跳精确映射')
    mapping = dict(pairs)
    investor_pairs = [(row['alias'], row['canonical']) for row in data.get('investor_aliases', [])]
    if (len(set(src for src, _ in investor_pairs)) != len(investor_pairs) or
            any(not src or not dst or src == dst for src, dst in investor_pairs) or
            set(src for src, _ in investor_pairs) & set(dst for _, dst in investor_pairs)):
        raise ValueError('认购机构映射须为唯一的单跳精确映射')
    investor_mapping = dict(investor_pairs)
    for row in data['distinct']:
        left, right = row['left'], row['right']
        if mapping.get(left, left) == mapping.get(right, right):
            raise ValueError(f'独立机构被错误归并：{left} / {right}')
        if investor_mapping.get(mapping.get(left, left), mapping.get(left, left)) == investor_mapping.get(mapping.get(right, right), mapping.get(right, right)):
            raise ValueError(f'独立认购机构被错误归并：{left} / {right}')
    return data


def registry() -> dict:
    """按当前路径及文件字节SHA缓存验证结果，批准规则更新后自动失效。"""
    path = Path(REGISTRY).resolve()
    content = path.read_bytes()
    return _registry_snapshot(str(path), hashlib.sha256(content).hexdigest(), content)


# 保留原lru_cache公开入口供调用方和现有测试清理/检查缓存。
registry.cache_clear = _registry_snapshot.cache_clear
registry.cache_info = _registry_snapshot.cache_info
registry.cache_parameters = _registry_snapshot.cache_parameters


def aliases() -> dict[str, str]:
    return {row['alias']: row['canonical'] for row in registry()['aliases']}


def canonical(name: str) -> str:
    """没有明确映射时原样保留，绝不用前缀/包含/去资管后缀推断。"""
    return aliases().get(name, name)


def investor_aliases() -> dict[str, str]:
    return {row['alias']: row['canonical'] for row in registry().get('investor_aliases', [])}


def canonical_investor(name: str) -> str:
    """先应用全局获批别名，再应用认购机构口径；不改写管理人名称。"""
    name = canonical(name)
    return investor_aliases().get(name, name)
