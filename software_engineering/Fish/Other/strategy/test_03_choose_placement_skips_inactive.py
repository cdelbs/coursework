from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Player.strategy import Strategy

def test_choose_placement_skips_inactive_first_tile():
    # 2x3 with (0,0) inactive
    board = GameBoard(rows=2, columns=3, board_data=[
        [0, 1, 1],
        [1, 1, 1],
    ])
    s = GameState(board, [Player(1), Player(2)], phase="Initialization", turn_num=0)

    # Sanity: (0,0) is inactive and unoccupied
    assert s.board.tiles[0][0].active is False
    assert s.board.tiles[0][0].occupied is None

    # Strategy should choose the first active and unoccupied tile: (0,1)
    strat = Strategy()
    assert strat.choose_placement(s) == (0, 1)
