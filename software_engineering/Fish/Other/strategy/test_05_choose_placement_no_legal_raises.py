import pytest
from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Player.strategy import Strategy

def test_choose_placement_raises_when_no_legal_tile_exists():
    # 2x2 board with all holes (0 means inactive)
    board = GameBoard(rows=2, columns=2, board_data=[
        [0, 0],
        [0, 0],
    ])
    s = GameState(board, [Player(1), Player(2)], phase="Initialization", turn_num=0)

    strat = Strategy()
    with pytest.raises(RuntimeError, match="No legal placement available"):
        strat.choose_placement(s)
