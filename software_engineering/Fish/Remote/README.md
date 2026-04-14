# Fish Remote Tournament System

This folder contains the remote tournament infrastructure for the Fish game, enabling distributed tournament play over WebSockets where players and spectators connect to a centralized tournament server.

## Purpose

The Remote system enables:
- Remote players to participate in tournaments via network connections
- Real-time GUI updates for both players and spectators
- Tournament management with distributed clients
- Asynchronous message-based protocol for game state synchronization

---

## File Organization

The files in this folder follow a conceptual organization based on the **remote tournament architecture**:

### **server.py** - Tournament Server
**Concept**: Central tournament coordinator that manages client connections and orchestrates tournament execution.

**Responsibilities**:
- Accept WebSocket connections from remote players and spectators
- Handle client signup with name validation (1-12 character unique names)
- Manage signup periods (two 30-second windows, minimum 5 players required, maximum 10 players allowed)
- Create `RemotePlayer` proxies for each connected player
- Delegate tournament execution to `TournamentManager`
- Broadcast disconnect messages and cleanly close all connections when tournament ends

**Key Components**:
- `TournamentServer` class: Main server coordinator
  - `signup_handler()`: Per-client connection handler
  - `run_server()`: Tournament lifecycle management
  - `close_conns()`: Graceful connection cleanup with disconnect broadcast

**Demo Mode**:
- When constructing a TournamentServer, there is an optional argument, demo.
- Assigning demo = True will:
  - Give randomized names to clients
  - Mandate all clients to be labeled as ai players
  - Limit all TCP communications throughout Remote to 1 second timeouts
  - Raise maximum number of player clients to 1000
  - All player clients will automatically acknowledge wins


### **client.py** - Tournament Client
**Concept**: Player/spectator client that connects to the tournament server and provides interactive GUI.

**Responsibilities**:
- Connect to tournament server via WebSocket
- Handle tournament protocol messages (`setup`, `take-turn`, `end`, `disconnect`, etc.)
- Provide interactive GUI for human players to make moves and placements
- Deserialize game states received from server
- Collect player input with timeout enforcement
- Clean up resources (GUI, QApplication, WebSocket) on disconnect

**Key Components**:
- `ClientHumanPlayer` class: Handles human player input via GUI and AI player input from strategy
  - `propose_placement()`: Blocks until GUI provides placement choice
  - `propose_move()`: Blocks until GUI provides move choice
  - Uses threading.Event for synchronization between GUI and async code

- `TournamentClient` class: Main client coordinator
  - `message_handler()`: Routes protocol messages to appropriate handlers
  - `match_end()`: Handles winner acknowledgement
  - `connect_to_server()`: Main message loop with cleanup in `finally` block
  - `disconnect()`: Cancels pending input and quits QApplication

### **remote_player.py** - Remote Player Proxy
**Concept**: Server-side proxy that implements the `PlayerInterface` and translates method calls to WebSocket protocol messages.

**Responsibilities**:
- Implement `PlayerInterface` for compatibility with existing tournament infrastructure
- Translate synchronous player API calls into asynchronous WebSocket messages
- Enforce timeout constraints on all player actions
- Handle protocol validation and errors
- Manage event loop bridge between synchronous tournament code and async WebSocket

**Key Protocol Messages**:
```
["setup", state]              -> [row, col, ...] placement positions
["take-turn", state]          -> [[from, to], ...] or false
["end", won: bool]            -> true (acknowledgement)
["game-over", state]          -> void
["disconnect"]                -> void
```

**Timeout Enforcement** (from logical protocol specification):
- Name exchange: 10 seconds
- Setup (initial placements): 10 seconds
- Placement (single penguin): 30 seconds
- Moves: 30 seconds
- Notifications (tournament results): 10 seconds

**Error Handling Strategy**:
- Game methods (`choose_placement`, `choose_move`, `setup`): Re-raise errors via `_handle_error()` to eliminate player. Does NOT send disconnect because client is blocked because of GUI and won't process it.
- Tournament methods (`notify_tournament_result`): Call `disconnect()` and return False. Client is listening and can process disconnect message.

### **remote_observer.py** - Remote Observer Implementations
**Concept**: Observer implementations that broadcast game/tournament updates to remote spectators.

