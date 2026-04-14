# The tournament ends when there are too few players for a single game

from Fish.Admin.manager import TournamentManager
from Fish.Player.player import LocalPlayer

class FastPlayer(LocalPlayer):
    """Fast player for testing - uses depth=1 for instant decisions."""
    def __init__(self, name="player"):
        super().__init__(name=name, depth_hero_turns=1)

def test_game_end_rule_2() -> None:
    players = [FastPlayer(name=str(i)) for i in range(1)]
    manager = TournamentManager(players)
    manager.run_tournament()
    assert manager.tournament_over(previous_winners=[]) is True