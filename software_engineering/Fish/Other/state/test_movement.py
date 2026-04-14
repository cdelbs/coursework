"""Tests for GameState movement phase."""
import pytest
from Common.gameboard import GameBoard
from Common.state import GameState, Player
from conftest import (
    get_current_player_id,
    get_current_player,
    get_player_by_id,
    find_empty_tile,
    place_all_penguins_sequentially,
)


class TestMovementBasics:
    """Test basic movement mechanics."""

    def test_move_avatar_basic(self, simple_board, two_players):
        """Test basic penguin movement."""
        gs = GameState(simple_board, two_players, "Initialization", 0)

        # Place penguins
        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 3, 3)

        # Force move phase
        gs.phase = "Move"
        gs.current_turn = 0  # Player 1's turn

        # Get player 1's penguin
        p1 = get_player_by_id(gs, 1)
        penguin = p1.penguins[0]
        assert penguin.coords == (0, 0)

        # Find a reachable tile
        from_tile = gs.board.tiles[0][0]
        reachable = gs.board.reachable_tiles(from_tile)
        assert len(reachable) > 0

        dest_r, dest_c = reachable[0]

        # Get fish count before move
        old_tile_fish = gs.board.tiles[0][0].fish

        # Move penguin
        gs.move_avatar(1, 0, dest_r, dest_c)

        # Check penguin moved
        p1_after = get_player_by_id(gs, 1)
        penguin_after = p1_after.penguins[0]
        assert penguin_after.coords == (dest_r, dest_c)

        # Check old tile is now inactive
        old_tile = gs.board.tiles[0][0]
        assert old_tile.active is False
        assert old_tile.fish == 0
        assert old_tile.occupied is None

        # Check new tile is occupied
        new_tile = gs.board.tiles[dest_r][dest_c]
        assert new_tile.occupied is not None
        assert new_tile.occupied.id == 0

        # Check score updated
        assert p1_after.score == old_tile_fish

    def test_move_advances_turn(self, simple_board, two_players):
        """Test that movement advances turn to next player."""
        gs = GameState(simple_board, two_players, "Initialization", 0)

        # Place penguins
        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 3, 3)

        # Both players placed all penguins, should be in Move phase
        place_all_penguins_sequentially(gs)

        initial_pid = get_current_player_id(gs)
        player = get_player_by_id(gs, initial_pid)
        penguin = player.active_penguins()[0]
        old_r, old_c = penguin.coords

        from_tile = gs.board.tiles[old_r][old_c]
        reachable = gs.board.reachable_tiles(from_tile)

        if reachable:
            dest_r, dest_c = reachable[0]
            gs.move_avatar(initial_pid, penguin.id, dest_r, dest_c)

            # Turn should have advanced
            new_pid = get_current_player_id(gs)
            assert new_pid != initial_pid

    def test_move_not_in_move_phase_fails(self, simple_board, two_players):
        """Test that movement only works in Move phase."""
        gs = GameState(simple_board, two_players, "Initialization", 0)
        gs.place_avatar(1, 0, 0)

        # Still in Placement phase
        with pytest.raises(Exception, match="Not in move phase"):
            gs.move_avatar(1, 0, 1, 0)

    def test_move_wrong_player_fails(self, simple_board, two_players):
        """Test that only current player can move."""
        gs = GameState(simple_board, two_players, "Initialization", 0)
        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 3, 3)
        place_all_penguins_sequentially(gs)

        current_pid = get_current_player_id(gs)
        wrong_pid = 2 if current_pid == 1 else 1

        with pytest.raises(Exception, match="Not this player's turn"):
            gs.move_avatar(wrong_pid, 0, 1, 0)

    def test_move_to_unreachable_tile_fails(self, simple_board, two_players):
        """Test that movement to unreachable tile fails."""
        gs = GameState(simple_board, two_players, "Initialization", 0)
        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 3, 3)
        place_all_penguins_sequentially(gs)

        # Force player 1's turn
        gs.current_turn = 0

        # Try to move to an unreachable position (blocked or too far)
        with pytest.raises(Exception, match="Destination not reachable"):
            gs.move_avatar(1, 0, 2, 2)  # Diagonal move that's not in straight line

    def test_move_to_occupied_tile_fails(self, simple_board, two_players):
        """Test that movement is blocked by occupied tiles."""
        gs = GameState(simple_board, two_players, "Initialization", 0)
        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 0, 1)  # Adjacent to player 1
        place_all_penguins_sequentially(gs)

        gs.current_turn = 0  # Player 1's turn

        # Note: The code checks reachability first, and occupied tiles block reachability
        # So we expect "Destination not reachable" because the penguin blocks the path
        with pytest.raises(Exception, match="Destination not reachable"):
            gs.move_avatar(1, 0, 0, 1)  # Try to move to player 2's position

    def test_move_to_same_position_fails(self, simple_board, two_players):
        """Test that moving to same position fails."""
        gs = GameState(simple_board, two_players, "Initialization", 0)
        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 3, 3)
        place_all_penguins_sequentially(gs)

        gs.current_turn = 0

        with pytest.raises(Exception, match="Cannot move penguin to its current position"):
            gs.move_avatar(1, 0, 0, 0)

    def test_move_invalid_penguin_fails(self, simple_board, two_players):
        """Test that moving non-existent penguin fails."""
        gs = GameState(simple_board, two_players, "Initialization", 0)
        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 3, 3)
        place_all_penguins_sequentially(gs)

        gs.current_turn = 0

        with pytest.raises(Exception, match="Invalid penguin"):
            gs.move_avatar(1, 999, 1, 0)  # Non-existent penguin ID

    def test_move_unplaced_penguin_fails(self, simple_board, two_players):
        """Test that moving unplaced penguin fails."""
        gs = GameState(simple_board, two_players, "Initialization", 0)
        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 3, 3)

        # Only place first penguin for each player, leaving others unplaced
        gs.phase = "Move"
        gs.current_turn = 0

        # Try to move an unplaced penguin
        p1 = get_player_by_id(gs, 1)
        unplaced_penguin = next(p for p in p1.penguins if not p.placed)

        with pytest.raises(Exception, match="Penguin has not been placed yet"):
            gs.move_avatar(1, unplaced_penguin.id, 1, 0)

    def test_move_out_of_bounds_fails(self, simple_board, two_players):
        """Test that out-of-bounds move fails."""
        gs = GameState(simple_board, two_players, "Initialization", 0)
        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 3, 3)
        place_all_penguins_sequentially(gs)

        gs.current_turn = 0

        with pytest.raises(Exception, match="out of bounds"):
            gs.move_avatar(1, 0, -1, 0)

        with pytest.raises(Exception, match="out of bounds"):
            gs.move_avatar(1, 0, 100, 100)


