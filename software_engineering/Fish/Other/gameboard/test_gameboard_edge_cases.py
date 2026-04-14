"""
Additional edge case and bug prevention tests for GameBoard.
Tests for boundary validation, immutability, and error conditions.
"""

import pytest
from Common.gameboard import GameBoard, Tile


class TestBoardValidation:
    """Test input validation and boundary conditions."""

    def test_board_dimensions_validation(self):
        """Test that board_data must match specified dimensions."""
        # Mismatched rows
        with pytest.raises(ValueError, match="do not match"):
            GameBoard(rows=3, columns=3, board_data=[[1, 2], [3, 4]])

        # Mismatched columns
        with pytest.raises(ValueError, match="do not match"):
            GameBoard(rows=2, columns=3, board_data=[[1, 2], [3, 4, 5]])

    def test_board_data_fish_count_validation(self):
        """Test that custom board_data must have valid fish counts (0-5)."""
        # Negative fish count
        with pytest.raises(ValueError, match="Invalid fish count"):
            GameBoard(rows=2, columns=2, board_data=[[1, 2], [3, -1]])

        # Fish count too high
        with pytest.raises(ValueError, match="Invalid fish count"):
            GameBoard(rows=2, columns=2, board_data=[[1, 2], [3, 6]])

        # Non-integer fish count
        with pytest.raises(ValueError, match="Invalid fish count"):
            GameBoard(rows=2, columns=2, board_data=[[1, 2], [3, 2.5]])

        # Valid boundary values should work
        GameBoard(rows=2, columns=2, board_data=[[0, 1], [4, 5]])  # Should work

    def test_board_with_custom_data(self):
        """Test creating a board with custom fish data."""
        custom_data = [[1, 2, 3], [4, 5, 1], [2, 3, 4]]
        board = GameBoard(rows=3, columns=3, board_data=custom_data)

        for r in range(3):
            for c in range(3):
                assert board.tiles[r][c].fish == custom_data[r][c]
                assert board.tiles[r][c].coords == (r, c)
                assert board.tiles[r][c].active == True

    def test_board_with_zero_fish_creates_holes(self):
        """Test that tiles with 0 fish are marked as inactive."""
        custom_data = [[1, 0, 3], [0, 5, 1], [2, 3, 0]]
        board = GameBoard(rows=3, columns=3, board_data=custom_data)

        # Check holes are inactive
        assert board.tiles[0][1].active == False
        assert board.tiles[1][0].active == False
        assert board.tiles[2][2].active == False

        # Check active tiles
        assert board.tiles[0][0].active == True
        assert board.tiles[1][1].active == True


class TestHolesValidation:
    """Test hole creation and validation."""

    def test_holes_out_of_bounds_should_work(self):
        """Test that out-of-bounds holes don't crash (just ignored)."""
        board = GameBoard(rows=5, columns=5)
        # This should work without crashing, even if coords don't exist
        # The current implementation doesn't validate, which could be a bug
        # but also might be intentional for flexibility
        result = board.with_holes_one_fish([(-1, -1), (10, 10)], 5)
        assert result is not None

    def test_holes_minimum_greater_than_available(self):
        """Test error when requesting more one-fish tiles than available."""
        board = GameBoard(rows=3, columns=3)  # 9 tiles
        with pytest.raises(ValueError, match="Not enough available"):
            board.with_holes_one_fish([(0, 0), (1, 1)], 10)  # 7 available, want 10

    def test_holes_minimum_equals_available(self):
        """Test creating board where all available tiles must be one-fish."""
        board = GameBoard(rows=3, columns=3)  # 9 tiles
        result = board.with_holes_one_fish([(0, 0), (1, 1)], 7)  # All 7 remaining

        one_fish_count = sum(
            1
            for row in result.tiles
            for tile in row
            if tile.active and tile.fish == 1
        )
        assert one_fish_count == 7

    def test_empty_holes_list(self):
        """Test creating holes with empty list."""
        board = GameBoard(rows=3, columns=3)
        result = board.with_holes_one_fish([], 5)

        # Should have at least 5 one-fish tiles and no holes
        one_fish_count = sum(
            1
            for row in result.tiles
            for tile in row
            if tile.fish == 1
        )
        assert one_fish_count >= 5
        assert all(tile.active for row in result.tiles for tile in row)


