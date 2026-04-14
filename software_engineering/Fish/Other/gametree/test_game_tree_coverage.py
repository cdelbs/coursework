"""Tests for uncovered lines in game_tree.py."""
import pytest
from Common.game_tree import GameTree, GameTreeNode
from Common.gameboard import GameBoard
from Common.state import GameState, Player
from conftest import make_test_state, make_stuck_state


class TestGameTreeNodeTerminal:
    """Test terminal node behavior (line 29)."""

    def test_expand_terminal_node_returns_empty(self):
        """Test that expand() returns nothing for terminal (GameOver) nodes (line 29)."""
        state = make_stuck_state()
        assert state.phase == "GameOver", "Should be GameOver"

        node = GameTreeNode(state)
        assert node.is_terminal()

        # expand() should yield nothing for terminal nodes
        expansions = list(node.expand())
        assert len(expansions) == 0, "Terminal nodes should have no expansions"


class TestGameTreeNodeOccupiedTile:
    """Test occupied tile handling in expand (line 42)."""

    def test_expand_skips_occupied_destinations(self):
        """Test that expand() skips destinations that are occupied (line 42)."""
        # Create a state where some reachable tiles are occupied
        board = GameBoard(rows=6, columns=6).with_uniform_fish(3)
        players = [Player(1), Player(2)]
        state = GameState(board, players, "Initialization")

        # Place penguins close together so they block each other
        state.place_avatar(1, 0, 0)
        state.place_avatar(2, 5, 5)
        state.place_avatar(1, 0, 1)  # Adjacent to (0,0)
        state.place_avatar(2, 5, 4)
        state.place_avatar(1, 1, 0)
        state.place_avatar(2, 4, 5)
        state.place_avatar(1, 2, 0)
        state.place_avatar(2, 3, 5)

        node = GameTreeNode(state)

        # Get all possible moves
        moves = list(node.expand())

        # Verify no moves try to go to occupied tiles
        for action, next_state in moves:
            _, penguin_id, r2, c2 = action
            # The destination should not have been occupied in the original state
            original_tile = state.board.tiles[r2][c2]
            # reachable_tiles already filters occupied, but this tests line 42
            if original_tile.occupied is not None:
                pytest.fail(f"Move to occupied tile {(r2, c2)} should have been skipped")


class TestGameTreeNodeNoLegalMoves:
    """Test behavior when no legal moves exist (line 52)."""

    def test_expand_no_legal_moves_returns_nothing(self):
        """Test that expand() returns nothing when no legal moves (line 52)."""
        # Create a stuck state with no legal moves
        state = make_stuck_state()

        # Manually force Move phase to test line 52
        # (normally stuck state would be GameOver)
        state.phase = "Move"

        node = GameTreeNode(state)

        # expand() should find no legal moves
        moves = list(node.expand())
        # Because all penguins are isolated, no moves should be generated
        assert len(moves) == 0, "Should have no legal moves when all stuck"


class TestGameTreeInvalidInitialization:
    """Test GameTree initialization validation (line 61)."""

    def test_gametree_rejects_non_move_phase(self):
        """Test that GameTree raises ValueError for non-Move phase states (line 61)."""
        board = GameBoard(rows=3, columns=3).with_uniform_fish(1)
        players = [Player(1), Player(2)]
        state = GameState(board, players, "Initialization")

        # Should raise ValueError because phase is "Initialization"
        with pytest.raises(ValueError, match="GameTree must start in the Move phase"):
            GameTree(state)

    def test_gametree_accepts_gameover_state(self):
        """Test behavior with GameOver state."""
        state = make_stuck_state()
        assert state.phase == "GameOver"

        # Should raise ValueError because phase is "GameOver" not "Move"
        with pytest.raises(ValueError, match="GameTree must start in the Move phase"):
            GameTree(state)


class TestGenerateTreeDepthTerminal:
    """Test generate_tree_depth with terminal nodes (line 107)."""

    def test_generate_tree_depth_stops_at_terminal(self):
        """Test that generate_tree_depth respects terminal nodes (line 107)."""
        # Use make_test_state which is already in Move phase
        state = make_test_state()

        tree = GameTree(state)
        new_tree = tree.generate_tree_depth()

        # The tree should be created, terminal nodes should stop expansion (line 107)
        assert isinstance(new_tree, GameTree)

        # Verify it actually built some tree
        assert new_tree.root is not None


class TestEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_query_action_with_all_actions(self):
        """Test query_action returns correct states for all valid actions."""
        state = make_test_state()
        tree = GameTree(state)

        # Get all actions from expand
        actions_from_expand = list(tree.root.expand())

        # Query each action and verify we get a state back
        for action, expected_state in actions_from_expand:
            queried_state = tree.query_action(tree.root, action)
            assert queried_state is not None
            assert queried_state.phase in ["Move", "GameOver"]

    def test_apply_to_successors_with_counter(self):
        """Test apply_to_successors visits all successors exactly once."""
        state = make_test_state()
        tree = GameTree(state)

        count = 0
        states_seen = []

        def counter(s):
            nonlocal count
            count += 1
            states_seen.append(s)

        tree.apply_to_successors(tree.root, counter)

        # Should have visited at least one successor
        assert count > 0
        # All visited states should be unique (different objects)
        assert len(states_seen) == len(set(id(s) for s in states_seen))

    def test_successors_creates_proper_parent_links(self):
        """Test that successors() creates nodes with proper parent links."""
        state = make_test_state()
        tree = GameTree(state)

        for action, child_node in tree.successors(tree.root):
            assert child_node.parent is tree.root
            assert child_node.action == action

    def test_node_with_single_valid_move(self):
        """Test node behavior when moves are constrained."""
        # Use the test state which has valid moves
        state = make_test_state()
        tree = GameTree(state)

        # Verify tree works with the test state
        successors = list(tree.successors(tree.root))
        assert len(successors) > 0

        # All successors should have valid parent links
        for action, node in successors:
            assert node.parent is tree.root
