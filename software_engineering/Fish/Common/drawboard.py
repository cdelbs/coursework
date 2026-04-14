# C:\SoftwareEngineeringFish\fiddlers\Fish\Common\drawboard.py
import math
import sys
from pathlib import Path

# Add parent directory to path to find Admin module
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PyQt5.QtCore import QEvent, QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt5.QtWidgets import QApplication, QWidget

from Fish.Admin.abstract_observer import Observer
from Fish.Admin.referee import Referee

COLOR_MAP = {
    "red": Qt.red,
    "white": Qt.white,
    "brown": QColor(165, 42, 42),
    "black": Qt.black,
}


def _qcolor_from_name(name: str) -> QColor:
    return COLOR_MAP.get((name or "").lower(), Qt.black)


# QPainter, float, float, float, str -> None
def draw_penguin(painter: QPainter, cx: float, cy: float, size: float, color_name: str):
    painter.setPen(QPen(Qt.black, 1))

    body_w = size * 0.6
    body_h = size
    painter.setBrush(_qcolor_from_name(color_name))
    rect_body = QRectF(cx - body_w / 2, cy - body_h / 2, body_w, body_h)
    painter.drawEllipse(rect_body)

    head_r = size * 0.25
    painter.setBrush(Qt.black)
    painter.drawEllipse(
        QRectF(cx - head_r, cy - body_h / 2 - head_r * 0.3, head_r * 2, head_r * 2)
    )

    flipper_w = body_w * 0.4
    flipper_h = body_h * 0.5
    painter.setBrush(Qt.black)
    painter.drawEllipse(
        QRectF(
            cx - body_w / 2 - flipper_w * 0.6, cy - flipper_h / 2, flipper_w, flipper_h
        )
    )
    painter.drawEllipse(
        QRectF(
            cx + body_w / 2 - flipper_w * 0.4, cy - flipper_h / 2, flipper_w, flipper_h
        )
    )

    foot_w = body_w * 0.4
    foot_h = size * 0.15
    painter.setBrush(Qt.yellow)
    painter.drawEllipse(
        QRectF(cx - foot_w * 0.9, cy + body_h / 2 - foot_h / 2, foot_w, foot_h)
    )
    painter.drawEllipse(
        QRectF(cx - foot_w * 0.1, cy + body_h / 2 - foot_h / 2, foot_w, foot_h)
    )


# QPainter, float, float, float -> None
def draw_fish(painter: QPainter, cx: float, cy: float, size: float):
    if size <= 0:
        return
    painter.setPen(QPen(Qt.black, 1))
    painter.setBrush(Qt.blue)

    body_w = size
    body_h = size * 0.5
    rect = QRectF(cx - body_w / 2, cy - body_h / 2, body_w, body_h)
    painter.drawEllipse(rect)

    tail = QPolygonF(
        [
            QPointF(cx - body_w / 2, cy),
            QPointF(cx - body_w / 2 - body_w * 0.3, cy - body_h / 2),
            QPointF(cx - body_w / 2 - body_w * 0.3, cy + body_h / 2),
        ]
    )
    painter.drawPolygon(tail)