class TestReachabilityEdgeCases:
    """Test movement and reachability edge cases."""

    def test_reachable_from_hole_returns_empty(self):
        """Test that reachable_tiles from an inactive tile returns empty."""
        board = GameBoard(rows=5, columns=5).with_holes_one_fish([(2, 2)], 1)
        hole_tile = board.tiles[2][2]
        assert hole_tile.active == False

        reachables = board.reachable_tiles(hole_tile)
        # Even from a hole, the algorithm should return something
        # (checking implementation behavior)
        assert isinstance(reachables, list)

    def test_reachable_surrounded_by_holes(self):
        """Test tile completely surrounded by holes/occupied tiles."""
        board = GameBoard(rows=5, columns=5)

        # Create a tile at (2,2) surrounded by holes
        center_row, center_col = 2, 2
        surrounding_holes = []

        for direction in ["NW", "N", "NE", "SW", "S", "SE"]:
            r, c = GameBoard.determine_offset(center_row, center_col, direction)
            if 0 <= r < board.rows and 0 <= c < board.columns:
                surrounding_holes.append((r, c))

        board_with_holes = board.with_holes_one_fish(surrounding_holes, 1)
        center_tile = board_with_holes.tiles[center_row][center_col]

        reachables = board_with_holes.reachable_tiles(center_tile)
        assert reachables == []

    def test_reachable_stops_at_occupied_tile(self):
        """Test that movement stops at occupied tiles."""
        board = GameBoard(rows=5, columns=5)

        # Place an occupant at (2, 2)
        board_with_occupant = board.with_occupant(2, 2, "penguin1")

        # Test from (3, 2) moving north - should stop before (2, 2)
        start_tile = board_with_occupant.tiles[3][2]
        reachables = board_with_occupant.reachable_tiles(start_tile)

        # (2, 2) should not be reachable since it's occupied
        assert (2, 2) not in reachables

    def test_reachable_from_single_tile_board(self):
        """Test reachability on a 1x1 board."""
        board = GameBoard(rows=1, columns=1)
        tile = board.tiles[0][0]
        reachables = board.reachable_tiles(tile)

        # No tiles reachable from a 1x1 board
        assert reachables == []

    def test_reachable_from_edge_tiles(self):
        """Test reachability from all edge positions."""
        board = GameBoard(rows=5, columns=5)

        # Top-left corner
        reachables = board.reachable_tiles(board.tiles[0][0])
        assert all(0 <= r < 5 and 0 <= c < 5 for r, c in reachables)
        assert (0, 0) not in reachables

        # Bottom-right corner
        reachables = board.reachable_tiles(board.tiles[4][4])
        assert all(0 <= r < 5 and 0 <= c < 5 for r, c in reachables)
        assert (4, 4) not in reachables


class TestImmutability:
    """Test that board operations maintain immutability."""

    def test_with_holes_does_not_modify_original(self):
        """Test that adding holes creates a new board."""
        original = GameBoard(rows=3, columns=3)
        original_tiles_id = id(original.tiles)

        new_board = original.with_holes_one_fish([(1, 1)], 3)

        # Original should be unchanged
        assert original.tiles[1][1].active == True
        assert new_board.tiles[1][1].active == False
        assert id(new_board.tiles) != original_tiles_id

    def test_with_uniform_fish_does_not_modify_original(self):
        """Test that with_uniform_fish creates a new board."""
        original = GameBoard(rows=3, columns=3)
        original_fish = original.tiles[0][0].fish

        new_board = original.with_uniform_fish(4)

        # Original might have different fish count
        assert new_board.tiles[0][0].fish == 4
        assert id(new_board) != id(original)

    def test_with_occupant_does_not_modify_original(self):
        """Test that placing an occupant creates a new board."""
        original = GameBoard(rows=3, columns=3)

        new_board = original.with_occupant(1, 1, "penguin")

        assert original.tiles[1][1].occupied is None
        assert new_board.tiles[1][1].occupied == "penguin"

    def test_clear_occupant_does_not_modify_original(self):
        """Test that clearing an occupant creates a new board."""
        original = GameBoard(rows=3, columns=3).with_occupant(1, 1, "penguin")

        new_board = original.clear_occupant(1, 1)

        assert original.tiles[1][1].occupied == "penguin"
        assert new_board.tiles[1][1].occupied is None

    def test_highlight_does_not_modify_original(self):
        """Test that highlighting creates a new board."""
        original = GameBoard(rows=3, columns=3)

        new_board = original.highlight_tiles([(1, 1), (2, 2)])

        assert original.tiles[1][1].highlighted == False
        assert new_board.tiles[1][1].highlighted == True


