"""Tests for mouse interactions with the BoardWidget."""

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtTest import QTest

from Common.drawboard import BoardWidget
from conftest import (
    DummyBoard,
    GameState,
    Owner,
    Penguin,
    Player,
    hex_center,
    create_player_with_penguins,
)


# ---- Selection and Reselection Tests ----


def test_click_selects_penguin_and_highlights_reachables(qapp):
    """Clicking a penguin should select it and highlight reachable tiles."""
    board = DummyBoard(rows=2, cols=2, reachable_map={(0, 0): [(0, 1)]})
    player = create_player_with_penguins(1, num_penguins=1, color="red")
    gs = GameState(board=board, phase="Move", players=[player, Player(2, color="white")])

    # Place penguin on (0,0)
    board.tiles[0][0].occupied = player.penguins[0]

    w = BoardWidget(board, gs, hex_size=40)
    w.show()
    QTest.qWaitForWindowExposed(w)

    # Click center of (0,0)
    cx, cy = hex_center(40, 0, 0)
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(cx, cy))

    assert w.selected == (0, 0)
    assert (0, 1) in set(w.reachables)


def test_reselect_another_penguin(qapp):
    """Clicking another owned penguin should reselect it."""
    board = DummyBoard(rows=2, cols=3, reachable_map={(0, 0): [(0, 1)], (0, 1): [(0, 2)]})

    # Create player with 2 penguins
    owner = Owner(1, "red")
    p0, p1 = Penguin(owner, 0), Penguin(owner, 1)
    player = Player(1, [p0, p1], color="red")
    gs = GameState(board=board, phase="Move", players=[player, Player(2, color="white")])

    # Place both penguins
    board.tiles[0][0].occupied = p0
    board.tiles[0][1].occupied = p1

    w = BoardWidget(board, gs, hex_size=40)
    w.show()
    QTest.qWaitForWindowExposed(w)

    # Click (0,0) → selected=(0,0)
    cx0, cy0 = hex_center(40, 0, 0)
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(cx0, cy0))
    assert w.selected == (0, 0)

    # Click (0,1) which also has owned penguin → reselection
    cx1, cy1 = hex_center(40, 0, 1)
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(cx1, cy1))
    assert w.selected == (0, 1)


def test_click_empty_tile_first_is_noop(qapp):
    """Clicking an empty tile when nothing is selected does nothing."""
    board = DummyBoard(rows=2, cols=3)
    gs = GameState(board=board, phase="Move", players=[Player(1, color="red")])

    w = BoardWidget(board, gs, hex_size=40)
    w.show()
    QTest.qWaitForWindowExposed(w)

    cx, cy = hex_center(40, 1, 2)
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(cx, cy))

    assert w.selected is None
    assert w.reachables == []


def test_click_same_tile_twice_is_noop(qapp):
    """Clicking the same selected tile again should deselect it."""
    board = DummyBoard(rows=1, cols=2, reachable_map={(0, 0): [(0, 1)]})
    player = create_player_with_penguins(1, num_penguins=1, color="red")

    # Create game state that would raise if move is called
    gs = GameState(board=board, phase="Move", players=[player, Player(2, color="white")])
    gs.move_avatar = lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not move on same-tile click"))

    board.tiles[0][0].occupied = player.penguins[0]

    w = BoardWidget(board, gs, hex_size=40)
    w.show()
    QTest.qWaitForWindowExposed(w)

    # First click selects (0,0)
    cx, cy = hex_center(40, 0, 0)
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(cx, cy))
    assert w.selected == (0, 0)
    assert (0, 1) in set(w.reachables)

    # Second click on same tile should deselect (not trigger move)
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(cx, cy))
    assert w.selected is None
    assert w.reachables == []


# ---- Move Execution Tests ----


def test_valid_move_clears_selection(qapp):
    """Clicking a reachable tile should execute move and clear selection."""
    board = DummyBoard(rows=1, cols=2, reachable_map={(0, 0): [(0, 1)]})
    player = create_player_with_penguins(1, num_penguins=1, color="red")
    gs = GameState(board=board, phase="Move", players=[player, Player(2, color="white")])

    # Track if move was called
    gs.moved = False
    original_move = gs.move_avatar
    gs.move_avatar = lambda *a, **k: (setattr(gs, 'moved', True), original_move(*a, **k))

    board.tiles[0][0].occupied = player.penguins[0]

    w = BoardWidget(board, gs, hex_size=40)
    w.show()
    QTest.qWaitForWindowExposed(w)

    # Select (0,0)
    cx0, cy0 = hex_center(40, 0, 0)
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(cx0, cy0))
    assert w.selected == (0, 0)
    assert (0, 1) in set(w.reachables)

    # Click reachable (0,1) to trigger move
    cx1, cy1 = hex_center(40, 0, 1)
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(cx1, cy1))

    # Selection should be cleared and move called
    assert w.selected is None
    assert w.reachables == []
    assert gs.moved is True


