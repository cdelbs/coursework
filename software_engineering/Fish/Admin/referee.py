# Fish/Admin/referee.py
from typing import Any, Dict, List, Tuple, Optional

import sys
import importlib
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import QTimer

from Fish.Common.gameboard import GameBoard, replace as replace_tile
from Fish.Common.state import GameState, Player as EnginePlayer, replace
from Fish.Common.game_tree import GameTree, GameTreeNode
from Fish.Player.player import LocalPlayer

player_interface_module = importlib.import_module('Fish.Common.player-interface')
PlayerInterface = player_interface_module.PlayerInterface

from Fish.Admin.abstract_observer import Observer

SpecAction = Tuple[Tuple[int, int], Tuple[int, int]]

class Referee:
    """
    Runs one local game. Single source of truth for state.
    Uses GameTree for legality and for applying moves.
    Does not read any player internals.
    """

    def __init__(self, board: GameBoard, players: List[PlayerInterface]) -> None:
        self.players = players[:]                         # seat i is pid i
        engine_players = [EnginePlayer(pid=p.name) for p in self.players]
        self.state = GameState(board, engine_players, "Initialization", 0)
        self.elims: List[Dict[str, Any]] = []

        self.observers : List[Observer] = []

    #-------------observer methods-------------
    def add_observer(self, observer: Observer):
        self.observers.append(observer)

    def remove_observer(self, observer: Observer):
        self.observers.remove(observer)

    def notify_observers(self):
        for obs in self.observers:
            obs.set_state(self.state)
            obs.update()
        QApplication.processEvents()

    # ---------- helpers

    def _from_to_for_engine_action(
        self, s: GameState, action: Tuple[str, int, int, int]
    ) -> SpecAction:
        _, peng_id, to_r, to_c = action
        pid = s.players[s.turn_order[s.current_turn]].pid
        hero = next(p for p in s.players if p.pid == pid)
        fr, fc = next(pg for pg in hero.penguins if pg.id == peng_id).coords
        return (fr, fc), (to_r, to_c)

    def _legal_map(self, node: GameTreeNode) -> Dict[SpecAction, GameTreeNode]:
        """Map spec actions to child nodes for the current seat."""
        out: Dict[SpecAction, GameTreeNode] = {}
        s = node.state
        tree = GameTree(s)
        for action, child in tree.successors(node):
            spec = self._from_to_for_engine_action(s, action)
            out[spec] = child
        return out

    def _eliminate(self, pid: str, reason: str) -> None:
        self.elims.append({"pid": pid, "reason": reason})
        self._wipe_player(pid)

        # apply changes to guis
        self.notify_observers()

    def _wipe_player(self, pid: str) -> None:
        """Turn all of pid tiles into holes and mark their penguins fallen."""
        s = self.state
        p = next(p for p in s.players if p.pid == pid)

        # remove standing penguins from the board
        new_tiles = [list(row) for row in s.board.tiles]
        for pg in p.penguins:
            if pg.placed and not pg.fallen and pg.coords[0] >= 0:
                r, c = pg.coords
                t = s.board.tiles[r][c]
                new_tiles[r][c] = replace_tile(t, fish=0, active=False, occupied=None)

        nb = GameBoard(s.board.rows, s.board.columns)
        nb.tiles = new_tiles
        s.board = nb

        # mark penguins
        npengs = []
        for pg in p.penguins:
            if pg.placed:
                npengs.append(replace(pg, fallen=True))
            else:
                npengs.append(replace(pg, placed=True, fallen=True, coords=(-1, -1)))
        new_p = replace(p, penguins=npengs)
        s.players = [new_p if q.pid == pid else q for q in s.players]

        s.eliminated.add(pid)

    def _next_turn_index_with_move(self, s: GameState) -> Optional[int]:
        """Find next seat that has any legal successor according to a tree view."""
        n = len(s.turn_order)
        i = s.current_turn
        for _ in range(n):
            i = (i + 1) % n
            probe = GameState(s.board, s.players, "Move", i)
            probe.turn_order = list(s.turn_order)
            probe.eliminated = set(s.eliminated)
            node = GameTreeNode(probe)
            if self._legal_map(node):
                return i
        return None

    # ---------- placement

    def _run_placement(self) -> None:
        while self.state.phase == "Placement":
            s = self.state
            pid: str = s.players[s.turn_order[s.current_turn]].pid
            turn = s.turn_order[s.current_turn]

            if pid in s.eliminated:
                print(f"Skipping eliminated player {pid} during placement.")
                s._advance_turn_after_placement()
                continue

            try:
                r, c = self.players[turn].propose_placement(s)
                s.place_avatar(pid, r, c)  # engine advances placement turn
            except Exception as ex:
                self._eliminate(pid, f"bad placement: {ex}")
                s._advance_turn_after_placement()
            
            #apply changes to guis
            self.notify_observers()

    # ---------- moves

    def _run_moves(self) -> None:
        while self.state.phase != "GameOver":
            s = self.state
            node = GameTreeNode(s)
            legal = self._legal_map(node)

            if not legal:
                nxt = self._next_turn_index_with_move(s)
                if nxt is None:
                    s.phase = "GameOver"
                    break
                # skip to next player who can move
                self.state = GameState(s.board, s.players, "Move", nxt)
                self.state.turn_order = list(s.turn_order)
                self.state.eliminated = set(s.eliminated)
                continue

            pid = s.players[s.turn_order[s.current_turn]].pid
            turn = s.turn_order[s.current_turn]
            try:
                proposal = self.players[turn].propose_move(GameTree(s))
            except Exception as ex:
                self._eliminate(pid, f"exception during move: {ex}")
                # after elimination, either someone can move or game ends next loop
                continue

            if proposal is False:
                self._eliminate(pid, "returned False though a legal move exists")
                continue

            child = legal.get(proposal)
            if child is None:
                self._eliminate(pid, "illegal move")
                continue

            # Apply by adopting the child state from the tree
            self.state = child.state

            #apply changes to guis
            self.notify_observers()

    # ---------- public entry

    def run(self) -> Dict[str, Any]:
        print("made it to ref.run()")
        for player in self.players:
            player.setup(self.state, player.name)
        self.notify_observers() #ensure observer is in start config
        self._run_placement()
        if self.state.phase != "GameOver":
            self._run_moves()

        scores = [{"pid": p.pid, "color": p.color, "score": p.score}
                  for p in self.state.players]
        top = max((s["score"] for s in scores), default=0)
        # Winners are players with top score who were NOT eliminated
        eliminated_pids = {elim["pid"] for elim in self.elims}
        winners: List[str] = [s["pid"] for s in scores
                             if s["score"] == top and s["pid"] not in eliminated_pids]
        self.notify_observers() #ensure observers display final game state

        winner_indices = [i for i, p in enumerate(self.state.players) if p.pid in winners]
        for player in self.players:
            player.game_over(self.state, winner_indices)

        return {
            "phase": self.state.phase,
            "winners": winners,
            "scores": scores,
            "eliminated": self.elims,
        }




