# Fish/Other/player/test_player_local.py
import os, sys, pytest

# repo path shim so `from Fish...` works when you run from repo root
HERE = os.path.dirname(os.path.abspath(__file__))          # ...\Fish\Other\player
FISH = os.path.dirname(os.path.dirname(HERE))              # ...\Fish
ROOT = os.path.dirname(FISH)                               # repo root
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player as EnginePlayer
from Fish.Common.game_tree import GameTree
from Fish.Player.player import LocalPlayer

def engine_board(rows, cols, fish=1, holes=()):
    grid = [[fish for _ in range(cols)] for _ in range(rows)]
    for r, c in holes:
        grid[r][c] = 0
    return GameBoard(rows, cols, board_data=grid)

def make_move_phase_state():
    """
    Build a legal Move phase state for two players.
    Each player has four penguins per the rule.
    Use a 4x4 board and place along the left and right columns to leave lanes open.
    """
    board = engine_board(4, 4, fish=1)
    players = [EnginePlayer(0), EnginePlayer(1)]
    gs = GameState(board, players, "Initialization", 0)

    # placement order: 0,1,0,1,0,1,0,1 (four each)
    gs.place_avatar(0, 0, 0)
    gs.place_avatar(1, 0, 3)
    gs.place_avatar(0, 1, 0)
    gs.place_avatar(1, 1, 3)
    gs.place_avatar(0, 2, 0)
    gs.place_avatar(1, 2, 3)
    gs.place_avatar(0, 3, 0)
    gs.place_avatar(1, 3, 3)

    assert gs.phase == "Move"
    return gs

def test_propose_placement_uses_strategy_row_major():
    board = engine_board(2, 2, fish=1, holes=[(0,0)])
    players = [EnginePlayer(0), EnginePlayer(1)]
    gs = GameState(board, players, "Initialization", 0)

    lp = LocalPlayer()
    r, c = lp.propose_placement(gs)

    # first open tile is (0,1)
    assert (r, c) == (0, 1)

def test_propose_move_returns_spec_action_or_false():
    gs = make_move_phase_state()
    tree = GameTree(gs)
    lp = LocalPlayer()

    proposal = lp.propose_move(tree)

    if proposal is not False:
        assert isinstance(proposal, tuple)
        assert len(proposal) == 2
        (fr, fc), (tr, tc) = proposal
        assert isinstance(fr, int) and isinstance(fc, int)
        assert isinstance(tr, int) and isinstance(tc, int)

def test_propose_move_raises_if_not_move_phase():
    board = engine_board(2, 2, fish=1)
    players = [EnginePlayer(0), EnginePlayer(1)]
    gs = GameState(board, players, "Initialization", 0)

    # GameTree requires Move phase, so this should raise ValueError
    lp = LocalPlayer()
    with pytest.raises(ValueError, match="GameTree must start in the Move phase"):
        tree = GameTree(gs)
        lp.propose_move(tree)
