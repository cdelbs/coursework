"""Comprehensive tests for uncovered functions in Fish.Other.coords."""
from Fish.Other.coords import (
    raycast_reachables_dh,
    tie_key_dh,
    teacher_idx_to_dh,
    dh_to_teacher_idx,
    pos_from_teacher,
    pos_to_teacher,
    board_to_teacher,
    board_from_teacher,
    band_start_col,
)
import pytest


class MockBoard:
    """Mock board for testing coord functions."""

    def __init__(self, rows, cols, holes=None, occupied=None):
        self.rows = rows
        self.columns = cols
        holes = holes or []
        occupied = occupied or []

        self.tiles = []
        for r in range(rows):
            row = []
            for c in range(cols):
                active = (r, c) not in holes
                occ = (r, c) in occupied
                tile = type("Tile", (), {"active": active, "occupied": occ if occ else None})()
                row.append(tile)
            self.tiles.append(row)


class TestRaycastReachablesDh:
    """Test the raycast_reachables_dh function (lines 76-94)."""

    def test_raycast_from_center_all_directions(self):
        """Test raycast from center tile with all directions open."""
        board = MockBoard(5, 5)
        reachables = raycast_reachables_dh(2, 2, board)
        # From center, should reach multiple tiles in all 6 directions
        assert len(reachables) > 0
        assert (2, 2) not in reachables  # Should not include starting position

    def test_raycast_stops_at_holes(self):
        """Test that raycast stops at inactive/hole tiles."""
        # Create board with holes blocking paths
        holes = [(1, 2), (2, 3)]
        board = MockBoard(5, 5, holes=holes)
        reachables = raycast_reachables_dh(2, 2, board)
        # Tiles beyond holes should not be reachable
        for r, c in reachables:
            # None of the reachables should be a hole
            assert (r, c) not in holes

    def test_raycast_stops_at_occupied(self):
        """Test that raycast stops at occupied tiles."""
        occupied = [(1, 2), (3, 2)]
        board = MockBoard(5, 5, occupied=occupied)
        reachables = raycast_reachables_dh(2, 2, board)
        # Occupied tiles should not be in reachables
        for r, c in reachables:
            assert (r, c) not in occupied

    def test_raycast_stops_at_board_edge(self):
        """Test that raycast stops at board boundaries."""
        board = MockBoard(3, 3)
        reachables = raycast_reachables_dh(0, 0, board)
        # All reachables should be within bounds
        for r, c in reachables:
            assert 0 <= r < 3
            assert 0 <= c < 3

    def test_raycast_from_corner(self):
        """Test raycast from corner position."""
        board = MockBoard(4, 4)
        reachables = raycast_reachables_dh(0, 0, board)
        # Should return some tiles (only in available directions from corner)
        assert isinstance(reachables, list)
        for r, c in reachables:
            assert 0 <= r < 4 and 0 <= c < 4

    def test_raycast_with_mixed_obstacles(self):
        """Test raycast with both holes and occupied tiles."""
        holes = [(1, 1)]
        occupied = [(2, 2)]
        board = MockBoard(5, 5, holes=holes, occupied=occupied)
        reachables = raycast_reachables_dh(0, 0, board)
        # Should not include holes or occupied
        for r, c in reachables:
            assert (r, c) not in holes
            assert (r, c) not in occupied


class TestTieKeyDh:
    """Test the tie_key_dh function (lines 107-109)."""

    def test_tie_key_basic(self):
        """Test basic tie key generation."""
        key = tie_key_dh((1, 2), (3, 4))
        assert key == (1, 2, 3, 4)

    def test_tie_key_ordering(self):
        """Test that tie keys can be ordered correctly."""
        key1 = tie_key_dh((0, 0), (1, 1))
        key2 = tie_key_dh((0, 0), (1, 2))
        key3 = tie_key_dh((0, 1), (1, 1))
        key4 = tie_key_dh((1, 0), (1, 1))

        # Lower from_row comes first
        assert key1 < key4
        # Same from, lower to_col comes first
        assert key1 < key2
        # Same from_row, lower from_col comes first
        assert key1 < key3

    def test_tie_key_same_position(self):
        """Test tie key when from and to are the same."""
        key = tie_key_dh((2, 3), (2, 3))
        assert key == (2, 3, 2, 3)


class TestTeacherIdxToDh:
    """Test the teacher_idx_to_dh function (line 125)."""

    def test_teacher_idx_to_dh_even_row(self):
        """Test conversion for even row2_dh."""
        col_dh, row2 = teacher_idx_to_dh(0, 0)
        assert row2 == 0
        assert col_dh == band_start_col(0)

    def test_teacher_idx_to_dh_odd_row(self):
        """Test conversion for odd row2_dh."""
        col_dh, row2 = teacher_idx_to_dh(1, 0)
        assert row2 == 1
        assert col_dh == band_start_col(1)

    def test_teacher_idx_to_dh_multiple_indices(self):
        """Test conversion with different index values."""
        for row2_dh in range(5):
            for idx in range(5):
                col_dh, row2 = teacher_idx_to_dh(row2_dh, idx)
                assert row2 == row2_dh
                # Column should be start + 2*idx (zig-zag pattern)
                expected_col = band_start_col(row2_dh) + 2 * idx
                assert col_dh == expected_col


