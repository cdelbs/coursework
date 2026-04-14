"""Tests for game over conditions and stuck player handling."""
import pytest
from Common.gameboard import GameBoard
from Common.state import GameState, Player
from conftest import get_current_player_id, get_player_by_id, place_all_penguins_sequentially


class TestGameOverConditions:
    """Test conditions that trigger game over."""

    def test_game_ends_when_no_moves_available(self):
        """Test game ends when no player can move."""
        # Create small board where moves will run out
        board_data = [
            [1, 0, 0],
            [1, 1, 0],
            [0, 0, 0],
        ]
        board = GameBoard(rows=3, columns=3, board_data=board_data)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        # Place penguins
        gs.place_avatar(1, 0, 0)  # P1 at (0,0)
        gs.place_avatar(2, 1, 1)  # P2 at (1,1) - will be stuck

        # Force move phase
        gs.phase = "Move"
        gs.current_turn = 0

        # P1 moves to (1,0) - this is the only move, then game should end
        gs.move_avatar(1, 0, 1, 0)

        assert gs.phase == "GameOver"

    def test_game_over_after_placement_if_no_moves(self, two_players):
        """Test game transitions to GameOver after placement if no moves available."""
        # Create board where all penguins can be placed but no moves possible
        # 2 players = 4 penguins each = 8 total penguins needed
        # Each 1-fish tile is surrounded by holes (0s) so no moves possible
        board = GameBoard(rows=5, columns=5, board_data=[
            [1, 0, 1, 0, 1],
            [0, 0, 0, 0, 0],
            [1, 0, 1, 0, 1],
            [0, 0, 0, 0, 0],
            [1, 0, 1, 0, 0]
        ])
        gs = GameState(board, two_players, "Initialization", 0)

        # Place all 8 penguins (4 per player) in isolated positions
        gs.place_avatar(1, 0, 0)  # P1 penguin 1
        gs.place_avatar(2, 0, 2)  # P2 penguin 1
        gs.place_avatar(1, 0, 4)  # P1 penguin 2
        gs.place_avatar(2, 2, 0)  # P2 penguin 2
        gs.place_avatar(1, 2, 2)  # P1 penguin 3
        gs.place_avatar(2, 2, 4)  # P2 penguin 3
        gs.place_avatar(1, 4, 0)  # P1 penguin 4
        gs.place_avatar(2, 4, 2)  # P2 penguin 4

        # All penguins placed, all isolated - should be GameOver
        assert all(not p.has_unplaced_penguins() for p in gs.players)
        assert gs.phase == "GameOver"

    def test_game_continues_if_moves_available(self):
        """Test game stays in Move phase if moves are available."""
        board = GameBoard(rows=5, columns=5).with_uniform_fish(3)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        # Place penguins with space to move
        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 4, 4)
        place_all_penguins_sequentially(gs)

        # Make one move
        from_tile = gs.board.tiles[0][0]
        reachable = gs.board.reachable_tiles(from_tile)

        if reachable and gs.phase == "Move":
            current_pid = get_current_player_id(gs)
            if current_pid == 1:
                dest_r, dest_c = reachable[0]
                gs.move_avatar(1, 0, dest_r, dest_c)

                # Game should still be in Move phase
                assert gs.phase == "Move"


