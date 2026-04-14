# Test Allocation of Players in TournamentManager
"""
Tests for TournamentManager functionality.
"""
from Fish.Admin.manager import TournamentManager
from Fish.Player.player import LocalPlayer

class FastPlayer(LocalPlayer):
    """Fast player for testing - uses depth=1 for instant decisions."""
    def __init__(self, name="player"):
        super().__init__(name=name, depth_hero_turns=1)

def test_tournament_manager_allocation() -> None:
    players = [FastPlayer(name=str(i)) for i in range(10)]
    manager = TournamentManager(players)
    manager._allocate_matches(0)
    total_players_allocated = sum(len(referee.players) for _ , referee in manager.referees)
    assert total_players_allocated == 10
    assert all(2 <= len(referee.players) <= 4 for _ , referee in manager.referees)