"""Ledger movement safeguards v1.0; no Excel execution or business-value correction."""
from copy import copy
from decimal import Decimal, InvalidOperation
import re

from openpyxl.formula import Tokenizer
from openpyxl.formula.translate import Translator
from openpyxl.utils.cell import coordinate_from_string

API_VERSION = '1.1'
AMOUNT_TOLERANCE = Decimal('0.0001')
PROJECT_KEY_COLS = (4, 12, 5, 6)  # asset, booking date, project, venue
_CELL = re.compile(r'^(\$?[A-Za-z]{1,3})(\$?)([1-9][0-9]*)$')
_PRODUCT = re.compile(r'^=\s*(\$?[JQ]\$?[1-9][0-9]*)\s*\*\s*(\$?[JQ]\$?[1-9][0-9]*)\s*$', re.I)


class LedgerFormulaError(ValueError):
    """A movement/calculation cannot be proved safe; callers must stop saving."""


def _value(value):
    if hasattr(value, 'isoformat'):
        return value.isoformat()[:10]
    return str(value).strip() if value is not None else ''


def project_key(ws, row):
    return tuple(_value(ws.cell(row, c).value) for c in PROJECT_KEY_COLS)


def tier_key(ws, row):
    return project_key(ws, row) + (_value(ws.cell(row, 16).value),)


def first_data_row(ws):
    """Row 2 may be a partial detail header, or already a real project row."""
    name = _value(ws.cell(2, 5).value)
    if name and name not in ('项目名称', '项目'):
        return 2
    headers = {5: {'项目名称', '项目'}, 16: {'分层情况'}, 20: {'成本'},
               21: {'认购机构'}, 22: {'认购份额'}, 23: {'申购利率'},
               24: {'穿透机构'}, 25: {'申购规模'}}
    return 3 if any(_value(ws.cell(2, c).value) in labels
                    for c, labels in headers.items()) else 2


def _number(value, label):
    if isinstance(value, bool) or value is None or isinstance(value, str):
        raise LedgerFormulaError(f'{label}: numeric value required, got {value!r}')
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise LedgerFormulaError(f'{label}: invalid number') from exc
    if not number.is_finite() or number < 0:
        raise LedgerFormulaError(f'{label}: finite nonnegative number required')
    return number


def validate_r_formula(ws, row, formula=None):
    """Return Decimal only for a direct J*Q with same project J/same tier Q.

    J may anchor at another tier in the same complete project identity. Absolute
    references are accepted only when their actual target identity is correct.
    Unknown formulas (including constants) must use original caches, not evaluation.
    """
    formula = ws.cell(row, 18).value if formula is None else formula
    match = _PRODUCT.fullmatch(formula or '') if isinstance(formula, str) else None
    if not match:
        raise LedgerFormulaError(f'{ws.title}!R{row}: only verified direct J*Q supported ({formula!r})')
    refs = {}
    for ref in match.groups():
        col, rr = coordinate_from_string(ref.replace('$', '').upper())
        refs[col] = rr
    if set(refs) != {'J', 'Q'}:
        raise LedgerFormulaError(f'{ws.title}!R{row}: must reference one J and one Q')
    key = project_key(ws, row)
    if not all(key) or not tier_key(ws, row)[-1]:
        raise LedgerFormulaError(f'{ws.title}!R{row}: incomplete project/tier identity')
    if project_key(ws, refs['J']) != key or tier_key(ws, refs['Q']) != tier_key(ws, row):
        raise LedgerFormulaError(f'{ws.title}!R{row}: J/Q reference crosses project or tier')
    j = _number(ws.cell(refs['J'], 10).value, f'J{refs["J"]}')
    q = _number(ws.cell(refs['Q'], 17).value, f'Q{refs["Q"]}')
    if q > 1:
        raise LedgerFormulaError(f'Q{refs["Q"]}: ratio must be within [0, 1]')
    return j * q


def formula_translate(formula, origin, dest):
    """Copy semantics: translate relative refs and preserve $ absolute semantics."""
    if not isinstance(formula, str) or not formula.startswith('='):
        return formula
    # Translator does not safely relocate defined names/structured/external refs.
    for token in Tokenizer(formula).items:
        if token.type == 'OPERAND' and token.subtype == 'RANGE':
            _reference(token.value)  # fail clearly on unsupported references
    try:
        return Translator(formula, origin=origin).translate_formula(dest)
    except Exception as exc:
        raise LedgerFormulaError(f'Cannot translate {origin} -> {dest}: {formula}') from exc


