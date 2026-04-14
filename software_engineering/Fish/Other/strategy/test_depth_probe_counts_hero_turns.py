import pytest
from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Common.game_tree import GameTree
from Fish.Player.strategy import Strategy

def build_open_state():
    # 5x5 fully active, 1 fish everywhere
    data = [[1]*5 for _ in range(5)]
    b = GameBoard(rows=5, columns=5, board_data=data)
    s = GameState(b, [Player(1), Player(2)], phase="Initialization", turn_num=0)

    # Place all 4 penguins per player, alternating, all on legal tiles
    s.place_avatar(1, 0, 0)
    s.place_avatar(2, 4, 4)
    s.place_avatar(1, 0, 2)
    s.place_avatar(2, 4, 2)
    s.place_avatar(1, 2, 0)
    s.place_avatar(2, 2, 4)
    s.place_avatar(1, 2, 2)
    s.place_avatar(2, 3, 3)

    # Move phase begins with P1
    s.phase = "Move"
    s.current_turn = 0
    return s

def test_depth_counts_hero_turns(monkeypatch):
    """
    Depth counts only hero turns.
    The depth parameter controls how many hero turns to look ahead.
    When _search is called, it records the current hero_turns_left value.
    """
    seen = []

    orig = Strategy._search
    def probe(self, tree, node, hero_pid, hero_turns_left, alpha=0, beta=0):
        st = node.state
        is_hero = (st.turn_order[st.current_turn] == hero_pid)
        seen.append((hero_turns_left, is_hero))
        return orig(self, tree, node, hero_pid, hero_turns_left, alpha, beta)

    monkeypatch.setattr(Strategy, "_search", probe, raising=True)

    # Depth 1: choose_move calls _search(child, hero, 0) on each root child
    # Those children have hero_turns_left=0, so _search immediately returns utility
    s1 = build_open_state()
    seen.clear()
    Strategy(depth_hero_turns=1).choose_move(GameTree(s1))
    # Verify that _search was called at least once (should be called on opponent children)
    assert len(seen) > 0, "Expected _search to be called at least once"
    # All calls should be with hero_turns_left=0 since depth=1 means depth-1=0
    levels_seen = {lvl for (lvl, _) in seen}
    assert levels_seen == {0}, f"Expected only level 0, but saw {levels_seen}"

    # Depth 3: should see deeper recursion
    s3 = build_open_state()
    seen.clear()
    Strategy(depth_hero_turns=3).choose_move(GameTree(s3))
    hero_levels = {lvl for (lvl, is_hero) in seen if is_hero}
    opp_levels = {lvl for (lvl, is_hero) in seen if not is_hero}
    # Hero should be seen at levels 2 and 1 (possibly 0)
    assert 2 in hero_levels or 1 in hero_levels, f"Expected hero at levels 2 or 1, got {hero_levels}"
    # Opponent should be seen at level 2 (first recursive call from root)
    assert 2 in opp_levels, f"Expected opponent at level 2, got {opp_levels}"
