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

def test_referee_winners_reporting_is_valid():
    board = engine_board(4, 4, fish=1)
    ref = Referee(board, [InstantPlayer(name="0"), InstantPlayer(name="1")])
    result = ref.run()
    assert isinstance(result["winners"], list) and len(result["winners"]) >= 1
    assert all(pid in ("0", "1") for pid in result["winners"])

def test_referee_skips_eliminated_seat_in_placement():
    class BadPlacer(InstantPlayer):
        def setup(self, gameState, player_id):
            return
    
        def game_over(self, gameState, player_id):
            return
        def propose_placement(self, state):
            raise RuntimeError("boom")
    board = engine_board(4, 4, fish=1)
    ref = Referee(board, [BadPlacer(name="0"), InstantPlayer(name="1")])
    result = ref.run()
    assert any(e["pid"] == "0" for e in result["eliminated"])
    assert result["phase"] in ("Move", "GameOver")

def test_referee_keeps_elims_and_scores_in_report():
    class AlwaysIllegal(LocalPlayer):
        def setup(self, gameState, player_id):
            return
    
        def game_over(self, gameState, player_id):
            return
        def propose_move(self, state):
            return ((0, 0), (0, 2))
    board = engine_board(4, 4, fish=1)
    ref = Referee(board, [InstantPlayer(name="0"), AlwaysIllegal(name="1")])
    result = ref.run()
    assert isinstance(result["scores"], list) and len(result["scores"]) == 2
    assert any(e["pid"] == "1" and "illegal move" in e["reason"] for e in result["eliminated"])
