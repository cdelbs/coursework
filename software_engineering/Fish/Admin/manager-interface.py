# Fish/Admin/manager_interface.py
"""
Interfaces for running full tournaments of Fish.

Roles
- Manager orchestrates a tournament across many matches.
- Croupier prepares and hosts a single match table.
- Referee enforces rules and runs one match to completion.
- Players implement the PlayerInterface elsewhere.

This module defines contracts only. Implementations live in your concrete files.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

# These are runtime types in your codebase. We keep them as Any here to avoid import cycles.
GameState = Any
GameBoard = Any
PlayerHandle = Any  # a local player object or a remote proxy that obeys your PlayerInterface


# -----------------------------------------------------------------------------
# Shared data models
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class TournamentConfig:
    """High level knobs for a tournament run."""
    rows: int
    cols: int
    seats_per_table: int  # 2..4
    max_rounds: int       # manager may end earlier if standings are decided
    random_seed: Optional[int] = None


@dataclass(frozen=True)
class TableAssignment:
    """A single match plan made by the manager."""
    table_id: str
    players: List[PlayerHandle]


@dataclass(frozen=True)
class RoundPlan:
    """A full set of table assignments for one round."""
    round_index: int  # starting at 1
    tables: List[TableAssignment]


@dataclass(frozen=True)
class MatchEvent:
    """
    Streamed notifications from a running match.

    Examples of type values:
      "placement_started", "placement_done",
      "turn_started", "move_applied", "player_skipped",
      "player_eliminated", "match_finished"
    """
    table_id: str
    type: str
    payload: Dict[str, Any]


@dataclass(frozen=True)
class MatchResult:
    """Outcome of a single match as returned by the referee."""
    table_id: str
    winners: List[int]                 # player ids that tie for first
    scores: Dict[int, int]             # pid -> final score
    final_state: GameState
    eliminated: List[int]              # pids removed for misbehavior or stuck cleanup
    errors: Dict[int, str]             # optional explanation per eliminated pid


@dataclass(frozen=True)
class RoundResult:
    """Bundle of results for a completed round."""
    round_index: int
    matches: List[MatchResult]


@dataclass(frozen=True)
class TournamentResult:
    """Final standings and per round details."""
    standings: List[Tuple[int, int]]   # [(pid, total_points)], sorted by total_points desc
    rounds: List[RoundResult]


# -----------------------------------------------------------------------------
# Croupier interface
# -----------------------------------------------------------------------------

class CroupierInterface:
    """
    The croupier prepares and hosts one match.

    Responsibilities
    - Build the board for the requested dimensions.
    - Assign a seat order and color set.
    - Create the initial Placement phase GameState.
    - Ask the referee to run the match and return the result.

    Misbehavior and timeouts are handled by the referee. The croupier does not
    validate player actions. It can inject holes up front to shape the board.
    """

    def __init__(self, rows: int, cols: int, seed: Optional[int] = None) -> None:
        raise NotImplementedError

    # Board creation

    def build_board(self) -> GameBoard:
        """Return a board for this match. The board may include initial holes."""
        raise NotImplementedError

    # Seating

    def assign_seats(self, players: List[PlayerHandle]) -> List[PlayerHandle]:
        """
        Return players in seat order for this table.

        Seat order must be stable for the duration of the match.
        Your default may be the given order or age sorted if available.
        """
        raise NotImplementedError

    # Initial state

    def make_initial_state(self, board: GameBoard, players: List[PlayerHandle]) -> GameState:
        """
        Return a GameState in Placement phase with colors and penguins assigned.

        The state must be ready for the referee to run placements.
        """
        raise NotImplementedError

    # One stop

    def run_match(
        self,
        referee: "RefereeInterface",
        players: List[PlayerHandle],
        on_event: Optional[Callable[[MatchEvent], None]] = None,
    ) -> MatchResult:
        """
        Full flow:
          1) build_board
          2) assign_seats
          3) make_initial_state
          4) call referee.run(initial_state, players, on_event)
          5) return MatchResult
        """
        raise NotImplementedError


# -----------------------------------------------------------------------------
# Referee interface
# -----------------------------------------------------------------------------

class RefereeInterface:
    """
    The referee runs a single match to completion and enforces rules.

    Rules the referee must enforce
    - Valid placements on active unoccupied tiles.
    - Legal straight line movement with clear path.
    - Score updates and tile removal after moves.
    - Skip players with no legal move on their turn.
    - End the game when no player can move.
    - Eliminate a player on misbehavior and continue the match.

    Misbehavior examples
    - Timeouts during setup, placement, or move choice.
    - Returning an illegal coordinate or an illegal move.
    - Raising an exception during any call.
    """

    def run(
        self,
        initial_state: GameState,
        players: List[PlayerHandle],
        on_event: Optional[Callable[[MatchEvent], None]] = None,
        per_call_timeout_s: float = 30.0,
    ) -> MatchResult:
        """
        Drive the full match from Placement to GameOver.

        The referee owns the loop and is the single writer of GameState.
        Players see read only snapshots and return choices.

        Events may be streamed via on_event for observers and the manager.
        """
        raise NotImplementedError


# -----------------------------------------------------------------------------
# Manager interface
# -----------------------------------------------------------------------------

class ManagerInterface:
    """
    The manager runs a complete tournament across many rounds and tables.

    Responsibilities
    - Accept a pool of players and a TournamentConfig.
    - Make pairings for each round and spawn one croupier per table.
    - Use the referee to run each table and collect results.
    - Maintain standings and decide when the tournament ends.

    The manager does not validate moves. It delegates to croupier and referee.
    """

    def __init__(self, config: TournamentConfig) -> None:
        raise NotImplementedError

    # Registration

    def register_players(self, players: Iterable[PlayerHandle]) -> None:
        """Add players to the tournament pool."""
        raise NotImplementedError

    # Pairings

    def plan_round(self, round_index: int) -> RoundPlan:
        """
        Produce a RoundPlan with tables of size seats_per_table.

        You may implement swiss, random, or another policy.
        The plan must be deterministic given the same state and seed.
        """
        raise NotImplementedError

    # Execution

    def run_round(
        self,
        round_plan: RoundPlan,
        mk_croupier: Callable[[int, int, Optional[int]], CroupierInterface],
        referee: RefereeInterface,
        on_event: Optional[Callable[[MatchEvent], None]] = None,
    ) -> RoundResult:
        """
        For each table in the plan:
          - create a croupier
          - croupier.run_match(referee, players, on_event)
        Aggregate MatchResult values and return a RoundResult.
        """
        raise NotImplementedError

    # Standings

    def update_standings(self, round_result: RoundResult) -> None:
        """Update internal standings from the given round result."""
        raise NotImplementedError

    # Full run

    def run_tournament(
        self,
        mk_croupier: Callable[[int, int, Optional[int]], CroupierInterface],
        referee: RefereeInterface,
        on_event: Optional[Callable[[MatchEvent], None]] = None,
    ) -> TournamentResult:
        """
        Loop:
          for r in 1..max_rounds:
            plan = plan_round(r)
            rr = run_round(plan, mk_croupier, referee, on_event)
            update_standings(rr)
            decide whether to stop early
        Return final standings and all round details.
        """
        raise NotImplementedError
