import pytest
from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Common.game_tree import GameTree
from Fish.Player.strategy import Strategy

def test_depth3_5x5_realistic_lookahead_prefers_center_line():
    """
    5x5 board, mixed fish, sparse holes. Two players, 4 penguins each.
    The hero has a tempting immediate move to the left corridor but a better
    depth-3 line through the center 3-fish tile. Strategy should pick the
    center line at depth=3.

    Grid (rows 0..4, cols 0..4), numbers are fish. 0 marks a pre-hole.

      r\c   0  1  2  3  4
       0   [1, 1, 1, 1, 1]
       1   [1, 0, 2, 0, 1]
       2   [2, 2, 3, 2, 1]
       3   [1, 0, 2, 0, 1]
       4   [1, 1, 1, 1, 1]

    Key idea
      - Hero penguin at (2,1) can go LEFT to (2,0) or INTO CENTER to (2,2).
      - Going center immediately gets 3 and keeps future access to a 2.
      - Going left only nets small follow-ups after the opponent reply.
      - Other penguins are placed to keep play realistic but not interfere.
    """
    board = GameBoard(
        rows=5,
        columns=5,
        board_data=[
            [1, 1, 1, 1, 1],
            [1, 0, 2, 0, 1],
            [2, 2, 3, 2, 1],
            [1, 0, 2, 0, 1],
            [1, 1, 1, 1, 1],
        ],
    )

    # Two players, four penguins each by rule for 2 players
    p1, p2 = Player(1), Player(2)
    s = GameState(board, [p1, p2], phase="Initialization", turn_num=0)

    # Placement order alternates P1, P2, P1, P2, ... on ACTIVE tiles
    # Hero focus penguin: P1 at (2,1) aiming toward the 3 at (2,2)
    s.place_avatar(1, 2, 1)  # P1-A (hero origin)

    # Opponent near the center-right to provide a realistic reply
    s.place_avatar(2, 2, 4)  # P2-A

    # Fill remaining P1 penguins in realistic spots that do not invalidate the central line
    s.place_avatar(1, 0, 0)  # P1-B corner
    s.place_avatar(2, 4, 0)  # P2-B corner
    s.place_avatar(1, 4, 4)  # P1-C corner
    s.place_avatar(2, 0, 4)  # P2-C corner
    s.place_avatar(1, 0, 2)  # P1-D upper middle (active and harmless here)
    s.place_avatar(2, 4, 2)  # P2-D lower middle (mirrors P1-D)

    # Start Move phase with P1 to move
    s.phase = "Move"
    s.current_turn = 0

    tree = GameTree(s)
    spec = Strategy(depth_hero_turns=3).choose_move(tree)

    # Expect the depth-3 lookahead to favor the center line:
    # from (2,1) into the 3-fish tile at (2,2)
    assert spec == ((2, 1), (2, 2))
