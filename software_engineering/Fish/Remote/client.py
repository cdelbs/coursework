import asyncio
import json
import sys
from pathlib import Path

from typing import List, Tuple, Dict, Union

import random
import string

from websockets.asyncio.client import ClientConnection
from websockets.asyncio.client import connect  # v15 style import

from PyQt5.QtWidgets import QApplication

from threading import Event
from inputimeout import inputimeout, TimeoutOccurred

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Fish.Common.drawboard import BoardWidget
from Fish.Admin.tournament_visualizer import TournamentWidget
from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState,Player, Penguin
from Fish.Common.game_tree import GameTree
from Fish.Player.strategy import Strategy


# Purpose: Convert the given json to a GameState object
def deserialize_state(state: Dict) -> GameState:
    state_json = state
    board_json = state_json["board"]
    players_json: List[Dict] = state_json["players"]

    board = GameBoard(len(board_json), len(board_json[0]), board_json)

    penguin_count_rule = {2: 4, 3: 3, 4: 2}
    total_penguins = penguin_count_rule.get(len(players_json), 3)

    players = []
    for j_player in players_json:
        player = Player(j_player["pid"], j_player["score"], j_player["color"])
        penguins = []

        places = j_player["places"]
        for penguin_id in range(total_penguins):
            if penguin_id < len(places):
                coords = places[penguin_id]
                penguin = Penguin(penguin_id, player, coords, placed=True)
            else:
                penguin = Penguin(penguin_id, player, (-1, -1), placed=False)
            penguins.append(penguin)

        player.penguins = penguins
        players.append(player)

    state = GameState(board, players, state_json["phase"], state_json["turn"])

    from Fish.Common.state import replace
    for player in state.players:
        for penguin in player.penguins:
            if penguin.placed and penguin.coords != (-1, -1):
                row, col = penguin.coords
                if state.board.in_bounds(row, col):
                    tile = state.board.tiles[row][col]
                    state.board.tiles[row][col] = replace(tile, occupied=penguin)

    return state

class ClientHumanPlayer():
    """
    Human player adapter for remote GUI-based gameplay.

    Bridges the gap between synchronous player interface and asynchronous GUI input
    using threading.Event for coordination. When the referee calls propose_placement()
    or propose_move(), this class blocks and waits for GUI callbacks to provide the
    user's choice.

    Attributes:
        name (str): Player's display name
        placement_result (Tuple[int, int] | None): Coordinates chosen during placement
        move_result (Tuple[Tuple[int, int], Tuple[int, int]] | None): Move coordinates
        placement_event (Event): Threading event signaling placement completion
        move_event (Event): Threading event signaling move completion
        cancelled (bool): Flag indicating player has disconnected
    """
    def __init__(self, name: str = "Human"):
        self.name = name
        self.strat: str
        self.placement_result = None
        self.move_result = None
        self.placement_event = Event()
        self.move_event = Event()
        self.cancelled = False

    def propose_placement(self, state: GameState) -> Tuple[int, int]:
        """
        Block and wait for the GUI to provide a placement via set_placement_choice().
        Returns (row, col) for penguin placement.
        """
        self.placement_result = None
        self.placement_event.clear()
        if self.strat == "human":
            # Process Qt events while waiting for human input
            app = QApplication.instance()
            while not self.placement_event.is_set() and not self.cancelled:
                app.processEvents()
        elif self.strat == "ai":
            self.placement_result = Strategy().choose_placement(state)

        if self.cancelled:
            raise Exception("Player disconnected during placement")

        return self.placement_result

    def propose_move(self, tree: GameTree) -> Union[Tuple[Tuple[int, int], Tuple[int, int]], bool]:
        """
        Block and wait for the GUI to provide a move via set_move_choice().
        Returns ((from_row, from_col), (to_row, to_col)) or False if no legal move.
        """
        self.move_result = None
        self.move_event.clear()

        
        if self.strat == "human":
            # Process Qt events while waiting for human input
            app = QApplication.instance()
            while not self.move_event.is_set() and not self.cancelled:
                app.processEvents()
        elif self.strat == "ai":
            self.move_result = Strategy().choose_move(tree)

        if self.cancelled:
            raise Exception("Player disconnected during move")

        return self.move_result

    def set_placement_choice(self, row: int, col: int) -> None:
        """Called by the GUI when the human clicks a tile during placement."""
        self.placement_result = (row, col)
        self.placement_event.set()

    def set_move_choice(self, from_row: int, from_col: int, to_row: int, to_col: int) -> None:
        """Called by the GUI when the human completes a move selection."""
        self.move_result = ((from_row, from_col), (to_row, to_col))
        self.move_event.set()