def relocate_project_formula(formula, row_map, source_sheet, target_sheet):
    """Relocate a complete project, mapping internal rows even with $ anchors.

    Ordinary copy uses formula_translate. This operation preserves columns and
    dollar markers, but every referenced row must belong to the project map.
    Cross-project/sheet, whole-column, named and external references are refused.
    """
    if not isinstance(formula, str) or not formula.startswith('='):
        return formula
    tokens = Tokenizer(formula).items
    for token in tokens:
        if token.type != 'OPERAND' or token.subtype != 'RANGE':
            continue
        sheet, address = _reference(token.value)
        if sheet is not None and sheet.casefold() != source_sheet.casefold():
            raise LedgerFormulaError(f'Project relocation: external sheet reference {token.value}')
        parts = address.split(':')
        source_rows = []
        translated = []
        for part in parts:
            match = _CELL.fullmatch(part)
            row_match = re.fullmatch(r'(\$?)([1-9][0-9]*)', part)
            if match:
                col, absolute, rr = match.groups()
            elif row_match:
                col, (absolute, rr) = '', row_match.groups()
            else:
                raise LedgerFormulaError(f'Project relocation: unbounded reference {token.value}')
            rr = int(rr)
            if rr not in row_map:
                raise LedgerFormulaError(f'Project relocation: reference {token.value} outside project row map')
            source_rows.append(rr)
            translated.append(f'{col}{absolute}{row_map[rr]}')
        if len(source_rows) == 2:
            low, high = sorted(source_rows)
            if any(rr not in row_map or row_map[rr] != row_map[low] + rr - low
                   for rr in range(low, high + 1)):
                raise LedgerFormulaError(f'Project relocation: noncontiguous range {token.value}')
        prefix = ("'" + target_sheet.replace("'", "''") + "'!") if sheet is not None else ''
        token.value = prefix + ':'.join(translated)
    return '=' + ''.join(token.value for token in tokens)


def _reference(value):
    sheet, address = None, value
    if '!' in value:
        sheet, address = value.rsplit('!', 1)
        sheet = sheet[1:-1].replace("''", "'") if sheet.startswith("'") and sheet.endswith("'") else sheet
        if any(c in sheet for c in '[]:'):
            raise LedgerFormulaError(f'External/3D reference unsupported: {value}')
    parts = address.split(':')
    if len(parts) > 2:
        raise LedgerFormulaError(f'Unsupported reference: {value}')
    # Full column/row ranges have insert semantics too.
    if not all(_CELL.fullmatch(p) for p in parts):
        if len(parts) != 2 or not (all(re.fullmatch(r'\$?[A-Za-z]{1,3}', p) for p in parts)
                                  or all(re.fullmatch(r'\$?[1-9][0-9]*', p) for p in parts)):
            raise LedgerFormulaError(f'Named/structured/unsupported reference: {value}')
    return sheet, address


def rebase_formula_for_insert(formula, formula_sheet, target_sheet, idx, amount):
    """Insert semantics affect target row numbers, including $; never shift columns."""
    if not isinstance(formula, str) or not formula.startswith('='):
        return formula
    tokens = Tokenizer(formula).items
    for token in tokens:
        if token.type != 'OPERAND' or token.subtype != 'RANGE':
            continue
        sheet, address = _reference(token.value)
        if (sheet if sheet is not None else formula_sheet).casefold() != target_sheet.casefold():
            continue
        def shift(part):
            match = _CELL.fullmatch(part)
            if match:
                col, absolute, rr = match.groups()
                return f'{col}{absolute}{int(rr) + amount if int(rr) >= idx else rr}'
            if re.fullmatch(r'\$?[1-9][0-9]*', part):
                rr = int(part.lstrip('$'))
                return ('$' if part.startswith('$') else '') + str(rr + amount if rr >= idx else rr)
            return part  # full-column references
        shifted = ':'.join(shift(p) for p in address.split(':'))
        prefix = token.value[:token.value.rfind('!') + 1] if sheet is not None else ''
        token.value = prefix + shifted
    return '=' + ''.join(token.value for token in tokens)


