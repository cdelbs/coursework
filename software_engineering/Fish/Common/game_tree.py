# C:\SoftwareEngineeringFish\fiddlers\Fish\Common\game_tree.py
from collections import deque
from typing import Callable, Generator, Optional, Tuple

from Fish.Common.state import GameState

class GameTreeNode:
    """
    Represents one node in the game tree.
    Each node corresponds to a GameState at the start of the Move phase.
    """

    def __init__(
        self,
        state: GameState,
        action: Optional[Tuple] = None,
        parent: Optional["GameTreeNode"] = None,
    ):
        self.state = state
        self.action = action
        self.parent = parent

    def is_terminal(self) -> bool:
        """Returns True if this node has no further moves (GameOver)."""
        return self.state.phase == "GameOver"

    def expand(self) -> Generator[Tuple[Tuple, GameState], None, None]:
        if self.is_terminal():
            return

        s = self.state
        pid_to_move = s.players[s.turn_order[s.current_turn]].pid
        current_player = next(p for p in s.players if p.pid == pid_to_move)
        legal_moves_found = False

        for penguin in current_player.active_penguins():
            r, c = penguin.coords
            old_tile = s.board.tiles[r][c]
            for r2, c2 in s.board.reachable_tiles(old_tile):
                new_tile = s.board.tiles[r2][c2]
                if new_tile.occupied is not None:
                    continue  # Skip if the destination is occupied

                next_state = s.next_state_after_move(
                    current_player.pid, penguin.id, r2, c2
                )
                legal_moves_found = True
                yield (("move", penguin.id, r2, c2), next_state)

        # If no legal moves were found, return None
        if not legal_moves_found:
            return

class GameTree:
    """
    Lazy game tree generator for the Move phase of the game only.
    """

    def __init__(self, root_state: GameState) -> None:
        if root_state.phase != "Move":
            raise ValueError("GameTree must start in the Move phase.")
        self.root = GameTreeNode(root_state)

    def successors(self, node: GameTreeNode) -> Generator:
        """Return a generator of (action, GameTreeNode) pairs for legal moves."""
        for action, next_state in node.expand():
            yield action, GameTreeNode(next_state, action=action, parent=node)

    # GameTreeNode, Tuple(Tuple, GameState)
    def query_action(self, node: GameTreeNode, action: Tuple) -> Optional[GameState]:
        """
        Return the GameState resulting from taking `action` at `node`,
        or None if the action is illegal.
        """
        for act, next_state in node.expand():
            if act == action:
                return next_state
        return None

    # GameTreeNode, Callable -> func result
    def apply_to_successors(self, node: GameTreeNode, func: Callable):
        """Apply a function to each directly reachable successor state."""
        for _, next_state in node.expand():
            func(next_state)

    # None -> GameTree
    def generate_tree_depth(self) -> "GameTree":
        """
        Iteratively expand the tree up to max_depth (player_count).
        Returns a new GameTree with nodes expanded up to depth.
        Note: This builds the entire tree in memory, which can be expensive.
        Consider using lazy evaluation (successors()) for large trees.
        """
        max_depth = len(self.root.state.players)
        # No need to deepcopy - GameTreeNode already creates independent references
        # and states are immutable via next_state_after_move()
        new_tree = GameTree(self.root.state)

        queue = deque([(0, new_tree.root)])

        while queue:
            depth, node = queue.popleft()

            if depth >= max_depth:
                break
            if node.is_terminal():
                continue

            for act, next_state in node.expand():
                child = GameTreeNode(next_state, action=act, parent=node)
                queue.append((depth + 1, child))

        return new_tree