**Responsibilities**:
- Implement `Observer` interface for referee and tournament manager
- Serialize game state and tournament bracket data to JSON
- Broadcast updates to all connected spectators via WebSocket
- Bridge synchronous Observer.update() to asynchronous WebSocket operations

**Key Components**:
- `RemoteBoardWidget`: Observes game state, broadcasts board/player updates
- `RemoteTournamentWidget`: Observes tournament bracket, broadcasts bracket updates

---

## How Remote Players Navigate the Game

### Initial Connection and Signup

1. **Start the client**:
   ```bash
   python Fish/Remote/client.py
   ```

2. **Registration prompt**:
   - To register as a **player**: Enter a unique username (1-12 ASCII characters)
   - To register as a **spectator**: Press Enter without typing anything

3. **Waiting for tournament start**:
   - Server waits for minimum 5 players
   - Two 30-second signup windows
   - Tournament starts automatically when conditions are met

### Playing the Game

#### **Placement Phase**
When it's your turn to place a penguin:

1. A GUI window appears showing the current game board
2. Your unplaced penguins are shown in the sidebar
3. Click on any valid tile (non-hole tile with no penguin) to place your penguin
4. Invalid placements will result in disqualification by the referee and inability to interact with the board
5. Wait for other players to complete their placements

#### **Movement Phase**
When it's your turn to move:

1. The GUI highlights the current player's turn in red in the sidebar
2. **First click**: Select one of your penguins to move
   - Click a tile with your penguin
   - Valid reachable tiles are highlighted in green
3. **Second click**: Click a highlighted destination tile
   - Click the same penguin again to deselect
   - Click another of your penguins to switch selection
4. Invalid moves will result in disqualification and inability to interact with the board

#### **Match Victory** (IMPORTANT!!!)
If you win a match:

1. Console displays: `"You have won your match!\nEnter 'true' to acknowledge (you have 10 seconds): "`
2. Type `true` and press Enter within 10 seconds
3. Failure to acknowledge results in elimination from the tournament
4. Winners who successfully acknowledge, advance to the next round

#### **Game Over**
When a game ends:

1. GUI displays "GAME OVER" banner
2. Scoreboard shows all players with their final scores
3. Winners are indicated by green WINNER text.
4. Window remains open to review final state

### Tournament Flow

1. **Round progression**: Winners from each match advance to the next round
2. **Final match**: When ≤4 players remain, a final match is run
3. **Tournament end conditions**:
   - Same winners in two consecutive rounds
   - Fewer than 2 players remain
   - Final match completes
4. **Cleanup**: All clients receive disconnect message and close gracefully

### Important Notes for Players

- **Timeouts are enforced**: You have limited time for each action (10-30 seconds)
- **One chance only**: Invalid moves or placements result in immediate disqualification
- **Stay connected**: Disconnecting eliminates you from the tournament
- **Acknowledgement required**: Winners must acknowledge victory within 10 seconds
- **GUI interaction**: All game actions are performed by clicking the GUI for Human Players

---

## Modifications to Code Outside Remote Folder

The following files in other folders were modified to support the remote tournament system:

### **Fish/Admin/manager.py**

**Modification**: Added support for remote observers and empty winner handling.

**Changes**:
1. **Constructor** (`__init__`, line 52-59):
   - Added `remote: List[ServerConnection]` parameter to accept WebSocket connections
   - Stores remote connections for observer broadcasting

2. **Match execution** (`run_matches`, line 118-132):
   - Lines 120-122: Attach `RemoteBoardWidget` observer to each referee when remote connections exist
   - Enables spectators to receive real-time game state updates

3. **Final match winner handling** (`tournament_over`, line 161-168):
   - Added check for empty `self.players` list before accessing `self.players[0]`
   - Prevents `IndexError` when all winners fail to acknowledge
   - Prints message: "No winners acknowledged - tournament ends with no winners"
   - Handles edge case where tournament ends with no valid winners

**Rationale**: The tournament manager needs to broadcast game updates to remote spectators and handle the case where winners are disqualified for failing to acknowledge victory.

---

### **Fish/Admin/referee.py**

**Modification**: Winner calculation excludes eliminated players.

**Changes**:
1. **Winner determination** (`run`, lines 207-210):
   - Previously: Winners were determined solely by highest score
   - Now: Winners must have highest score AND not be in `self.elims` list
   - Prevents eliminated/disqualified players from being declared winners