class TestMovementScoring:
    """Test scoring mechanics during movement."""

    def test_move_collects_fish_from_old_tile(self, two_players):
        """Test that moving collects fish from the tile being left."""
        # Create board with specific fish counts
        board = GameBoard(rows=3, columns=3).with_uniform_fish(3)
        gs = GameState(board, two_players, "Initialization", 0)

        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 2, 2)
        place_all_penguins_sequentially(gs)

        gs.current_turn = 0  # Player 1's turn

        p1_before = get_player_by_id(gs, 1)
        initial_score = p1_before.score

        # Move player 1
        from_tile = gs.board.tiles[0][0]
        fish_count = from_tile.fish
        reachable = gs.board.reachable_tiles(from_tile)

        if reachable:
            dest_r, dest_c = reachable[0]
            gs.move_avatar(1, 0, dest_r, dest_c)

            p1_after = get_player_by_id(gs, 1)
            assert p1_after.score == initial_score + fish_count

    def test_multiple_moves_accumulate_score(self, two_players):
        """Test that multiple moves accumulate score."""
        board = GameBoard(rows=4, columns=4).with_uniform_fish(2)
        gs = GameState(board, two_players, "Initialization", 0)

        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 3, 3)
        place_all_penguins_sequentially(gs)

        # Make multiple moves for player 1
        moves_made = 0
        max_moves = 3

        while moves_made < max_moves and gs.phase == "Move":
            current_pid = get_current_player_id(gs)
            if current_pid == 1:
                p1 = get_player_by_id(gs, 1)
                for penguin in p1.active_penguins():
                    from_tile = gs.board.tiles[penguin.coords[0]][penguin.coords[1]]
                    reachable = gs.board.reachable_tiles(from_tile)
                    if reachable:
                        dest_r, dest_c = reachable[0]
                        gs.move_avatar(1, penguin.id, dest_r, dest_c)
                        moves_made += 1
                        break
            else:
                # Player 2's turn, skip
                p2 = get_player_by_id(gs, 2)
                for penguin in p2.active_penguins():
                    from_tile = gs.board.tiles[penguin.coords[0]][penguin.coords[1]]
                    reachable = gs.board.reachable_tiles(from_tile)
                    if reachable:
                        dest_r, dest_c = reachable[0]
                        gs.move_avatar(2, penguin.id, dest_r, dest_c)
                        break

        p1_final = get_player_by_id(gs, 1)
        assert p1_final.score >= moves_made * 2  # At least 2 fish per move


class TestMovementTileRemoval:
    """Test tile removal after movement."""

    def test_old_tile_becomes_inactive(self, simple_board, two_players):
        """Test that the tile penguin moves from becomes inactive."""
        gs = GameState(simple_board, two_players, "Initialization", 0)
        gs.place_avatar(1, 1, 1)
        gs.place_avatar(2, 3, 3)
        place_all_penguins_sequentially(gs)

        gs.current_turn = 0

        from_tile = gs.board.tiles[1][1]
        reachable = gs.board.reachable_tiles(from_tile)

        if reachable:
            dest_r, dest_c = reachable[0]
            gs.move_avatar(1, 0, dest_r, dest_c)

            # Old tile should be inactive with 0 fish
            old_tile = gs.board.tiles[1][1]
            assert old_tile.active is False
            assert old_tile.fish == 0
            assert old_tile.occupied is None

    def test_old_tile_cleared_of_occupant(self, simple_board, two_players):
        """Test that old tile's occupant is cleared."""
        gs = GameState(simple_board, two_players, "Initialization", 0)
        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 3, 3)
        place_all_penguins_sequentially(gs)

        gs.current_turn = 0

        # Verify tile is occupied before move
        assert gs.board.tiles[0][0].occupied is not None

        from_tile = gs.board.tiles[0][0]
        reachable = gs.board.reachable_tiles(from_tile)

        if reachable:
            dest_r, dest_c = reachable[0]
            gs.move_avatar(1, 0, dest_r, dest_c)

            # Old tile should have no occupant
            assert gs.board.tiles[0][0].occupied is None
