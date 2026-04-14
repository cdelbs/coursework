# Player-Referee Protocol Specification

## Overview

This document specifies the communication protocol between the **Referee** and **Player** components in the "Hey, That's My Fish!" game engine. The protocol defines the exact sequence of method calls, timing constraints, and behavioral expectations for both parties.
---

## Protocol Phases

The game proceeds through four phases, each with specific call sequences:

### Phase 1: Game Setup

**Sequence:**
```
Referee                           Player
   |                                |
   |------- setup(state, pid) ---->|
   |                                |
   |<------ (void return) ----------|
   |                                |
```

**Details:**
- **Called once** per player at game start
- Referee provides initial GameState (phase = "Placement")
- **Timeout**: 10 seconds
- **Failure**: Player disqualified if timeout or exception occurs

**Preconditions:**
- initial_state.phase == "Placement"
- player_id matches one of initial_state.turn_order

**Postconditions:**
- Player is ready for placement requests

---

### Phase 2: Placement Phase

**Sequence (repeated N * M times, where N = number of penguins per player and M is the number of players):**
```
Referee                                    Player
   |                                          |
   |-- choose_placement(state) --------------> |
   |                                          |
   |<-- return (row, col) --------------------|
   |                                          |
   |  [Referee validates and applies move]    |
   |                                          |
   |-- notify(new_state) -------------------->|
   |                                          |
   |<-- (void return) ------------------------|
   |                                          |
```

**Details:**
- **Repeated** until all players have placed all penguins
- Players take turns in round-robin order (state.turn_order)
- choose_placement() is only called when it's the player's turn
- **Timeout**: 30 seconds per placement
- **Failure**: Player disqualified; Referee skips their remaining placements

**Preconditions for choose_placement(tree):**
- state.phase == "Placement"
- state.turn_order[state.current_turn] == player_id
- Player has unplaced penguins

**Expected Return:**
- (row, col) tuple where both are integers
- Coordinates must correspond to a legal placement (unoccupied, active tile with 1 <= fish <= 5)
- Coordinates must be within board bounds

**Postconditions:**
- Referee applies placement via state.place_avatar(player_id, row, col)
- All players receive notify(new_state) with updated state
- Game transitions to Move phase when all penguins placed

---

### Phase 3: Movement Phase

**Sequence (repeated until game ends):**
```
Referee                                    Player
   |                                          |
   |-- choose_move(tree) -------------------->|
   |                                          |
   |    [Player analyzes tree]                |
   |                                          |
   |<-- return (penguin_id, row, col) --------|
   |    OR return None                        |
   |                                          |
   |  [Referee validates and applies move]    |
   |                                          |
   |-- notify(new_state) -------------------->|
   |    (to ALL players)                      |
   |                                          |
   |<-- (void return) ------------------------|
   |                                          |
```

**Details:**
- **Repeated** until no player can move (game over)
- Only current turn player's choose_move() is called
- **Timeout**: 30 seconds per move
- **Failure**: Player disqualified; all their penguins removed from board

**Preconditions for choose_move(tree):**
- tree.root.state.phase == "Move"
- tree.root.state.turn_order[tree.root.state.current_turn] == player_id

**Expected Return:**

**Case 1: Player can move**
- Returns (penguin_id, new_row, new_col) tuple
- penguin_id must belong to the current player
- (new_row, new_col) must be reachable from penguin's current position
- Move must correspond to a legal successor in the tree

**Case 2: Player cannot move**
- Returns None
- Referee verifies no legal moves exist via tree.successors(tree.root)
- If player timed-out, they are disqualified

**Postconditions:**
- Referee applies move via state.move_avatar(player_id, penguin_id, row, col)
- Player's score increases by fish count from old tile
- All players receive notify(new_state)
- Stuck players' penguins automatically removed

---

### Phase 4: Game Over

**Sequence:**
```
Referee                                    Player
   |                                          |
   |-- game_over(final_state, winners) ----->|
   |                                          |
   |<-- (void return) ------------------------|
   |                                          |
```

**Details:**
- **Called once** when `state.phase == "GameOver"`
- All players notified simultaneously
- No further method calls after this