**Rationale**: Eliminated players (timeouts, invalid moves, disconnections) should not show being a winner even if they have the highest score.

---

### **Fish/Common/drawboard.py**

**Modification**: Enhanced game-over display and remote player support.

**Changes**:
1. **Constructor** (`__init__`, lines 95-120):
   - Added `interactive` parameter: Controls whether mouse input is enabled (default True)
   - Added `human_player` parameter: Optional `ClientHumanPlayer` instance for remote play
   - Added `player_index` parameter: Restricts interaction to specific player's turn
   - Enables view-only mode for spectators and turn-based interaction for remote players

2. **Game over winner calculation** (`paintEvent`, lines 164-168):
   - Handles case where all players are eliminated (max_score = 0)
   - Prevents showing false winners when everyone was disqualified
   - Returns empty list instead of declaring players with 0 score as winners

3. **Mouse interaction filtering** (`mousePressEvent`, lines 290-297):
   - Non-interactive mode: All clicks ignored (spectator view)
   - Remote player mode: Only process clicks during player's own turn
   - Prevents out-of-turn actions in remote play

4. **Placement handling** (lines 317-334):
   - When `human_player` is set: Notify player via `set_placement_choice()` instead of modifying state
   - Invalid placements sent to server for referee validation
   - Disqualification handled server-side rather than client-side

5. **Move handling** (lines 376-382):
   - Similar delegation to `human_player.set_move_choice()`
   - Client sends all moves to server regardless of local validity checks
   - Server referee performs authoritative validation

**Rationale**: The GUI must support both local play (direct state modification) and remote play (notify player proxy, server validates). Spectators need view-only access, and remote players should only interact on their turn.

---

## Protocol Overview

### Message Format
All messages are JSON-encoded arrays: `[message_type, args]`

### Client → Server Messages
- **Name registration**: `"username"` or `""` (empty string for spectator)
- **Placement response**: `[row, col]`
- **Move response**: `[[from_row, from_col], [to_row, to_col]]` or `false`
- **Acknowledgement**: `true` (boolean, not string)

### Server → Client Messages
- `["name request"]` - Request client to send username
- `["start"]` - Tournament is starting
- `["setup", state]` - Request initial penguin placements
- `["take-turn", state]` - Request move for current turn
- `["end", won: bool]` - Notify match result (true=won, false=lost)
- `["game-over", state]` - Game has ended, here's final state
- `["playing-as", color]` - Your assigned color
- `["playing-with", [colors]]` - Opponent colors
- `["disconnect"]` - Server is disconnecting you
- `["not enough players"]` - Tournament cancelled

### Observer Messages (Server → Spectators)
- `{"type": "B-gui update", "state": {...}}` - Game state update
- `{"type": "T-gui update", "bracket": [...]}` - Tournament bracket update

---

## Architecture Highlights

### Event Loop Integration
The remote system bridges three execution models:
1. **Synchronous tournament code** (Manager, Referee run in threads)
2. **Asynchronous WebSocket I/O** (server, client message loops)
3. **GUI event loop** (PyQt5 QApplication)

**Bridging mechanisms**:
- `asyncio.to_thread()`: Run tournament in thread pool from async context
- `asyncio.run_coroutine_threadsafe()`: Schedule async operations from sync code
- `QApplication.processEvents()`: Pump GUI events while waiting for input

### Fire-and-Forget Disconnect
`RemotePlayer.disconnect()` uses fire-and-forget pattern:

**Rationale**: Blocked clients can't process disconnect messages. Calling `future.result()` would deadlock. Fire-and-forget schedules the message but doesn't wait, allowing tournament to continue.

## Testing Notes

### Starting a Local Tournament

1. **Terminal 1 - Start server**:
   ```bash
   python Fish/Remote/server.py
   ```

2. **Terminals 2-6 - Start clients** (minimum 5 players):
   ```bash
   python Fish/Remote/client.py
   ```
   Enter unique usernames when prompted.

3. **Tournament runs automatically** when minimum players join within signup windows.

### Common Issues

1. **Client hangs on exit**: Ensure `inputimeout` is installed (`pip install inputimeout`)
2. **Timeout errors**: Check network connectivity, ensure server is reachable
3. **IndexError in manager**: Fixed - handles case where all winners fail to acknowledge
4. **GUI not responding**: Make sure you're clicking during your turn (name highlighted in red)

