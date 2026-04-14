# Fish/Other/admin/test_referee_tree_apply.py
import os, sys
from typing import Dict, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
FISH = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(FISH)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Fish.Common.gameboard import GameBoard
from Fish.Common.game_tree import GameTree, GameTreeNode
from Fish.Admin.referee import Referee
from Fish.Player.player import LocalPlayer

SpecAction = Tuple[Tuple[int, int], Tuple[int, int]]

def engine_board(rows, cols, fish=1, holes=()):
    grid = [[fish for _ in range(cols)] for _ in range(rows)]
    for r, c in holes:
        grid[r][c] = 0
    return GameBoard(rows, cols, board_data=grid)

class FirstLegalChooser(LocalPlayer):
    def __init__(self, placements, name="player"):
        super().__init__(name=name)
        self._placements = list(placements)
    def setup(self, gameState, player_id):
        return
    
    def game_over(self, gameState, player_id):
        return
    def propose_placement(self, state):
        return self._placements.pop(0)
    def propose_move(self, state):
        # choose the first legal successor the way our Strategy would
        tree = GameTree(state)
        for action, _child in tree.successors(tree.root):
            tag, peng_id, to_r, to_c = action
            turn_idx = state.turn_order[state.current_turn]
            hero = state.players[turn_idx]
            fr, fc = next(pg for pg in hero.penguins if pg.id == peng_id).coords
            return (fr, fc), (to_r, to_c)
        return False

def map_successors_to_spec(node: GameTreeNode) -> Dict[SpecAction, GameTreeNode]:
    s = node.state
    out: Dict[SpecAction, GameTreeNode] = {}
    tree = GameTree(s)
    for action, child in tree.successors(node):
        tag, peng_id, to_r, to_c = action
        turn_idx = s.turn_order[s.current_turn]
        hero = s.players[turn_idx]
        fr, fc = next(pg for pg in hero.penguins if pg.id == peng_id).coords
        out[((fr, fc), (to_r, to_c))] = child
    return out

def test_first_proposed_move_is_from_legal_successors():
    board = engine_board(4, 4, fish=1)
    p0 = FirstLegalChooser(placements=[(0,0), (1,0), (2,0), (3,0)], name="0")
    p1 = FirstLegalChooser(placements=[(0,3), (1,3), (2,3), (3,3)], name="1")
    ref = Referee(board, [p0, p1])

    # Finish placement only
    ref._run_placement()
    assert ref.state.phase in ("Move", "GameOver")
    if ref.state.phase == "GameOver":
        # On some geometries the game can end right away; in that case nothing to check
        return

    # Build the root legal set
    root = GameTreeNode(ref.state)
    legal = set(map_successors_to_spec(root).keys())

    # Ask the current player what they will propose and assert it is legal
    proposal = ref.players[ref.state.turn_order[ref.state.current_turn]].propose_move(ref.state)
    assert proposal in legal
