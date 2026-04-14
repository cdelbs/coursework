# Fish/Other/strategy/test_12_pass_preserves_hero_depth_5x5.py
import pytest
from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Common.game_tree import GameTree
from Fish.Player.strategy import Strategy

def build_pass_position_5x5():
    # 5x5 grid, ones are active tiles, zeros are holes
    data = [
        [1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1],
        [1, 1, 1, 0, 1],  # hole at (3,3) blocks north of (4,4)
        [1, 1, 1, 1, 1],  # we will make (4,3) blocked by occupation below
    ]
    b = GameBoard(rows=5, columns=5, board_data=data)
    s = GameState(b, [Player(1), Player(2)], phase="Initialization", turn_num=0)

    # Place just enough avatars to create the pass situation.
    # P1 has a legal move from (0,1). P2 is stuck at (4,4).
    s.place_avatar(1, 0, 1)   # P1 hero
    s.place_avatar(2, 4, 4)   # P2 at corner, north is hole (3,3)

    # Also occupy (4,3) with P1 so P2 has no legal neighbor there either.
    s.place_avatar(1, 4, 3)

    # Begin Move with P1 to move
    s.phase = "Move"
    s.current_turn = 0
    return s

def test_pass_does_not_consume_hero_depth(monkeypatch):
    s = build_pass_position_5x5()

    seen = []

    orig = Strategy._search
    def probe(self, tree, node, hero_pid, hero_turns_left, alpha=0, beta=0):
        st = node.state
        is_hero = (st.turn_order[st.current_turn] == hero_pid)
        seen.append((hero_turns_left, is_hero))
        return orig(self, tree, node, hero_pid, hero_turns_left, alpha, beta)

    monkeypatch.setattr(Strategy, "_search", probe, raising=True)

    depth = 3
    spec = Strategy(depth_hero_turns=depth).choose_move(GameTree(s))

    # We called _search on each root child with hero_turns_left == depth-1.
    # Because P2 is stuck, search should pass turn and immediately see a hero node
    # again with the SAME hero_turns_left (no decrement on pass).
    hero_levels = [lvl for (lvl, is_hero) in seen if is_hero]
    assert (depth - 1) in hero_levels

    # Sanity on action shape and legality
    assert isinstance(spec, tuple) and len(spec) == 2
    (fr, fc), (tr, tc) = spec
    assert (fr, fc) in [(0,1), (4,3)]  # hero can only move one of those penguins