---

## Creating Custom AI Strategies

To create a custom AI strategy for your remote players, you need to replace the file [Fish/Player/strategy.py](../Player/strategy.py) with your own implementation. This section explains the required interface and the game components you'll work with.

### Required Interface

Your `strategy.py` file **must** contain a class named `Strategy` with the following two methods:

```python
class Strategy:
    def choose_placement(self, state: GameState) -> Tuple[int, int]:
        """
        Choose where to place a penguin during the placement phase.

        Args:
            state: The current game state

        Returns:
            (row, col): The coordinates where you want to place a penguin
        """
        pass

    def choose_move(self, tree: GameTree) -> Optional[SpecAction]:
        """
        Choose which penguin to move and where to move it.

        Args:
            tree: A game tree with the current state as root

        Returns:
            ((from_row, from_col), (to_row, to_col)): Source and destination coordinates
            OR None/False: If no legal move is available (will eliminate your player)
        """
        pass
```

### Required Imports

At the top of your `strategy.py` file, you must include these imports:

```python
from typing import List, Optional, Tuple
from Fish.Common.game_tree import GameTree, GameTreeNode
from Fish.Common.state import GameState
```

### Type Definitions

The following type aliases are useful for clarity:

```python
SpecAction = Tuple[Tuple[int, int], Tuple[int, int]]  # ((from_row, from_col), (to_row, to_col))
```

### Game Components Explained

#### **GameState**
Represents the current state of the game at a specific point in time.

**Key attributes**:
- `state.board`: The game board (see GameBoard below)
- `state.players`: List of Player objects in turn order
- `state.phase`: Current game phase - `"Placement"`, `"Move"`, or `"GameOver"`
- `state.turn_order`: List of player indices indicating turn sequence
- `state.current_turn`: Index into `turn_order` for the current player

**Example usage**:
```python
current_player_index = state.turn_order[state.current_turn]
current_player = state.players[current_player_index]
```

#### **GameBoard**
Represents the hexagonal tile grid where the game is played.

**Key attributes**:
- `board.rows`: Number of rows in the board
- `board.columns`: Number of columns in the board
- `board.tiles`: 2D list of Tile objects (`board.tiles[row][col]`)

**Key methods**:
- `board.in_bounds(row, col)`: Check if coordinates are valid
- `board.reachable_tiles(tile)`: Returns list of `(row, col)` tuples reachable from a tile in straight lines

**Tile attributes**:
- `tile.fish`: Number of fish on this tile (1-5)
- `tile.active`: Whether the tile exists (True) or is a hole (False)
- `tile.occupied`: The Penguin object on this tile, or None if empty

**Example usage**:
```python
for row in range(state.board.rows):
    for col in range(state.board.columns):
        tile = state.board.tiles[row][col]
        if tile.active and tile.occupied is None and tile.fish == 1:
            # This is an empty 1-fish tile
            return (row, col)
```

#### **Player**
Represents a player in the game.

**Key attributes**:
- `player.pid`: Player ID (string, unique identifier)
- `player.color`: Player's color (e.g., "red", "white", "brown", "black")
- `player.score`: Current score (accumulated fish)
- `player.penguins`: List of Penguin objects belonging to this player

**Key methods**:
- `player.active_penguins()`: Returns list of penguins that have been placed

**Example usage**:
```python
hero_player = state.players[state.turn_order[state.current_turn]]
print(f"Current player: {hero_player.pid} with score {hero_player.score}")
```

#### **Penguin**
Represents a single penguin on the board.

**Key attributes**:
- `penguin.id`: Penguin ID (0-3 for 2-player, 0-2 for 3-player, 0-1 for 4-player games)
- `penguin.coords`: Current position as `(row, col)` tuple
- `penguin.placed`: Boolean indicating if penguin has been placed on the board
- `penguin.player`: Reference to the Player object this penguin belongs to

**Example usage**:
```python
for penguin in current_player.penguins:
    if penguin.placed:
        row, col = penguin.coords
        # This penguin is at (row, col)
```

#### **GameTree**
Provides a tree-based view of the game for move search algorithms.

**Key attributes**:
- `tree.root`: The root GameTreeNode (current game state)

