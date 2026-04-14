"""Comprehensive tests for GameBoard tile reachability."""
import pytest
from Common.gameboard import GameBoard
from conftest import get_reachable_coords


class TestReachabilityBasics:
    """Test basic reachability functionality."""

    def test_reachable_tiles_all_six_directions(self, large_board):
        """Test that reachable_tiles explores all 6 hex directions."""
        # Use central tile (3,4) on 7x8 board for maximum reach
        tile = large_board.tiles[3][4]
        reachables = large_board.reachable_tiles(tile)

        # Verify all 6 directions are explored
        # N Path
        assert (0, 4) in reachables
        assert (1, 4) in reachables
        assert (2, 4) in reachables
        # S Path
        assert (4, 4) in reachables
        assert (5, 4) in reachables
        assert (6, 4) in reachables
        # NW Path
        assert (2, 3) in reachables
        assert (2, 2) in reachables
        assert (1, 1) in reachables
        assert (1, 0) in reachables
        # NE Path
        assert (2, 5) in reachables
        assert (2, 6) in reachables
        assert (1, 7) in reachables
        # SW Path
        assert (3, 3) in reachables
        assert (4, 2) in reachables
        assert (4, 1) in reachables
        assert (5, 0) in reachables
        # SE Path
        assert (3, 5) in reachables
        assert (4, 6) in reachables
        assert (4, 7) in reachables
        # Does not include self
        assert (3, 4) not in reachables

    def test_reachable_does_not_include_self(self, empty_board):
        """Test that reachable tiles never include the starting tile."""
        for r in range(empty_board.rows):
            for c in range(empty_board.columns):
                tile = empty_board.tiles[r][c]
                reachables = empty_board.reachable_tiles(tile)
                assert (r, c) not in reachables

    def test_reachable_stays_in_bounds(self, empty_board):
        """Test that all reachable coordinates are within board bounds."""
        # Test from corner (most likely to go out of bounds)
        tile = empty_board.tiles[0][0]
        reachables = empty_board.reachable_tiles(tile)

        for r, c in reachables:
            assert 0 <= r < empty_board.rows
            assert 0 <= c < empty_board.columns


class TestReachabilityWithHoles:
    """Test reachability when board has holes."""

    def test_reachable_stops_at_holes(self):
        """Test that movement stops at holes in all directions."""
        board = GameBoard().with_holes_one_fish([(0, 3), (5, 3), (2, 4), (3, 5)], 1)
        tile = board.tiles[2][3]
        reachables = board.reachable_tiles(tile)

        # NW path works
        assert (2, 2) in reachables
        assert (1, 1) in reachables
        assert (1, 0) in reachables

        # N path stops at hole (0, 3)
        assert (1, 3) in reachables
        assert (0, 3) not in reachables

        # NE path stops at hole (2, 4)
        assert (2, 4) not in reachables

        # SW path works
        assert (3, 2) in reachables
        assert (3, 1) in reachables
        assert (4, 0) in reachables

        # S path stops at hole (5, 3)
        assert (3, 3) in reachables
        assert (4, 3) in reachables
        assert (5, 3) not in reachables

        # SE path stops at hole (3, 5)
        assert (3, 4) in reachables
        assert (3, 5) not in reachables

        # Should not include self
        assert (2, 3) not in reachables

    def test_reachable_from_hole_tile(self, board_with_holes):
        """Test reachability from an inactive (hole) tile."""
        hole_tile = board_with_holes.tiles[0][0]
        assert hole_tile.active == False

        reachables = board_with_holes.reachable_tiles(hole_tile)
        # Implementation returns empty list for holes
        assert isinstance(reachables, list)

    def test_reachable_surrounded_by_holes(self):
        """Test tile completely surrounded by holes has no reachable tiles."""
        board = GameBoard(rows=5, columns=5)
        center_row, center_col = 2, 2

        # Get all surrounding tiles
        surrounding_holes = []
        for direction in ["NW", "N", "NE", "SW", "S", "SE"]:
            r, c = GameBoard.determine_offset(center_row, center_col, direction)
            if 0 <= r < board.rows and 0 <= c < board.columns:
                surrounding_holes.append((r, c))

        board_with_holes = board.with_holes_one_fish(surrounding_holes, 1)
        center_tile = board_with_holes.tiles[center_row][center_col]
        reachables = board_with_holes.reachable_tiles(center_tile)

        assert reachables == []

    def test_reachable_on_empty_board(self):
        """Test that empty board (all holes) has no reachable tiles."""
        board = GameBoard()
        all_holes = [(r, c) for r in range(board.rows) for c in range(board.columns)]
        holes_board = board.with_holes_one_fish(all_holes, 0)

        tile = holes_board.tiles[0][0]
        reachables = holes_board.reachable_tiles(tile)

        assert reachables == []


