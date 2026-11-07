"""明细文件名 → 台账项目名的别名登记表（精确、单跳、可审计）。

为什么要有这张表
----------------
簿记明细的文件名由各家承销商自己起，写法与台账项目名几乎从不一致：
”26东裕9-1“、”【26东裕ABN001】“、”金采玖2A“ 分别对应台账里的
”26东裕9号一期“、”26东裕8号一期“、”金采9-2“。这些对应关系只能人工确认，
无法从字符串推出来——东裕系列里”东裕9号“同时能对上伯裕/仲裕/叔裕/季裕/春裕，
一旦按前缀匹配就会把某一期的明细记到另一期项目上。

因此：未登记 = 不归并。`increment_merge.map_detail_to_project` 只查这张表，
查不到就原样返回，宁可在录入前报”需确认“，也不猜。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / 'data' / 'project_name_aliases.json'


def _validate(rows: list[dict]) -> dict[str, str]:
    pairs = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('项目别名须为对象数组')
        alias, canonical = row.get('alias'), row.get('canonical')
        if not alias or not canonical:
            raise ValueError('项目别名缺少 alias 或 canonical')
        if alias == canonical:
            raise ValueError(f'项目别名不允许指向自身：{alias}')
        if not row.get('reason'):
            raise ValueError(f'项目别名缺少判定理由：{alias}')
        pairs.append((alias.strip(), canonical.strip()))
    if len({alias for alias, _ in pairs}) != len(pairs):
        raise ValueError('项目别名必须唯一')
    # 单跳：别名集合与目标集合不能相交，否则同一串既是别名又是结果，
    # 解析结果会随查询顺序变化（A→B 且 B→C 时 A 到底落 B 还是 C 取决于跳数）。
    overlap = {alias for alias, _ in pairs} & {canonical for _, canonical in pairs}
    if overlap:
        raise ValueError('项目别名须为单跳映射，禁止链式：' + '、'.join(sorted(overlap)))
    return dict(pairs)


@lru_cache(maxsize=1)
def _snapshot(path: str, sha256: str, content: bytes) -> dict[str, str]:
    # 指纹与解析使用同一次读取的字节，避免校验和解析之间文件被改动。
    data = json.loads(content.decode('utf-8'))
    return _validate(data.get('aliases', []))


def mapping() -> dict[str, str]:
    """按当前路径及文件字节指纹缓存，改表后自动失效。"""
    path = Path(REGISTRY).resolve()
    content = path.read_bytes()
    return _snapshot(str(path), hashlib.sha256(content).hexdigest(), content)


def resolve(name: str) -> str:
    return mapping().get(name, name)


def registered(name: str) -> bool:
    return name in mapping()


def policy() -> str:
    return json.loads(Path(REGISTRY).read_text(encoding='utf-8')).get('policy', '')


_CN_DIGITS = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
              '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}


def _loose(name: str) -> str:
    """仅用于提示”可能漏登记“，不参与任何归并。

    把”第/期/号“、方括号、连字符、中文数字、ABN/ABS 编号后缀、括号说明
    都折叠掉，得到只保留主体和期次的粗粒度指纹。折叠本身会产生歧义
    （”十一“会变成”101“），所以结果只用于提示，不用于匹配。
    """
    text = re.sub(r'[（(][^）)]*[）)]', '', name)
    text = re.sub(r'[【】\[\]\s]', '', text)
    text = text.replace('第', '').replace('期', '').replace('号', '')
    text = text.replace('ABN', '').replace('ABS', '').replace('-', '')
    for cn, digit in _CN_DIGITS.items():
        text = text.replace(cn, digit)
    return text.upper()


def lookalikes(name: str, canonical_names) -> list[str]:
    """返回与未登记名称形似的台账项目名，供录入前提示人工确认。

    只做提示：调用方必须把它当”需确认“，不能据此自动归并。
    """
    loose = _loose(name)
    if len(loose) < 3:
        return []
    hits = []
    for canonical in canonical_names:
        target = _loose(canonical)
        if not target:
            continue
        if loose == target or loose in target or target in loose:
            hits.append(canonical)
    return hits


def stale_entries(project_names) -> list[dict]:
    """列出目标项目已不在当前台账里的别名（台账改名或登记写错）。"""
    names = set(project_names)
    aliases = mapping()
    return [
        {'alias': alias, 'canonical': canonical}
        for alias, canonical in sorted(aliases.items())
        if canonical not in names
    ]


def describe() -> list[tuple[str, str]]:
    return sorted(mapping().items(), key=lambda pair: (pair[1], pair[0]))


def _main(argv: list[str]) -> int:
    rows = describe()
    print(f'项目名别名登记：{len(rows)} 条（{REGISTRY.name}）')
    print(policy())
    print()
    print(f'{"明细/文件名写法":<28}{"台账项目名"}')
    for alias, canonical in rows:
        print(f'{alias:<28}{canonical}')
    return 0


if __name__ == '__main__':
    sys.exit(_main(sys.argv[1:]))
