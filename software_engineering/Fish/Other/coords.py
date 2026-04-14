# Fish/Other/coords.py
# Doubled-height helpers for the course hex grid (flat-top, odd-q).
# Also includes adapters for the teacher’s “zig-zag down” band format.
#
# Requires only a board-like object with:
#   .rows, .columns, .tiles[r][c] and each tile has .active (bool) and .occupied (optional)

from typing import List, Sequence, Tuple

__all__ = [
    "to_dh",
    "from_dh",
    "neighbors_dh_in_order",
    "raycast_reachables_dh",
    "tie_key_dh",
    "band_start_col",
    "teacher_idx_to_dh",
    "dh_to_teacher_idx",
    "pos_from_teacher",
    "pos_to_teacher",
    "board_from_teacher",
    "board_to_teacher",
]

# ── Engine (row,col) ⇄ Doubled-height (col_dh,row2_dh) ───────────────────────
# Flat-top, odd-q mapping:
#   to_dh:   col_dh  = col
#            row2_dh = 2*row + (col % 2)
#   from_dh: col     = col_dh
#            row     = (row2_dh - (col_dh % 2)) // 2


def to_dh(row: int, col: int) -> Tuple[int, int]:
    """Engine (row, col) → doubled-height (col_dh, row2_dh)."""
    col_dh = col
    row2_dh = 2 * row + (col & 1)
    return col_dh, row2_dh


def from_dh(col_dh: int, row2_dh: int) -> Tuple[int, int]:
    """Doubled-height (col_dh, row2_dh) → engine (row, col)."""
    col = col_dh
    row = (row2_dh - (col_dh & 1)) // 2
    return row, col


# ── Neighbors (spec order) and DH raycast ────────────────────────────────────


def neighbors_dh_in_order(row: int, col: int, board) -> List[Tuple[int, int]]:
    """
    Immediate neighbors around (row, col) in EXACT spec order:
      N, NE, SE, S, SW, NW.
    Returns only cells that are in-bounds, active, and unoccupied.
    """
    STEPS = [(0, -2), (1, -1), (1, 1), (0, 2), (-1, 1), (-1, -1)]
    col_dh, row2_dh = to_dh(row, col)
    out: List[Tuple[int, int]] = []
    for dx, dy in STEPS:
        c2 = col_dh + dx
        r2 = row2_dh + dy
        rr, cc = from_dh(c2, r2)
        if 0 <= rr < board.rows and 0 <= cc < board.columns:
            t = board.tiles[rr][cc]
            if getattr(t, "active", False) and getattr(t, "occupied", None) is None:
                out.append((rr, cc))
    return out


def raycast_reachables_dh(row: int, col: int, board) -> List[Tuple[int, int]]:
    """
    All straight-line destinations from (row, col) along the six DH axes
    in spec order (N, NE, SE, S, SW, NW). A ray stops at the first hole
    or occupied tile and never jumps over it.
    """
    STEPS = [(0, -2), (1, -1), (1, 1), (0, 2), (-1, 1), (-1, -1)]
    col_dh, row2_dh = to_dh(row, col)
    out: List[Tuple[int, int]] = []
    for dx, dy in STEPS:
        c2 = col_dh + dx
        r2 = row2_dh + dy
        while True:
            rr, cc = from_dh(c2, r2)
            if not (0 <= rr < board.rows and 0 <= cc < board.columns):
                break
            tile = board.tiles[rr][cc]
            if not getattr(tile, "active", False):
                break
            if getattr(tile, "occupied", None) is not None:
                break
            out.append((rr, cc))
            c2 += dx
            r2 += dy
    return out


# ── Tie-break key (engine coords) ────────────────────────────────────────────


def tie_key_dh(
    from_rc: Tuple[int, int], to_rc: Tuple[int, int]
) -> Tuple[int, int, int, int]:
    """
    Sort key for ties: lower is better.
    (from_row, from_col, to_row, to_col), all ascending.
    """
    fr, fc = from_rc
    tr, tc = to_rc
    return (fr, fc, tr, tc)


# ── Teacher “zig-zag down” bands layered on DH ───────────────────────────────
# A teacher row is a DH band identified by row2_dh.
# Valid cells in that band satisfy: col_dh % 2 == row2_dh % 2.
# Scanning a band left→right for row2_dh = 0,1,2,… produces the visual zig-zag.


def band_start_col(row2_dh: int) -> int:
    """First valid DH column in this band. Equals row2_dh % 2."""
    return row2_dh & 1


def teacher_idx_to_dh(row2_dh: int, idx: int) -> Tuple[int, int]:
    """Teacher (row2_dh, idx) → DH (col_dh, row2_dh)."""
    return band_start_col(row2_dh) + 2 * idx, row2_dh


def dh_to_teacher_idx(col_dh: int, row2_dh: int) -> Tuple[int, int]:
    """DH (col_dh, row2_dh) → Teacher (row2_dh, idx)."""
    start = band_start_col(row2_dh)
    if (col_dh - start) % 2 != 0:
        raise ValueError("Not a valid teacher cell in this band.")
    idx = (col_dh - start) // 2
    return row2_dh, idx


def pos_from_teacher(row2_dh: int, idx: int) -> Tuple[int, int]:
    """Teacher position → engine (row, col)."""
    col_dh, r2 = teacher_idx_to_dh(row2_dh, idx)
    return from_dh(col_dh, r2)


def pos_to_teacher(row: int, col: int) -> Tuple[int, int]:
    """Engine (row, col) → teacher position (row2_dh, idx)."""
    col_dh, row2_dh = to_dh(row, col)
    return dh_to_teacher_idx(col_dh, row2_dh)


# ── Teacher board (ragged) ⇄ engine fish grid (rectangular) ─────────────────


def board_from_teacher(teacher_rows: Sequence[Sequence[int]]) -> List[List[int]]:
    """
    Convert ragged teacher rows (one band per row2_dh) to a rectangular
    engine fish grid. Every teacher cell maps to exactly one engine cell.
    """
    cells: List[Tuple[int, int, int]] = []
    max_row = -1
    max_col = -1
    for row2_dh, band in enumerate(teacher_rows):
        start = band_start_col(row2_dh)
        for idx, fish in enumerate(band):
            col_dh = start + 2 * idx
            r, c = from_dh(col_dh, row2_dh)
            cells.append((r, c, fish))
            if r > max_row:
                max_row = r
            if c > max_col:
                max_col = c
    rows = max_row + 1 if max_row >= 0 else 0
    cols = max_col + 1 if max_col >= 0 else 0
    grid = [[0] * cols for _ in range(rows)]
    for r, c, fish in cells:
        grid[r][c] = fish
    return grid


def board_to_teacher(engine_grid: List[List[int]]) -> List[List[int]]:
    """
    Convert a rectangular engine fish grid into ragged teacher rows.
    Produces one band for each row2_dh, then trims trailing all-zero bands.
    """
    if not engine_grid:
        return []
    rows = len(engine_grid)
    cols = len(engine_grid[0])
    teacher: List[List[int]] = []
    for row2_dh in range(2 * rows):
        start = band_start_col(row2_dh)
        max_idx = (cols - 1 - start) // 2 if cols > start else -1
        band = [0] * (max_idx + 1) if max_idx >= 0 else []
        for col in range(start, cols, 2):
            row = (row2_dh - (col & 1)) // 2
            if 0 <= row < rows:
                idx = (col - start) // 2
                band[idx] = engine_grid[row][col]
        teacher.append(band)
    while teacher and (not teacher[-1] or all(v == 0 for v in teacher[-1])):
        teacher.pop()
    return teacher