**Preconditions:**
- final_state.phase == "GameOver"
- No player can make any legal moves
- winners list contains player IDs with highest score

**Postconditions:**
- Game session ends

---

## Complete Game Protocol (Full Sequence)

```
Referee                                    Player A              Player B
   |                                          |                     |
   |------- setup(state, 1) ----------------> |                     |
   |------- setup(state, 2) ----------------------------------->|
   |                                          |                     |
   | ============== PLACEMENT PHASE ==============
   |                                          |                     |
   |-- choose_placement(tree) --------------->|                     |
   |<-- (0, 0) -------------------------------|                     |
   |-- notify(new_state) -------------------->|                     |
   |-- notify(new_state) ------------------------------------------->|
   |                                          |                     |
   |-- choose_placement(tree) -------------------------------------->|
   |<-- (4, 4) --------------------------------------------------------------|
   |-- notify(new_state) -------------------->|                     |
   |-- notify(new_state) ------------------------------------------->|
   |                                          |                     |
   |   [... repeat until all penguins placed ...]
   |                                          |                     |
   | ============== MOVE PHASE ==============
   |                                          |                     |
   |-- choose_move(tree) -------------------->|                     |
   |<-- (0, 1, 2) ----------------------------|                     |
   |-- notify(new_state) -------------------->|                     |
   |-- notify(new_state) ------------------------------------------->|
   |                                          |                     |
   |-- choose_move(tree) -------------------------------------->|
   |<-- (0, 3, 3) -----------------------------------------------------------|
   |-- notify(new_state) -------------------->|                     |
   |-- notify(new_state) ------------------------------------------->|
   |                                          |                     |
   |   [... repeat until game ends ...]
   |                                          |                     |
   | ============== GAME OVER ==============
   |                                          |                     |
   |-- game_over(final_state, [1]) --------->|                     |
   |-- game_over(final_state, [1]) ----------------------------->|
   |                                          |                     |
```

---

## Error Handling

### Player Timeout
- If player exceeds time limit, they are disqualified
- Referee removes all their penguins from the board
- Game continues with remaining players

### Invalid Move/Placement
- If player returns illegal coordinates:
  - **First offense**: Referee re-requests with warning
  - **Second offense**: Referee re-requests with harsher warning
  - **Third offense**: Disqualification

### Player Exception
- If player method raises unhandled exception:
  - Player immediately disqualified
  - Exception logged by Referee

---

## API Usage Examples

### Example 1: Simple Greedy Player

```python
class Player(PlayerInterface):
    def __init__(self):
        self.player_id = None

    def setup(self, initial_state: GameState, player_id: int) -> None:
        self.player_id = player_id

    def choose_placement(self, state: GameState) -> Tuple[int, int]:
        best_pos = None
        max_fish = -1

        for tile in state.board:
            if tile.fish > max_fish and tile.occupied == None and tile.active == True:
                max_fish = tile.fish
                best_pos = (row, col)
        return best_pos

    def choose_move(self, tree: GameTree) -> Optional[Tuple[int, int, int]]:
        successors = list(tree.successors(tree.root))

        if not successors:
            return None

        best_action = None
        max_score_gain = -1

        for action, child_node in successors:
            _, penguin_id, row, col = action
            player = next(p for p in child_node.state.players
                         if p.pid == self.player_id)
            score_gain = player.score - tree.root.state.players[
                tree.root.state.current_turn].score

            if score_gain > max_score_gain:
                max_score_gain = score_gain
                best_action = action

        _, penguin_id, row, col = best_action
        return (penguin_id, row, col)

    def notify(self, new_state: GameState) -> None:
        pass

    def game_over(self, final_state: GameState, winners: List[int]) -> None:
        if self.player_id in winners:
            print(f"Player {self.player_id} won!")
```

---

## Invariants and Contracts

### Referee Guarantees:
1. setup() called exactly once before any other method
2. choose_placement() / choose_move() only called on player's turn
3. notify() called after every successful action
4. game_over() called exactly once at end
5. GameTree provided always has legal successors (unless game over)

### Player Guarantees:
1. Never mutate GameState or GameTree
2. Return values within timeout limits
3. Return only legal moves from tree successors
4. Handle all method calls without raising exceptions