class TestReachabilityWithOccupants:
    """Test reachability when tiles are occupied."""

    def test_reachable_stops_at_occupied_tile(self):
        """Test that movement stops at occupied tiles."""
        board = GameBoard(rows=7, columns=8)
        start = board.tiles[3][3]

        # Place hole two steps SE
        r1, c1 = GameBoard.determine_offset(3, 3, "SE")
        r2, c2 = GameBoard.determine_offset(r1, c1, "SE")
        if 0 <= r2 < board.rows and 0 <= c2 < board.columns:
            board = board.with_holes_one_fish([(r2, c2)], 1)

        # Place occupant one step N
        rn, cn = GameBoard.determine_offset(3, 3, "N")
        if 0 <= rn < board.rows and 0 <= cn < board.columns:
            board = board.with_occupant(rn, cn, "penguin")

        start = board.tiles[3][3]
        reachable = set(board.reachable_tiles(start))

        # Occupied tile and tiles beyond it are not reachable
        assert (rn, cn) not in reachable
        r_next, c_next = GameBoard.determine_offset(rn, cn, "N")
        if 0 <= r_next < board.rows and 0 <= c_next < board.columns:
            assert (r_next, c_next) not in reachable

        # Hole and tiles beyond it are not reachable
        assert (r2, c2) not in reachable
        r_beyond, c_beyond = GameBoard.determine_offset(r2, c2, "SE")
        if 0 <= r_beyond < board.rows and 0 <= c_beyond < board.columns:
            assert (r_beyond, c_beyond) not in reachable

    def test_reachable_stops_immediately_at_adjacent_occupant(self, small_board):
        """Test that adjacent occupied tile blocks movement."""
        # Place occupant at (1, 1)
        board = small_board.with_occupant(1, 1, "penguin")

        # Test from (0, 1) - penguin at (1,1) should block south
        tile = board.tiles[0][1]
        reachables = board.reachable_tiles(tile)

        # (1, 1) should not be reachable
        assert (1, 1) not in reachables


class TestReachabilityEdgeCases:
    """Test edge cases for reachability."""

    def test_reachable_from_single_tile_board(self):
        """Test reachability on minimal 1x1 board."""
        board = GameBoard(rows=1, columns=1)
        tile = board.tiles[0][0]
        reachables = board.reachable_tiles(tile)

        assert reachables == []

    def test_reachable_from_corners(self):
        """Test reachability from all four corners."""
        board = GameBoard(rows=5, columns=5)

        # Top-left corner
        reachables = board.reachable_tiles(board.tiles[0][0])
        assert all(0 <= r < 5 and 0 <= c < 5 for r, c in reachables)
        assert (0, 0) not in reachables

        # Top-right corner
        reachables = board.reachable_tiles(board.tiles[0][4])
        assert all(0 <= r < 5 and 0 <= c < 5 for r, c in reachables)
        assert (0, 4) not in reachables

        # Bottom-left corner
        reachables = board.reachable_tiles(board.tiles[4][0])
        assert all(0 <= r < 5 and 0 <= c < 5 for r, c in reachables)
        assert (4, 0) not in reachables

        # Bottom-right corner
        reachables = board.reachable_tiles(board.tiles[4][4])
        assert all(0 <= r < 5 and 0 <= c < 5 for r, c in reachables)
        assert (4, 4) not in reachables

    def test_reachable_from_edges(self):
        """Test reachability from edge positions."""
        board = GameBoard(rows=5, columns=5)

        # Top edge
        for c in range(5):
            reachables = board.reachable_tiles(board.tiles[0][c])
            assert all(0 <= r < 5 and 0 <= col < 5 for r, col in reachables)

        # Bottom edge
        for c in range(5):
            reachables = board.reachable_tiles(board.tiles[4][c])
            assert all(0 <= r < 5 and 0 <= col < 5 for r, col in reachables)

        # Left edge
        for r in range(5):
            reachables = board.reachable_tiles(board.tiles[r][0])
            assert all(0 <= row < 5 and 0 <= c < 5 for row, c in reachables)

        # Right edge
        for r in range(5):
            reachables = board.reachable_tiles(board.tiles[r][4])
            assert all(0 <= row < 5 and 0 <= c < 5 for row, c in reachables)
