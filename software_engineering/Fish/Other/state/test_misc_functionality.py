"""Tests for miscellaneous GameState functionality."""
import pytest
from unittest.mock import patch, Mock
from Common.gameboard import GameBoard
from Common.state import GameState, Player, Penguin
from conftest import get_current_player_id, get_player_by_id


class TestReprAndStringMethods:
    """Test string representation methods."""

    def test_game_state_repr(self, simple_board, two_players):
        """Test GameState __repr__ method."""
        gs = GameState(simple_board, two_players, "Initialization", 0)

        repr_str = repr(gs)
        assert "GameState" in repr_str
        assert "phase=Placement" in repr_str
        assert "players=2" in repr_str

    def test_player_repr(self):
        """Test Player __repr__ method."""
        player = Player(1, 5, "red", [])

        repr_str = repr(player)
        assert "Player" in repr_str
        assert "1" in repr_str
        assert "red" in repr_str
        assert "score=5" in repr_str

    def test_penguin_repr(self):
        """Test Penguin __repr__ method."""
        player = Player(1, 0, "red")
        penguin = Penguin(0, player, (2, 3), placed=True, fallen=False)

        repr_str = repr(penguin)
        assert "Penguin" in repr_str
        assert "0" in repr_str
        assert "(2, 3)" in repr_str
        assert "placed=True" in repr_str
        assert "fallen=False" in repr_str


class TestPlayerHelperMethods:
    """Test Player helper methods."""

    def test_has_unplaced_penguins_true(self):
        """Test has_unplaced_penguins returns True when penguins unplaced."""
        player = Player(1, 0, "red")
        penguin1 = Penguin(0, player, placed=False)
        penguin2 = Penguin(1, player, placed=True)
        player.penguins = [penguin1, penguin2]

        assert player.has_unplaced_penguins() is True

    def test_has_unplaced_penguins_false(self):
        """Test has_unplaced_penguins returns False when all placed."""
        player = Player(1, 0, "red")
        penguin1 = Penguin(0, player, placed=True)
        penguin2 = Penguin(1, player, placed=True)
        player.penguins = [penguin1, penguin2]

        assert player.has_unplaced_penguins() is False

    def test_active_penguins_filters_correctly(self):
        """Test active_penguins returns only placed and not-fallen penguins."""
        player = Player(1, 0, "red")
        peng1 = Penguin(0, player, placed=True, fallen=False)
        peng2 = Penguin(1, player, placed=False, fallen=False)
        peng3 = Penguin(2, player, placed=True, fallen=True)
        peng4 = Penguin(3, player, placed=True, fallen=False)
        player.penguins = [peng1, peng2, peng3, peng4]

        active = player.active_penguins()

        assert len(active) == 2
        assert peng1 in active
        assert peng4 in active
        assert peng2 not in active  # Not placed
        assert peng3 not in active  # Fallen


class TestNextStateAfterMove:
    """Test the next_state_after_move method (tree building)."""

    def test_next_state_creates_new_state(self):
        """Test that next_state_after_move creates a new GameState instance."""
        board = GameBoard(rows=4, columns=4).with_uniform_fish(2)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        # Set up the game
        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 3, 3)
        while gs.phase == "Placement":
            pid = get_current_player_id(gs)
            empty = None
            for r in range(board.rows):
                for c in range(board.columns):
                    if gs.board.tiles[r][c].active and gs.board.tiles[r][c].occupied is None:
                        empty = (r, c)
                        break
                if empty:
                    break
            if empty:
                gs.place_avatar(pid, *empty)

        # Ensure we're in Move phase
        if gs.phase == "Move":
            current_pid = get_current_player_id(gs)
            player = get_player_by_id(gs, current_pid)
            penguin = player.active_penguins()[0]
            from_tile = gs.board.tiles[penguin.coords[0]][penguin.coords[1]]
            reachable = gs.board.reachable_tiles(from_tile)

            if reachable:
                dest_r, dest_c = reachable[0]

                # Create next state
                next_state = gs.next_state_after_move(current_pid, penguin.id, dest_r, dest_c)

                # Should be a different instance
                assert next_state is not gs
                assert isinstance(next_state, GameState)


class TestDrawMethod:
    """Test the draw method for GUI integration."""

    def test_draw_calls_board_draw(self):
        """Test that draw method calls board.draw_board."""
        board = GameBoard(rows=3, columns=3).with_uniform_fish(2)
        players = [Player(1), Player(2)]
        gs = GameState(board, players, "Initialization", 0)

        # Mock the board's draw_board method
        with patch.object(gs.board, 'draw_board') as mock_draw:
            gs.draw()
            mock_draw.assert_called_once_with(gs)


class TestActivePids:
    """Test the active_pids method."""

    def test_active_pids_returns_all_when_none_eliminated(self, simple_board, three_players):
        """Test active_pids returns all player IDs when none eliminated."""
        gs = GameState(simple_board, three_players, "Initialization", 0)

        active = gs.active_pids()
        assert len(active) == 3
        assert 1 in active
        assert 2 in active
        assert 3 in active

    def test_active_pids_excludes_eliminated(self, simple_board, three_players):
        """Test active_pids excludes eliminated players."""
        gs = GameState(simple_board, three_players, "Initialization", 0)

        # Eliminate player 2
        gs.eliminated.add(2)

        active = gs.active_pids()
        assert len(active) == 2
        assert 1 in active
        assert 3 in active
        assert 2 not in active


class TestImmutability:
    """Test that game state operations maintain immutability where expected."""

    def test_place_avatar_creates_new_penguin(self, simple_board, two_players):
        """Test that place_avatar creates new penguin objects."""
        gs = GameState(simple_board, two_players, "Initialization", 0)

        pid = get_current_player_id(gs)
        player_before = get_player_by_id(gs, pid)
        penguin_before = player_before.penguins[0]
        penguin_id_before = id(penguin_before)

        gs.place_avatar(pid, 0, 0)

        player_after = get_player_by_id(gs, pid)
        penguin_after = player_after.penguins[0]
        penguin_id_after = id(penguin_after)

        # Penguin should be a new object
        assert penguin_id_after != penguin_id_before
        assert penguin_after.placed is True
        assert penguin_before.placed is False

    def test_move_avatar_creates_new_penguin(self, simple_board, two_players):
        """Test that move_avatar creates new penguin objects."""
        gs = GameState(simple_board, two_players, "Initialization", 0)

        gs.place_avatar(1, 0, 0)
        gs.place_avatar(2, 3, 3)

        while gs.phase == "Placement":
            pid = get_current_player_id(gs)
            for r in range(simple_board.rows):
                for c in range(simple_board.columns):
                    tile = gs.board.tiles[r][c]
                    if tile.active and tile.occupied is None:
                        gs.place_avatar(pid, r, c)
                        break
                else:
                    continue
                break

        if gs.phase == "Move":
            gs.current_turn = 0
            p1 = get_player_by_id(gs, 1)
            penguin_before = p1.penguins[0]
            coords_before = penguin_before.coords

            from_tile = gs.board.tiles[coords_before[0]][coords_before[1]]
            reachable = gs.board.reachable_tiles(from_tile)

            if reachable:
                dest_r, dest_c = reachable[0]
                gs.move_avatar(1, 0, dest_r, dest_c)

                p1_after = get_player_by_id(gs, 1)
                penguin_after = p1_after.penguins[0]

                # Coordinates should have changed
                assert penguin_after.coords != coords_before
                assert penguin_after.coords == (dest_r, dest_c)
