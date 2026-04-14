# Fish/Other/manager/conftest.py
"""Shared fixtures and test utilities for manager tests."""
import pytest
from Fish.Player.player import LocalPlayer
from Fish.Common.game_tree import GameTree

class InstantPlayer(LocalPlayer):
    """
    Ultra-fast player for testing - returns first valid move instantly.
    No AI computation, just picks the first available action.
    """
    def setup(self, gameState, player_id):
        pass
    
    def game_over(self, gameState, player_id):
        pass
    
    def __init__(self, name="player"):
        # Don't call super().__init__ to avoid creating Strategy
        self.name = name

    def propose_placement(self, state):
        """Return first valid placement position."""
        # Find first active, unoccupied tile
        for r in range(state.board.rows):
            for c in range(state.board.columns):
                tile = state.board.tiles[r][c]
                if tile.active and tile.occupied is None:
                    return (r, c)
        # Should never happen in a valid game
        raise Exception("No valid placement tiles found")

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
