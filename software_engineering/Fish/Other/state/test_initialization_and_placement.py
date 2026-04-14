"""Tests for GameState initialization and placement phase."""
import pytest
from Common.gameboard import GameBoard
from Common.state import GameState, Player, PENGUIN_COUNT_RULE, COLORS
from conftest import (
    get_current_player_id,
    get_current_player,
    get_player_by_id,
    find_empty_tile,
    all_penguins_placed,
)


class TestInitialization:
    """Test game state initialization."""

    def test_initialization_creates_correct_penguin_count(self, simple_board, two_players):
        """Test that initialization creates correct number of penguins per player."""
        gs = GameState(simple_board, two_players, "Initialization", 0)

        assert gs.phase == "Placement"
        expected_penguins = PENGUIN_COUNT_RULE[2]  # 2 players = 4 penguins each

        for player in gs.players:
            assert len(player.penguins) == expected_penguins
            assert all(not p.placed for p in player.penguins)
            assert all(not p.fallen for p in player.penguins)

    def test_initialization_assigns_colors(self, simple_board):
        """Test that initialization assigns colors from COLORS list."""
        players = [Player(1), Player(2), Player(3)]
        gs = GameState(simple_board, players, "Initialization", 0)

        for i, player in enumerate(gs.players):
            assert player.color == COLORS[i]

    def test_initialization_creates_unique_penguin_ids(self, simple_board, two_players):
        """Test that each penguin gets a unique ID within a player."""
        gs = GameState(simple_board, two_players, "Initialization", 0)

        for player in gs.players:
            penguin_ids = [p.id for p in player.penguins]
            assert len(penguin_ids) == len(set(penguin_ids))
            assert penguin_ids == list(range(len(penguin_ids)))

    def test_initialization_sets_correct_phase(self, simple_board, two_players):
        """Test that initialization transitions to Placement phase."""
        gs = GameState(simple_board, two_players, "Initialization", 0)
        assert gs.phase == "Placement"

    def test_initialization_with_three_players(self, simple_board, three_players):
        """Test initialization with 3 players gets 3 penguins each."""
        gs = GameState(simple_board, three_players, "Initialization", 0)

        expected_penguins = PENGUIN_COUNT_RULE[3]  # 3 players = 3 penguins each
        for player in gs.players:
            assert len(player.penguins) == expected_penguins

    def test_initialization_with_four_players(self, simple_board, four_players):
        """Test initialization with 4 players gets 2 penguins each."""
        gs = GameState(simple_board, four_players, "Initialization", 0)

        expected_penguins = PENGUIN_COUNT_RULE[4]  # 4 players = 2 penguins each
        for player in gs.players:
            assert len(player.penguins) == expected_penguins

    def test_turn_order_initialized_correctly(self, simple_board, three_players):
        """Test that turn_order is list of indices."""
        gs = GameState(simple_board, three_players, "Initialization", 0)

        assert gs.turn_order == [0, 1, 2]
        assert gs.current_turn == 0


class TestPlacementPhase:
    """Test placement phase mechanics."""

    def test_place_avatar_basic(self, simple_game):
        """Test basic penguin placement."""
        pid = get_current_player_id(simple_game)
        empty_tile = find_empty_tile(simple_game.board)
        r, c = empty_tile

        simple_game.place_avatar(pid, r, c)

        # Check tile is occupied
        tile = simple_game.board.tiles[r][c]
        assert tile.occupied is not None
        assert tile.occupied.owner.pid == pid
        assert tile.occupied.placed is True
        assert tile.occupied.coords == (r, c)

    def test_placement_advances_turn(self, simple_game):
        """Test that placement advances to next player."""
        initial_turn = simple_game.current_turn
        pid = get_current_player_id(simple_game)
        empty_tile = find_empty_tile(simple_game.board)

        simple_game.place_avatar(pid, *empty_tile)

        # Turn should advance
        assert simple_game.current_turn == (initial_turn + 1) % len(simple_game.players)

    def test_placement_requires_correct_turn(self, simple_game):
        """Test that only current player can place."""
        current_pid = get_current_player_id(simple_game)
        wrong_pid = 999  # Non-existent player

        with pytest.raises(Exception, match="Not this player's turn"):
            simple_game.place_avatar(wrong_pid, 0, 0)

    def test_placement_on_occupied_tile_fails(self, simple_game):
        """Test that placement on occupied tile fails."""
        pid = get_current_player_id(simple_game)
        empty_tile = find_empty_tile(simple_game.board)
        r, c = empty_tile

        # Place first penguin
        simple_game.place_avatar(pid, r, c)

        # Try to place on same tile (after turn advances)
        next_pid = get_current_player_id(simple_game)
        with pytest.raises(Exception, match="Invalid tile for placement"):
            simple_game.place_avatar(next_pid, r, c)

    def test_placement_on_inactive_tile_fails(self, two_players):
        """Test that placement on hole fails."""
        board = GameBoard(rows=3, columns=3, board_data=[[1, 0, 1], [1, 1, 1], [1, 1, 1]])
        gs = GameState(board, two_players, "Initialization", 0)

        pid = get_current_player_id(gs)

        # Tile (0,1) is a hole (fish=0)
        with pytest.raises(Exception, match="Invalid tile for placement"):
            gs.place_avatar(pid, 0, 1)

    def test_placement_out_of_bounds_fails(self, simple_game):
        """Test that out-of-bounds placement fails."""
        pid = get_current_player_id(simple_game)

        with pytest.raises(Exception, match="out of bounds"):
            simple_game.place_avatar(pid, -1, 0)

        with pytest.raises(Exception, match="out of bounds"):
            simple_game.place_avatar(pid, 100, 100)

    def test_placement_not_in_placement_phase_fails(self, simple_game):
        """Test that placement only works in Placement phase."""
        simple_game.phase = "Move"
        pid = get_current_player_id(simple_game)

        with pytest.raises(Exception, match="Not in placement phase"):
            simple_game.place_avatar(pid, 0, 0)

    def test_placement_transitions_to_move_when_complete(self, simple_game):
        """Test transition to Move phase after all placements."""
        # Place all penguins
        while simple_game.phase == "Placement":
            pid = get_current_player_id(simple_game)
            empty_tile = find_empty_tile(simple_game.board)
            if empty_tile:
                simple_game.place_avatar(pid, *empty_tile)
            else:
                break

        # Should transition to Move phase
        assert simple_game.phase == "Move"
        assert all_penguins_placed(simple_game)

    def test_placement_round_robin_order(self, simple_board, two_players):
        """Test that placement follows round-robin order."""
        gs = GameState(simple_board, two_players, "Initialization", 0)

        placements = []
        for _ in range(4):  # Each player places 2 penguins (4 total placements)
            pid = get_current_player_id(gs)
            placements.append(pid)
            empty_tile = find_empty_tile(gs.board)
            gs.place_avatar(pid, *empty_tile)

        # Should alternate: P1, P2, P1, P2
        assert placements == [1, 2, 1, 2]

    def test_no_unplaced_penguins_left_error(self, simple_game):
        """Test error when trying to place when player has no unplaced penguins."""
        # Force all penguins to be placed for current player
        current_player = get_current_player(simple_game)
        for i, penguin in enumerate(current_player.penguins):
            penguin.placed = True
            penguin.coords = (i, 0)

        pid = get_current_player_id(simple_game)

        with pytest.raises(Exception, match="No unplaced penguins left"):
            simple_game.place_avatar(pid, 1, 1)
