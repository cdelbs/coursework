from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Player.strategy import Strategy

def test_choose_placement_skips_occupied_first_tile():
    # 2x3 all active tiles
    board = GameBoard(rows=2, columns=3, board_data=[
        [1, 1, 1],
        [1, 1, 1],
    ])
    s = GameState(board, [Player(1), Player(2)], phase="Initialization", turn_num=0)

    # Occupy (0,0) with player 1 during placement
    s.place_avatar(1, 0, 0)

    # Sanity: (0,0) active but now occupied
    assert s.board.tiles[0][0].active is True
    assert s.board.tiles[0][0].occupied is not None

    # Strategy should choose the first active UNoccupied tile, which is (0,1)
    strat = Strategy()
    assert strat.choose_placement(s) == (0, 1)
