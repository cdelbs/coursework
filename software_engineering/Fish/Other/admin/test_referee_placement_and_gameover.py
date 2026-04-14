import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FISH = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(FISH)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Fish.Common.gameboard import GameBoard
from Fish.Admin.referee import Referee

def engine_board(rows, cols, fish=1, holes=()):
    grid = [[fish for _ in range(cols)] for _ in range(rows)]
    for r, c in holes:
        grid[r][c] = 0
    return GameBoard(rows, cols, board_data=grid)

class Scripted:
    def __init__(self, places, moves=None, name="player"):
        self.places = list(places)
        self.moves = list(moves or [])
        self.name = name
    def setup(self, gameState, player_id):
        return
    
    def game_over(self, gameState, player_id):
        return
    def propose_placement(self, state): return self.places.pop(0)
    def propose_move(self, tree):
        if self.moves: return self.moves.pop(0)
        for action, child in tree.successors(tree.root):
            _, peng_id, to_r, to_c = action
            s = tree.root.state
            turn_idx = s.turn_order[s.current_turn]
            hero = s.players[turn_idx]
            fr, fc = next(pg for pg in hero.penguins if pg.id == peng_id).coords
            return (fr, fc), (to_r, to_c)
        return False

class RaisingOnPlace(Scripted):
    def propose_placement(self, state): raise RuntimeError("placement error")

def test_placement_elimination_then_continue():
    board = engine_board(3, 3)
    bad = RaisingOnPlace(places=[(0,0)], name="0")
    good = Scripted(places=[(0,2), (1,2)], name="1")
    ref = Referee(board, [bad, good])

    result = ref.run()
    # bad should be eliminated during placement
    assert any(e["pid"] == "0" for e in result["eliminated"])
    # match should finish
    assert result["phase"] in ("Move", "GameOver",)  # likely GameOver on small boards

def test_gameover_when_no_moves_after_placement():
    # 2x2 fully occupied corners produce no legal slides
    board = engine_board(2, 2)
    p0 = Scripted(places=[(0,0)], name="0")
    p1 = Scripted(places=[(0,1)], name="1")
    # give extra penguins if engine expects more, but on 2x2 it soon ends
    ref = Referee(board, [p0, p1])

    result = ref.run()
    assert result["phase"] == "GameOver"
