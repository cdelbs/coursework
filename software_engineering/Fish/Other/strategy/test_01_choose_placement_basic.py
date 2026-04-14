from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Player.strategy import Strategy

def test_choose_placement_skips_inactive_and_picks_first_open():
    # 2x3 board where (0,0) is inactive and everything else is active
    board = GameBoard(rows=2, columns=3, board_data=[
        [0, 1, 1],
        [1, 1, 1],
    ])
    s = GameState(board, [Player(1), Player(2)], phase="Initialization", turn_num=0)
    # GameState moves to Placement during initialization, so we can call the strategy now
    strat = Strategy()
    assert strat.choose_placement(s) == (0, 1)
