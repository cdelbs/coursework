from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Common.game_tree import GameTree
from Fish.Player.strategy import Strategy

def test_tiebreak_prefers_lower_from_when_utils_equal():
    # 1 x 5 corridor with a choke on the far left so P2 is stuck
    # tiles: [1, 0, 1, 1, 1]
    board = GameBoard(rows=1, columns=5, board_data=[[1, 0, 1, 1, 1]])
    s = GameState(board, [Player(1), Player(2)], phase="Initialization", turn_num=0)

    # P1 places two penguins
    s.place_avatar(1, 0, 2)   # this is the lower-from candidate
    s.place_avatar(2, 0, 0)   # P2 is stuck because (0,1) is a hole
    s.place_avatar(1, 0, 4)   # higher-from candidate

    # Move phase, P1 to act
    s.phase = "Move"
    s.current_turn = 0

    # From (0,2) and from (0,4), both can move to (0,3) with the same value.
    # Depth 2 also evaluates equal because no one has a follow-up move.
    spec = Strategy(depth_hero_turns=2).choose_move(GameTree(s))

    # Must pick the lower 'from' first, then the same 'to'
    assert spec == ((0, 2), (0, 3))