def insert_rows_rebase(ws, idx, amount=1):
    """Preflight all workbook formulas, then insert and repair target-sheet refs.

    Qualified cross-sheet A1 references are supported. Named, external, 3D and
    structured references fail before mutation; callers must not silently retry.
    """
    if idx < 1 or amount < 1:
        raise LedgerFormulaError('insert idx/amount must be positive')
    changes = []
    for sheet in ws.parent.worksheets:
        for cells in sheet.iter_rows():
            for cell in cells:
                if cell.data_type == 'f':
                    updated = rebase_formula_for_insert(cell.value, sheet.title, ws.title, idx, amount)
                    new_row = cell.row + amount if sheet is ws and cell.row >= idx else cell.row
                    changes.append((sheet, new_row, cell.column, updated))
    merges = list(ws.merged_cells.ranges)
    for merged in merges:
        ws.unmerge_cells(str(merged))
    ws.insert_rows(idx, amount)
    for sheet, row, col, formula in changes:
        sheet.cell(row, col).value = formula
    for merged in merges:
        start = merged.min_row + amount if merged.min_row >= idx else merged.min_row
        end = merged.max_row + amount if merged.max_row >= idx else merged.max_row
        ws.merge_cells(start_row=start, end_row=end, start_column=merged.min_col, end_column=merged.max_col)
    return ws


def rebase_formula_for_delete(formula, formula_sheet, target_sheet, idx, amount):
    """Delete semantics: reject references intersecting removed rows, shift later refs."""
    if not isinstance(formula, str) or not formula.startswith('='):
        return formula
    tokens = Tokenizer(formula).items
    end = idx + amount - 1
    for token in tokens:
        if token.type != 'OPERAND' or token.subtype != 'RANGE':
            continue
        sheet, address = _reference(token.value)
        if (sheet if sheet is not None else formula_sheet).casefold() != target_sheet.casefold():
            continue
        rows = []
        for part in address.split(':'):
            match = _CELL.fullmatch(part)
            if match:
                rows.append(int(match.group(3)))
            elif re.fullmatch(r'\$?[1-9][0-9]*', part):
                rows.append(int(part.lstrip('$')))
        if rows and min(rows) <= end and max(rows) >= idx:
            raise LedgerFormulaError(f'Delete rows {idx}-{end}: reference {token.value} intersects deleted target')
        def shift(part):
            match = _CELL.fullmatch(part)
            if match:
                col, absolute, rr = match.groups()
                return f'{col}{absolute}{int(rr) - amount if int(rr) > end else rr}'
            if re.fullmatch(r'\$?[1-9][0-9]*', part):
                rr = int(part.lstrip('$'))
                return ('$' if part.startswith('$') else '') + str(rr - amount if rr > end else rr)
            return part
        shifted = ':'.join(shift(p) for p in address.split(':'))
        prefix = token.value[:token.value.rfind('!') + 1] if sheet is not None else ''
        token.value = prefix + shifted
    return '=' + ''.join(token.value for token in tokens)


def delete_rows_rebase(ws, idx, amount=1):
    """Preflight workbook dependencies before deletion; never silently emit #REF!."""
    if idx < 1 or amount < 1:
        raise LedgerFormulaError('delete idx/amount must be positive')
    end = idx + amount - 1
    changes = []
    for sheet in ws.parent.worksheets:
        for cells in sheet.iter_rows():
            for cell in cells:
                if cell.data_type != 'f' or (sheet is ws and idx <= cell.row <= end):
                    continue
                updated = rebase_formula_for_delete(cell.value, sheet.title, ws.title, idx, amount)
                new_row = cell.row - amount if sheet is ws and cell.row > end else cell.row
                changes.append((sheet, new_row, cell.column, updated))
    merges = list(ws.merged_cells.ranges)
    for merged in merges:
        if merged.min_row <= end and merged.max_row >= idx:
            raise LedgerFormulaError(f'Delete intersects merged metadata/detail {merged}; review required')
    for merged in merges:
        ws.unmerge_cells(str(merged))
    ws.delete_rows(idx, amount)
    for sheet, row, col, formula in changes:
        sheet.cell(row, col).value = formula
    for merged in merges:
        start = merged.min_row - amount if merged.min_row > end else merged.min_row
        stop = merged.max_row - amount if merged.max_row > end else merged.max_row
        ws.merge_cells(start_row=start, end_row=stop, start_column=merged.min_col, end_column=merged.max_col)
    return ws


