
# Manager Protocol

## Purpose

This document defines how a tournament manager runs a full Fish tournament across many matches. It explains the roles, the life cycle for a tournament, the messages and data the parts exchange, timing and misbehavior rules, and the expected behavior for pairings and standings. The goal is that another team could implement compatible components from this description.

## Roles

1. Manager orchestrates the tournament across rounds and tables.
2. Croupier prepares one match table. It builds the board, assigns seats and colors, and produces the initial placement state.
3. Referee runs one match to completion and enforces rules.
4. Players implement the PlayerInterface. They choose placements and moves. They never mutate shared state.

Turn order follows seat order assigned by the croupier. This replaces the age ordering from the early spec.

## Key terms

Tournament means many rounds.

Round means a set of concurrent matches.

Table means one match and its seat order.

Seat means a player position at a table, numbered from zero.

## Data contracts

All shapes below are logical contracts. You can carry them as Python objects or JSON. Field names are normative.

### TournamentConfig

```json
{
  "rows": 7,
  "cols": 8,
  "seats_per_table": 2,
  "max_rounds": 3,
  "random_seed": 42
}
```

### TableAssignment

```json
{
  "table_id": "R1-T3",
  "players": ["p17","p24"]
}
```

`players` is an ordered list. Order is the intended seat order unless the croupier applies its own seat policy. If the croupier changes order it must report the final order back in the first event.

### RoundPlan

```json
{
  "round_index": 1,
  "tables": [ { "table_id": "R1-T1", "players": ["p1","p2"] } ]
}
```

### MatchEvent

Emitted by the referee and croupier to observers and the manager.

```json
{
  "table_id": "R1-T1",
  "type": "move_applied",
  "payload": {
    "seat": 0,
    "from": [2,0],
    "to": [2,1],
    "fish_collected": 3,
    "turn_number": 12
  }
}
```

Event types that every implementation must support

1. placement_started
2. placement_done
3. turn_started
4. player_skipped
5. move_applied
6. player_eliminated
7. match_finished

### MatchResult

```json
{
  "table_id": "R1-T1",
  "winners": [0],
  "scores": { "0": 23, "1": 19 },
  "final_state": "<opaque snapshot>",
  "eliminated": [],
  "errors": {}
}
```

Seats are used as keys for winners and scores. If your implementation prefers player ids, you may carry both but seats must be present.

### RoundResult

```json
{
  "round_index": 1,
  "matches": [ { /* MatchResult */ } ]
}
```

### TournamentResult

```json
{
  "standings": [ ["p1", 3], ["p2", 1] ],
  "rounds": [ { /* RoundResult */ } ]
}
```

The second item in each pair is total tournament points. See scoring below.

## Life cycle

### Registration

1. The manager receives a list of players. Each entry includes a stable id and a handle that implements the PlayerInterface.
2. The manager verifies the pool size is at least seats per table times the number of tables it plans to run per round. The manager may keep a wait list.

### Planning a round

1. The manager selects players for the round and produces a RoundPlan.
2. The plan is deterministic given the current standings and the seed.
3. The plan defines the player lists per table in intended seat order.

Pairing policy is a manager choice. Examples include simple random and swiss by total points. The policy must be stated in the codebase and remain stable for grading.

### Running a round

For each table in the plan the manager does the following.

1. Create a croupier with rows, cols, and an optional seed.
2. The croupier builds a board. The croupier may remove tiles up front to improve gameplay.
3. The croupier assigns seats. If it changes order it must emit a placement_started event that includes the final seat mapping.
4. The croupier makes an initial GameState in Placement with colors and penguins assigned for each seat.
5. The manager asks the referee to run the match. The manager attaches an event sink to collect MatchEvent values.
6. The referee runs the match to completion and returns a MatchResult.
7. The manager aggregates all results into a RoundResult and updates standings.

### Ending the tournament

1. The manager stops after max_rounds or earlier if the policy says the standings are decided.
2. The manager returns a TournamentResult with standings and all round results.

## Rules that the referee enforces

1. Valid placements on active unoccupied tiles.
2. Legal straight line moves that stop before holes or avatars.
3. Score updates equal to fish on the origin tile.
4. Skip a player that cannot move on its turn.
5. End the match when no player can move.
6. Eliminate a player on misbehavior and continue the match.

Misbehavior includes timeouts, illegal coordinates, illegal moves, and raising an exception during any call.

## Timing

Per call timeout is thirty seconds by default. This includes setup, placement choice, and move choice. The referee enforces this and eliminates on violation. The manager does not set per call timers itself unless it needs an overall guardrail for a match.

## Skipping and starting turn semantics

If a match enters Move and the next player in seat order has no legal move the engine must advance to the next seat that can move. Strategy code must not be asked to move for a stuck player. This matches the tests and the engine behavior in this codebase.

## Determinism

The manager must be able to run a full tournament deterministically when given the same seed, player pool, and pairing policy. This implies the following.

1. The croupier board generator is seeded.
2. Seat assignment is deterministic for a given input order.
3. Pairings are deterministic for a given standings state and seed.

## Scoring

Default scoring mode is match win points.

1. Each match winner gets one tournament point. In a tie each winner gets one point.
2. Losers get zero points.
3. The manager keeps secondary statistics such as total fish captured for tie breaks across the tournament.

Alternative scoring modes are allowed if declared. For example sum of fish across rounds as primary points. If you choose an alternative mode, document it in the manager code and keep the TournamentResult shape the same.

## Concurrency and ordering

A manager may run tables in parallel. Events may arrive interleaved across tables. Each table id defines its own event order which must be preserved.

## Error handling

1. If a croupier fails to build a board the table is abandoned and all seats at that table are marked eliminated with an error string.
2. If a referee raises an error the manager records a technical failure for that table.
3. If a player misbehaves the referee eliminates the player and continues. At the end the MatchResult must include the eliminated seats and an error string per seat.

The tournament continues unless the manager policy says to abort.

## Observer channel

The manager may pass an event sink to every referee so that observers can consume events. The sink takes a MatchEvent and returns nothing. The manager may also mirror events to a log for replay.

## Compliance checklist

A conforming implementation provides the following.

1. A manager that accepts TournamentConfig, registers players, plans deterministic rounds, runs them through croupiers and a referee, updates standings, and returns a TournamentResult.
2. A croupier that can build boards, assign seats, produce initial placement state, and run a match through the referee.
3. A referee that enforces rules, timeouts, and misbehavior, and returns a MatchResult.
4. A PlayerInterface implementation that never mutates shared state and returns legal placements and moves.
5. Event emission for the required event types.
6. Deterministic behavior under the same seed.
