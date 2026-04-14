import os, sys, pytest

# repo path shim
HERE = os.path.dirname(os.path.abspath(__file__))          # .../Fish/Other/player
FISH = os.path.dirname(os.path.dirname(HERE))              # .../Fish
ROOT = os.path.dirname(FISH)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player as EnginePlayer
from Fish.Common.game_tree import GameTree
from Fish.Player.strategy import Strategy


def engine_board(rows, cols, fish=1, holes=()):
    # Start with a uniform active board
    grid = [[fish for _ in range(cols)] for _ in range(rows)]
    gb = GameBoard(rows, cols, board_data=grid)

    # Proper holes: deactivate those tiles and zero their fish
    for r, c in holes:
        tile = gb.tiles[r][c]
        tile.active = False
        tile.fish = 0
        tile.occupied = None

    return gb


def place_four_each(gs: GameState):
    # same pattern as other tests: p0 left col, p1 right col
    gs.place_avatar(0, 0, 0); gs.place_avatar(1, 0, 3)
    gs.place_avatar(0, 1, 0); gs.place_avatar(1, 1, 3)
    gs.place_avatar(0, 2, 0); gs.place_avatar(1, 2, 3)
    gs.place_avatar(0, 3, 0); gs.place_avatar(1, 3, 3)


def make_move_state(rows=4, cols=4, fish=1, holes=()):
    board = engine_board(rows, cols, fish=fish, holes=holes)
    gs = GameState(board, [EnginePlayer(0), EnginePlayer(1)], "Initialization", 0)
    place_four_each(gs)
    assert gs.phase == "Move"
    return gs


def test_choose_move_uses_spec_tie_break_lowest_from_then_to():
    # Uniform fish so utilities tie. For p0 at (0,0) the two earliest reachables
    # are (0,1) and (1,2). Tie break must pick ((0,0),(0,1)).
    gs = make_move_state()
    tree = GameTree(gs)
    strat = Strategy(depth_hero_turns=1)
    move = strat.choose_move(tree)
    assert move == ((0, 0), (0, 1))


def test_choose_move_raises_when_no_legal_move_for_current():
    board = engine_board(4, 4, fish=1, holes=[(0,1),(1,1),(2,1),(3,1)])
    gs = GameState(board, [EnginePlayer(0), EnginePlayer(1)], "Initialization", 0)

    gs.place_avatar(0, 0, 0); gs.place_avatar(1, 0, 3)
    gs.place_avatar(0, 1, 0); gs.place_avatar(1, 1, 3)
    gs.place_avatar(0, 2, 0); gs.place_avatar(1, 2, 3)
    gs.place_avatar(0, 3, 0); gs.place_avatar(1, 3, 3)

    assert gs.phase == "Move"

    # Force turn back to p0 so Strategy is asked to move with no legal moves
    gs.current_turn = gs.turn_order.index(0)

    tree = GameTree(gs)
    with pytest.raises(Strategy.NoLegalMoveError):
        Strategy(1).choose_move(tree)

def test_engine_skips_blocked_player_on_enter_move():
    board = engine_board(4, 4, fish=1, holes=[(0,1),(1,1),(2,1),(3,1)])
    gs = GameState(board, [EnginePlayer(0), EnginePlayer(1)], "Initialization", 0)
    gs.place_avatar(0,0,0); gs.place_avatar(1,0,3)
    gs.place_avatar(0,1,0); gs.place_avatar(1,1,3)
    gs.place_avatar(0,2,0); gs.place_avatar(1,2,3)
    gs.place_avatar(0,3,0); gs.place_avatar(1,3,3)
    assert gs.phase == "Move"
    # Since p0 is blocked, engine should have skipped to p1
    assert gs.turn_order[gs.current_turn] == 1
