# Fish/Other/admin/conftest.py
"""Shared fixtures and test utilities for admin (referee) tests."""
import pytest
from Fish.Player.player import LocalPlayer
from Fish.Common.game_tree import GameTree

class InstantPlayer(LocalPlayer):
    """
    Ultra-fast player for testing - returns first valid action instantly.
    No AI computation, just picks the first available action.
    Used to test referee logic without AI overhead.
    """
    def __init__(self, name="player"):
        # Don't call super().__init__ to avoid creating Strategy
        self.name = name
    
    def setup(self, gameState, player_id):
        return
    
    def game_over(self, gameState, player_id):
        return

    def propose_placement(self, state):
        """Return first valid placement position."""
        # Find first unoccupied tile with 1 fish
        board = state.board
        for r in range(board.rows):
            for c in range(board.columns):
                t = board.tiles[r][c]
                # Check if tile is active and not occupied (same logic as Strategy)
                if getattr(t, "active", False) and getattr(t, "occupied", None) is None:
                    return (r, c)
        raise RuntimeError("No legal placement available")

    def propose_move(self, tree: GameTree):
        """Return first available move without any AI computation."""
        # Get first successor if any exist
        successors = list(tree.successors(tree.root))
        if successors:
            action, _ = successors[0]
            # Convert action to move format: ((from_r, from_c), (to_r, to_c))
            if action[0] == "move":
                _, penguin_id, to_r, to_c = action
                # Find penguin position
                state = tree.root.state
                turn_idx = state.turn_order[state.current_turn]
                player = state.players[turn_idx]
                penguin = next(p for p in player.penguins if p.id == penguin_id)
                return ((penguin.coords[0], penguin.coords[1]), (to_r, to_c))
        return False

    def notify_tournament_start(self):
        """Acknowledge tournament start."""
        return True

    def notify_tournament_result(self, won: bool):
        """Acknowledge tournament result."""
        return True

    def notify_eliminated(self):
        """Acknowledge elimination."""
        pass
