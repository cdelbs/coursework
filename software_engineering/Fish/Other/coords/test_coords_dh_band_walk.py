# Fish/Other/test_coords_dh_band_walk.py
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FISH = os.path.dirname(HERE)
if FISH not in sys.path:
    sys.path.insert(0, FISH)

from Fish.Other.coords import band_start_col, from_dh


def test_band_walk_scans_every_real_cell_once_small_board():
    rows, cols = 3, 4
    seen = set()
    for row2_dh in range(2 * rows):
        start = band_start_col(row2_dh)
        for col_dh in range(start, cols, 2):
            r, c = from_dh(col_dh, row2_dh)
            if 0 <= r < rows and 0 <= c < cols:
                seen.add((r, c))
    # every cell is visited at least once
    assert len(seen) == rows * cols
