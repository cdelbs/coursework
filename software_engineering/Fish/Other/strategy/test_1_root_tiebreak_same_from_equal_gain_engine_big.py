# Fish/Other/strategy/test_1_root_tiebreak_same_from_equal_gain_engine_big.py
from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Common.game_tree import GameTree
from Fish.Player.strategy import Strategy

def test_root_tiebreak_same_from_equal_gain_engine_big():
    """
    1 x 9 corridor, leftmost tile is a hole to block moving left from (0,1).
    P2 is stuck behind a double hole, so P1 will immediately move again.
    From (0,1), legal TO are exactly (0,2) and (0,3) with equal total gain.
    Tie must pick the lower TO which is (0,2).
    """
    # cols: 0 1 2 3 4 5 6 7 8
    #       0 1 1 1 1 1 0 0 1
    board = GameBoard(rows=1, columns=9, board_data=[[0,1,1,1,1,1,0,0,1]])
    s = GameState(board, [Player(1), Player(2)], phase="Initialization", turn_num=0)

    # Placement order P1, P2, P1
    s.place_avatar(1, 0, 1)  # P1 A at col 1
    s.place_avatar(2, 0, 8)  # P2 at far right, stuck by holes at 6 and 7
    s.place_avatar(1, 0, 4)  # P1 B at col 4 blocks farther right for A

    # Move phase
    s.phase = "Move"
    s.current_turn = 0

    spec = Strategy(depth_hero_turns=2).choose_move(GameTree(s))

    # From is fixed; lower TO among equal-gain moves must be (0,2)
    assert spec[0] == (0, 1)
    assert spec[1] == (0, 2)