class TestStuckPlayerHandling:
    """Test handling of players who cannot move."""

    def test_stuck_player_is_skipped(self):
        """Test that stuck players are skipped in turn order."""
        # Create board where P2 will be stuck
        board_data = [
            [1, 0, 1, 0],  # P1 at (0,0), P2 at (0,2) surrounded by holes
            [1, 0, 0, 0],  # P1 can move here
            [1, 0, 0, 0],  # And here
        ]
        board = GameBoard(rows=3, columns=4, board_data=board_data)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        # Place penguins
        gs.place_avatar(1, 0, 0)  # P1 can move south
        gs.place_avatar(2, 0, 2)  # P2 is stuck (surrounded by holes)

        # Force move phase
        gs.phase = "Move"
        gs.current_turn = 0

        # P1 moves from (0,0) to (1,0)
        gs.move_avatar(1, 0, 1, 0)

        # Game should still be in Move phase
        assert gs.phase == "Move"

        # Turn should skip P2 and come back to P1
        current_pid = get_current_player_id(gs)
        assert current_pid == 1

    def test_stuck_player_penguin_not_fallen(self):
        """Test that stuck player's penguins are not marked as fallen."""
        board_data = [
            [1, 0, 1, 0],
            [1, 0, 0, 0],
            [1, 0, 0, 0],
        ]
        board = GameBoard(rows=3, columns=4, board_data=board_data)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 0, 2)  # Stuck position

        gs.phase = "Move"
        gs.current_turn = 0

        # Get P2's penguin before move
        p2_before = get_player_by_id(gs, 2)
        penguin_before = p2_before.penguins[0]
        assert penguin_before.fallen is False
        assert penguin_before.coords == (0, 2)

        # P1 makes a move
        gs.move_avatar(1, 0, 1, 0)

        # P2's penguin should still not be fallen
        p2_after = get_player_by_id(gs, 2)
        penguin_after = p2_after.penguins[0]
        assert penguin_after.fallen is False
        assert penguin_after.coords == (0, 2)
        assert p2_after.score == 0

    def test_stuck_player_tile_remains_occupied(self):
        """Test that stuck player's tile remains occupied."""
        board_data = [
            [1, 0, 1, 0],
            [1, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        board = GameBoard(rows=3, columns=4, board_data=board_data)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 0, 2)

        gs.phase = "Move"
        gs.current_turn = 0

        # Verify P2's tile is occupied
        assert gs.board.tiles[0][2].occupied is not None
        assert gs.board.tiles[0][2].active is True

        # P1 moves
        gs.move_avatar(1, 0, 1, 0)

        # P2's tile should still be occupied and active
        assert gs.board.tiles[0][2].occupied is not None
        assert gs.board.tiles[0][2].active is True

    def test_all_players_stuck_triggers_game_over(self):
        """Test that game ends when all players are stuck."""
        # Create board where all players get stuck after placing all penguins
        # 2 players = 4 penguins each = 8 total penguins
        # Need 8 isolated tiles surrounded by holes
        board_data = [
            [1, 0, 1, 0, 1],
            [0, 0, 0, 0, 0],
            [1, 0, 1, 0, 1],
            [0, 0, 0, 0, 0],
            [1, 0, 1, 0, 0]
        ]
        board = GameBoard(rows=5, columns=5, board_data=board_data)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        # Place all 8 penguins (4 per player) in isolated positions
        # 8 isolated tiles: (0,0), (0,2), (0,4), (2,0), (2,2), (2,4), (4,0), (4,2)
        gs.place_avatar(1, 0, 0)  # P1 penguin 1
        gs.place_avatar(2, 0, 2)  # P2 penguin 1
        gs.place_avatar(1, 0, 4)  # P1 penguin 2
        gs.place_avatar(2, 2, 0)  # P2 penguin 2
        gs.place_avatar(1, 2, 2)  # P1 penguin 3
        gs.place_avatar(2, 2, 4)  # P2 penguin 3
        gs.place_avatar(1, 4, 0)  # P1 penguin 4
        gs.place_avatar(2, 4, 2)  # P2 penguin 4

        # All placed and stuck - should transition to GameOver
        assert all(not p.has_unplaced_penguins() for p in gs.players)
        assert gs.phase == "GameOver"


class TestPlayerCanMove:
    """Test the _player_can_move helper method."""

    def test_player_can_move_with_available_moves(self):
        """Test player_can_move returns True when moves available."""
        board = GameBoard(rows=4, columns=4).with_uniform_fish(2)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        gs.place_avatar(1, 1, 1)  # Central position with many moves
        gs.place_avatar(2, 3, 3)
        place_all_penguins_sequentially(gs)

        # Player 1 should be able to move
        assert gs._player_can_move(1) is True

    def test_player_cannot_move_when_surrounded(self):
        """Test player_can_move returns False when surrounded."""
        # Create board with P1 surrounded by holes
        board_data = [
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ]
        board = GameBoard(rows=3, columns=3, board_data=board_data)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        gs.place_avatar(1, 1, 1)  # Surrounded by holes

        # Player 1 should not be able to move
        assert gs._player_can_move(1) is False

    def test_player_cannot_move_when_all_penguins_fallen(self):
        """Test player_can_move returns False when all penguins have fallen."""
        board = GameBoard(rows=4, columns=4).with_uniform_fish(2)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 3, 3)

        # Mark all P1's penguins as fallen
        p1 = get_player_by_id(gs, 1)
        for penguin in p1.penguins:
            penguin.fallen = True

        # Player 1 should not be able to move
        assert gs._player_can_move(1) is False
