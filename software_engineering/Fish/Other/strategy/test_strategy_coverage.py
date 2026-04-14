"""Comprehensive tests for uncovered lines and edge cases in strategy.py."""
import pytest
from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState, Player
from Fish.Common.game_tree import GameTree
from Fish.Player.strategy import Strategy


def build_board(rows, cols, fish=1, holes=()):
    """Helper to build a board with specific configuration."""
    grid = [[fish for _ in range(cols)] for _ in range(rows)]
    for r, c in holes:
        grid[r][c] = 0
    return GameBoard(rows, cols, board_data=grid)


class TestStrategyInitialization:
    """Test Strategy initialization validation."""

    def test_init_with_zero_depth_raises_valueerror(self):
        """Test that depth_hero_turns=0 raises ValueError (line 29)."""
        with pytest.raises(ValueError, match="depth_hero_turns must be at least 1"):
            Strategy(depth_hero_turns=0)

    def test_init_with_negative_depth_raises_valueerror(self):
        """Test that negative depth raises ValueError (line 29)."""
        with pytest.raises(ValueError, match="depth_hero_turns must be at least 1"):
            Strategy(depth_hero_turns=-5)

    def test_init_with_valid_depth_succeeds(self):
        """Test that valid depth values succeed."""
        s1 = Strategy(depth_hero_turns=1)
        assert s1.depth_hero_turns == 1

        s5 = Strategy(depth_hero_turns=5)
        assert s5.depth_hero_turns == 5


class TestNotInMovePhaseError:
    """Test NotInMovePhaseError exception (line 47)."""

    def test_choose_move_raises_not_in_move_phase_for_initialization(self):
        """Test that choose_move raises NotInMovePhaseError for Initialization phase (line 47)."""
        board = build_board(3, 3, fish=1)
        players = [Player(1), Player(2)]
        state = GameState(board, players, "Initialization", 0)

        # Don't wrap in GameTree - call choose_move directly with a mock tree
        # Actually, we need a tree, so let's create one with Move phase then modify it
        # Or better: create a state in Move, wrap it, then modify the wrapped state

        # Place penguins to get to Move phase
        state.place_avatar(1, 0, 0)
        state.place_avatar(2, 2, 2)
        state.place_avatar(1, 0, 1)
        state.place_avatar(2, 2, 1)
        state.place_avatar(1, 0, 2)
        state.place_avatar(2, 2, 0)
        state.place_avatar(1, 1, 0)
        state.place_avatar(2, 1, 2)

        tree = GameTree(state)

        # Now modify the root state to be in Initialization phase
        tree.root.state.phase = "Initialization"

        strategy = Strategy(depth_hero_turns=2)
        with pytest.raises(Strategy.NotInMovePhaseError, match="Root state is not in Move phase"):
            strategy.choose_move(tree)

    def test_choose_move_raises_not_in_move_phase_for_gameover(self):
        """Test that choose_move raises NotInMovePhaseError for GameOver phase (line 47)."""
        board = build_board(3, 3, fish=1)
        players = [Player(1), Player(2)]
        state = GameState(board, players, "Initialization", 0)

        # Place penguins to get to Move phase
        state.place_avatar(1, 0, 0)
        state.place_avatar(2, 2, 2)
        state.place_avatar(1, 0, 1)
        state.place_avatar(2, 2, 1)
        state.place_avatar(1, 0, 2)
        state.place_avatar(2, 2, 0)
        state.place_avatar(1, 1, 0)
        state.place_avatar(2, 1, 2)

        tree = GameTree(state)

        # Modify to GameOver phase
        tree.root.state.phase = "GameOver"

        strategy = Strategy(depth_hero_turns=2)
        with pytest.raises(Strategy.NotInMovePhaseError, match="Root state is not in Move phase"):
            strategy.choose_move(tree)


