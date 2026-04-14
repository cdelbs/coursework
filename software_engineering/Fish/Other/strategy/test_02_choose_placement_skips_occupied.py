from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Player.strategy import Strategy

def test_choose_placement_skips_occupied_tile():
    # 2x3 all active
    board = GameBoard(rows=2, columns=3, board_data=[
        [1, 1, 1],
        [1, 1, 1],
    ])
    s = GameState(board, [Player(1), Player(2)], phase="Initialization", turn_num=0)

    # Verify (0,0) starts unoccupied
    assert s.board.tiles[0][0].occupied is None

    # Occupy (0,0) using the engine
    s.place_avatar(1, 0, 0)

    # Verify it is now occupied
    assert s.board.tiles[0][0].occupied is not None

    # Strategy must skip the occupied first tile and choose the next legal one
    strat = Strategy()
    assert strat.choose_placement(s) == (0, 1)