class TournamentClient():
    """
    WebSocket client for remote Fish tournament participation.

    Connects to a TournamentServer, handles the full client lifecycle including
    signup, game visualization, human player input, and tournament progression.
    Supports both player and spectator modes.

    Connection Lifecycle:
        1. Connect to server via WebSocket
        2. Receive "name request" and respond with username (or empty for spectator)
        3. Wait for "start" message when tournament begins
        4. Receive game state updates and respond to requests
        5. Display GUI for game visualization and input
        6. Handle disconnection and cleanup

    Player vs Spectator Mode:
        - Player: Interactive GUI with mouse input, must respond to placement/move requests
        - Spectator: Read-only GUI, observes tournament without participating

    Attributes:
        host (str): Server hostname or IP (default: "localhost")
        port (int): Server port number (default: 8765)
        ws (ClientConnection): Active WebSocket connection to server
        name (str): Player's username (or empty string for spectator)
        type (str): Client role - "player" or "obs" (observer)
        player (ClientHumanPlayer): Human player adapter for GUI input
        gui (BoardWidget): PyQt5 game visualization widget
        app (QApplication): Qt application instance for event loop management
    """
    def __init__(self, host: str = "localhost", port: int = 8765, demo=False):
        self.host = host
        self.port = port
        self.demo = demo
        self.ws: ClientConnection
        self.name: str
        self.type: str
        self.player = ClientHumanPlayer()
        self.gui: BoardWidget = None
        self.tgui: TournamentWidget = None
        self.app = QApplication([])

    # Purpose: handles incoming messages by calling associated methods
    async def message_handler(self, data):
        if data[0] == "name request":
            await self.name_request()
        elif data[0] == "not enough players":
            print("Not enough players to start a tournament.")
            await self.ws.close()
        elif data[0] == "start":
            print("Tournament is about to begin.")
        elif data[0] == "setup":
            state = deserialize_state(data[1])
            print(f"In tournamentclient.messagehandler()/setup for {self.name}: state successfully deserialized")
            await self.placement(state)
        elif data[0] == "take-turn":
            state = deserialize_state(data[1])
            await self.take_turn(state)
        elif data[0] == "end":
            result = data[1]
            print(f"[CLIENT {self.name}] Received 'end' message with result: {result}")
            await self.match_end(result)
        elif data[0] == "playing-as":
            color = data[1][0]
            self.play_as(color)
        elif data[0] == "playing-with":
            colors = data[1]
            self.play_with(colors)
        elif data[0] == "disconnect":
            await self.disconnect()
        elif data[0] == "game-over":
            # Receive final game state and display game-over screen
            state = deserialize_state(data[1])
            await self.show_game_over(state)
        elif data[0] == "B-gui update":
            state = deserialize_state(data[1])
            self.obs_gui_update(state)
        elif data[0] == "T-gui update":
            bracket = data[1]
            self.obs_tgui_update(bracket)
        else:
            raise ValueError(f"Received message is not an expected message type: {data}")
        
    # Purpose: Close a player's socket.
    async def disconnect(self):
        print("You are being disconnected")
        self.player.cancelled = True
        if self.gui is not None:
            self.gui.close()
            QApplication.processEvents()
        self.app.quit()
        await self.ws.close()

    # Purpose: Identify colors of opponents
    def play_with(self, colors):
        print("\nYou are playing against colors:")
        for color in colors:
            print(color)

    # Purpose: Identify player's color. 
    def play_as(self, color):
        print(f"\nYou are playing with the color: {color}")

    async def show_game_over(self, state: GameState):
        """Display the final game state with game-over screen."""
        print("\n=== GAME OVER ===")
        if self.gui is not None:
            self.gui.set_state(state)
            self.gui.update()
            QApplication.processEvents()
        else:
            # If GUI wasn't created yet, create it now to show the final state
            self.guisetup(state)
            self.gui.set_state(state)
            self.gui.update()
            QApplication.processEvents()

    # Purpose: Handle end of round acknowledgement with winning players
    async def match_end(self, result):
        print(f"[CLIENT {self.name}] match_end called with result: {result}")
        if result and not self.demo:
            # Use inputimeout for proper timeout support
            try:
                ack = await asyncio.to_thread(
                    inputimeout,
                    prompt="\nYou have won your match!\nEnter 'true' to acknowledge (you have 10 seconds): ",
                    timeout=10
                )
                if ack.strip().lower() == "true":
                    print(f"[CLIENT {self.name}] Sending acknowledgement")
                    await self.ws.send(json.dumps(True))  # Send boolean, not string
                    print(f"[CLIENT {self.name}] Acknowledgement sent successfully")
                else:
                    print(f"[CLIENT {self.name}] Invalid acknowledgement: {ack}")
                    await self.ws.close()
            except TimeoutOccurred:
                print(f"\n[CLIENT {self.name}] Acknowledgement timeout - you took too long")
                await self.ws.close()
            except Exception as e:
                print(f"\n[CLIENT {self.name}] Connection closed: {e}")
                await self.ws.close()
        elif result and self.demo:
            await self.ws.send(json.dumps(True))
        else:
            print("You have lost your match and are eliminated from the tournament.")
            await self.ws.close()

    # Purpose: Handle take_turn calls to players
    async def take_turn(self, state: GameState):
        self.gui.set_state(state)
        self.gui.update()
        QApplication.processEvents()

        try:
            choice = self.player.propose_move(GameTree(state))
            await self.ws.send(json.dumps(choice))
        except Exception as e:
            print(f"Move cancelled: {e}")

    # Purpose: Handle placement calls to players
    async def placement(self, state: GameState):
        if self.gui is None:
            self.guisetup(state)
        self.gui.set_state(state)
        self.gui.update()
        QApplication.processEvents()

        try:
            choice = self.player.propose_placement(state)
            await self.ws.send(json.dumps(choice))
        except Exception as e:
            # Player was disconnected or eliminated
            print(f"Placement cancelled: {e}")
            # Don't send anything, just let the connection close

    def obs_gui_update(self, state: GameState):
        if self.gui is None:
            self.guisetup(state)
        self.gui.set_state(state)
        self.gui.update()
        QApplication.processEvents()

    def obs_tgui_update(self, bracket: List):
        if self.tgui is None:
            self.tguisetup()
        self.tgui.set_state(bracket)
        self.tgui.update()
        QApplication.processEvents()

    def tguisetup(self):
        if self.type == "obs":
            self.tgui = TournamentWidget()
        self.tgui.show()

    # Purpose: Handle setting up gui BoardWidget for players
    def guisetup(self, state: GameState):
        state = state
        if self.type == "player":
            self.gui = BoardWidget(state.board, state,
                                   interactive=True, human_player=self.player)
        else:
            self.gui = BoardWidget(state.board, state, interactive=False)
            self.gui.fullscreen()
        self.gui.show()
        
    # Purpose: input desired username and send to server
    async def name_request(self):
        name:str
        if self.demo:
            name = ''.join(random.choices(string.ascii_letters, k=12))
        else:
            name = input("To register as a player: input username (1-12 characters)\n" \
                                "To register as a spectator: press Enter\n" \
                                "Username: ")
        if name:
            self.type = "player"
            strat: str
            if self.demo:
                strat = 'ai'
            else:
                strat = inputimeout("Will you be playing yourself or using a strategy algorithm?\n" \
                                    "(Type 'human' or 'ai): ", 10)
            if strat == "human":
                self.player.strat = strat
            elif strat == "ai":
                self.player.strat = strat
            else:
                print("Input error: defaulting to human")
                self.player.strat = "human"
        else:
            self.type = "obs"
        self.name = name
        await self.ws.send(json.dumps(name))


    # Purpose: connects to server and continuously listens for messages
    async def connect_to_server(self):
        uri = f"ws://{self.host}:{self.port}"

        async with connect(uri) as ws:
            self.ws = ws
            try:
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    await self.message_handler(data)
            except Exception as e:
                print("Connection closed:", repr(e))
            finally:
                # Ensure cleanup happens regardless of how connection closes
                self.player.cancelled = True
                if self.gui is not None:
                    self.gui.close()
                    QApplication.processEvents()
                self.app.quit()



async def main():
    tclient = TournamentClient()
    await tclient.connect_to_server()


if __name__ == "__main__":
    asyncio.run(main())
