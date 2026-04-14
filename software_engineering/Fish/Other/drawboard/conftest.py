"""Shared fixtures and test helpers for drawboard tests."""
import math
import pytest


# ---- Shared Dummy Domain Objects ----


class Owner:
    """Minimal owner stub for GUI tests."""
    def __init__(self, pid, color="red"):
        self.pid = pid
        self.color = color


class Penguin:
    """Minimal penguin stub for GUI tests."""
    def __init__(self, owner, id=0, placed=True):
        self.owner = owner
        self.id = id
        self.placed = placed
        self.fallen = False


class DummyTile:
    """Minimal tile stub for GUI tests."""
    def __init__(self, r, c, fish=1, active=True):
        self.fish = fish
        self.coords = (r, c)
        self.active = active
        self.highlighted = False
        self.occupied = None


class DummyBoard:
    """Minimal board stub for GUI tests."""
    def __init__(self, rows=2, cols=3, reachable_map=None):
        self.rows = rows
        self.columns = cols
        self.tiles = [[DummyTile(r, c) for c in range(cols)] for r in range(rows)]
        self._reachable_map = reachable_map or {}

    def reachable_tiles(self, tile):
        """Return reachable tiles based on configured map."""
        return self._reachable_map.get(tile.coords, [])


class Player:
    """Minimal player stub for GUI tests."""
    def __init__(self, pid, penguins=None, color="red", score=0):
        self.pid = pid
        self.penguins = penguins or []
        self.score = score
        self.color = color

    def active_penguins(self):
        """Return penguins that haven't fallen."""
        return [p for p in self.penguins if not p.fallen]


class GameState:
    """Minimal game state stub for GUI tests."""
    def __init__(self, board=None, phase="Move", players=None, current_turn=0):
        self.board = board or DummyBoard()
        self.phase = phase
        self.players = players or []
        self.turn_order = [p.pid for p in self.players]
        self.current_turn = current_turn

    def place_avatar(self, player_id, row, col):
        """Stub for placement - override in tests if needed."""
        pass

    def move_avatar(self, player_id, penguin_id, row, col):
        """Stub for movement - override in tests if needed."""
        pass


# ---- Test Helpers ----


def hex_center(hex_size, row, col):
    """Calculate the pixel center of a hexagonal tile."""
    x = col * hex_size * 1.5 + 100
    y = row * hex_size * math.sqrt(3) + (col % 2) * (hex_size * math.sqrt(3) / 2) + 100
    return int(x), int(y)


def create_board_with_reachability(rows, cols, reachable_map):
    """
    Create a board with specific reachability rules.

    Args:
        rows: Number of rows
        cols: Number of columns
        reachable_map: Dict mapping (row, col) -> [(row, col), ...]

    Returns:
        DummyBoard instance
    """
    return DummyBoard(rows, cols, reachable_map)


def create_player_with_penguins(pid, num_penguins, color="red", placed=True):
    """
    Create a player with a specified number of penguins.

    Args:
        pid: Player ID
        num_penguins: Number of penguins to create
        color: Player color
        placed: Whether penguins are placed on board

    Returns:
        Player instance
    """
    owner = Owner(pid, color)
    penguins = [Penguin(owner, i, placed=placed) for i in range(num_penguins)]
    return Player(pid, penguins, color)


# ---- Pytest Fixtures ----
# Note: qapp fixture is provided by root conftest.py


@pytest.fixture
def dummy_board():
    """Fixture providing a basic DummyBoard instance."""
    return DummyBoard()


@pytest.fixture
def game_state(dummy_board):
    """Fixture providing a basic GameState instance."""
    return GameState(board=dummy_board)
