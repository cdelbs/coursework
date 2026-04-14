"""Tests for previously uncovered code paths in GameState."""
import pytest
from Common.gameboard import GameBoard
from Common.state import GameState, Player
from conftest import get_current_player_id, place_all_penguins_sequentially


class TestNextStateAfterMove:
    """Test the next_state_after_move method (lines 241-300)."""

    def test_next_state_after_move_creates_independent_state(self):
        """Test that next_state_after_move creates a new independent state."""
        # Create a simple board with few penguins to ensure movement is possible
        board = GameBoard(rows=6, columns=6).with_uniform_fish(3)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        # Place penguins far apart to ensure there are reachable tiles
        gs.place_avatar(1, 0, 0)  # P1 penguin 1
        gs.place_avatar(2, 5, 5)  # P2 penguin 1 - far away
        gs.place_avatar(1, 2, 2)  # P1 penguin 2
        gs.place_avatar(2, 3, 3)  # P2 penguin 2
        gs.place_avatar(1, 4, 0)  # P1 penguin 3
        gs.place_avatar(2, 0, 4)  # P2 penguin 3
        gs.place_avatar(1, 5, 1)  # P1 penguin 4
        gs.place_avatar(2, 1, 5)  # P2 penguin 4

        # Should be in Move phase now
        assert gs.phase == "Move"

        # Get current player's first penguin
        current_pid = get_current_player_id(gs)
        player = next(p for p in gs.players if p.pid == current_pid)
        penguin = player.penguins[0]
        old_row, old_col = penguin.coords

        # Find a reachable tile
        old_tile = gs.board.tiles[old_row][old_col]
        reachable = gs.board.reachable_tiles(old_tile)
        assert len(reachable) > 0, f"Penguin at {penguin.coords} should have reachable tiles"
        new_row, new_col = reachable[0]

        # Create next state using next_state_after_move
        next_state = gs.next_state_after_move(current_pid, penguin.id, new_row, new_col)

        # Verify new state is different from original
        assert next_state is not gs
        assert next_state.board is not gs.board
        assert next_state.players is not gs.players

        # Verify penguin moved in new state
        next_player = next(p for p in next_state.players if p.pid == current_pid)
        next_penguin = next(p for p in next_player.penguins if p.id == penguin.id)
        assert next_penguin.coords == (new_row, new_col)

        # Verify original state unchanged
        orig_player = next(p for p in gs.players if p.pid == current_pid)
        orig_penguin = next(p for p in orig_player.penguins if p.id == penguin.id)
        assert orig_penguin.coords == (old_row, old_col)

    def test_next_state_after_move_validates_phase(self):
        """Test that next_state_after_move requires Move phase."""
        board = GameBoard(rows=5, columns=5).with_uniform_fish(3)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        # Still in Placement phase
        with pytest.raises(Exception, match="Not in move phase"):
            gs.next_state_after_move(1, 0, 1, 1)

    def test_next_state_after_move_validates_turn(self):
        """Test that next_state_after_move validates it's the player's turn."""
        board = GameBoard(rows=5, columns=5).with_uniform_fish(3)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 4, 4)
        place_all_penguins_sequentially(gs)

        # Get wrong player's penguin
        current_pid = get_current_player_id(gs)
        wrong_pid = 2 if current_pid == 1 else 1
        wrong_player = next(p for p in gs.players if p.pid == wrong_pid)
        penguin = wrong_player.penguins[0]

        with pytest.raises(Exception, match="Not this player's turn"):
            gs.next_state_after_move(wrong_pid, penguin.id, 2, 2)

    def test_next_state_after_move_validates_penguin(self):
        """Test that next_state_after_move validates penguin exists."""
        board = GameBoard(rows=5, columns=5).with_uniform_fish(3)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 4, 4)
        place_all_penguins_sequentially(gs)

        current_pid = get_current_player_id(gs)

        # Use invalid penguin ID
        with pytest.raises(Exception, match="Invalid penguin"):
            gs.next_state_after_move(current_pid, 9999, 2, 2)

    def test_next_state_after_move_validates_reachability(self):
        """Test that next_state_after_move validates destination is reachable."""
        board = GameBoard(rows=5, columns=5).with_uniform_fish(3)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 4, 4)
        place_all_penguins_sequentially(gs)

        current_pid = get_current_player_id(gs)
        player = next(p for p in gs.players if p.pid == current_pid)
        penguin = player.penguins[0]

        # Try unreachable diagonal jump
        with pytest.raises(Exception, match="Destination not reachable"):
            gs.next_state_after_move(current_pid, penguin.id, 2, 2)

    def test_next_state_after_move_updates_score(self):
        """Test that next_state_after_move updates player score."""
        board = GameBoard(rows=6, columns=6).with_uniform_fish(3)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        # Place penguins
        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 5, 5)
        gs.place_avatar(1, 2, 2)
        gs.place_avatar(2, 3, 3)
        gs.place_avatar(1, 4, 0)
        gs.place_avatar(2, 0, 4)
        gs.place_avatar(1, 5, 1)
        gs.place_avatar(2, 1, 5)

        current_pid = get_current_player_id(gs)
        player = next(p for p in gs.players if p.pid == current_pid)
        penguin = player.penguins[0]
        old_score = player.score
        old_row, old_col = penguin.coords
        fish_to_collect = gs.board.tiles[old_row][old_col].fish

        # Find reachable tile
        old_tile = gs.board.tiles[old_row][old_col]
        reachable = gs.board.reachable_tiles(old_tile)
        new_row, new_col = reachable[0]

        # Move using next_state_after_move
        next_state = gs.next_state_after_move(current_pid, penguin.id, new_row, new_col)

        # Verify score increased
        next_player = next(p for p in next_state.players if p.pid == current_pid)
        assert next_player.score == old_score + fish_to_collect

    def test_next_state_after_move_removes_old_tile(self):
        """Test that next_state_after_move makes old tile inactive."""
        board = GameBoard(rows=6, columns=6).with_uniform_fish(3)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 5, 5)
        gs.place_avatar(1, 2, 2)
        gs.place_avatar(2, 3, 3)
        gs.place_avatar(1, 4, 0)
        gs.place_avatar(2, 0, 4)
        gs.place_avatar(1, 5, 1)
        gs.place_avatar(2, 1, 5)

        current_pid = get_current_player_id(gs)
        player = next(p for p in gs.players if p.pid == current_pid)
        penguin = player.penguins[0]
        old_row, old_col = penguin.coords

        # Find reachable tile
        old_tile = gs.board.tiles[old_row][old_col]
        reachable = gs.board.reachable_tiles(old_tile)
        new_row, new_col = reachable[0]

        # Move using next_state_after_move
        next_state = gs.next_state_after_move(current_pid, penguin.id, new_row, new_col)

        # Verify old tile is inactive in new state
        assert next_state.board.tiles[old_row][old_col].active is False
        assert next_state.board.tiles[old_row][old_col].fish == 0
        assert next_state.board.tiles[old_row][old_col].occupied is None

        # Verify original tile still active
        assert gs.board.tiles[old_row][old_col].active is True

    def test_next_state_after_move_advances_turn(self):
        """Test that next_state_after_move advances the turn."""
        board = GameBoard(rows=6, columns=6).with_uniform_fish(3)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 5, 5)
        gs.place_avatar(1, 2, 2)
        gs.place_avatar(2, 3, 3)
        gs.place_avatar(1, 4, 0)
        gs.place_avatar(2, 0, 4)
        gs.place_avatar(1, 5, 1)
        gs.place_avatar(2, 1, 5)

        old_turn = gs.current_turn
        current_pid = get_current_player_id(gs)
        player = next(p for p in gs.players if p.pid == current_pid)
        penguin = player.penguins[0]
        old_row, old_col = penguin.coords

        # Find reachable tile
        old_tile = gs.board.tiles[old_row][old_col]
        reachable = gs.board.reachable_tiles(old_tile)
        new_row, new_col = reachable[0]

        # Move using next_state_after_move
        next_state = gs.next_state_after_move(current_pid, penguin.id, new_row, new_col)

        # Verify turn advanced
        assert next_state.current_turn != old_turn
        assert next_state.current_turn == (old_turn + 1) % len(players)

    def test_next_state_after_move_within_same_row(self):
        """Test next_state_after_move when moving within the same row (line 286-287)."""
        # Create a board where we can move horizontally within same row
        board_data = [
            [3, 3, 3, 3, 3, 3, 3, 3],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 1, 1]
        ]
        board = GameBoard(rows=5, columns=8, board_data=board_data)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        # Place penguins far apart on separate rows
        gs.place_avatar(1, 0, 0)  # P1 penguin 1 on row 0
        gs.place_avatar(2, 4, 7)  # P2 penguin 1 on row 4
        gs.place_avatar(1, 0, 3)  # P1 penguin 2 on row 0
        gs.place_avatar(2, 4, 4)  # P2 penguin 2 on row 4
        gs.place_avatar(1, 0, 5)  # P1 penguin 3 on row 0
        gs.place_avatar(2, 4, 2)  # P2 penguin 3 on row 4
        gs.place_avatar(1, 0, 7)  # P1 penguin 4 on row 0
        gs.place_avatar(2, 4, 0)  # P2 penguin 4 on row 4

        # P1's first penguin at (0,0) should be able to move along row 0
        # Reachable: (0,1) and (0,2) before hitting penguin at (0,3)
        player1 = next(p for p in gs.players if p.pid == 1)
        penguin = player1.penguins[0]
        assert penguin.coords == (0, 0)

        # Move within same row from (0,0) to (0,1)
        next_state = gs.next_state_after_move(1, penguin.id, 0, 1)

        # Verify the move succeeded
        next_player1 = next(p for p in next_state.players if p.pid == 1)
        next_penguin = next(p for p in next_player1.penguins if p.id == penguin.id)
        assert next_penguin.coords == (0, 1)

        # Verify old position is inactive
        assert next_state.board.tiles[0][0].active is False

        # Verify new position is occupied
        assert next_state.board.tiles[0][1].occupied is not None


class TestTurnAdvancementEdgeCases:
    """Test edge cases in turn advancement that trigger GameOver (line 340)."""

    def test_game_over_when_all_players_become_stuck_during_turn(self):
        """Test GameOver when turn advancement finds no player can move (line 340)."""
        # Create a scenario where after one move, all players become stuck
        # P1 has one move available, P2 is already stuck
        # After P1 moves, both are stuck -> GameOver
        board_data = [
            [1, 1, 0],  # P1 at (0,0), can move to (0,1), then stuck
            [0, 0, 0],
            [1, 0, 0],  # P2 at (2,0), already stuck
        ]
        board = GameBoard(rows=3, columns=3, board_data=board_data)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        # Place penguins
        gs.place_avatar(1, 0, 0)  # P1 can move to (0,1)
        gs.place_avatar(2, 2, 0)  # P2 is stuck

        # Force move phase
        gs.phase = "Move"
        gs.current_turn = 0

        # Verify we're in Move phase before the move
        assert gs.phase == "Move"

        # P1 makes the only available move
        gs.move_avatar(1, 0, 0, 1)

        # After this move, both players are stuck -> should transition to GameOver
        # This tests line 340 where phase becomes "GameOver"
        assert gs.phase == "GameOver"
