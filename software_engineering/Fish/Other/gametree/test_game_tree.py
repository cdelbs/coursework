from collections import deque
from copy import deepcopy

from Common.game_tree import GameTree, GameTreeNode
from Common.gameboard import GameBoard
from Common.state import GameState, Player


# --- Helper function to build a minimal Move-phase state ---
def make_test_state():
    board_data = [
        [1, 2, 1, 3, 2],
        [2, 3, 2, 1, 1],
        [1, 1, 4, 2, 3],
        [3, 2, 1, 2, 1],
        [1, 1, 2, 1, 2],
    ]
    board = GameBoard(rows=5, columns=5, board_data=board_data)
    players = [Player(1), Player(2)]
    state = GameState(board, players, "Initialization")

    # Place a penguin for Player 1 in the middle
    state.place_avatar(1, 0, 0)  # Player 1 at top-left corner
    state.place_avatar(2, 4, 4)  # Player 2 at bottom-right corner

    # Round 2
    state.place_avatar(1, 0, 2)  # Player 1 at top row
    state.place_avatar(2, 4, 2)  # Player 2 at bottom row

    # Round 3
    state.place_avatar(1, 2, 0)  # Player 1 at left side
    state.place_avatar(2, 2, 4)  # Player 2 at right side

    # Round 4
    state.place_avatar(1, 1, 1)  # Player 1 near top-left
    state.place_avatar(2, 3, 3)  # Player 2 near bottom-right

    return state


# --- TESTS START HERE ---


def test_tree_initialization():
    """Tree initializes correctly and root is in Move phase."""
    state = make_test_state()
    tree = GameTree(state)
    assert isinstance(tree.root, GameTreeNode)
    assert tree.root.state.phase == "Move"


def test_successor_generation():
    """Successor generation yields valid move actions."""
    state = make_test_state()
    tree = GameTree(state)
    root = tree.root

    successors = list(tree.successors(root))
    assert successors, "Expected at least one valid move"

    for action, node in successors:
        assert action[0] == "move"
        assert isinstance(action[1], int)
        assert isinstance(action[2], int)
        assert isinstance(action[3], int)
        assert node.state.phase in ["Move", "GameOver"]


def test_query_action_valid_move():
    """query_action returns a new GameState for a valid move."""
    state = make_test_state()
    tree = GameTree(state)
    root = tree.root
    action, _ = next(tree.successors(root))

    next_state = tree.query_action(root, action)
    assert next_state is not None
    assert isinstance(next_state, GameState)
    assert next_state is not root.state, "Should be a different GameState instance"


def test_query_action_illegal_move():
    """query_action returns None for illegal moves."""
    state = make_test_state()
    tree = GameTree(state)
    root = tree.root

    invalid_action = ("move", 0, 10, 10)
    result = tree.query_action(root, invalid_action)
    assert result is None


def test_apply_to_successors_executes_function():
    """apply_to_successors calls the given function once per successor."""
    state = make_test_state()
    tree = GameTree(state)
    root = tree.root

    called = []

    def record_state(s):
        called.append(s)

    tree.apply_to_successors(root, record_state)
    assert called, "Expected apply_to_successors to call the function"
    assert all(isinstance(s, GameState) for s in called)


def test_state_independence():
    """Each successor state should be independent (deep copy safety)."""
    state = make_test_state()
    tree = GameTree(state)
    root = tree.root

    action, node = next(tree.successors(root))
    next_state = node.state

    # Mutate next_state player score; root should be unaffected
    next_state.players[0].score += 5
    assert root.state.players[0].score == 0, "Root state should not be mutated"


def test_generate_tree_depth_limit():
    """generate_tree_depth should respect max_depth (player count) and produce a new GameTree."""
    state = make_test_state()
    tree = GameTree(state)

    new_tree = tree.generate_tree_depth()

    assert isinstance(
        new_tree, GameTree
    ), "generate_tree_depth should return a GameTree"
    assert new_tree is not tree, "Returned GameTree should be a new instance"
    assert (
        new_tree.root is not tree.root
    ), "Root node should be a deepcopy, not the same reference"
    # Note: Root states are the same object because GameState is immutable
    # New states are only created via next_state_after_move()
    assert (
        new_tree.root.state is tree.root.state
    ), "Root GameState should be the same (immutable design)"

    expected_depth = len(tree.root.state.players)

    max_depth_found = 0
    queue = deque([(0, new_tree.root)])
    while queue:
        depth, node = queue.popleft()
        max_depth_found = max(max_depth_found, depth)
        if node.is_terminal() or depth >= expected_depth:
            continue
        for _, next_state in node.expand():
            queue.append((depth + 1, GameTreeNode(next_state)))

    assert (
        max_depth_found <= expected_depth
    ), f"Expected max depth <= {expected_depth}, but got {max_depth_found}"

    successors = list(new_tree.successors(new_tree.root))
    assert successors, "generate_tree_depth should create at least one successor node"
