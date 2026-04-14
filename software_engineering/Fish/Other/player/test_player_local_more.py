# Fish/Other/player/test_player_local_more.py
import os, sys, pytest

# repo path shim
HERE = os.path.dirname(os.path.abspath(__file__))          # ...\Fish\Other\player
FISH = os.path.dirname(os.path.dirname(HERE))              # ...\Fish
ROOT = os.path.dirname(FISH)
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

def test_placement_picks_first_open_after_holes():
    # board:
    # [0, 0, 1]
    # [1, 1, 1]
    board = engine_board(2, 3, fish=1, holes=[(0,0), (0,1)])
    gs = GameState(board, [EnginePlayer(0), EnginePlayer(1)], "Initialization", 0)

    lp = LocalPlayer()
    assert lp.propose_placement(gs) == (0, 2)  # first open by row-major

def test_propose_move_shape_on_small_open_board():
    # 4x4 placement to reach Move, then verify the tuple shape
    board = engine_board(4, 4, fish=1)
    gs = GameState(board, [EnginePlayer(0), EnginePlayer(1)], "Initialization", 0)

    # place 4 each (rule)
    gs.place_avatar(0,0,0); gs.place_avatar(1,0,3)
    gs.place_avatar(0,1,0); gs.place_avatar(1,1,3)
    gs.place_avatar(0,2,0); gs.place_avatar(1,2,3)
    gs.place_avatar(0,3,0); gs.place_avatar(1,3,3)
    assert gs.phase == "Move"

    tree = GameTree(gs)
    lp = LocalPlayer()
    proposal = lp.propose_move(tree)
    assert proposal is not False
    (fr, fc), (tr, tc) = proposal
    assert isinstance(fr, int) and isinstance(fc, int)
    assert isinstance(tr, int) and isinstance(tc, int)