class TestPassLogic:
    """Test the pass logic when current player is stuck (lines 119-130)."""

    def test_any_moves_available_returns_false_all_stuck(self):
        """Test _any_moves_available when no moves exist (line 173)."""
        # Create a board with 8 isolated tiles (4 penguins per player for 2 players)
        board_data = [
            [1, 0, 1, 0, 1],
            [0, 0, 0, 0, 0],
            [1, 0, 1, 0, 1],
            [0, 0, 0, 0, 0],
            [1, 0, 1, 0, 0]
        ]
        board = GameBoard(rows=5, columns=5, board_data=board_data)
        players = [Player(1), Player(2)]
        state = GameState(board, players, "Initialization", 0)

        # Place all 8 penguins on isolated tiles (4 per player)
        state.place_avatar(1, 0, 0)
        state.place_avatar(2, 0, 2)
        state.place_avatar(1, 0, 4)
        state.place_avatar(2, 2, 0)
        state.place_avatar(1, 2, 2)
        state.place_avatar(2, 2, 4)
        state.place_avatar(1, 4, 0)
        state.place_avatar(2, 4, 2)

        # Now in GameOver phase since all are stuck
        assert state.phase == "GameOver"

        # Test the helper directly by forcing Move phase
        state.phase = "Move"
        state.current_turn = 0

        strategy = Strategy(depth_hero_turns=2)
        any_moves = strategy._any_moves_available(state)
        assert any_moves == False

    def test_next_turn_index_with_move_cycles_through_players(self):
        """Test _next_turn_index_with_move helper (lines 176-182)."""
        # Create a 6x6 board with enough space
        board = build_board(6, 6, fish=1)
        players = [Player(1), Player(2)]
        state = GameState(board, players, "Initialization", 0)

        # Place penguins far apart so both can move
        state.place_avatar(1, 0, 0)
        state.place_avatar(2, 5, 5)
        state.place_avatar(1, 0, 2)
        state.place_avatar(2, 5, 3)
        state.place_avatar(1, 0, 4)
        state.place_avatar(2, 5, 1)
        state.place_avatar(1, 2, 0)
        state.place_avatar(2, 3, 5)

        strategy = Strategy(depth_hero_turns=2)

        # Test finding next player with a move
        next_idx = strategy._next_turn_index_with_move(state)
        # From current_turn=0, next should be 1
        assert next_idx == 1

        # Test from player 2's perspective
        state.current_turn = 1
        next_idx = strategy._next_turn_index_with_move(state)
        # From current_turn=1, next should wrap to 0
        assert next_idx == 0

    def test_next_turn_index_returns_none_when_all_stuck(self):
        """Test _next_turn_index_with_move returns None when all players stuck (line 182)."""
        # Create isolated board
        board_data = [
            [1, 0, 1],
            [0, 0, 0],
            [1, 0, 1]
        ]
        board = GameBoard(rows=3, columns=3, board_data=board_data)
        players = [Player(1), Player(2)]
        state = GameState(board, players, "Initialization", 0)

        # Place all penguins isolated
        state.place_avatar(1, 0, 0)
        state.place_avatar(2, 2, 2)
        state.place_avatar(1, 0, 2)
        state.place_avatar(2, 2, 0)

        # Force Move phase to test the helper
        state.phase = "Move"
        state.current_turn = 0

        strategy = Strategy(depth_hero_turns=2)
        next_idx = strategy._next_turn_index_with_move(state)
        assert next_idx is None


class TestIsHeroTurn:
    """Test _is_hero_turn helper (line 134)."""

    def test_is_hero_turn_correctly_identifies_hero(self):
        """Test that _is_hero_turn correctly identifies hero turn (line 134)."""
        board = build_board(3, 3, fish=1)
        players = [Player(1), Player(2)]
        state = GameState(board, players, "Initialization", 0)

        # Place all penguins
        state.place_avatar(1, 0, 0)
        state.place_avatar(2, 2, 2)
        state.place_avatar(1, 0, 1)
        state.place_avatar(2, 2, 1)
        state.place_avatar(1, 0, 2)
        state.place_avatar(2, 2, 0)
        state.place_avatar(1, 1, 0)
        state.place_avatar(2, 1, 2)

        strategy = Strategy(depth_hero_turns=2)

        # At start of Move phase, current_turn=0, which is Player 1
        hero_pid = state.players[state.turn_order[state.current_turn]].pid
        assert strategy._is_hero_turn(state, hero_pid) == True

        # Check for opponent
        opponent_pid = state.players[state.turn_order[1]].pid
        assert strategy._is_hero_turn(state, opponent_pid) == False


