# Fish/Other/strategy/test_11_depth3_diff_fish_low_holes.py
import pytest
from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Common.game_tree import GameTree
from Fish.Player.strategy import Strategy

def test_depth3_diff_fish_low_holes_root_tiebreak_on_to():
    """
    1x7 corridor, no holes. Different fish values on each tile.
    We place blockers so the hero at FROM (0,3) has exactly two legal TO squares,
    and both lines yield the same total at depth=3. Tie must pick the lower TO.

    Fish per column: [4, 2, 5, 1, 3, 2, 4]
                      0  1  2  3  4  5  6
    Placements:
      P1 at (0,3) and (0,0)
      P2 at (0,1) and (0,5)
    Legal root moves from (0,3): to (0,2) and to (0,4) only.
    Both futures end with the hero stuck after the opponent reply, so totals are equal.
    """
    board = GameBoard(rows=1, columns=7, board_data=[[4,2,5,1,3,2,4]])
    s = GameState(board, [Player(1), Player(2)], phase="Initialization", turn_num=0)

    # Place in alternating order, all on active tiles
    s.place_avatar(1, 0, 3)  # hero FROM
    s.place_avatar(2, 0, 1)  # blocks farther-left stops
    s.place_avatar(1, 0, 0)  # friendly left anchor
    s.place_avatar(2, 0, 5)  # blocks farther-right stops

    # Start Move with P1
    s.phase = "Move"
    s.current_turn = 0

    tree = GameTree(s)

    # Sanity: exactly the two expected legal actions from (0,3)
    root_legal = set()
    hero = next(p for p in s.players if p.pid == 1)
    for action, _child in tree.successors(tree.root):
        tag, peng_id, to_r, to_c = action
        if tag != "move":
            continue
        fr = next(pg for pg in hero.penguins if pg.id == peng_id).coords
        root_legal.add((fr, (to_r, to_c)))

    assert root_legal == {
        ((0, 3), (0, 2)),
        ((0, 3), (0, 4)),
    }

    # Depth=3 counts hero turns only: root move + 2 more hero turns inside the search.
    spec = Strategy(depth_hero_turns=3).choose_move(tree)

    # Tie breaker after equal gain from the same FROM picks the lower TO
    assert spec == ((0, 3), (0, 2))