**Key methods**:
- `tree.successors(node)`: Generator yielding `(action, child_node)` tuples
  - `action`: Tuple `("move", penguin_id, to_row, to_col)`
  - `child_node`: GameTreeNode representing the state after this move

**GameTreeNode attributes**:
- `node.state`: The GameState at this node

**Example usage** (simple search):
```python
def choose_move(self, tree: GameTree) -> Optional[SpecAction]:
    best_score = -1
    best_move = None

    current_state = tree.root.state
    hero_pid = current_state.players[current_state.turn_order[current_state.current_turn]].pid

    for action, child_node in tree.successors(tree.root):
        # action is ("move", penguin_id, to_row, to_col)
        child_state = child_node.state

        # Find hero's score in child state
        hero = next(p for p in child_state.players if p.pid == hero_pid)

        if hero.score > best_score:
            best_score = hero.score
            # Convert action to SpecAction format
            _, peng_id, to_r, to_c = action
            hero_current = next(p for p in current_state.players if p.pid == hero_pid)
            penguin = hero_current.penguins[peng_id]
            from_r, from_c = penguin.coords
            best_move = ((from_r, from_c), (to_r, to_c))

    return best_move
```

### Minimal Working Example

Here's a minimal strategy that places penguins on the first available tile and always chooses the first legal move:

```python
from typing import Optional, Tuple
from Fish.Common.game_tree import GameTree
from Fish.Common.state import GameState

SpecAction = Tuple[Tuple[int, int], Tuple[int, int]]

class Strategy:
    def choose_placement(self, state: GameState) -> Tuple[int, int]:
        """Place penguin on first available tile."""
        board = state.board
        for row in range(board.rows):
            for col in range(board.columns):
                tile = board.tiles[row][col]
                if tile.active and tile.occupied is None:
                    return (row, col)
        raise RuntimeError("No legal placement available")

    def choose_move(self, tree: GameTree) -> Optional[SpecAction]:
        """Choose the first legal move available."""
        current_state = tree.root.state

        if current_state.phase != "Move":
            raise RuntimeError("Not in move phase")

        hero_pid = current_state.players[current_state.turn_order[current_state.current_turn]].pid
        hero = next(p for p in current_state.players if p.pid == hero_pid)

        # Try to find any legal move
        for action, child in tree.successors(tree.root):
            # action is ("move", penguin_id, to_row, to_col)
            _, peng_id, to_r, to_c = action
            penguin = hero.penguins[peng_id]
            from_r, from_c = penguin.coords
            return ((from_r, from_c), (to_r, to_c))

        # No legal moves available
        return None
```

### Important Considerations

#### **Timeout Constraints**
Your strategy methods are subject to timeout enforcement by the server:
- **Placement**: 30 seconds per penguin
- **Moves**: 30 seconds per move

If your strategy takes too long, your player will be eliminated from the tournament. Design your algorithms to complete well within these limits.

#### **Error Handling**
- Returning an invalid placement or move will result in **immediate disqualification**
- The referee validates all actions server-side
- If you return `None` or `False` from `choose_move()`, your player will be eliminated
- Only return `None`/`False` when you genuinely have no legal moves

#### **Game Rules to Remember**
1. **Placement phase**: Penguins can only be placed on non-hole tiles that are unoccupied
2. **Movement phase**: Penguins move in straight lines based on neighboring tiles (6 hex directions) until they reach another penguin or board edge
3. **Scoring**: When a penguin moves, the player gains fish equal to the fish count on the tile they left
4. **Victory condition**: Highest score when no players have legal moves remaining ('GameOver' Phase)

---

## Future Enhancements

Potential improvements to the remote system:

1. **Reconnection Support**: Allow disconnected players to rejoin mid-tournament
2. **Replay System**: Record tournament history for post-game analysis
3. **Authentication**: Add player authentication beyond username uniqueness
4. **TLS/SSL**: Encrypt WebSocket connections for security
5. **Spectator Chat**: Enable spectators to communicate during tournament
7. **Tournament Configuration**: Make game board size, fish counts, timeouts configurable
8. **Observer Connection Monitoring**: Track and log observer connections/disconnections, remove stale observers from list
9. **Add House Bots**: Allow tournaments and games to have AI players that are run by the house (server).

---