class TestChoosePlacementEdgeCases:
    """Test choose_placement edge cases."""

    def test_choose_placement_raises_when_no_legal_tiles(self):
        """Test that choose_placement raises RuntimeError when board is full."""
        # Create a 2x2 board with all tiles inactive or occupied
        board_data = [[0, 0], [0, 0]]
        board = GameBoard(rows=2, columns=2, board_data=board_data)
        players = [Player(1), Player(2)]
        state = GameState(board, players, "Initialization", 0)

        strategy = Strategy(depth_hero_turns=2)
        with pytest.raises(RuntimeError, match="No legal placement available"):
            strategy.choose_placement(state)

    def test_choose_placement_picks_first_available_row_major(self):
        """Test that choose_placement uses row-major ordering."""
        board_data = [
            [0, 0, 1],
            [1, 1, 1]
        ]
        board = GameBoard(rows=2, columns=3, board_data=board_data)
        players = [Player(1), Player(2)]
        state = GameState(board, players, "Initialization", 0)

        strategy = Strategy(depth_hero_turns=2)
        placement = strategy.choose_placement(state)

        # Should pick (0, 2) - first active tile in row-major order
        assert placement == (0, 2)


class TestUtilityAndTieBreaking:
    """Test utility calculation and tie-breaking."""

    def test_utility_returns_hero_score(self):
        """Test that _utility correctly returns hero's score."""
        board = build_board(5, 5, fish=3)
        players = [Player(1), Player(2)]
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

        # Make a move to give P1 some score
        penguin = state.players[0].penguins[0]
        state = state.move_avatar(1, penguin.id, 1, 0)

        strategy = Strategy(depth_hero_turns=2)
        utility = strategy._utility(state, 1)  # Player ID is integer

        assert utility == state.players[0].score
        assert utility > 0


class TestPlayerCanMove:
    """Test _player_can_move helper."""

    def test_player_can_move_returns_false_for_isolated_player(self):
        """Test that _player_can_move returns False when player is completely stuck."""
        # Create isolated penguins
        board_data = [
            [1, 0, 1],
            [0, 0, 0],
            [1, 0, 1]
        ]
        board = GameBoard(rows=3, columns=3, board_data=board_data)
        players = [Player(1), Player(2)]
        state = GameState(board, players, "Initialization", 0)

        # Place all penguins on isolated tiles
        state.place_avatar(1, 0, 0)
        state.place_avatar(2, 2, 2)
        state.place_avatar(1, 0, 2)
        state.place_avatar(2, 2, 0)

        # Force Move phase to test the helper
        state.phase = "Move"
        state.current_turn = 0

        strategy = Strategy(depth_hero_turns=2)

        # Both players are isolated
        can_move_p1 = strategy._player_can_move(state, 1)  # Player ID is integer
        can_move_p2 = strategy._player_can_move(state, 2)

        assert can_move_p1 == False
        assert can_move_p2 == False

    def test_player_can_move_returns_true_when_moves_available(self):
        """Test that _player_can_move returns True when player has legal moves."""
        board = build_board(5, 5, fish=1)
        players = [Player(1), Player(2)]
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

        strategy = Strategy(depth_hero_turns=2)

        # Both players should have moves
        can_move_p1 = strategy._player_can_move(state, 1)  # Player ID is integer
        can_move_p2 = strategy._player_can_move(state, 2)

        assert can_move_p1 == True
        assert can_move_p2 == True