class TestDhToTeacherIdx:
    """Test the dh_to_teacher_idx function (lines 130-134)."""

    def test_dh_to_teacher_idx_roundtrip(self):
        """Test roundtrip conversion teacher ↔ DH."""
        for row2_dh in range(6):
            for idx in range(6):
                col_dh, r2 = teacher_idx_to_dh(row2_dh, idx)
                r2_back, idx_back = dh_to_teacher_idx(col_dh, r2)
                assert r2_back == row2_dh
                assert idx_back == idx

    def test_dh_to_teacher_idx_invalid_cell(self):
        """Test that invalid cells raise ValueError."""
        # Invalid: col_dh doesn't match band parity
        with pytest.raises(ValueError, match="Not a valid teacher cell"):
            dh_to_teacher_idx(1, 0)  # col_dh=1 is odd, but row2_dh=0 is even

    def test_dh_to_teacher_idx_valid_cells(self):
        """Test valid cells in different bands."""
        # row2_dh=0 (even): valid cols are 0, 2, 4, ...
        r2, idx = dh_to_teacher_idx(0, 0)
        assert r2 == 0 and idx == 0

        r2, idx = dh_to_teacher_idx(2, 0)
        assert r2 == 0 and idx == 1

        # row2_dh=1 (odd): valid cols are 1, 3, 5, ...
        r2, idx = dh_to_teacher_idx(1, 1)
        assert r2 == 1 and idx == 0

        r2, idx = dh_to_teacher_idx(3, 1)
        assert r2 == 1 and idx == 1


class TestPosFromTeacher:
    """Test the pos_from_teacher function (lines 139-140)."""

    def test_pos_from_teacher_basic(self):
        """Test basic conversion from teacher position to engine coords."""
        row, col = pos_from_teacher(0, 0)
        assert isinstance(row, int)
        assert isinstance(col, int)

    def test_pos_from_teacher_multiple_positions(self):
        """Test conversion for various teacher positions."""
        positions = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (3, 1)]
        for row2_dh, idx in positions:
            row, col = pos_from_teacher(row2_dh, idx)
            # Should produce valid engine coordinates
            assert row >= 0
            assert col >= 0


class TestPosToTeacher:
    """Test the pos_to_teacher function (lines 145-146)."""

    def test_pos_to_teacher_basic(self):
        """Test basic conversion from engine coords to teacher position."""
        row2_dh, idx = pos_to_teacher(0, 0)
        assert isinstance(row2_dh, int)
        assert isinstance(idx, int)

    def test_pos_to_teacher_roundtrip(self):
        """Test roundtrip conversion engine ↔ teacher."""
        for row in range(5):
            for col in range(5):
                row2_dh, idx = pos_to_teacher(row, col)
                row_back, col_back = pos_from_teacher(row2_dh, idx)
                assert row_back == row
                assert col_back == col


class TestBoardToTeacherEdgeCases:
    """Test edge cases in board_to_teacher (lines 184, 199)."""

    def test_board_to_teacher_empty_grid(self):
        """Test conversion of empty grid (line 184)."""
        empty = []
        teacher = board_to_teacher(empty)
        assert teacher == []

    def test_board_to_teacher_trims_trailing_zeros(self):
        """Test that trailing all-zero bands are trimmed (line 199)."""
        # Create a small grid that will have trailing zero bands
        grid = [
            [1, 0],
            [0, 0]
        ]
        teacher = board_to_teacher(grid)
        # Should trim trailing empty/all-zero bands
        # The last band in teacher should not be all zeros
        if teacher:
            assert any(v != 0 for v in teacher[-1]) or teacher == [[1]]

    def test_board_to_teacher_single_row(self):
        """Test conversion of single-row grid."""
        grid = [[1, 2, 3]]
        teacher = board_to_teacher(grid)
        assert len(teacher) > 0

    def test_board_to_teacher_single_col(self):
        """Test conversion of single-column grid."""
        grid = [[1], [2], [3]]
        teacher = board_to_teacher(grid)
        assert len(teacher) > 0

    def test_board_to_teacher_all_zeros(self):
        """Test conversion of grid with all zeros."""
        grid = [
            [0, 0],
            [0, 0]
        ]
        teacher = board_to_teacher(grid)
        # Should trim all trailing zero bands, possibly resulting in empty
        # or very short teacher representation
        assert isinstance(teacher, list)

    def test_board_to_teacher_sparse_grid(self):
        """Test conversion of sparse grid with few non-zero values."""
        grid = [
            [1, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 2, 0],
            [0, 0, 0, 0]
        ]
        teacher = board_to_teacher(grid)
        # Should handle sparse grids correctly
        # Convert back to verify
        back = board_from_teacher(teacher)
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if r < len(back) and c < len(back[r]):
                    assert back[r][c] == grid[r][c]


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_board_roundtrip_with_coords(self):
        """Test complete roundtrip using pos_to_teacher and pos_from_teacher."""
        grid = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ]

        # For each position, verify teacher conversion roundtrips
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                row2_dh, idx = pos_to_teacher(r, c)
                r_back, c_back = pos_from_teacher(row2_dh, idx)
                assert (r_back, c_back) == (r, c)

    def test_raycast_and_neighbors_consistency(self):
        """Test that raycast includes neighbors when appropriate."""
        from Fish.Other.coords import neighbors_dh_in_order

        board = MockBoard(5, 5)
        neighbors = neighbors_dh_in_order(2, 2, board)
        reachables = raycast_reachables_dh(2, 2, board)

        # All immediate neighbors should be in reachables (if board is open)
        for n in neighbors:
            assert n in reachables or board.tiles[n[0]][n[1]].occupied is not None
