# Fish/Player/player.py
from typing import Tuple, Union

from Fish.Common.state import GameState
from Fish.Common.game_tree import GameTree
from Fish.Player.strategy import Strategy

SpecAction = Tuple[Tuple[int, int], Tuple[int, int]]

class LocalPlayer:
    """Stateless facade over Strategy."""

    def __init__(self, name: str = "101", depth_hero_turns: int = 2) -> None:
        self.name = name
        self.strategy = Strategy(depth_hero_turns=depth_hero_turns)

    def propose_placement(self, state: GameState) -> Tuple[int, int]:
        return self.strategy.choose_placement(state)

    def propose_move(self, tree: GameTree) -> Union[SpecAction, bool]:
        try:
            return self.strategy.choose_move(tree)
        except Strategy.NoLegalMoveError:
            return False
        
    def notify_tournament_start(self) -> bool:
        """Return True if the player acknowledges the start of the tournament."""
        return True

    def notify_tournament_result(self, won: bool) -> bool:
        """Return True if the player acknowledges the final result."""
        return True
