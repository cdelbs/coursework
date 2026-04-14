from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Common.game_tree import GameTree
from Fish.Player.strategy import Strategy

def test_tiebreak_same_gain_prefers_lower_from():
    # 1x5 corridor, all active with 1 fish
    board = GameBoard(rows=1, columns=5, board_data=[[1, 1, 1, 1, 1]])
    s = GameState(board, [Player(1), Player(2)], phase="Initialization", turn_num=0)

    # Place P1 at (0,0), P2 at (0,4), then P1 at (0,2)
    s.place_avatar(1, 0, 0)
    s.place_avatar(2, 0, 4)
    s.place_avatar(1, 0, 2)

    # Move phase with P1 to act
    s.phase = "Move"
    s.current_turn = 0

    # With depth=1, both moves earn 1 point immediately
    #   A: from (0,0) -> (0,1)
    #   B: from (0,2) -> (0,1)
    # Tie break must choose the action whose FROM is lexicographically smaller
    spec = Strategy(depth_hero_turns=1).choose_move(GameTree(s))
    assert spec == ((0, 0), (0, 1))
