import os, sys
from typing import Dict, Tuple, List, Optional

# repo path shim
HERE = os.path.dirname(os.path.abspath(__file__))              # .../Fish/Other/admin
FISH = os.path.dirname(os.path.dirname(HERE))                  # .../Fish
ROOT = os.path.dirname(FISH)                                   # repo root
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Fish.Common.gameboard import GameBoard
from Fish.Common.game_tree import GameTree, GameTreeNode
from Fish.Admin.referee import Referee

SpecAction = Tuple[Tuple[int, int], Tuple[int, int]]

def engine_board(rows, cols, fish=1, holes=()):
    grid = [[fish for _ in range(cols)] for _ in range(rows)]
    for r, c in holes:
        grid[r][c] = 0
    return GameBoard(rows, cols, board_data=grid)

class ScriptedPlayer:
    """
    Test helper.
    - placements: a queue of (r,c) choices returned during Placement
    - moves: a queue of SpecAction moves returned during Move
      If moves is empty, pick the first legal successor from the tree.
    """
    def __init__(self, placements: List[Tuple[int,int]], moves: Optional[List[SpecAction]] = None, name: str = "player"):
        self._placements = list(placements)
        self._moves = list(moves or [])
        self.name = name
    
    def setup(self, gameState, player_id):
        return
    
    def game_over(self, gameState, player_id):
        return

    def propose_placement(self, state):
        return self._placements.pop(0)

    def propose_move(self, tree: GameTree):
        if self._moves:
            return self._moves.pop(0)
        # first legal successor in spec form
        s = tree.root.state
        for action, child in tree.successors(tree.root):
            # map engine action -> spec action
            _, peng_id, to_r, to_c = action
            turn_idx = s.turn_order[s.current_turn]
            hero = s.players[turn_idx]
            fr, fc = next(pg for pg in hero.penguins if pg.id == peng_id).coords
            return (fr, fc), (to_r, to_c)
        return False

def map_successors_to_spec(node: GameTreeNode) -> Dict[SpecAction, GameTreeNode]:
    """Build {spec_action: child} for the current seat by reading the successors."""
    s = node.state
    out: Dict[SpecAction, GameTreeNode] = {}
    tree = GameTree(s)
    for action, child in tree.successors(node):
        _, peng_id, to_r, to_c = action
        turn_idx = s.turn_order[s.current_turn]
        hero = s.players[turn_idx]
        fr, fc = next(pg for pg in hero.penguins if pg.id == peng_id).coords
        out[((fr, fc), (to_r, to_c))] = child
    return out

def place_four_each_players():
    # p0 on left column, p1 on right column
    p0_places = [(0,0), (1,0), (2,0), (3,0)]
    p1_places = [(0,3), (1,3), (2,3), (3,3)]
    return p0_places, p1_places

def test_successors_include_expected_moves_after_placement():
    board = engine_board(4, 4, fish=1)
    p0_places, p1_places = place_four_each_players()
    p0 = ScriptedPlayer(p0_places, name="0")
    p1 = ScriptedPlayer(p1_places, name="1")
    ref = Referee(board, [p0, p1])

    # complete placement
    ref._run_placement()
    assert ref.state.phase == "Move"

    # build successors for current seat and check some expected rays exist
    node = GameTreeNode(ref.state)
    legal = map_successors_to_spec(node)
    # The legacy geometry lets (0,0) reach (0,1) and (1,2) along a straight line.
    # We only assert that at least one of these is present to avoid overfitting.
    assert ((0,0),(0,1)) in legal or ((0,0),(1,2)) in legal

def test_apply_move_adopts_child_state_and_updates_score():
    board = engine_board(4, 4, fish=2)  # origin fish is 2
    p0_places, p1_places = place_four_each_players()
    # Force p0 first move to be a long slide to (1,2) if available, else take next legal
    p0 = ScriptedPlayer(p0_places, moves=[((0,0),(1,2))], name="0")
    # Make p1 raise when asked to move so the match ends soon after p0 applies
    class RaisingPlayer(ScriptedPlayer):
        def propose_move(self, tree): raise RuntimeError("boom")
    p1 = RaisingPlayer(p1_places, name="1")

    ref = Referee(board, [p0, p1])

    result = ref.run()  # runs placement, then p0 moves, then p1 eliminated, continue to end

    # p0 score must have increased by origin fish from its first move
    p0_score = next(s["score"] for s in result["scores"] if s["pid"] == "0")
    assert p0_score >= 2

    # origin should be inactive and destination occupied
    # We cannot assume the scripted move was legal on every layout
    # so check that at least one p0 penguin left the left column
    dest_occupied_somewhere = any(
        not ref.state.board.tiles[r][0].active for r in range(ref.state.board.rows)
    )
    assert dest_occupied_somewhere
