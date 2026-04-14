import pytest
from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Common.game_tree import GameTree
from Fish.Player.strategy import Strategy

def test_choose_move_raises_when_hero_has_no_legal_moves():
    # 2x2 board with only (0,0) and (1,1) active
    board = GameBoard(rows=2, columns=2, board_data=[
        [1, 0],
        [0, 1],
    ])
    s = GameState(board, [Player(1), Player(2)], phase="Initialization", turn_num=0)

    # place one penguin each on the active tiles
    s.place_avatar(1, 0, 0)
    s.place_avatar(2, 1, 1)

    # enter Move with P1 to act, but P1 at (0,0) has no reachable tiles
    s.phase = "Move"
    s.current_turn = 0

    with pytest.raises(Strategy.NoLegalMoveError):
        Strategy(depth_hero_turns=2).choose_move(GameTree(s))
