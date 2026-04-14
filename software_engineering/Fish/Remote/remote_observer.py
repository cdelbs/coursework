from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPainter, QFont, QPen, QColor
from PyQt5.QtWidgets import QApplication, QWidget

from typing import List, Tuple, Dict, Any
import sys
from time import sleep
import json

from pathlib import Path

import asyncio
from websockets.asyncio.server import serve, ServerConnection, broadcast
from websockets.exceptions import ConnectionClosed

# The asyncio event loop that owns the websocket ServerConnection objects.
# This is set from server.py when the server starts.
MAIN_LOOP = None  # type: asyncio.AbstractEventLoop | None


def register_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    """
    Remember the main asyncio event loop so that observer updates coming
    from background threads can safely schedule websocket work on it.
    """
    global MAIN_LOOP
    MAIN_LOOP = loop


HERE = Path(__file__).resolve()

# Find the Fish package root
for parent in HERE.parents:
    if (parent / "Fish").is_dir():
        sys.path.insert(0, str(parent))
        break

from Fish.Admin.abstract_observer import Observer
from Fish.Common.state import GameState


def _serialize_state(state: GameState) -> Dict[str, Any]:
        """
        Convert GameState object to proper JSON object.
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


def run_async(coro) -> None:
    """
    Schedule an async coroutine from synchronous code *without blocking*.

    - If we're in the tournament's worker thread, this hands the coroutine to
      the main asyncio loop (the one that owns the ServerConnection objects)
      using call_soon_threadsafe.
    - If we're already on that loop, it just creates a task.
    """
    global MAIN_LOOP

    loop = MAIN_LOOP
    if loop is None:
        # Fallback: try the current thread's loop (useful for tests / local tools)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Last resort: run in a fresh loop (shouldn't happen in the real server).
            asyncio.run(coro)
            return

    if loop.is_running():
        # Fire-and-forget scheduling on the main loop; don't block the caller.
        loop.call_soon_threadsafe(asyncio.create_task, coro)
    else:
        # Mostly for unit tests (no running loop yet).
        loop.run_until_complete(coro)



class RemoteTournamentWidget(Observer):
    def __init__(self, lo_ws: List[ServerConnection]):
        super().__init__()
        self.lo_ws = lo_ws
        self.bracket: List[List[List[List[str, bool]]]] = []

    def set_state(self, bracket):
        self.bracket = bracket

    def update(self):
        """Sync wrapper that calls async update_async()"""
        self.update_async()

    def update_async(self):
        broadcast(self.lo_ws, json.dumps(["T-gui update", self.bracket]))

    '''
    def closeEvent(self, event):
        if self.tournament != None:
            self.tournament.remove_observer(self)
        super().closeEvent(event)
    '''


class RemoteBoardWidget(Observer):
    def __init__(self, lo_ws: List[ServerConnection]):
        super().__init__()
        self.lo_ws: List[ServerConnection] = lo_ws
        self.state: GameState

    def set_state(self, state):
        self.state = state

    def update(self):
        """Sync wrapper that calls async update_async()"""
        run_async(self.update_async())

    async def update_async(self):
        json_state = _serialize_state(self.state)

        broadcast(self.lo_ws, json.dumps(["B-gui update",
                                                json_state]))