def test_invalid_move_recomputes_reachables(qapp):
    """Invalid move attempt (non-reachable tile) should deselect the penguin."""
    board = DummyBoard(rows=1, cols=3, reachable_map={(0, 0): [(0, 1)]})
    player = create_player_with_penguins(1, num_penguins=1, color="red")
    gs = GameState(board=board, phase="Move", players=[player, Player(2, color="white")])

    board.tiles[0][0].occupied = player.penguins[0]

    w = BoardWidget(board, gs, hex_size=40)
    w.show()
    QTest.qWaitForWindowExposed(w)

    # Select (0,0)
    cx0, cy0 = hex_center(40, 0, 0)
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(cx0, cy0))
    assert (0, 1) in set(w.reachables)

    # Click invalid destination (0,2) which is not reachable → should deselect
    cx2, cy2 = hex_center(40, 0, 2)
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(cx2, cy2))

    # Selection should be cleared (new behavior)
    assert w.selected is None
    assert w.reachables == []


# ---- Placement Phase Tests ----


def test_placement_click_on_inactive_tile_is_ignored(qapp):
    """Clicking an inactive tile during placement should be ignored."""
    board = DummyBoard(rows=1, cols=2)
    board.tiles[0][0].active = False  # Make first tile inactive
    board.tiles[0][1].active = True

    gs = GameState(
        board=board,
        phase="Placement",
        players=[Player(1, color="red"), Player(2, color="white")]
    )
    gs.place_avatar = lambda *a: (_ for _ in ()).throw(Exception("Tile is not active"))

    w = BoardWidget(board, gs, hex_size=40)
    w.show()
    QTest.qWaitForWindowExposed(w)

    # Click the inactive tile (0,0)
    cx, cy = hex_center(40, 0, 0)
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(cx, cy))

    # No crash, no state change
    assert w.selected is None
    assert w.reachables == []
    assert gs.phase == "Placement"


def test_placement_invalid_click_catches_exception(qapp):
    """Invalid placement should catch exception and clear selection."""
    board = DummyBoard(rows=1, cols=2)
    gs = GameState(
        board=board,
        phase="Placement",
        players=[Player(1, color="red"), Player(2, color="white")]
    )

    # Make place_avatar always fail
    gs.place_avatar = lambda *a: (_ for _ in ()).throw(Exception("Invalid placement"))

    w = BoardWidget(board, gs, hex_size=40)
    w.show()
    QTest.qWaitForWindowExposed(w)

    # Click an active tile
    cx, cy = hex_center(40, 0, 1)
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(cx, cy))

    # Exception should be caught, selection cleared
    assert w.selected is None
    assert w.reachables == []


def test_placement_valid_click_clears_selection(qapp):
    """Valid placement should succeed and clear selection."""
    board = DummyBoard(rows=1, cols=2)
    gs = GameState(
        board=board,
        phase="Placement",
        players=[Player(1, color="red"), Player(2, color="white")]
    )

    # Track if placement was called
    gs.placement_called = False
    original_place = gs.place_avatar
    gs.place_avatar = lambda *a, **k: (setattr(gs, 'placement_called', True), original_place(*a, **k))

    w = BoardWidget(board, gs, hex_size=40)
    w.show()
    QTest.qWaitForWindowExposed(w)

    # Click an active tile
    cx, cy = hex_center(40, 0, 1)
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(cx, cy))

    # Placement should succeed and clear selection
    assert gs.placement_called is True
    assert w.selected is None
    assert w.reachables == []


def test_move_with_no_penguin_at_selection_clears_state(qapp):
    """Trying to move when selected tile has no penguin should clear selection."""
    board = DummyBoard(rows=1, cols=2, reachable_map={(0, 0): [(0, 1)]})
    player = create_player_with_penguins(1, num_penguins=1, color="red")
    gs = GameState(board=board, phase="Move", players=[player, Player(2, color="white")])

    # Don't place penguin on board
    w = BoardWidget(board, gs, hex_size=40)
    w.show()
    QTest.qWaitForWindowExposed(w)

    # Manually set selected tile (as if user clicked empty tile somehow)
    w.selected = (0, 0)
    w.reachables = [(0, 1)]

    # Click destination - should detect no penguin and clear
    cx, cy = hex_center(40, 0, 1)
    QTest.mouseClick(w, Qt.LeftButton, Qt.NoModifier, QPoint(cx, cy))

    # Should have cleared selection
    assert w.selected is None
    assert w.reachables == []