class BoardWidget(Observer):
    def __init__(self, board, gameState, referee: Referee =None, hex_size=45, interactive=True, human_player=None, player_index=None):
        """
        Initialize the BoardWidget.

        Args:
            board: Initial GameBoard instance (used for sizing).
            gameState: The GameState (truth for board/phase/players).
            hex_size (int): Size of each hexagon tile in pixels.
            interactive (bool): If False, mouse clicks are ignored (view-only mode).
            human_player: Optional HumanPlayer instance. When provided, clicks notify this player
                         instead of directly modifying gameState.
            player_index (int): Index of the player this window belongs to. When provided with
                               human_player, only allows interaction during this player's turn.
        """
        super().__init__()
        self.gameState = gameState
        self.referee = referee  # Initialize to None or the provided referee
        if referee != None:
            self.referee.add_observer(self)
        self.hex_size = hex_size
        self._flags = self.windowFlags()
        self.selected = None  # (row, col) or None
        self.reachables = []  # [(row, col), ...] fallback highlight list
        self.interactive = interactive  # Controls whether mouse input is enabled
        self.human_player = human_player  # If set, notify this player of moves
        self.player_index = player_index  # Which player this window is for

        # Size scales with initial board dimensions (okay even if board is replaced later)
        self.resize(
            int(250 + board.columns * hex_size * 2.0),
            int(200 + board.rows * hex_size * math.sqrt(3)),
        )

    def set_state(self, state):
        """Observer pattern: update the game state when notified by the referee."""
        self.gameState = state

    def closeEvent(self, event):
        if self.referee != None:
            self.referee.remove_observer(self)
        super().closeEvent(event)

    # --- helper: set highlights into immutable board if supported ---
    def _set_highlights(self, coords_list):
        """
        If GameBoard has highlight helpers, use them.
        Otherwise, fall back to storing coords in self.reachables and paint from that.
        """
        self.reachables = coords_list or []
        # Try immutable highlight helpers if present on the *current* board
        current_board = self.gameState.board
        highlight_fn = getattr(current_board, "highlight_tiles", None)
        clear_fn = getattr(current_board, "clear_highlights", None)

        if clear_fn is not None and highlight_fn is not None:
            # Replace the board in game state with highlighted copy
            self.gameState.board = highlight_fn(coords_list)
        # else: rely on self.reachables in paintEvent

    # Purpose: Renders the game board: draws hex tiles, fish, highlights, and penguins
    def paintEvent(self, event: QEvent):
        painter = QPainter(self)
        board = self.gameState.board  # <- ALWAYS use the live board

        # GameOver banner + scoreboard
        if self.gameState.phase == "GameOver":
            painter.setPen(Qt.black)
            painter.drawText(50, 50, "GAME OVER")

            max_score = max(p.score for p in self.gameState.players)
            if max_score != 0:
                winner_ids = [p.pid for p in self.gameState.players if p.score == max_score]
            else:
                winner_ids = []
                
            start_x = 200
            start_y = 150
            spacing_x = 250

            for i, player in enumerate(self.gameState.players):
                x = start_x + i * spacing_x
                y = start_y
                painter.setPen(Qt.black)
                painter.drawText(x, y, f"Player {player.pid} ({player.color})")
                painter.drawText(x, y + 40, f"Score: {player.score}")
                if player.pid in winner_ids:
                    painter.setPen(Qt.green)
                    painter.drawText(x, y + 100, "Winner!")
            return

        # Phase label
        painter.setPen(Qt.black)
        painter.drawText(50, 30, f"Phase: {self.gameState.phase}")

        # --- Draw tiles from the live board ---
        for row in range(board.rows):
            for col in range(board.columns):
                tile = board.tiles[row][col]
                if not tile.active:
                    # Skip rendering holes entirely
                    continue

                # Odd-r horizontal layout (column parity controls vertical offset)
                x = col * self.hex_size * 1.5 + 100
                y = (
                    row * self.hex_size * math.sqrt(3)
                    + (col % 2) * (self.hex_size * math.sqrt(3) / 2)
                    + 100
                )

                polygon = self.hexagon_outline(x, y, self.hex_size)

                # Fill: highlighted/green if either tile.highlighted is True (immutable board path)
                # or (row,col) lives in self.reachables (fallback path)
                if getattr(tile, "highlighted", False) or (row, col) in self.reachables:
                    painter.setBrush(Qt.green)
                else:
                    painter.setBrush(Qt.NoBrush)

                # Base outline
                painter.setPen(QPen(Qt.black, 2))
                painter.drawPolygon(polygon)

                # If this tile is the currently selected one, draw a thicker outline ring
                if self.selected == (row, col):
                    painter.setPen(QPen(Qt.yellow, 4))
                    painter.drawPolygon(
                        self.hexagon_outline(x, y, self.hex_size * 0.92)
                    )
                    painter.setPen(QPen(Qt.black, 2))

                # Draw penguin or fish
                if getattr(tile, "occupied", None):
                    draw_penguin(
                        painter, x, y, self.hex_size * 0.6, tile.occupied.owner.color
                    )
                else:
                    f = max(0, int(tile.fish))
                    if f > 0:
                        for i in range(f):
                            angle = (2 * math.pi * i / f) if f > 1 else 0
                            fx = x + 20 * math.cos(angle)
                            fy = y + 20 * math.sin(angle)
                            draw_fish(
                                painter, fx, fy, max(1, self.hex_size // max(1, f))
                            )

        # --- Sidebar with turn & unplaced penguins ---
        sidebar_x = board.columns * self.hex_size * 2 + 200
        start_y = 50
        spacing_y = self.hex_size * 2

        # Get the current turn player's PID
        current_turn_index = self.gameState.turn_order[self.gameState.current_turn]
        current_turn_pid = self.gameState.players[current_turn_index].pid

        for idx, player in enumerate(self.gameState.players):
            y = start_y + idx * spacing_y * 2
            painter.setPen(Qt.red if player.pid == current_turn_pid else Qt.black)
            painter.drawText(sidebar_x, y, f"Player {player.pid} ({player.color})")
            penguin_y = y + 30
            # Draw only unplaced penguins in the sidebar (placed ones are on tiles)
            for penguin in player.penguins:
                if not penguin.placed and not penguin.fallen:
                    draw_penguin(
                        painter, sidebar_x, penguin_y, self.hex_size * 0.6, player.color
                    )
                    penguin_y += self.hex_size

    # float, float, float -> QPolygonF
    def hexagon_outline(self, cx: float, cy: float, size: float):
        points = []
        for i in range(6):
            angle_deg = 60 * i
            angle_rad = math.radians(angle_deg)
            x = cx + size * math.cos(angle_rad)
            y = cy + size * math.sin(angle_rad)
            points.append(QPointF(x, y))
        return QPolygonF(points)

    # None -> None
    def fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    # QEvent -> None
    def keyPressEvent(self, event: QEvent):
        if event.key() == Qt.Key_F11:
            self.fullscreen()
        else:
            super().keyPressEvent(event)

    # QEvent -> None
    # Purpose: Handle clicks for placement and moves (and highlighting)
    def mousePressEvent(self, event: QEvent):
        # If not interactive, ignore all mouse input
        if not self.interactive:
            return

        # If this is a human player window, only allow interaction on their turn
        if self.human_player is not None and self.player_index is not None:
            if self.gameState.current_turn != self.player_index:
                return  # Not this player's turn

        click_pos = event.pos()
        board = self.gameState.board  # <- always read the live one

        for row in range(board.rows):
            for col in range(board.columns):
                tile = board.tiles[row][col]
                if not tile.active:
                    continue
                x = col * self.hex_size * 1.5 + 100
                y = (
                    row * self.hex_size * math.sqrt(3)
                    + (col % 2) * (self.hex_size * math.sqrt(3) / 2)
                    + 100
                )
                hexagon = self.hexagon_outline(x, y, self.hex_size)
                if hexagon.containsPoint(click_pos, Qt.OddEvenFill):
                    if event.button() == Qt.LeftButton:
                        if self.gameState.phase == "Placement":
                            # If human_player is set, notify it; otherwise modify state directly
                            if self.human_player is not None:
                                # Invalid placements will result in disqualification by the referee
                                self.human_player.set_placement_choice(row, col)
                                self.selected = None
                                self._set_highlights([])
                            else:
                                # Original behavior: modify state directly
                                current_pid = self.gameState.turn_order[
                                    self.gameState.current_turn
                                ]
                                try:
                                    self.gameState.place_avatar(current_pid, row, col)
                                    # After a placement, clear selection/highlights and repaint
                                    self.selected = None
                                    self._set_highlights([])
                                except Exception as e:
                                    print("Invalid placement:", e)

                        elif self.gameState.phase == "Move":
                            # Get current player's PID
                            current_pid = self.gameState.players[self.gameState.turn_order[
                                self.gameState.current_turn
                            ]].pid if self.human_player else self.gameState.turn_order[self.gameState.current_turn]

                            occupied = getattr(tile, "occupied", None)
                            clicked_has_current_penguin = bool(
                                occupied and occupied.owner.pid == current_pid
                            )

                            if not self.selected:
                                # First click: select a penguin to move
                                if clicked_has_current_penguin:
                                    self.selected = (row, col)
                                    # compute reachables from this tile using the live board
                                    self.reachables = board.reachable_tiles(tile)
                                    self._set_highlights(self.reachables)
                                    self.update()
                                return

                            # Already have a selection
                            old_row, old_col = self.selected
                            if (row, col) == (old_row, old_col):
                                # Clicking the same tile: deselect
                                self.selected = None
                                self._set_highlights([])
                                self.update()
                                return

                            if clicked_has_current_penguin:
                                # Switch selection to another penguin of the same current player
                                self.selected = (row, col)
                                self.reachables = board.reachable_tiles(tile)
                                self._set_highlights(self.reachables)
                                self.update()
                                return

                            # Attempt the move from selected -> clicked
                            # Invalid moves will result in disqualification by the referee
                            if self.human_player is not None:
                                # Send the move regardless of whether it's in reachables
                                # The referee will validate and potentially disqualify
                                self.human_player.set_move_choice(old_row, old_col, row, col)
                                self.selected = None
                                self._set_highlights([])
                                self.update()
                            else:
                                # Original behavior for non-human players: validate first
                                if (row, col) in self.reachables:
                                    old_tile = board.tiles[old_row][old_col]
                                    penguin = getattr(old_tile, "occupied", None)
                                    if not penguin:
                                        print("Invalid selection: no penguin here")
                                        self.selected = None
                                        self._set_highlights([])
                                        return
                                    player = penguin.owner
                                    try:
                                        self.gameState.move_avatar(
                                            player.pid, penguin.id, row, col
                                        )
                                        # Clear selection/highlights on success
                                        self.selected = None
                                        self._set_highlights([])
                                    except Exception as e:
                                        print("Invalid move:", e)
                                        # re-highlight the valid set from the original tile
                                        cur_board = self.gameState.board
                                        self.reachables = cur_board.reachable_tiles(
                                            cur_board.tiles[old_row][old_col]
                                        )
                                        self._set_highlights(self.reachables)
                                else:
                                    # Invalid move: deselect
                                    print(f"Invalid move: ({row}, {col}) is not reachable")
                                    self.selected = None
                                    self._set_highlights([])
                                    self.update()
                self.update()


# GameBoard -> None
def begin_app(board, gameState):
    app = QApplication([])
    w = BoardWidget(board, gameState)
    w.show()
    app.exec_()
