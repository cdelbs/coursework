"""Tests for keyboard interactions with the BoardWidget."""

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtTest import QTest

from Common.drawboard import BoardWidget
from conftest import DummyBoard, GameState, Player


def test_f11_toggles_fullscreen(qapp):
    """F11 key should toggle fullscreen mode."""
    board = DummyBoard(rows=0, cols=0)
    board.tiles = []

    gs = GameState(
        board=board,
        phase="Placement",
        players=[Player(1, color="red")],
    )

    w = BoardWidget(board, gs, hex_size=30)
    w.show()

    # Toggle fullscreen on and off
    initial_fullscreen = w.isFullScreen()
    QTest.keyPress(w, Qt.Key_F11)
    assert w.isFullScreen() != initial_fullscreen, "F11 should toggle fullscreen"

    QTest.keyPress(w, Qt.Key_F11)
    assert w.isFullScreen() == initial_fullscreen, "F11 should toggle back"

    # Ensure widget still paints after toggling
    w.paintEvent(QEvent(QEvent.Paint))


def test_non_f11_keypress_does_nothing(qapp):
    """Non-F11 keypresses should not affect widget state."""
    board = DummyBoard(rows=0, cols=0)
    board.tiles = []

    gs = GameState(
        board=board,
        phase="Placement",
        players=[Player(1, color="red")],
    )

    w = BoardWidget(board, gs, hex_size=30)
    w.show()

    initial_fullscreen = w.isFullScreen()

    # Press various other keys
    QTest.keyPress(w, Qt.Key_A)
    QTest.keyPress(w, Qt.Key_Space)
    QTest.keyPress(w, Qt.Key_Escape)

    # State should be unchanged
    assert w.isFullScreen() == initial_fullscreen
    w.paintEvent(QEvent(QEvent.Paint))
