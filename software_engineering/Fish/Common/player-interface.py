# Fish/Common/player-interface.py
"""
Defines the API contract between a Player and the Referee for our Fish game.

This interface is logic level only. All objects the Referee passes in must
be treated as read only by the Player. The Referee is the single source of truth.
"""

from typing import List, Optional, Tuple

from Fish.Common.game_tree import GameTree
from Fish.Common.state import GameState


class PlayerInterface:
    """
    Contract that all player components must follow when they talk to the Referee.

    Ground rules
      • The Referee owns the game state. The Player must not mutate any object it receives.
      • The Player returns choices only. The Referee validates and applies them.
      • Time limits are enforced by the Referee. Unhandled exceptions or timeouts eliminate the Player.
      • Turn order follows fixed seat order that the croupier assigns at game start.
      • If the current seat has no legal move when a turn begins, the engine skips that seat.
        In that case the Referee will not call choose_move for that seat.
    """

    # SETUP

    def setup(self, initial_state: GameState, player_id: int) -> None:
        """
        Prepare the Player for a new match.

        Purpose
          Initialize any local memory the Player needs before play begins.

        Inputs
          initial_state: a state in Placement with a board, seats, colors, and penguins assigned
          player_id: the numeric seat id for this Player in the current match

        Contract
          • Treat initial_state as read only
          • Return None
          • Must not raise

        Time limit
          Up to 10 seconds
        """
        raise NotImplementedError

    # PLACEMENT PHASE

    def choose_placement(self, state: GameState) -> Tuple[int, int]:
        """
        Pick a tile for the next penguin during Placement.

        Purpose
          Choose a legal coordinate for one penguin that belongs to this Player.

        Inputs
          state: a read only snapshot in Placement
                 state.turn_order[state.current_turn] is this Player's seat when called

        Return
          (row, col) as zero based coordinates of an active and unoccupied tile with fish in 1..5

        Contract
          • Tile must be legal for placement
          • Must not mutate state
          • Must not raise

        Time limit
          Up to 30 seconds
        """
        raise NotImplementedError

    # MOVE PHASE

    def choose_move(self, tree: GameTree) -> Optional[Tuple[int, int, int]]:
        """
        Pick a move during the Move phase.

        Purpose
          Select which penguin to move and where to move it.

        Inputs
          tree: a read only game tree whose root holds the current Move state
                • The root state turn belongs to this Player when called
                • tree.successors(tree.root) yields all legal engine actions for this turn

        Return
          • (penguin_id, new_row, new_col) for a legal move from the root, or
          • None if this Player cannot move any penguin

        Contract
          • Must not mutate the tree or the state inside it
          • If internal strategy raises on no legal moves, catch it and return None
          • Must not raise otherwise

        Time limit
          Up to 30 seconds
        """
        raise NotImplementedError("Subclasses must implement choose_move()")

    # NOTIFICATIONS

    def notify(self, new_state: GameState) -> None:
        """
        Receive the latest applied state after any action.

        Purpose
          Let the Player observe progress and keep local notes if desired.

        Inputs
          new_state: a read only snapshot after a placement or a move

        Contract
          • Must not mutate new_state
          • Return None
          • Must not raise
        """
        raise NotImplementedError

    def game_over(self, final_state: GameState, winners: List[int]) -> None:
        """
        Inform the Player that the match is complete.

        Purpose
          Allow cleanup and recording of results.

        Inputs
          final_state: a read only snapshot with phase GameOver
          winners: list of seat ids that achieved the top score, one or more seats

        Contract
          • Return None
          • Must not raise
        """
        raise NotImplementedError("Subclasses must implement game_over()")
