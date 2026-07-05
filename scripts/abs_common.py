"""ABS发行定价公共模块：合并单元格预处理、列名映射、QC框架

供三个工具脚本共享：
  gen_abs_cost_report.py（工具一：成本分布）
  gen_compare_tool.py    （工具二：机构比对）
  gen_spread_report.py   （工具三：利差分析）
"""

import os
import tempfile
from copy import copy

import pandas as pd

# ── 成本区间配置（工具一使用）──────────────────────────────────────
COST_BINS = [round(1.50 + i * 0.05, 4) for i in range(20)] + [2.55]
COST_LABELS = [f"{COST_BINS[i]:.2f}%~{COST_BINS[i+1]:.2f}%"
               for i in range(len(COST_BINS) - 1)]

# ── 利差区间配置（工具三使用）──────────────────────────────────────
SPREAD_BINS   = [round(0.05 + i * 0.05, 4) for i in range(21)] + [1.15]
SPREAD_LABELS = [f"+{SPREAD_BINS[i]:.2f}%~+{SPREAD_BINS[i+1]:.2f}%"
                 for i in range(len(SPREAD_BINS) - 1)]

# ── 台账列名（25列，A~Y）──────────────────────────────────────
COLNAMES = [
    '序号', '月份', '类别', '资产类型', '项目名称', '发行场所',
    '计划管理人', '联席承销商', '托管行', '规模', '期限',
    '簿记时间', '国股CD', 'ALL-IN成本', '认购倍数',
    '分层情况', '分层占比', '对应金额（亿）', '评级',
    '成本', '认购机构', '认购份额',
    '申购利率', '穿透机构', '申购规模',
]

# ── WXY/TUV 列名常量 ──────────────────────────────────────────
RESOLVED_COST_COL = '实际成本'
RESOLVED_INST_COL = '实际机构'
RESOLVED_SHARE_COL = '实际份额'
NON_NUMERIC_COST_VALS = {'成本', '自持', '不出表', '-'}

# ── 期限分类 ───────────────────────────────────────────────────
OVER_1Y_ASSETS = {'信托企业主贷', '小贷企业主贷', '京企贷'}

TENOR_COL_CANDIDATES = ['期限（月）', '期限']

PRODUCT_ORDER_TEMPLATE = [
    '1年期赊销白条', '超1年期赊销白条',
    '1年期信托金条', '超1年期信托金条',
    '1年期白条取现', '超1年期白条取现',
    '1年期信托企业主贷', '超1年期信托企业主贷',
    '1年期小贷企业主贷', '超1年期小贷企业主贷',
]

# ── 优先分层过滤条件 ──────────────────────────────────────────
PRIORITY_LAYERS = ['优先A', '优先级']

# ── 配色 ───────────────────────────────────────────────────────
ASSET_COLORS = {
    '赊销白条':              {'header': '#1a3a5c', 'tag': '#2563a8'},
    '信托金条':              {'header': '#1c3a2a', 'tag': '#2d7a4f'},
    '信托企业主贷':           {'header': '#3a2010', 'tag': '#c05a20'},
    '小贷企业主贷':           {'header': '#2a1040', 'tag': '#6b3daa'},
    '白条取现':              {'header': '#1a3048', 'tag': '#3a6090'},
    '动产质押':              {'header': '#2a2a10', 'tag': '#8a8a30'},
    '保理':                 {'header': '#0d3a3a', 'tag': '#1a7a7a'},
    '京企贷':               {'header': '#3a1010', 'tag': '#a03030'},
    '金条&白取&信托白条混发':  {'header': '#2a2a3a', 'tag': '#5a5a7a'},
    '信托白条':              {'header': '#3a3010', 'tag': '#8a7020'},
    '金条&白取混发':          {'header': '#2a1020', 'tag': '#6a2a6a'},
    '信托白取':              {'header': '#103a2a', 'tag': '#207a5a'},
    '金采':                 {'header': '#1a1a1a', 'tag': '#4a4a4a'},
}
DEFAULT_COLOR = {'header': '#2a2a2a', 'tag': '#555555'}

BASE_COLORS = ASSET_COLORS  # 利差报告用BASE_COLORS作为别名

MONTH_COLORS = [
    '#0d2a4a', '#1a3a6c', '#2a4a8c', '#3a5a9c',
    '#4a6aac', '#5a7abc', '#6a8acc', '#7a9adc',
]
MONTH_ACCENT = '#e8f0fc'


