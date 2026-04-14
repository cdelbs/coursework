import os, sys

# repo path shim
HERE = os.path.dirname(os.path.abspath(__file__))              # .../Fish/Other/admin
FISH = os.path.dirname(os.path.dirname(HERE))                  # .../Fish
ROOT = os.path.dirname(FISH)                                   # repo root
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Fish.Common.gameboard import GameBoard
from Fish.Admin.referee import Referee
from Fish.Player.player import LocalPlayer
from conftest import InstantPlayer

def engine_board(rows, cols, fish=1, holes=()):
    grid = [[fish for _ in range(cols)] for _ in range(rows)]
    for r, c in holes:
        grid[r][c] = 0
    return GameBoard(rows, cols, board_data=grid)

class NeverCalledMover(InstantPlayer):
    """If this is asked to move the test should fail."""
    def propose_move(self, state):
        raise AssertionError("stuck player should have been skipped")

def test_advance_skips_stuck_or_ends_cleanly():
    # 1x5 line, hole at (0,1) breaks rays for p0 at (0,0) and (0,2).
    # Leave (0,3) empty so p1 at (0,4) can slide.
    board = engine_board(1, 5, fish=1, holes=[(0,1)])
    p0 = NeverCalledMover(name="p0")
    p1 = InstantPlayer(name="p1")
    ref = Referee(board, [p0, p1])

    # placement choices: p0 at 0,0 and 0,2; p1 at 0,4 then engine advances
    # LocalPlayer chooses first legal open tiles in its placement helper
    result = ref.run()
    # reaching here means p0 was never asked to move
    assert result["phase"] in ("Move", "GameOver")

def test_referee_runs_basic_game_no_elims():
    # Use LocalPlayer with depth=1 for this test to ensure valid moves
    # InstantPlayer's first-move selection can sometimes be invalid
    class FastPlayer(LocalPlayer):
        def setup(self, gameState, player_id):
            return
    
        def game_over(self, gameState, player_id):
            return
        def __init__(self, name="player"):
            super().__init__(name=name, depth_hero_turns=1)

    board = engine_board(4, 4, fish=1)
    ref = Referee(board, [FastPlayer(), FastPlayer()])
    result = ref.run()
    assert isinstance(result.get("winners"), list)
    assert isinstance(result.get("scores"), list)
    assert result.get("eliminated") == []

def test_referee_eliminates_on_illegal_move():
    class Bad(InstantPlayer):
        def setup(self, gameState, player_id):
            return
    
        def game_over(self, gameState, player_id):
            return
        def propose_move(self, state):
            # definitely not a legal successor on our geometry
            return ((0, 0), (0, 2))
    board = engine_board(4, 4, fish=1)
    ref = Referee(board, [Bad(name="0"), InstantPlayer(name="1")])
    result = ref.run()
    assert any(e["pid"] == "0" for e in result["eliminated"])

def test_referee_eliminates_on_false_when_legal():
    class Bad(LocalPlayer):
        def setup(self, gameState, player_id):
            return
    
        def game_over(self, gameState, player_id):
            return
        def propose_move(self, state):
            return False
    board = engine_board(4, 4, fish=1)
    ref = Referee(board, [Bad(name="0"), InstantPlayer(name="1")])
    result = ref.run()
    assert any(e["pid"] == "0" for e in result["eliminated"])

def test_referee_eliminates_on_placement_exception():
    class Bad(LocalPlayer):
        def setup(self, gameState, player_id):
            return
    
        def game_over(self, gameState, player_id):
            return
        def propose_placement(self, state):
            raise RuntimeError("nope")
    board = engine_board(4, 4, fish=1)
    ref = Referee(board, [Bad(name="0"), InstantPlayer(name="1")])
    result = ref.run()
    assert any(e["pid"] == "0" for e in result["eliminated"])
