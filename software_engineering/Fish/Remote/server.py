from typing import List, Tuple, Any
import sys
from pathlib import Path
import json

import asyncio
from websockets.asyncio.server import serve, ServerConnection, broadcast
from websockets.exceptions import ConnectionClosed

from PyQt5.QtWidgets import QApplication

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Fish.Remote.remote_player import RemotePlayer

from Fish.Admin.manager import TournamentManager
from Fish.Remote.remote_observer import RemoteTournamentWidget, register_main_loop

app = QApplication([])


class TournamentServer:
    '''
    WebSocket-based tournament server for remote Fish game clients.

    Manages the full lifecycle of a remote tournament:
    1. Accepts WebSocket connections from remote clients
    2. Handles player signup with 30-second waiting periods
    3. Creates RemotePlayer proxies for registered players
    4. Runs the tournament using TournamentManager
    5. Broadcasts game state updates to spectators
    6. Closes all connections when tournament ends

    Signup Protocol:
        - Server accepts connections for up to two 30-second periods
        - Players must provide a name within 10 seconds of connecting
        - Names must be 1-12 alphabetical ASCII characters
        - Duplicate names are not allowed
        - Maximum 10 players accepted
        - Clients connecting without a name become spectators
        - Clients connecting after signup closes become spectators

    Tournament Requirements:
        - Minimum 5 players required to start
        - If fewer than 5 players after signup, server closes with notification
        - Players are ordered youngest-to-oldest by registration completion

    Attributes:
        host (str): Server hostname or IP address (default: 'localhost')
        port (int): Server port number (default: 8765)
        clients (List[Tuple[str, str, ServerConnection]]): Connected clients as (name, role, websocket)
            where role is either 'player' or 'obs' (observer/spectator)
        signup (bool): Whether signup period is still active
        t_manager (TournamentManager): Tournament manager instance (created after signup)

    '''
    def __init__(self, host: str = 'localhost', port: int = 8765, demo=False):
        self.host: str = host # localhost or ip addr to enable connection over net
        self.port: int = port # 8765 or any given port
        self.demo = demo
        self.clients: List[Tuple[str, str, ServerConnection]] = [] # list of (ID, player/obs, WebSocket)
        self.signup: bool = True
        self.t_manager: TournamentManager

    # Purpose: Validate uniqueness of a given name based on clients
    def check_names(self, name: str) -> bool:
        unique = True
        for client in self.clients:
            if client[0] == name:
                unique = False
        return unique
    
    # Purpose: Return the list of player clients
    def players_only(self) -> List[Tuple]:
        players = []
        for client in self.clients:
            if client[1] == 'player':
                players.append(client)
        return players
    
    # Purpose: Return the list of observers
    def observers_only(self) -> List[Tuple]:
        players = []
        for client in self.clients:
            if client[1] == 'obs':
                players.append(client)
        return players

    # Purpose: handle signup upon websocket connection
    async def signup_handler(self, ws: ServerConnection) -> None:
        print("handshake made")
        player_cap = 10
        if self.demo:
            player_cap = 1000
        if self.signup and len(self.players_only()) < player_cap: # signup period is still active
            await ws.send(json.dumps(["name request"]))
            print("name request sent")

            try: # must provide name within 10 seconds
                raw: Any
                if self.demo:
                    raw = await asyncio.wait_for(ws.recv(), timeout=1)
                else:
                    raw = await asyncio.wait_for(ws.recv(), timeout=10)  # str | bytes
            except TimeoutError:
                await ws.close(reason='signup timeout')
                return

            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode("utf-8")
            name = json.loads(raw)

            if name: # provided name and is registered as a player
                # enforce unique names/ids and name length
                if self.check_names(name) and isinstance(name, str) and 1 <= len(name) <= 12 and name.isascii() and name.isalpha():
                    self.clients.append((name, "player", ws))
                    print(f"player: {name}, is registered")
                else:
                    # strict/brutal enforcement
                    await ws.close(reason='Improper username or username is already taken.')
                    return
            else: # did not provide a name and is registered as observer
                self.clients.append(("", "obs", ws))
                print("A spectator has registered")
        else: # signup period is over and client is registered as observer
            await ws.close(reason='Registraton is over.')
            return

        try:
            await ws.wait_closed()  # keep alive until disconnect
        except ConnectionClosed: # remove client from list when disconnected
            for client in self.clients:
                if client[2] == ws:
                    self.clients.remove(client)

    # Purpose: Disconnect all clients by performing the closing handshake
    async def close_conns(self, reason="") -> None:
        disconnect_msg = json.dumps(["disconnect"])
        for client in self.clients:
            try:
                await client[2].send(disconnect_msg)
            except:
                pass 

        await asyncio.sleep(0.5)

        for client in self.clients:
            try:
                await client[2].close(reason=reason)
            except:
                pass

    # Purpose: Run the server
    async def run_server(self) -> None:
        server = await serve(self.signup_handler, self.host, self.port)
        server_task = asyncio.create_task(server.serve_forever())
        print(f"server is live at {self.host} on port {self.port}")
        waits = 0
        while len(self.players_only()) < 5 and waits < 2:
            waits += 1
            try:
                await asyncio.wait_for(asyncio.Future(), timeout=30)
            except TimeoutError:
                print(f'timeout #{waits} completed')
                if len(self.players_only()) >= 5:
                    self.signup = False

        if len(self.players_only()) < 5:
            print("Not enough players to start a tournament.")
            msg = json.dumps(["not enough players"])
            conns: List[ServerConnection] = [c[2] for c in self.clients]
            broadcast(conns, msg)
            server_task.cancel()
            server.close(close_connections=True)
            return
        
        r_players = []
        for client in self.clients:
            if client[1] == 'player':
                r_players.append(RemotePlayer(client[0], client[2], demo=self.demo))

        self.t_manager = TournamentManager(r_players, [c[2] for c in self.observers_only()], demo=self.demo)  

        self.t_manager.add_observer(RemoteTournamentWidget([c[2] for c in self.observers_only()]))

        msg = json.dumps(["start"])
        conns: List[ServerConnection] = [c[2] for c in self.clients]
        broadcast(conns, msg)
        await asyncio.to_thread(self.t_manager.run_tournament)
        winners = await asyncio.to_thread(self.t_manager.run_tournament)

        # At this point the tournament is over and TournamentManager has:
        #   - winners: list of PlayerInterface objects
        #   - failures: set of player IDs eliminated for non-normal reasons
        num_winners = len(winners)
        num_failures = len(getattr(self.t_manager, "failures", []))

        # Print JSON array: [number_of_winners, number_of_failures]
        # This is what xserver/xclients harness will read.
        print(json.dumps([num_winners, num_failures]))
        sys.stdout.flush()

        await self.close_conns(reason="Tournament has ended.")
        server_task.cancel()
        server.close()



async def main():
    # This is the loop that owns all websocket ServerConnection objects.
    loop = asyncio.get_running_loop()
    register_main_loop(loop)

    tserver = TournamentServer()
    await tserver.run_server()



if __name__ == "__main__":
    asyncio.run(main())





