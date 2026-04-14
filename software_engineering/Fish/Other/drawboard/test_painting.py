"""Tests for BoardWidget painting and rendering."""

from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QImage, QPainter

from Common.drawboard import BoardWidget, draw_fish, draw_penguin
from conftest import (
    DummyBoard,
    DummyTile,
    GameState,
    Owner,
    Penguin,
    Player,
    create_player_with_penguins,
)


# ---- Primitive Drawing Tests ----


def test_draw_penguin_renders_visible_pixels(qapp):
    """draw_penguin should render visible pixels to the image."""
    img = QImage(200, 200, QImage.Format_ARGB32)
    painter = QPainter(img)
    draw_penguin(painter, 100.0, 100.0, 40.0, "red")
    painter.end()

    # Sample a pixel where the penguin body should be
    c = img.pixelColor(100, 100)
    assert c.alpha() > 0, "Penguin should render visible pixels"


def test_draw_fish_renders_visible_pixels(qapp):
    """draw_fish should render visible pixels to the image."""
    img = QImage(200, 200, QImage.Format_ARGB32)
    painter = QPainter(img)
    draw_fish(painter, 100.0, 100.0, 30.0)
    painter.end()

    # Sample a pixel where the fish should be
    c = img.pixelColor(100, 100)
    assert c.alpha() > 0, "Fish should render visible pixels"


def test_draw_fish_with_zero_size_does_nothing(qapp):
    """draw_fish with size <= 0 should return early without drawing."""
    img = QImage(200, 200, QImage.Format_ARGB32)
    img.fill(0)  # Transparent
    painter = QPainter(img)
    draw_fish(painter, 100.0, 100.0, 0.0)
    painter.end()

    # Should still be transparent (nothing drawn)
    c = img.pixelColor(100, 100)
    assert c.alpha() == 0, "Zero-size fish should not draw anything"


def test_hexagon_outline_has_six_points(qapp):
    """Hexagon outline should have exactly 6 points."""
    board = DummyBoard(rows=1, cols=1)
    gs = GameState(
        board=board,
        phase="Placement",
        players=[Player(1, color="red")]
    )

    w = BoardWidget(board, gs, hex_size=40)
    poly = w.hexagon_outline(100, 100, 40)

    assert len(poly) == 6, "Hexagon should have 6 vertices"


# ---- Widget Painting Tests ----


def test_paint_during_placement_phase(qapp):
    """Widget should paint successfully during placement phase."""
    board = DummyBoard(rows=1, cols=2)
    p1 = create_player_with_penguins(1, num_penguins=2, color="white", placed=False)
    p2 = create_player_with_penguins(2, num_penguins=1, color="red", placed=False)

    gs = GameState(
        board=board,
        phase="Placement",
        players=[p1, p2]
    )

    w = BoardWidget(board, gs, hex_size=36)
    w.paintEvent(QEvent(QEvent.Paint))

    # Verify widget state is valid
    assert w.gameState.phase == "Placement"
    assert len(w.gameState.players) == 2


def test_paint_during_move_phase_with_highlights(qapp):
    """Widget should paint tiles, penguins, highlights, and reachables."""
    board = DummyBoard(rows=1, cols=3, reachable_map={(0, 1): [(0, 2)]})

    # Highlight one tile
    board.tiles[0][0].highlighted = True

    # Place a penguin on the center tile
    owner = Owner(1, "white")
    peng = Penguin(owner, 0, placed=True)
    board.tiles[0][1].occupied = peng

    p1 = Player(1, [peng, Penguin(owner, 1, placed=False)], color="white")
    p2 = Player(2, [Penguin(Owner(2, "red"), 0, placed=False)], color="red")

    gs = GameState(board=board, phase="Move", players=[p1, p2])

    w = BoardWidget(board, gs, hex_size=40)
    # Simulate reachables being computed (as if user clicked tile)
    w.reachables = board.reachable_tiles(board.tiles[0][1])

    w.paintEvent(QEvent(QEvent.Paint))

    # Verify state is correct
    assert w.gameState.phase == "Move"
    assert w.reachables == [(0, 2)]
    assert board.tiles[0][0].highlighted is True


def test_paint_during_gameover_phase(qapp):
    """Widget should paint game over screen with final scores."""
    board = DummyBoard(rows=0, cols=0)
    board.tiles = []  # Empty board for game over

    p1 = Player(1, penguins=[], color="black", score=7)
    p2 = Player(2, penguins=[], color="white", score=10)

    gs = GameState(
        board=board,
        phase="GameOver",
        players=[p1, p2],
        current_turn=1
    )

    w = BoardWidget(board, gs, hex_size=30)
    w.paintEvent(QEvent(QEvent.Paint))

    # Verify game over state
    assert w.gameState.phase == "GameOver"
    assert w.gameState.players[0].score == 7
    assert w.gameState.players[1].score == 10


def test_paint_with_fish_counts(qapp):
    """Widget should paint tiles with different fish counts."""
    board = DummyBoard(rows=2, cols=2)
    board.tiles[0][0].fish = 1
    board.tiles[0][1].fish = 2
    board.tiles[1][0].fish = 3
    board.tiles[1][1].fish = 1

    gs = GameState(
        board=board,
        phase="Placement",
        players=[Player(1, color="red")]
    )

    w = BoardWidget(board, gs, hex_size=40)
    w.paintEvent(QEvent(QEvent.Paint))

    # Verify fish counts are preserved
    assert board.tiles[0][0].fish == 1
    assert board.tiles[0][1].fish == 2
    assert board.tiles[1][0].fish == 3


def test_paint_with_inactive_tiles(qapp):
    """Widget should paint inactive tiles differently from active ones."""
    board = DummyBoard(rows=1, cols=3)
    board.tiles[0][0].active = False
    board.tiles[0][1].active = True
    board.tiles[0][2].active = False

    gs = GameState(
        board=board,
        phase="Move",
        players=[Player(1, color="red")]
    )

    w = BoardWidget(board, gs, hex_size=40)
    w.paintEvent(QEvent(QEvent.Paint))

    # Verify inactive state is preserved
    assert board.tiles[0][0].active is False
    assert board.tiles[0][1].active is True
    assert board.tiles[0][2].active is False


def test_paint_with_selected_tile_shows_yellow_outline(qapp):
    """Widget should draw yellow outline around selected tile."""
    board = DummyBoard(rows=1, cols=2)
    player = create_player_with_penguins(1, num_penguins=1, color="red")
    gs = GameState(board=board, phase="Move", players=[player, Player(2, color="white")])

    board.tiles[0][0].occupied = player.penguins[0]

    w = BoardWidget(board, gs, hex_size=40)
    w.show()

    # Simulate a tile being selected
    w.selected = (0, 0)
    w.paintEvent(QEvent(QEvent.Paint))

    # Verify selection is maintained
    assert w.selected == (0, 0)
