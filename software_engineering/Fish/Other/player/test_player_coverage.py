"""Comprehensive tests for uncovered lines and edge cases in player.py."""
import pytest
from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player as EnginePlayer
from Fish.Common.game_tree import GameTree
from Fish.Player.player import LocalPlayer


def build_board(rows, cols, fish=1, holes=()):
    """Helper to build a board with specific configuration."""
    grid = [[fish for _ in range(cols)] for _ in range(rows)]
    for r, c in holes:
        grid[r][c] = 0
    return GameBoard(rows, cols, board_data=grid)


class TestLocalPlayerInitialization:
    """Test LocalPlayer initialization."""

    def test_init_with_default_parameters(self):
        """Test that LocalPlayer initializes with default values."""
        player = LocalPlayer()
        assert player.name == "101"
        assert player.strategy.depth_hero_turns == 2

    def test_init_with_custom_name(self):
        """Test that LocalPlayer can be initialized with custom name."""
        player = LocalPlayer(name="Alice")
        assert player.name == "Alice"
        assert player.strategy.depth_hero_turns == 2

    def test_init_with_custom_depth(self):
        """Test that LocalPlayer can be initialized with custom depth."""
        player = LocalPlayer(depth_hero_turns=5)
        assert player.name == "101"
        assert player.strategy.depth_hero_turns == 5

    def test_init_with_all_custom_parameters(self):
        """Test that LocalPlayer can be initialized with all custom parameters."""
        player = LocalPlayer(name="Bob", depth_hero_turns=3)
        assert player.name == "Bob"
        assert player.strategy.depth_hero_turns == 3


class TestProposeMoveNoLegalMoveError:
    """Test propose_move when there are no legal moves (lines 23-24)."""

    def test_propose_move_returns_false_when_no_legal_moves(self):
        """Test that propose_move returns False when player has no legal moves (line 24)."""
        # Create a board where the current player is completely stuck
        board_data = [
            [1, 0, 1, 0, 1],
            [0, 0, 0, 0, 0],
            [1, 0, 1, 0, 1],
            [0, 0, 0, 0, 0],
            [1, 0, 1, 0, 0]
        ]
        board = GameBoard(rows=5, columns=5, board_data=board_data)
        players = [EnginePlayer(1), EnginePlayer(2)]
        state = GameState(board, players, "Initialization", 0)

        # Place 4 penguins per player, all isolated
        state.place_avatar(1, 0, 0)
        state.place_avatar(2, 0, 2)
        state.place_avatar(1, 0, 4)
        state.place_avatar(2, 2, 0)
        state.place_avatar(1, 2, 2)
        state.place_avatar(2, 2, 4)
        state.place_avatar(1, 4, 0)
        state.place_avatar(2, 4, 2)

        # Game should be over since all are stuck
        assert state.phase == "GameOver"

        # But let's force Move phase and make P1's turn to test the exception path
        state.phase = "Move"
        state.current_turn = 0

        tree = GameTree(state)
        player = LocalPlayer()

        # Should return False since no legal moves
        result = player.propose_move(tree)
        assert result is False

    def test_propose_move_returns_action_when_moves_available(self):
        """Test that propose_move returns an action when moves are available."""
        board = build_board(5, 5, fish=1)
        players = [EnginePlayer(1), EnginePlayer(2)]
        state = GameState(board, players, "Initialization", 0)

        # Place penguins far apart
        state.place_avatar(1, 0, 0)
        state.place_avatar(2, 4, 4)
        state.place_avatar(1, 0, 2)
        state.place_avatar(2, 4, 2)
        state.place_avatar(1, 2, 0)
        state.place_avatar(2, 2, 4)
        state.place_avatar(1, 1, 1)
        state.place_avatar(2, 3, 3)

        tree = GameTree(state)
        player = LocalPlayer()

        result = player.propose_move(tree)

        # Should return a valid action
        assert result is not False
        assert isinstance(result, tuple)
        assert len(result) == 2
        (fr, fc), (tr, tc) = result
        assert isinstance(fr, int) and isinstance(fc, int)
        assert isinstance(tr, int) and isinstance(tc, int)


class TestTournamentNotifications:
    """Test tournament notification methods (lines 28, 32)."""

    def test_notify_tournament_start_returns_true(self):
        """Test that notify_tournament_start returns True (line 28)."""
        player = LocalPlayer()
        result = player.notify_tournament_start()
        assert result is True

    def test_notify_tournament_result_won_returns_true(self):
        """Test that notify_tournament_result returns True when won=True (line 32)."""
        player = LocalPlayer()
        result = player.notify_tournament_result(won=True)
        assert result is True

    def test_notify_tournament_result_lost_returns_true(self):
        """Test that notify_tournament_result returns True when won=False (line 32)."""
        player = LocalPlayer()
        result = player.notify_tournament_result(won=False)
        assert result is True


class TestProposeMovementEdgeCases:
    """Test edge cases for propose_move."""

    def test_propose_move_with_different_depths(self):
        """Test that propose_move works with different depth values."""
        board = build_board(5, 5, fish=1)
        players = [EnginePlayer(1), EnginePlayer(2)]
        state = GameState(board, players, "Initialization", 0)

        # Place penguins
        state.place_avatar(1, 0, 0)
        state.place_avatar(2, 4, 4)
        state.place_avatar(1, 0, 2)
        state.place_avatar(2, 4, 2)
        state.place_avatar(1, 2, 0)
        state.place_avatar(2, 2, 4)
        state.place_avatar(1, 1, 1)
        state.place_avatar(2, 3, 3)

        tree = GameTree(state)

        # Test with depth=1
        player1 = LocalPlayer(depth_hero_turns=1)
        result1 = player1.propose_move(tree)
        assert result1 is not False

        # Test with depth=3
        player3 = LocalPlayer(depth_hero_turns=3)
        result3 = player3.propose_move(tree)
        assert result3 is not False


class TestProposePlacementEdgeCases:
    """Test edge cases for propose_placement."""

    def test_propose_placement_with_holes(self):
        """Test that propose_placement correctly skips holes."""
        board_data = [
            [0, 0, 1],
            [1, 1, 1]
        ]
        board = GameBoard(rows=2, columns=3, board_data=board_data)
        players = [EnginePlayer(1), EnginePlayer(2)]
        state = GameState(board, players, "Initialization", 0)

        player = LocalPlayer()
        placement = player.propose_placement(state)

        # Should pick (0, 2) - first active tile in row-major order
        assert placement == (0, 2)

    def test_propose_placement_with_occupied_tiles(self):
        """Test that propose_placement skips occupied tiles."""
        board = build_board(3, 3, fish=1)
        players = [EnginePlayer(1), EnginePlayer(2)]
        state = GameState(board, players, "Initialization", 0)

        # Place a penguin at (0, 0)
        state.place_avatar(1, 0, 0)

        player = LocalPlayer()
        placement = player.propose_placement(state)

        # Should pick (0, 1) - next available tile
        assert placement == (0, 1)
