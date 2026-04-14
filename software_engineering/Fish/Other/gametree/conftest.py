"""Shared fixtures for gametree tests."""
from Common.gameboard import GameBoard
from Common.state import GameState, Player


def make_test_state():
    """Create a test state in Move phase with penguins placed."""
    board_data = [
        [1, 2, 1, 3, 2],
        [2, 3, 2, 1, 1],
        [1, 1, 4, 2, 3],
        [3, 2, 1, 2, 1],
        [1, 1, 2, 1, 2],
    ]
    board = GameBoard(rows=5, columns=5, board_data=board_data)
    players = [Player(1), Player(2)]
    state = GameState(board, players, "Initialization")

    # Place penguins for both players (4 each)
    state.place_avatar(1, 0, 0)
    state.place_avatar(2, 4, 4)
    state.place_avatar(1, 0, 2)
    state.place_avatar(2, 4, 2)
    state.place_avatar(1, 2, 0)
    state.place_avatar(2, 2, 4)
    state.place_avatar(1, 1, 1)
    state.place_avatar(2, 3, 3)

    return state


def make_stuck_state():
    """Create a state where all players are stuck (no legal moves)."""
    board_data = [
        [1, 0, 1, 0, 1],
        [0, 0, 0, 0, 0],
        [1, 0, 1, 0, 1],
        [0, 0, 0, 0, 0],
        [1, 0, 1, 0, 0]
    ]
    board = GameBoard(rows=5, columns=5, board_data=board_data)
    players = [Player(1), Player(2)]
    state = GameState(board, players, "Initialization")

    # Place penguins in isolated positions
    state.place_avatar(1, 0, 0)
    state.place_avatar(2, 0, 2)
    state.place_avatar(1, 0, 4)
    state.place_avatar(2, 2, 0)
    state.place_avatar(1, 2, 2)
    state.place_avatar(2, 2, 4)
    state.place_avatar(1, 4, 0)
    state.place_avatar(2, 4, 2)

    # Should be in GameOver phase since all stuck
    return state