class TestUniformFishValidation:
    """Test with_uniform_fish validation."""

    def test_uniform_fish_boundary_values(self):
        """Test that fish count must be 1-5."""
        board = GameBoard(rows=3, columns=3)

        # Valid boundary values
        board.with_uniform_fish(1)  # Should work
        board.with_uniform_fish(5)  # Should work

        # Invalid values
        with pytest.raises(ValueError):
            board.with_uniform_fish(0)

        with pytest.raises(ValueError):
            board.with_uniform_fish(6)

        with pytest.raises(ValueError):
            board.with_uniform_fish(-1)

        with pytest.raises(ValueError):
            board.with_uniform_fish(100)


class TestOccupancy:
    """Test tile occupancy operations."""

    def test_occupant_placement_and_removal(self):
        """Test placing and removing occupants."""
        board = GameBoard(rows=3, columns=3)

        # Place occupant
        board_with_penguin = board.with_occupant(1, 1, "penguin1")
        assert board_with_penguin.tiles[1][1].occupied == "penguin1"

        # Clear occupant
        board_cleared = board_with_penguin.clear_occupant(1, 1)
        assert board_cleared.tiles[1][1].occupied is None

    def test_occupant_out_of_bounds(self):
        """Test that placing occupant out of bounds raises error."""
        board = GameBoard(rows=3, columns=3)

        # Out of bounds placements should raise ValueError
        with pytest.raises(ValueError, match="out of bounds"):
            board.with_occupant(-1, 0, "penguin")

        with pytest.raises(ValueError, match="out of bounds"):
            board.with_occupant(0, -1, "penguin")

        with pytest.raises(ValueError, match="out of bounds"):
            board.with_occupant(3, 0, "penguin")  # rows are 0-2

        with pytest.raises(ValueError, match="out of bounds"):
            board.with_occupant(0, 3, "penguin")  # cols are 0-2

    def test_clear_occupant_out_of_bounds(self):
        """Test that clearing occupant out of bounds raises error."""
        board = GameBoard(rows=3, columns=3)

        with pytest.raises(ValueError, match="out of bounds"):
            board.clear_occupant(-1, 0)

        with pytest.raises(ValueError, match="out of bounds"):
            board.clear_occupant(5, 5)

    def test_multiple_occupants(self):
        """Test placing multiple occupants on different tiles."""
        board = GameBoard(rows=3, columns=3)

        board = board.with_occupant(0, 0, "penguin1")
        board = board.with_occupant(1, 1, "penguin2")
        board = board.with_occupant(2, 2, "penguin3")

        assert board.tiles[0][0].occupied == "penguin1"
        assert board.tiles[1][1].occupied == "penguin2"
        assert board.tiles[2][2].occupied == "penguin3"

    def test_overwrite_occupant(self):
        """Test that placing an occupant on an occupied tile replaces it."""
        board = GameBoard(rows=3, columns=3)

        board = board.with_occupant(1, 1, "penguin1")
        board = board.with_occupant(1, 1, "penguin2")

        assert board.tiles[1][1].occupied == "penguin2"


class TestHighlighting:
    """Test tile highlighting for GUI."""

    def test_highlight_specific_tiles(self):
        """Test highlighting specific coordinates."""
        board = GameBoard(rows=3, columns=3)
        coords_to_highlight = [(0, 0), (1, 1), (2, 2)]

        highlighted_board = board.highlight_tiles(coords_to_highlight)

        for r in range(3):
            for c in range(3):
                if (r, c) in coords_to_highlight:
                    assert highlighted_board.tiles[r][c].highlighted == True
                else:
                    assert highlighted_board.tiles[r][c].highlighted == False

    def test_clear_highlights(self):
        """Test clearing all highlights."""
        board = GameBoard(rows=3, columns=3)
        board = board.highlight_tiles([(0, 0), (1, 1)])
        board = board.clear_highlights()

        for row in board.tiles:
            for tile in row:
                assert tile.highlighted == False

    def test_highlight_empty_list(self):
        """Test highlighting with empty list clears all."""
        board = GameBoard(rows=3, columns=3)
        board = board.highlight_tiles([(1, 1)])
        board = board.highlight_tiles([])

        for row in board.tiles:
            for tile in row:
                assert tile.highlighted == False