# ── 合并单元格预处理（pandas只读场景）──────────────────────────
def preprocess_xlsx_for_pandas(xlsx_path):
    """预处理合并单元格Excel，返回临时文件路径供pandas读取。

    步骤：
    1. 保存P/U/V/W/X/Y列原始值（pandas只读，无需保存格式）
    2. 取消所有合并单元格
    3. A~T列向下填充（跳过P列），继承格式
    4. 恢复P/U/V/W/X/Y列原始值
    5. 保存为临时文件，返回路径

    调用方负责在pandas读取后删除临时文件（或由系统自动清理）。
    """
    from openpyxl import load_workbook

    wb = load_workbook(xlsx_path)
    ws = wb.active

    # 1. 保存P(16)/U(21)/V(22)列合并单元格原始值
    protected_data = {}
    for mrange in list(ws.merged_cells.ranges):
        for row in range(mrange.min_row, mrange.max_row + 1):
            for col in range(mrange.min_col, mrange.max_col + 1):
                if col in (16, 21, 22):
                    val = ws.cell(row=mrange.min_row, column=col).value
                    if val is not None:
                        protected_data[(row, col)] = val

    # 保存W(23)/X(24)/Y(25)列全部数据（只保存值，pandas不需要格式）
    wxy_values = {}
    for r in range(1, ws.max_row + 1):
        for c in (23, 24, 25):
            cell = ws.cell(row=r, column=c)
            if cell.value is not None:
                wxy_values[(r, c)] = cell.value

    # 2. 取消所有合并单元格
    for mrange in list(ws.merged_cells.ranges):
        ws.unmerge_cells(str(mrange))

    # 3. A~T列向下填充（跳过P列=16），继承格式
    last_values = {}
    last_cells = {}
    for r in range(2, ws.max_row + 1):
        for c in range(1, 21):
            if c == 16:
                continue
            cell = ws.cell(row=r, column=c)
            if cell.value is not None:
                last_values[c] = cell.value
                last_cells[c] = cell
            elif c in last_values and last_values[c] is not None:
                cell.value = last_values[c]
                src = last_cells[c]
                if src:
                    cell.font = copy(src.font)
                    cell.border = copy(src.border)
                    cell.alignment = copy(src.alignment)
                    cell.number_format = src.number_format

    # 4. 恢复P/U/V列原始值
    for (row, col), val in protected_data.items():
        ws.cell(row=row, column=col).value = val

    # 恢复W/X/Y列原始值（填充范围1-20不含23-25，不会覆盖WXY，此处仅恢复原始值）
    for (r, c), val in wxy_values.items():
        ws.cell(row=r, column=c).value = val

    # 5. 保存为临时文件
    tmp_dir = tempfile.gettempdir()
    tmp_name = f'abs_preprocessed_{os.getpid()}_{id(wb)}.xlsx'
    tmp_path = os.path.join(tmp_dir, tmp_name)
    wb.save(tmp_path)
    wb.close()
    return tmp_path


# ── 公共函数 ───────────────────────────────────────────────────
def classify_tenor(tenor_str, asset_type):
    """将期限字符串解析为 1年期 / 超1年期"""
    import re
    nums = re.findall(r'\d+', str(tenor_str))
    if not nums:
        return '未知'
    x = int(nums[0])
    if x == 12 and asset_type in OVER_1Y_ASSETS:
        return '超1年期'
    return '1年期' if x <= 12 else '超1年期'


def resolve_tenor_col(df):
    """返回实际存在的期限列名，找不到则报错"""
    for c in TENOR_COL_CANDIDATES:
        if c in df.columns:
            return c
    raise ValueError(
        f"[INPUT ERROR] 缺少期限列，期望列名之一：{TENOR_COL_CANDIDATES}\n"
        f"当前列：{list(df.columns)}"
    )


def clean_colnames(df_raw):
    """检查列数并返回25列标准列名"""
    if df_raw.shape[1] < 25:
        raise ValueError(
            f"[INPUT ERROR] 输入文件列数不足（{df_raw.shape[1]}列），"
            "请使用含25列的总表（含WXY补充列）而非子表明细"
        )
    return COLNAMES


def resolve_columns(df):
    """WXY列优先，TUV列回退；忽略非数值脏数据"""
    w = pd.to_numeric(df['申购利率'], errors='coerce')
    x = df['穿透机构']
    y = pd.to_numeric(df['申购规模'], errors='coerce')

    cost_raw = df['成本'].astype(str).str.strip()
    cost_clean = cost_raw.where(~cost_raw.isin(NON_NUMERIC_COST_VALS), pd.NA)
    t = pd.to_numeric(cost_clean, errors='coerce')

    u = df['认购机构'].where(
        ~df['认购机构'].astype(str).str.strip().isin(NON_NUMERIC_COST_VALS), pd.NA
    )
    v = pd.to_numeric(df['认购份额'], errors='coerce')

    df[RESOLVED_COST_COL] = w.fillna(t)
    df[RESOLVED_INST_COL] = x.where(x.notna(), u)
    df[RESOLVED_SHARE_COL] = y.fillna(v)

    self_hold_mask = df['申购利率'].astype(str).str.strip().str.match(r'^自持$', na=False)
    return df[~self_hold_mask]


