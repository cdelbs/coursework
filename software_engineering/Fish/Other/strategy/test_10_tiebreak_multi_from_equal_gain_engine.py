from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Common.game_tree import GameTree
from Fish.Player.strategy import Strategy

def test_tiebreak_multi_from_equal_gain_bigger_corridor():
    """
    Bigger corridor that forces two different FROM squares to have the same
    total maximin value at depth 2. Tie must resolve by lower FROM.
    
    Layout (1 x 9):
      cols: 0 1 2 3 4 5 6 7 8
             0 1 1 0 0 1 1 0 1

    P1 at (0,1) and (0,5). P2 at (0,8).
    Holes at 0, 3, 4, 7 isolate segments and block backtracking.

    From (0,1): only legal to (0,2) because (0,0) is a hole and (0,3) is a hole.
    From (0,5): only legal to (0,6) because (0,4) is a hole and (0,7) is a hole.
    P2 at (0,8) cannot move due to the hole at (0,7).

    With depth_hero_turns=2, either first move gives hero 1 fish now and then
    hero immediately moves again for another 1 on the other penguin. Equal total gain.
    Strategy must break the tie by choosing the lower FROM: (0,1)->(0,2).
    """
    board = GameBoard(rows=1, columns=9, board_data=[[0,1,1,0,0,1,1,0,1]])
    s = GameState(board, [Player(1), Player(2)], phase="Initialization", turn_num=0)

    # Placement order P1, P2, P1
    s.place_avatar(1, 0, 1)  # P1 A at col 1
    s.place_avatar(2, 0, 8)  # P2 at far right, isolated by hole at 7
    s.place_avatar(1, 0, 5)  # P1 B at col 5

    # Move phase starts with P1
    s.phase = "Move"
    s.current_turn = 0

    spec = Strategy(depth_hero_turns=2).choose_move(GameTree(s))
    assert spec == ((0, 1), (0, 2))
