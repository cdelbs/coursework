# Test prompt_winners in TournamentManager

from Fish.Admin.manager import TournamentManager
from Fish.Player.player import LocalPlayer

class FastPlayer(LocalPlayer):
    """Fast player for testing - uses depth=1 for instant decisions."""
    def __init__(self, name="player"):
        super().__init__(name=name, depth_hero_turns=1)

def test_prompt_winners() -> None:
    players = [FastPlayer(name=str(i)) for i in range(4)]
    manager = TournamentManager(players)
    # Simulate that all players are winners
    manager.players = players.copy()
    manager.prompt_winners()
    # After prompting, all players should still be winners as they acknowledge
    assert len(manager.players) == 4
    remaining_names = {p.name for p in manager.players}
    original_names = {str(i) for i in range(4)}
    assert remaining_names == original_names
    