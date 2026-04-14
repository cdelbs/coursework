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
    grid = [[fish for _ in cols*[1]] for _ in range(rows)]
    for r, c in holes:
        grid[r][c] = 0
    return GameBoard(rows, cols, board_data=grid)

def test_eliminate_on_exception_during_move_and_finish():
    class BoomLater(InstantPlayer):
        calls = 0
        def propose_move(self, state):
            BoomLater.calls += 1
            if BoomLater.calls == 1:
                return super().propose_move(state)
            raise RuntimeError("explode")

    board = engine_board(4, 4, fish=1)
    ref = Referee(board, [InstantPlayer(name="0"), BoomLater(name="1")])
    result = ref.run()
    assert any(e["pid"] == "1" for e in result["eliminated"])
    assert result["phase"] in ("Move", "GameOver")
