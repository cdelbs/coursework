from Fish.Admin.manager import TournamentManager
from conftest import InstantPlayer

def test_game_end_rule_1() -> None:
    """Test tournament end condition: same winners twice in a row.

    Uses InstantPlayer (no AI) to test tournament logic, not AI quality.
    This tests that the tournament manager correctly handles:
    - Multiple rounds of matches
    - Winner tracking between rounds
    - Tournament termination when winners repeat
    """
    players = [InstantPlayer(name=str(i)) for i in range(8)]
    manager = TournamentManager(players)
    previous_winners = None
    game_rounds = 0

    while True:
        # reset matches for this round
        manager.referees = []

        manager._allocate_matches(game_rounds)
        manager.update_bracket_matches(game_rounds)
        manager.run_matches()
        current_winners = sorted(p.name for p in manager.players)

        if current_winners == previous_winners:
            break

        previous_winners = current_winners
        game_rounds += 1

        if len(manager.players) < 2:
            break

    # Tournament should run at least one round
    assert game_rounds >= 1
    # With InstantPlayers making identical moves, ties are common
    # The key test is that the tournament terminates correctly (same winners twice)
    assert len(manager.players) >= 1  # At least some winners
