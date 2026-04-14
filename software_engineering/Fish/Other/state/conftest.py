"""Shared fixtures and utilities for GameState tests."""
import pytest
from Common.gameboard import GameBoard
from Common.state import GameState, Player, Penguin


# ---- Test Fixtures ----


@pytest.fixture
def simple_board():
    """Fixture providing a small 4x4 uniform board."""
    return GameBoard(rows=4, columns=4).with_uniform_fish(2)


@pytest.fixture
def default_board():
    """Fixture providing default 5x5 board."""
    return GameBoard(rows=5, columns=5).with_uniform_fish(3)


@pytest.fixture
def two_players():
    """Fixture providing two basic players."""
    return [Player(1), Player(2)]


@pytest.fixture
def three_players():
    """Fixture providing three basic players."""
    return [Player(1), Player(2), Player(3)]


@pytest.fixture
def four_players():
    """Fixture providing four basic players."""
    return [Player(1), Player(2), Player(3), Player(4)]


@pytest.fixture
def simple_game(simple_board, two_players):
    """Fixture providing a simple game in initialization phase."""
    return GameState(simple_board, two_players, "Initialization", 0)


# ---- Utility Functions ----


def get_current_player_id(game_state):
    """Get the current player's ID from the game state."""
    return game_state.players[game_state.turn_order[game_state.current_turn]].pid


def get_current_player(game_state):
    """Get the current player object from the game state."""
    pid = get_current_player_id(game_state)
    return next(p for p in game_state.players if p.pid == pid)


def force_move_phase(game_state):
    """Force game into move phase (helper for testing)."""
    game_state.phase = "Move"
    # Ensure all penguins are placed
    for player in game_state.players:
        for penguin in player.penguins:
            if not penguin.placed:
                penguin.placed = True


def count_placed_penguins(game_state):
    """Count total placed penguins across all players."""
    return sum(
        1
        for player in game_state.players
        for penguin in player.penguins
        if penguin.placed
    )


def count_active_penguins(player):
    """Count active (placed and not fallen) penguins for a player."""
    return len(player.active_penguins())


def get_player_by_id(game_state, pid):
    """Get a player by their ID."""
    return next((p for p in game_state.players if p.pid == pid), None)


def all_penguins_placed(game_state):
    """Check if all penguins have been placed."""
    return all(not p.has_unplaced_penguins() for p in game_state.players)


def find_empty_tile(board):
    """Find first empty active tile on the board."""
    for r in range(board.rows):
        for c in range(board.columns):
            tile = board.tiles[r][c]
            if tile.active and tile.occupied is None:
                return (r, c)
    return None


def place_all_penguins_sequentially(game_state):
    """Place all penguins in turn order for testing."""
    while game_state.phase == "Placement":
        pid = get_current_player_id(game_state)
        empty_pos = find_empty_tile(game_state.board)
        if empty_pos:
            r, c = empty_pos
            game_state.place_avatar(pid, r, c)
        else:
            break
