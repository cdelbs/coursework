import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FISH = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(FISH)
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

def test_gameover_directly_after_placement_on_2x2():
    board = engine_board(2, 2, fish=1)
    ref = Referee(board, [InstantPlayer(), InstantPlayer()])
    result = ref.run()
    assert result["phase"] == "GameOver"
