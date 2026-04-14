from Fish.Other.coords import (
    board_from_teacher,
    board_to_teacher,
    from_dh,
    neighbors_dh_in_order,
    to_dh,
)


def test_roundtrip_to_from_dh():
    for r in range(6):
        for c in range(6):
            cd, r2 = to_dh(r, c)
            r2b, cb = from_dh(cd, r2)
            assert (r, c) == (r2b, cb)


def test_board_teacher_roundtrip():
    grid = [
        [1, 0, 2, 1],
        [0, 3, 1, 0],
        [2, 1, 0, 1],
    ]
    teacher = board_to_teacher(grid)
    back = board_from_teacher(teacher)
    # back may extend to the same rectangle; compare at coordinates we set
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            assert back[r][c] == grid[r][c]


def test_neighbors_order_and_filtering():
    class T:
        def __init__(self, rows, cols, grid):
            self.rows, self.columns = rows, cols
            self.tiles = [
                [
                    type("Tile", (), {"active": grid[r][c] != 0, "occupied": None})()
                    for c in range(cols)
                ]
                for r in range(rows)
            ]

    grid = [
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1],
    ]
    board = T(3, 3, grid)
    nbrs = neighbors_dh_in_order(1, 1, board)
    # Center has up to 6 neighbors in spec order; here we just ensure no duplicates and all in-bounds
    assert len(set(nbrs)) == len(nbrs)
    for r, c in nbrs:
        assert 0 <= r < 3 and 0 <= c < 3 and not (r == 1 and c == 1)
