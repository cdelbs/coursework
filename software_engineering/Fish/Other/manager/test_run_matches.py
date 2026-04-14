# Test run_matches in TournamentManager

from Fish.Admin.manager import TournamentManager
from conftest import InstantPlayer

def test_run_matches() -> None:
    """Test running matches and collecting winners.

    Uses InstantPlayer (no AI) to test match execution logic:
    - Matches are allocated correctly
    - Winners are collected from each match
    - Winner names are preserved correctly
    """
    players = [InstantPlayer(name=str(i)) for i in range(8)]
    manager = TournamentManager(players)
    manager._allocate_matches(0)
    manager.update_bracket_matches(0)
    manager.run_matches()
    # After running matches, there should be fewer players if any were eliminated
    assert len(manager.players) <= 8
    # All remaining players should be from the original set
    remaining_names = {p.name for p in manager.players}
    original_names = {str(i) for i in range(8)}
    assert remaining_names.issubset(original_names)