def validate_input(df, extra_required=None):
    """Fail-fast 入口校验：缺失列 + 关键列空值比例"""
    required = ['簿记时间', '资产类型', '分层情况',
                RESOLVED_SHARE_COL, RESOLVED_INST_COL, RESOLVED_COST_COL]
    if extra_required:
        required.extend(extra_required)

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"[INPUT ERROR] 缺少必需列：{missing}\n"
            f"当前列：{list(df.columns)}\n"
            f"请检查Excel表头是否与示例一致"
        )

    # 关键列空值比例检查
    null_check_cols = [c for c in required if c in df.columns]
    null_ratio = df[null_check_cols].isna().mean()
    high_null = null_ratio[null_ratio > 0.3].index.tolist()
    if high_null:
        from warnings import warn
        warn(f"[INPUT WARN] 以下关键列空值比例>30%：{high_null}，数据可能不完整")


def load_and_filter(xlsx_path, need_tenor=False, extra_required=None):
    """统一的数据读取与预处理入口

    Args:
        xlsx_path: 台账Excel路径
        need_tenor: 是否需要期限分类（工具二/三需要）
        extra_required: 额外必需列

    Returns:
        df: 全量数据DataFrame（过滤自持后）
        dfa: 仅优先A/优先级子集
        tmp_path: 预处理临时文件路径（调用方应负责删除）
        tenor_col: 期限列名（need_tenor=True时）或None
    """
    # 合并单元格预处理
    tmp_path = preprocess_xlsx_for_pandas(xlsx_path)
    try:
        df_raw = pd.read_excel(tmp_path, engine='openpyxl', header=None)
    except Exception as e:
        # 预处理已成功生成临时文件，读取失败应报错而非静默回退
        # （回退到未预处理文件会导致合并单元格数据失真）
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise ValueError(
            f"[INPUT ERROR] 预处理后的临时文件读取失败：{e}\n"
            f"临时文件路径：{tmp_path}\n"
            f"请检查原始Excel文件是否损坏"
        )

    colnames = clean_colnames(df_raw)
    df_raw.columns = colnames
    df = df_raw.iloc[2:].copy()
    title_mask = df['成本'].astype(str).str.match(r'^成本$', na=False)
    df = df[~title_mask]
    df.reset_index(drop=True, inplace=True)

    for c in ['规模', '国股CD']:
        df[c] = pd.to_numeric(
            df[c].astype(str).str.strip()
            .replace({v: pd.NA for v in NON_NUMERIC_COST_VALS}),
            errors='coerce'
        )
    df['簿记时间'] = pd.to_datetime(df['簿记时间'], errors='coerce')

    df = resolve_columns(df)
    dfa = df[df['分层情况'].isin(PRIORITY_LAYERS)].copy()

    if need_tenor:
        tenor_col = resolve_tenor_col(dfa)
    else:
        tenor_col = None

    extra = list(extra_required or [])
    if need_tenor:
        extra.append('国股CD')
    validate_input(dfa, extra_required=extra if extra else None)

    return df, dfa, tmp_path, tenor_col


# ── QC 框架基类 ───────────────────────────────────────────────
class QCRunner:
    """QC检查框架：ok/warn/fail + 汇总 + 返回值"""

    def __init__(self, title):
        self.title = title
        self.issues = []
        self.ok_count = 0

    def ok(self, msg):
        self.ok_count += 1
        print(f'  [OK]   {msg}')

    def warn(self, msg):
        self.issues.append(('WARN', msg))
        print(f'  [WARN] {msg}')

    def fail(self, msg):
        self.issues.append(('FAIL', msg))
        print(f'  [FAIL] {msg}')

    def header(self):
        print('\n' + '=' * 52)
        print(f'  QC Report — {self.title}')
        print('=' * 52)

    def summary(self):
        print('\n' + '=' * 52)
        fail_items = [x for x in self.issues if x[0] == 'FAIL']
        warn_items = [x for x in self.issues if x[0] == 'WARN']

        if not fail_items and not warn_items:
            print(f'  QC PASSED — {self.ok_count}项全部通过')
        elif not fail_items:
            print(f'  QC PASSED WITH WARNINGS — {self.ok_count}项通过，{len(warn_items)}项需关注：')
            for _, msg in warn_items:
                print(f'    ! {msg}')
        else:
            print(f'  QC FAILED — {len(fail_items)}项严重错误，{len(warn_items)}项警告：')
            for level, msg in self.issues:
                mark = 'X' if level == 'FAIL' else '!'
                print(f'    {mark} {msg}')
        print('=' * 52 + '\n')
        return not bool(fail_items)


def product_color(asset_type, tenor_label):
    """1年期用基色；超1年期用浅30%亮度的同色相"""
    base = BASE_COLORS.get(asset_type, DEFAULT_COLOR)
    h = base['header']
    t = base['tag']

    def shift_hex(hex_color, amount=50):
        r = min(255, int(hex_color[1:3], 16) + amount)
        g = min(255, int(hex_color[3:5], 16) + amount)
        b = min(255, int(hex_color[5:7], 16) + amount)
        return f'#{r:02x}{g:02x}{b:02x}'

    if '超1年' in tenor_label:
        return {'header': shift_hex(h, 45), 'tag': shift_hex(t, 25)}
    return {'header': h, 'tag': t}
