import json
import asyncio
import importlib
import sys
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any, Union

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# WebSocket support (matches server.py)
from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed

# Import from hyphenated filename using importlib
player_interface_module = importlib.import_module('Fish.Common.player-interface')
PlayerInterface = player_interface_module.PlayerInterface

from Fish.Common.state import GameState
from Fish.Common.game_tree import GameTree

# ==============================================================================
# CUSTOM EXCEPTIONS
# ==============================================================================
# These exceptions represent the three failure modes for remote players:
# 1. Timeout - player too slow (DoS bug)
# 2. Disconnect - network failure or client crash (safety bug)
# 3. Protocol - malformed JSON or invalid responses (business logic bug)
# All three result in player elimination by the Referee.
# ==============================================================================

class RemotePlayerTimeoutError(Exception):
    pass


class RemotePlayerDisconnectError(Exception):
    pass


class RemotePlayerProtocolError(Exception):
    pass


# ==============================================================================
# REMOTEPLAYERPROXY CLASS
# ==============================================================================

class RemotePlayer(PlayerInterface):
    """
    Server-side proxy representing a remote player connected via TCP.

    Protocol Compliance:
        All network messages follow the Remote Interactions specification:
            [MethodName, [Argument1, Argument2, ...]]

        Examples:
            ["start", [true]]
            ["setup", [<state-json>]]
            ["tt", [<state-json>, <actions-json>]]
            ["end", [false]]

    Timeout Enforcement:
        Default values from logical protocol:
            - Name exchange: 10 seconds
            - Setup: 10 seconds
            - Placement: 30 seconds
            - Moves: 30 seconds
            - Notifications: 10 seconds
    """
    TIMEOUT_SETUP = 10         # setup() method call (logical protocol)
    TIMEOUT_PLACEMENT = 30     # choose_placement() (logical protocol)
    TIMEOUT_MOVE = 30          # choose_move() - DEFAULT (logical protocol)
    TIMEOUT_NOTIFY = 10         # notify(), game_over(), tournament methods

    def __init__(self, name: str, websocket: ServerConnection, demo=False):
        """
        Initialize a RemotePlayer proxy wrapping a WebSocket connection.

        Args:
            name: Player's display name (1-12 alphabetic ASCII characters)
                  Already validated by Server during handshake
                  Example: "Alice", "Bob", "Player123" (would fail - has digits)
                  This name serves as both display name and unique identifier (pid)

            websocket: WebSocket ServerConnection object connected to the client
        """
        self.name = name

        self.websocket = websocket
        self.demo = demo
        self.is_connected = True

        # Store the event loop that manages this websocket
        # This is critical for the sync-async bridge: when the synchronous
        # TournamentManager calls player methods from a worker thread, we need
        # to schedule WebSocket I/O on the main event loop.
        try:
            self.event_loop = asyncio.get_running_loop()
        except RuntimeError:
            # No loop running (shouldn't happen in normal server flow)
            self.event_loop = None

        

    def __repr__(self) -> str:
        """Human-readable representation for debugging."""
        return f"<RemotePlayer {self.name}>"

    def _run_async(self, coro):
        """
        Execute an async coroutine from synchronous code (tournament thread).

        How it works:
            1. TournamentManager runs in thread pool (asyncio.to_thread)
            2. Calls RemotePlayer.choose_placement() (sync method)
            3. choose_placement() needs to do WebSocket I/O (async)
            4. _run_async() schedules the coroutine on main event loop
            5. Worker thread blocks waiting for result
            6. Main event loop executes WebSocket operation
            7. Result returned to worker thread
            8. choose_placement() returns to TournamentManager
        """
        if self.event_loop is not None:
            future = asyncio.run_coroutine_threadsafe(coro, self.event_loop)
            return future.result()
        else:
            return asyncio.run(coro)

    def setup(self, initial_state: GameState, player_id: str) -> None:
        """
        Initialize the remote player for a new game.

        PROTOCOL FLOW:
            Server (Referee) calls: remote_player.setup(state, seat_id)
            RemotePlayer sends: ["playing-as", [<color>]]
            RemotePlayer sends: ["playing-with", [<opponent-colors>]]
            Client responds: (no response - void methods)

        TIMEOUT:
            10 seconds

        Args:
            initial_state: GameState in "Placement" phase with:
                          - Board fully initialized
                          - All players assigned colors
                          - All penguins created but not placed (placed=False)
                          - Turn order established

            player_id: This player's seat number (0-based index)
                      Corresponds to position in state.turn_order
        """
        my_color = None
        for p in initial_state.players:
            if p.pid == player_id:
                my_color = p.color
                break

        opponent_colors = [
            p.color for i, p in enumerate(initial_state.players)
            if p.pid != player_id
        ]
        print(f'in remoteplayer.setup() for {self.name}: colors created')
        try:
            playing_as_msg = ["playing-as", [my_color]]
            if self.demo:
                self._send_message(playing_as_msg, timeout=1)
            else:
                self._send_message(playing_as_msg, timeout=self.TIMEOUT_SETUP)

            playing_with_msg = ["playing-with", [opponent_colors]]
            if self.demo:
                self._send_message(playing_with_msg, timeout=1)
            else:
                self._send_message(playing_with_msg, timeout=self.TIMEOUT_SETUP)
            print(f'in remoteplayer.setup() for {self.name}: color messages sent')

        except (RemotePlayerTimeoutError, RemotePlayerDisconnectError,
                RemotePlayerProtocolError) as e:
            self._handle_error(e)

    def choose_placement(self, state: GameState) -> Tuple[int, int]:
        """
        Request a penguin placement position from the remote player.

        PROTOCOL FLOW:
            Server calls: position = remote_player.choose_placement(state)
            RemotePlayer sends: ["setup", [<serialized-state>]]
            Client responds: [row, col]
            RemotePlayer returns: (row, col)

        TIMEOUT:
            30 seconds

        VALIDATION RESPONSIBILITY:
            We validate the JSON structure (must be [int, int]), but the
            Referee validates the game rules. 

        Args:
            state: Current GameState in "Placement" phase

        Returns:
            (row, col)
        """
        print(f"in remoteplayer.chooseplacement() for {self.name}")
        state_json = self._serialize_state(state)

        message = ["setup", state_json]

        try:
            response:Any
            if self.demo:
                response = self._send_and_receive(message, timeout=1)
            else:
                response = self._send_and_receive(message, timeout=self.TIMEOUT_PLACEMENT)
            print(f"in remoteplayer.chooseplacement() for {self.name}: sent and received setup message")
            print(f"in remoteplayer.chooseplacement() for {self.name}: setup response = {response}")
            # VALIDATION LAYER 1: Structural validation
            # Ensure response is a list with exactly 2 elements
            if not isinstance(response, list) or len(response) != 2:
                raise RemotePlayerProtocolError(
                    f"Invalid placement response format: {response}. "
                    f"Expected [row, col] but got {type(response)}"
                )

            # VALIDATION LAYER 2: Type validation
            # Ensure both elements are integers (not floats, strings, etc.)
            row, col = response
            if not isinstance(row, int) or not isinstance(col, int):
                raise RemotePlayerProtocolError(
                    f"Placement coordinates must be integers: {response}. "
                    f"Got row={type(row)}, col={type(col)}"
                )

            return (row, col)

        except (RemotePlayerTimeoutError, RemotePlayerDisconnectError,
                RemotePlayerProtocolError) as e:
            self._handle_error(e)

    def propose_placement(self, state: GameState) -> Tuple[int, int]:
        """
        Wrapper for choose_placement to match Referee's expected interface.

        Args:
            state: Current GameState in "Placement" phase

        Returns:
            (row, col): Placement coordinates
        """
        return self.choose_placement(state)

    def choose_move(self, tree: GameTree) -> Optional[Tuple[int, int, int]]:
        """
        Request a move from the remote player.

        PROTOCOL FLOW:
            Server calls: move = remote_player.choose_move(tree)
            RemotePlayer sends: ["tt", [<state-json>, <actions-json>]]
            Client responds: [[from_row, from_col], [to_row, to_col]] or false
            RemotePlayer converts: (penguin_id, to_row, to_col) or None

        TIMEOUT:
            30 seconds

        Args:
            tree: GameTree with root state in "Move" phase

        Returns:
            (penguin_id, new_row, new_col): Move in engine format
            None: No legal moves available 
        """
        print(f"in remoteplayer.choosemove() for {self.name}")
        state_json = self._serialize_state(tree.root.state)

        actions_json = []

        message = ["take-turn", state_json, actions_json]

        try:
            response:Any
            if self.demo:
                response = self._send_and_receive(message, timeout=1)
            else:
                response = self._send_and_receive(message, timeout=self.TIMEOUT_MOVE)
            print(f"in remoteplayer.choosemove() for {self.name}: take-turn message sent and received")
            print(f"in remoteplayer.choosemove() for {self.name}: take-turn response = {response}")

            # CASE 1: Client has no legal moves
            # Response: false (JSON boolean, becomes Python False)
            if response is False:
                return None

            # CASE 2: Client is making a move
            # Response: [[from_row, from_col], [to_row, to_col]]

            # VALIDATION LAYER 1: Structural validation
            if not isinstance(response, list) or len(response) != 2:
                raise RemotePlayerProtocolError(
                    f"Invalid move response format: {response}. "
                    f"Expected [[from_r, from_c], [to_r, to_c]] or false"
                )

            from_pos, to_pos = response

            # VALIDATION LAYER 2: Position format validation
            if (not isinstance(from_pos, list) or len(from_pos) != 2 or
                not isinstance(to_pos, list) or len(to_pos) != 2):
                raise RemotePlayerProtocolError(
                    f"Invalid move coordinates format: {response}. "
                    f"Each position must be [row, col]"
                )

            # VALIDATION LAYER 3: Type validation
            from_row, from_col = from_pos
            to_row, to_col = to_pos

            if not all(isinstance(x, int) for x in [from_row, from_col, to_row, to_col]):
                raise RemotePlayerProtocolError(
                    f"Move coordinates must be integers: {response}"
                )

            # FORMAT CONVERSION: Spec → Engine
            penguin_id = self._find_penguin_at(
                tree.root.state,
                from_row,
                from_col
            )
            print(f"in remoteplayer.choosemove() for {self.name}: successfully found penguin")
            # VALIDATION LAYER 4: Semantic validation
            if penguin_id is None:
                raise RemotePlayerProtocolError(
                    f"No penguin belonging to {self.name} found at "
                    f"position ({from_row}, {from_col}). Player may be cheating "
                    f"or misunderstanding game state."
                )
            return (penguin_id, to_row, to_col)

        except (RemotePlayerTimeoutError, RemotePlayerDisconnectError,
                RemotePlayerProtocolError) as e:
            self._handle_error(e)

    def propose_move(self, tree: GameTree) -> Union[Tuple[Tuple[int, int], Tuple[int, int]], bool]:
        """
        Wrapper for choose_move to match Referee's expected interface.

        Args:
            tree: GameTree with current state

        Returns:
            [[from_row, from_col], [to_row, to_col]] if move available
            False if no legal moves
        """
        engine_move = self.choose_move(tree)

        if engine_move is None:
            return False

        penguin_id, to_row, to_col = engine_move

        state = tree.root.state

        
        current_turn_index = state.turn_order[state.current_turn]
        

        my_player = state.players[current_turn_index]
        from_row, from_col = my_player.penguins[penguin_id].coords

        return ((from_row, from_col), (to_row, to_col))

    def notify(self, new_state: GameState) -> None:
        """
        Notify remote player of state update (optional in remote protocol).

        Args:
            new_state: Updated GameState after some action occurred

        Returns:
            None (void method)
        """
        pass

    def game_over(self, final_state: GameState, winners: List[int]) -> None:
        """
        Notify remote player that the game has concluded.
        Sends the final game state so the GUI can display game-over screen.
        """
        try:
            state_json = self._serialize_state(final_state)
            message = ["game-over", state_json]
            if self.demo:
                self._send_message(message, timeout=1)
            else:
                self._send_message(message, timeout=self.TIMEOUT_NOTIFY)
        except (RemotePlayerTimeoutError, RemotePlayerDisconnectError,
                RemotePlayerProtocolError):
            # If notification fails, don't crash - player might be disconnected
            pass

    # ==========================================================================
    # TOURNAMENT-LEVEL METHODS
    # ==========================================================================
    # These methods are called by the Manager, not the Referee. They coordinate
    # the tournament lifecycle: starting, allocating to games, and ending.
    # ==========================================================================

    def notify_tournament_start(self) -> bool:
        """
        Notify remote player that the tournament is beginning.

        PROTOCOL FLOW:
            Manager calls: ack = remote_player.notify_tournament_start()
            RemotePlayer sends: ["start", [true]]
            Client responds: true
            RemotePlayer returns: True

        TIMEOUT:
            10 seconds

        Returns:
            bool: True if client acknowledged, False otherwise
                 Manager may choose to eliminate non-acknowledging players
        """
        message = ["start", True]

        try:
            if self.demo:
                self._send_message(message, timeout=1)
            else:
                self._send_message(message, timeout=self.TIMEOUT_NOTIFY)
            return True

        except (RemotePlayerTimeoutError, RemotePlayerDisconnectError,
                RemotePlayerProtocolError) as e:
            self.disconnect()
            return False

    def notify_tournament_result(self, won: bool) -> bool:
        """
        Notify remote player of round or tournament outcome.

        PROTOCOL FLOW:
            Manager calls: ack = remote_player.notify_tournament_result(True)
            RemotePlayer sends: ["end", [true]]
            Client responds: true (acknowledgment)
            Client either:
              - Waits for next "setup" message (more rounds)
              - Disconnects (tournament is over, determined by no more messages)

        TIMEOUT:
            10 seconds

        Args:
            won: True if this player won the current round/tournament,
                 False otherwise

        Returns:
            bool: True if client acknowledged, False otherwise
        """
        message = ["end", won]
        print(f"notify_tournament_result message: {message} for {self.name}")
        try:
            response:Any
            if self.demo:
                response = self._send_and_receive(
                    message,
                    timeout=1
                )
            else:
                response = self._send_and_receive(
                    message,
                    timeout=self.TIMEOUT_NOTIFY
                )
            print(f"Acknowledgement for round win sent and received for {self.name}")
            # VALIDATION: Expect 'true' acknowledgment
            if response is not True:
                raise RemotePlayerProtocolError(
                    f"Invalid tournament_result acknowledgment: {response}. "
                    f"Expected true but got {type(response)}"
                )
            print(f"received true for acknowledgement for {self.name}")
            return True
        except (RemotePlayerTimeoutError, RemotePlayerDisconnectError,
                RemotePlayerProtocolError) as e:
            self.disconnect()
            print(f"received false or timeout for acknowledgement for {self.name}")
            return False

    # ==========================================================================
    # NETWORK COMMUNICATION LAYER
    # ==========================================================================
    # These methods handle the low-level details of sending/receiving JSON
    # over TCP. They implement message framing, timeout enforcement, and
    # error handling.
    # ==========================================================================

    def _send_message(self, message: List, timeout: float = 5.0) -> None:
        """
        Send a JSON message to the client without expecting a response.

        Args:
            message: List in format [method_name, [args...]]
                    Example: ["start", [true]]

            timeout: Time limit for sending (WebSocket handles this internally)

        Returns:
            None
        """
        if not self.is_connected:
            raise RemotePlayerDisconnectError(
                f"Cannot send to {self.name}: Already disconnected"
            )

        try:
            json_str = json.dumps(message)

            async def send_async():
                await self.websocket.send(json_str)

            self._run_async(send_async())

        except ConnectionClosed as e:
            self.is_connected = False
            raise RemotePlayerDisconnectError(
                f"WebSocket connection lost to {self.name} during send: {e}"
            )

        except (TypeError, ValueError, OverflowError) as e:
            raise RemotePlayerProtocolError(
                f"Failed to encode message {message}: {e}"
            )

    def _receive_message(self, timeout: float) -> Any:
        """
        Receive and parse a JSON message from the client.

        Args:
            timeout: Maximum seconds to wait for response

        Returns:
            Any: Parsed JSON data
        """
        if not self.is_connected:
            raise RemotePlayerDisconnectError(
                f"Cannot receive from {self.name}: Already disconnected"
            )

        try:
            async def receive_async():
                raw = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=timeout
                )
                return raw
            raw = self._run_async(receive_async())

            if isinstance(raw, (bytes, bytearray)):
                json_str = raw.decode('utf-8')
            else:
                json_str = raw

            response = json.loads(json_str)
            return response

        except asyncio.TimeoutError:
            raise RemotePlayerTimeoutError(
                f"No response from {self.name} within {timeout} seconds"
            )

        except ConnectionClosed as e:
            self.is_connected = False
            raise RemotePlayerDisconnectError(
                f"WebSocket connection lost to {self.name} during receive: {e}"
            )

        except json.JSONDecodeError as e:
            raise RemotePlayerProtocolError(
                f"Malformed JSON from {self.name}: {e}. "
                f"Received: {json_str if 'json_str' in locals() else 'unknown'}"
            )

        except UnicodeDecodeError as e:
            raise RemotePlayerProtocolError(
                f"Invalid UTF-8 from {self.name}: {e}"
            )

    def _send_and_receive(self, message: List, timeout: float) -> Any:
        """
        Convenience method: Send a message and wait for response.

        Args:
            message: JSON message to send
            timeout: Time limit for response

        Returns:
            Any: Parsed response from client
        """
        self._send_message(message, timeout)
        return self._receive_message(timeout)

    # ==========================================================================
    # SERIALIZATION LAYER
    # ==========================================================================
    # These methods convert game objects (GameState, GameTree) to JSON-serializable
    # dictionaries. This is the boundary between Python objects and network protocol.
    # ==========================================================================

    def _serialize_state(self, state: GameState) -> Dict[str, Any]:
        """
        Convert GameState object to proper JSON object.

        STRUCTURE (Official Spec):
            {
                "players": [
                    {
                        "color": str,         # "red" | "white" | "brown" | "black"
                        "score": int,         # Fish collected (natural number)
                        "places": [           # Penguin positions
                            [int, int],       # Position: [row, col]
                            ...
                        ]
                    }
                ],
                "board": [                    # 2D array of integers
                    [int, int, ...],          # Row: 0=hole, 1-5=fish count
                    ...
                ]
                "phase": str
                "turn": int
            }

        Args:
            state: GameState object

        Returns:
            Dict[str, Any]: JSON-serializable dictionary
        """
        return {
            "players": [
                {
                    "pid": p.pid,
                    "color": p.color,
                    "score": p.score,
                    "places": [
                        list(penguin.coords) 
                        for penguin in p.penguins
                        if penguin.placed
                    ]
                }
                for p in state.players
            ],

            "board": [
                [
                    tile.fish if tile.active else 0
                    for tile in row
                ]
                for row in state.board.tiles
            ],
            "phase": state.phase,
            "turn": state.current_turn
        }

    def _find_penguin_at(self, state: GameState, row: int, col: int) -> Optional[int]:
        """
        Find which penguin belonging to this player is at the given position.

        Args:
            state: Current GameState to search
            row: Row coordinate to check
            col: Column coordinate to check

        Returns:
            int: Penguin ID (0-3) if found at position
            None: No penguin belonging to this player at position
        """
        player = next((p for p in state.players if p.pid == self.name), None)

        if not player:
            return None

        for penguin in player.penguins:
            if penguin.coords == (row, col) and penguin.placed:
                return penguin.id

        return None

    # ==========================================================================
    # ERROR HANDLING
    # ==========================================================================
    # These methods handle communication failures and ensure clean shutdown.
    # ==========================================================================

    def _handle_error(self, error: Exception) -> None:
        """
        Handle communication error by re-raising to eliminate the player.

        Does NOT call disconnect() because:
        - The client is likely blocked in propose_placement/propose_move
        - They won't process the disconnect message until they're unblocked
        - The exception will eliminate them anyway
        - They'll get disconnected at tournament end via close_conns()

        Args:
            error: The exception that occurred

        Returns:
            Never returns - always re-raises
        """
        # Don't call disconnect() here - just let the exception eliminate the player
        raise error

    def disconnect(self) -> None:
        """
        Close the WebSocket connection to the client.

        This is a fire-and-forget operation - it schedules the disconnect message
        to be sent on the event loop but doesn't wait for it to complete.
        This prevents blocking the Referee when eliminating players.
        """
        if self.is_connected:
            self.is_connected = False

            try:
                async def close_async():
                    try:
                        await self.websocket.send(json.dumps(["disconnect"]))
                    except:
                        pass

                # Fire-and-forget: schedule on event loop but don't wait
                if self.event_loop is not None:
                    asyncio.run_coroutine_threadsafe(close_async(), self.event_loop)
                    # Don't call future.result() - let it run in the background
            except:
                pass