def expand_ledger_metadata(ws):
    """Expand explicit A:T vertical merges and bounded metadata; preserve U:Y.

    A:O fill stays inside project segments; P carries inside a project; Q/S/T
    fill stays inside a tier. Unmerged missing R is never inferred. R from an
    explicit merge retains its anchor only after same-project/tier validation.
    """
    start = first_data_row(ws)
    merged_formulas = []
    for merged in list(ws.merged_cells.ranges):
        # Detail merges remain intact, so their placeholders remain exact.
        if merged.min_col > 20 or merged.max_row < start:
            continue
        if merged.max_col > 20 or merged.min_col != merged.max_col:
            raise LedgerFormulaError(f'Unsupported metadata merge: {merged}')
        anchor = ws.cell(merged.min_row, merged.min_col)
        value, style = anchor.value, copy(anchor._style)
        ws.unmerge_cells(str(merged))
        for rr in range(merged.min_row, merged.max_row + 1):
            cell = ws.cell(rr, merged.min_col)
            cell.value, cell._style = value, copy(style)
            if isinstance(value, str) and value.startswith('='):
                if merged.min_col == 18:
                    merged_formulas.append(rr)
                else:
                    cell.value = formula_translate(value, anchor.coordinate, cell.coordinate)
    project_values, tier_values = {}, {}
    current_name, current_tier = None, None
    segment_amounts = {}
    for rr in range(start, ws.max_row + 1):
        vals = {c: ws.cell(rr, c).value for c in range(1, 26)}
        if not any(v is not None for v in vals.values()):
            project_values, tier_values = {}, {}
            current_name, current_tier = None, None
            segment_amounts = {}
            continue
        name = _value(vals[5])
        boundary = bool(name and name != current_name)
        boundary |= any(vals[c] is not None and c in project_values
                        and _value(vals[c]) != _value(project_values[c][0])
                        for c in (4, 6, 12))
        if boundary:
            project_values, tier_values = {}, {}
            current_name, current_tier = name, None
            segment_amounts = {}
        if not current_name:
            continue
        for c in range(1, 16):
            cell = ws.cell(rr, c)
            if cell.value is not None:
                project_values[c] = (cell.value, cell.coordinate, copy(cell._style))
            elif c in project_values:
                value, origin, style = project_values[c]
                cell.value, cell._style = formula_translate(value, origin, cell.coordinate), copy(style)
        explicit_tier = _value(vals[16])
        if explicit_tier and explicit_tier != current_tier:
            tier_values = {}
            current_tier = explicit_tier
            segment_amounts = {}
        if not explicit_tier and current_tier:
            ws.cell(rr, 16).value = current_tier
        if current_tier:
            # A repeated label can contain legitimate explicit subsegments.
            # Changed explicit Q/R starts a segment; never erase those records
            # or infer uniqueness from a nonstandard label.
            changed = False
            for c in (17, 18):
                value = vals[c]
                if value is None or (isinstance(value, str) and value.startswith('=')):
                    continue
                if c in segment_amounts and _value(value) != _value(segment_amounts[c]):
                    changed = True
            if changed:
                tier_values = {}
                segment_amounts = {}
            for c in (17, 18):
                value = vals[c]
                if value is not None and not (isinstance(value, str) and value.startswith('=')):
                    segment_amounts[c] = value
            for c in (17, 19, 20):
                cell = ws.cell(rr, c)
                if cell.value is not None:
                    tier_values[c] = (cell.value, cell.coordinate, copy(cell._style))
                elif c in tier_values:
                    value, origin, style = tier_values[c]
                    cell.value, cell._style = formula_translate(value, origin, cell.coordinate), copy(style)
    for rr in merged_formulas:
        validate_r_formula(ws, rr)
    return ws


def validate_project_j_update(ws, start, end, new_j):
    """Preflight J change: do not overwrite literal R or unknown Q/formulas."""
    j = _number(new_j, 'new J')
    for rr in range(start, end + 1):
        r = ws.cell(rr, 18).value
        q = ws.cell(rr, 17).value
        if r is None and q is None:
            continue
        qn = _number(q, f'Q{rr}')
        if qn > 1:
            raise LedgerFormulaError(f'Q{rr}: ratio outside [0,1]')
        if isinstance(r, str) and r.startswith('='):
            validate_r_formula(ws, rr)
        elif r is None or abs(_number(r, f'R{rr}') - j * qn) > AMOUNT_TOLERANCE:
            raise LedgerFormulaError(f'R{rr}: J update conflicts with literal/missing R; review required')