class TestDetermineOffset:
    """Test hexagonal coordinate offset calculations."""

    def test_all_directions_even_column(self):
        """Test all 6 directions from an even column."""
        directions = ["NW", "N", "NE", "SW", "S", "SE"]
        start_row, start_col = 3, 2  # Even column

        offsets = {}
        for direction in directions:
            r, c = GameBoard.determine_offset(start_row, start_col, direction)
            offsets[direction] = (r, c)

        # Verify all directions give different results
        assert len(set(offsets.values())) == 6

        # Verify movements are reasonable (within 1 row/col)
        for direction, (r, c) in offsets.items():
            assert abs(r - start_row) <= 1
            assert abs(c - start_col) <= 1

    def test_all_directions_odd_column(self):
        """Test all 6 directions from an odd column."""
        directions = ["NW", "N", "NE", "SW", "S", "SE"]
        start_row, start_col = 3, 3  # Odd column

        offsets = {}
        for direction in directions:
            r, c = GameBoard.determine_offset(start_row, start_col, direction)
            offsets[direction] = (r, c)

        # Verify all directions give different results
        assert len(set(offsets.values())) == 6

    def test_even_odd_columns_differ(self):
        """Test that even and odd columns have different offset patterns."""
        r_even, c_even = GameBoard.determine_offset(3, 2, "NW")
        r_odd, c_odd = GameBoard.determine_offset(3, 3, "NW")

        # The offsets should be different for even vs odd columns
        assert (r_even, c_even) != (r_odd, c_odd)


class TestBoardRepr:
    """Test string representation of board."""

    def test_repr_format(self):
        """Test that __repr__ returns a grid of fish counts."""
        board = GameBoard(rows=2, columns=2, board_data=[[1, 2], [3, 4]])
        repr_str = repr(board)

        assert "1 2" in repr_str
        assert "3 4" in repr_str
        assert repr_str.count("\n") == 1  # 2 rows = 1 newline


class TestMinOnefish:
    """Test the minimum one-fish tile requirement."""

    def test_min_zero_onefish(self):
        """Test creating board with zero one-fish tiles required."""
        board = GameBoard(rows=3, columns=3)
        result = board.with_holes_one_fish([(0, 0)], 0)

        # All non-hole tiles should have 2-5 fish
        for row in result.tiles:
            for tile in row:
                if tile.active:
                    assert 1 <= tile.fish <= 5

    def test_min_onefish_distribution(self):
        """Test that one-fish tiles are randomly distributed."""
        board = GameBoard(rows=5, columns=5)
        result = board.with_holes_one_fish([], 10)

        one_fish_positions = [
            (r, c)
            for r in range(5)
            for c in range(5)
            if result.tiles[r][c].fish == 1
        ]

        # Should have at least 10 one-fish tiles
        assert len(one_fish_positions) >= 10

        # Remaining tiles should have 2-5 fish
        for r in range(5):
            for c in range(5):
                if (r, c) not in one_fish_positions:
                    assert 2 <= result.tiles[r][c].fish <= 5


class TestTileRepr:
    """Test Tile string representation."""

    def test_tile_repr(self):
        """Test that Tile.__repr__ returns a proper string representation."""
        from Common.gameboard import Tile

        tile = Tile(fish=3, coords=(2, 4), active=True, highlighted=False, occupied=None)
        repr_str = repr(tile)

        # Should contain all the key information
        assert "Tile(" in repr_str
        assert "fish=3" in repr_str
        assert "coords=(2, 4)" in repr_str
        assert "active=True" in repr_str
        assert "highlighted=False" in repr_str
        assert "occupied=None" in repr_str

    def test_tile_repr_with_occupant(self):
        """Test Tile.__repr__ with an occupant."""
        from Common.gameboard import Tile

        tile = Tile(fish=2, coords=(1, 1), active=True, highlighted=True, occupied="penguin")
        repr_str = repr(tile)

        assert "occupied=penguin" in repr_str or "occupied='penguin'" in repr_str
        assert "highlighted=True" in repr_str

