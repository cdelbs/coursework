from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Common.game_tree import GameTree
from Fish.Player.strategy import Strategy

def test_tiebreak_lower_to_with_depth2_engine():
    # 1 x 5 corridor, hole at column 1 isolates P2 at (0,0)
    # board: [1, 0, 1, 1, 1]
    board = GameBoard(rows=1, columns=5, board_data=[[1, 0, 1, 1, 1]])
    s = GameState(board, [Player(1), Player(2)], phase="Initialization", turn_num=0)

    # Place P1 at (0,2). Place P2 at (0,0) which is isolated by the hole at (0,1).
    s.place_avatar(1, 0, 2)
    s.place_avatar(2, 0, 0)

    # Move phase. P1 to act.
    s.phase = "Move"
    s.current_turn = 0

    # From (0,2) P1 can go to (0,3) or (0,4).
    # Immediate gain is equal in both cases. P2 cannot move and is skipped.
    # On the second hero turn, P1 will collect a second tile either way.
    # Utilities are equal, so tie break must pick lower 'to' from the same 'from'.
    spec = Strategy(depth_hero_turns=2).choose_move(GameTree(s))
    assert spec[0] == (0, 2)     # same origin
    assert spec[1] == (0, 3)     # lower destination chosen by tie break
