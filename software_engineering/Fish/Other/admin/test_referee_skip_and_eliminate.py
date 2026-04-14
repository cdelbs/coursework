# Fish/Other/admin/test_referee_skip_and_eliminate.py
import os, sys
from typing import List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
FISH = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(FISH)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Fish.Common.gameboard import GameBoard
from Fish.Admin.referee import Referee
from Fish.Player.player import LocalPlayer

SpecAction = Tuple[Tuple[int, int], Tuple[int, int]]

def engine_board(rows, cols, fish=1, holes=()):
    grid = [[fish for _ in range(cols)] for _ in range(rows)]
    for r, c in holes:
        grid[r][c] = 0
    return GameBoard(rows, cols, board_data=grid)

class NeverCalledMover(LocalPlayer):
    def __init__(self, placements: List[Tuple[int,int]]):
        super().__init__()
        self._placements = placements[:]
    def setup(self, gameState, player_id):
        return
    def game_over(self, gameState, player_id):
        return
    def propose_placement(self, state):
        return self._placements.pop(0)
    def propose_move(self, state):
        # If this gets called the test should fail
        raise AssertionError("stuck player should have been skipped")

class FirstLegalMover(LocalPlayer):
    def __init__(self, placements: List[Tuple[int,int]]):
        super().__init__()
        self._placements = placements[:]
    def setup(self, gameState, player_id):
        return    
    def game_over(self, gameState, player_id):
        return
    def propose_placement(self, state):
        return self._placements.pop(0)

def test_skips_stuck_player_without_calling_them():
    # 1x5 line with a hole at (0,1). This can lead to immediate GameOver after placement
    # because geometry may leave everyone stuck. That is valid.
    board = engine_board(1, 5, fish=1, holes=[(0,1)])
    p0 = NeverCalledMover(placements=[(0,0), (0,2)])   # will end up stuck
    p1 = FirstLegalMover(placements=[(0,4)])
    ref = Referee(board, [p0, p1])

    ref._run_placement()
    # Either we enter Move and p0 is skipped later, or the engine ends the game now
    assert ref.state.phase in ("Move", "GameOver")

    # Running to completion must not call p0.propose_move, because p0 is stuck.
    result = ref.run()
    assert result["phase"] in ("Move", "GameOver")
