"""Shared fixtures and utilities for GameBoard tests."""
import pytest
from Common.gameboard import GameBoard, Tile


# ---- Test Fixtures ----


@pytest.fixture
def empty_board():
    """Fixture providing a default 5x5 board."""
    return GameBoard(rows=5, columns=5)


@pytest.fixture
def small_board():
    """Fixture providing a small 3x3 board for quick tests."""
    return GameBoard(rows=3, columns=3)


@pytest.fixture
def large_board():
    """Fixture providing a larger 7x8 board for complex tests."""
    return GameBoard(rows=7, columns=8)


@pytest.fixture
def board_with_holes(empty_board):
    """Fixture providing a board with pre-defined holes."""
    return empty_board.with_holes_one_fish([(0, 0), (2, 2), (4, 4)], 10)


@pytest.fixture
def uniform_board(empty_board):
    """Fixture providing a board with uniform 3-fish tiles."""
    return empty_board.with_uniform_fish(3)


# ---- Test Utilities ----


def count_fish(board):
    """Count total fish on a board."""
    return sum(tile.fish for row in board.tiles for tile in row)


def count_active_tiles(board):
    """Count the number of active tiles on a board."""
    return sum(1 for row in board.tiles for tile in row if tile.active)


def count_one_fish_tiles(board):
    """Count tiles with exactly 1 fish."""
    return sum(1 for row in board.tiles for tile in row if tile.fish == 1 and tile.active)


def get_tile_at(board, row, col):
    """Safely get a tile at coordinates."""
    return board.tiles[row][col]


def get_all_coords(board):
    """Get all (row, col) coordinates on the board."""
    return [(r, c) for r in range(board.rows) for c in range(board.columns)]


def get_reachable_coords(board, row, col):
    """Get reachable coordinates from a given position."""
    tile = board.tiles[row][col]
    return board.reachable_tiles(tile)
