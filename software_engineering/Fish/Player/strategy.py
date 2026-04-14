# Fish/Player/strategy.py
from typing import List, Optional, Tuple
from time import sleep

from Fish.Common.game_tree import GameTree, GameTreeNode
from Fish.Common.state import GameState

EngineAction = Tuple[str, int, int, int]  # ("move", penguin_id, to_r, to_c)
SpecAction = Tuple[Tuple[int, int], Tuple[int, int]]
Child = Tuple[EngineAction, GameTreeNode]


class Strategy:
    """Depth limited maximin over hero turns. Default N2. Streams successors."""

    class NoLegalMoveError(Exception):
        """Raised when the current player has no legal moves at the root."""

        pass

    class NotInMovePhaseError(Exception):
        """Raised when choose_move is called but the tree's root is not in Move."""

        pass

    def __init__(self, depth_hero_turns: int = 2) -> None:
        """Initialize with a search depth that counts only the hero's turns."""
        if depth_hero_turns < 1:
            raise ValueError("depth_hero_turns must be at least 1")
        self.depth_hero_turns = depth_hero_turns

    # Placement
    def choose_placement(self, state: GameState) -> Tuple[int, int]:
        board = state.board
        for r in range(board.rows):
            for c in range(board.columns):
                t = board.tiles[r][c]
                if getattr(t, "active", False) and getattr(t, "occupied", None) is None:
                    return (r, c)
        raise RuntimeError("No legal placement available")

    def choose_move(self, tree: GameTree) -> Optional[SpecAction]:
        root_state = tree.root.state
        if root_state.phase != "Move":
            raise Strategy.NotInMovePhaseError("Root state is not in Move phase")

        hero_pid = root_state.players[root_state.turn_order[root_state.current_turn]].pid

        # New: if the root player has no legal moves, raise immediately
        if not self._player_can_move(root_state, hero_pid):
            raise Strategy.NoLegalMoveError("No legal moves for current player")

        best_val: Optional[int] = None
        best_actions: List[EngineAction] = []
        for action, child in tree.successors(tree.root):  # streamed
            v = self._search(tree, child, hero_pid, self.depth_hero_turns - 1)
            if best_val is None or v > best_val:
                best_val = v
                best_actions = [action]
            elif v == best_val:
                best_actions.append(action)

        if best_val is None:
            raise Strategy.NoLegalMoveError("No legal moves for current player")

        chosen = min(best_actions, key=lambda a: self._tie_key(root_state, hero_pid, a))
        return self._to_spec_action(root_state, hero_pid, chosen)

    # Depth limited minimax where depth counts only hero turns
    def _search(
        self,
        tree: GameTree,
        node: GameTreeNode,
        hero_pid: str,
        hero_turns_left: int,
        alpha: int = 0,
        beta: int = 0
    ) -> int:
        s = node.state

        # stop when game is over or hero quota is reached
        if s.phase == "GameOver" or hero_turns_left == 0:
            return self._utility(s, hero_pid)

        hero_to_move = s.players[s.turn_order[s.current_turn]].pid == hero_pid
        next_quota = hero_turns_left - 1 if hero_to_move else hero_turns_left

        saw_child = False
        if hero_to_move:
            best: Optional[int] = None
            for _a, child in tree.successors(node):
                saw_child = True
                v = self._search(tree, child, hero_pid, next_quota, alpha, beta)
                if best is None or v > best:
                    best = v
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            if saw_child:
                assert best is not None
                return best
        else:
            worst: Optional[int] = None
            for _a, child in tree.successors(node):
                saw_child = True
                v = self._search(tree, child, hero_pid, next_quota, alpha, beta)
                if worst is None or v < worst:
                    worst = v
                beta = min(beta, worst)
                if beta <= alpha:
                    break
            if saw_child:
                assert worst is not None
                return worst

        # no legal move for current player but game may continue
        if not self._any_moves_available(s):
            return self._utility(s, hero_pid)

        # pass to next player who can move and keep hero quota
        nxt = self._next_turn_index_with_move(s)
        if nxt is None or nxt == s.current_turn:
            return self._utility(s, hero_pid)

        pass_state = GameState(s.board, s.players, "Move", nxt)
        pass_state.turn_order = list(s.turn_order)
        pass_state.eliminated = set(s.eliminated)
        return self._search(tree, GameTreeNode(pass_state), hero_pid, hero_turns_left)

    # Helpers
    def _is_hero_turn(self, state: GameState, hero_pid: str) -> bool:
        return state.players[state.turn_order[state.current_turn]].pid == hero_pid

    def _utility(self, state: GameState, hero_pid: str) -> int:
        player = next(p for p in state.players if p.pid == hero_pid)
        return int(player.score)

    def _tie_key(
        self, state: GameState, hero_pid: str, action: EngineAction
    ) -> Tuple[int, int, int, int]:
        (fr, fc), (to_r, to_c) = self._from_to_for_engine_action(
            state, hero_pid, action
        )
        return (fr, fc, to_r, to_c)

    def _from_to_for_engine_action(
        self, state: GameState, hero_pid: str, action: EngineAction
    ) -> SpecAction:
        _tag, peng_id, to_r, to_c = action
        hero = next(p for p in state.players if p.pid == hero_pid)
        fr, fc = next(pg for pg in hero.penguins if pg.id == peng_id).coords
        return (fr, fc), (to_r, to_c)

    def _to_spec_action(
        self, state: GameState, hero_pid: str, action: EngineAction
    ) -> SpecAction:
        return self._from_to_for_engine_action(state, hero_pid, action)

    def _player_can_move(self, state: GameState, pid: str) -> bool:
        player = next(p for p in state.players if p.pid == pid)
        b = state.board
        for pg in player.active_penguins():
            r, c = pg.coords
            from_tile = b.tiles[r][c]
            for rr, cc in b.reachable_tiles(from_tile):
                if b.tiles[rr][cc].occupied is None:
                    return True
        return False

    def _any_moves_available(self, state: GameState) -> bool:
        return any(self._player_can_move(state, p.pid) for p in state.players)

    def _next_turn_index_with_move(self, state: GameState) -> Optional[int]:
        n = len(state.turn_order)
        i = state.current_turn
        for _ in range(n):
            i = (i + 1) % n 
            if self._player_can_move(state, state.players[state.turn_order[i]].pid):
                return i
        return None
