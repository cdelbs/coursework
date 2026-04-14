# C:\SoftwareEngineeringFish\fiddlers\Fish\Common\gameboard.py
import os
import random

# from dataclasses import dataclass, replace
from typing import Any, List, Optional, Tuple


def begin_app(board: Any, gameState: Any) -> None:
    """
    Launch the GUI board viewer if PyQt is available.

    Falls back to a no-op when GUI dependencies are missing.
    """
    try:
        from Fish.Common.drawboard import begin_app as _begin_app
    except Exception:
        return None
    _begin_app(board, gameState)


def replace(obj, **changes):
    """
    Replacement for dataclasses.replace().
    """
    # Copy all current attributes
    attrs = obj.__dict__.copy()
    # Apply the changes
    attrs.update(changes)
    # Create a new instance of the same class
    return obj.__class__(**attrs)


# @dataclass(frozen=True)
class Tile:
    def __init__(self, fish, coords, active=True, highlighted=False, occupied=None):
        self.fish = fish
        self.coords = coords
        self.active = active
        self.highlighted = highlighted
        self.occupied = occupied

    def __repr__(self):
        return (
            f"Tile(fish={self.fish}, coords={self.coords}, active={self.active}, "
            f"highlighted={self.highlighted}, occupied={self.occupied})"
        )


class GameBoard:
    # int, int, Optional[List[List[int]]] | None -> None
    # Purpose: Initialize a GameBoard
    def __init__(
        self,
        rows: int = 5,
        columns: int = 5,
        board_data: Optional[List[List[int]]] = None,
    ):
        """
        Initialize a GameBoard.

        Args:
            rows (int): Number of rows in the board.
            columns (int): Number of columns in the board.
            board_data (List[List[int]] | None): 2D list of fish counts (optional).
        """
        self.rows = rows
        self.columns = columns

        if board_data:
            if len(board_data) != rows or any(len(r) != columns for r in board_data):
                raise ValueError(
                    f"Board data dimensions {len(board_data)}x{len(board_data[0]) if board_data else 0} "
                    f"do not match specified rows={rows}, columns={columns}."
                )
            # Validate fish counts are in valid range (0-5, where 0 means hole)
            for r_idx, row in enumerate(board_data):
                for c_idx, fish_count in enumerate(row):
                    if not isinstance(fish_count, int) or fish_count < 0 or fish_count > 5:
                        raise ValueError(
                            f"Invalid fish count {fish_count} at position ({r_idx}, {c_idx}). "
                            f"Fish count must be an integer between 0 and 5."
                        )
        else:
            board_data = [
                [random.randint(1, 5) for _ in range(columns)] for _ in range(rows)
            ]

        self.tiles: List[List[Tile]] = [
            [
                Tile(
                    fish=board_data[r][c], coords=(r, c), active=(board_data[r][c] > 0)
                )
                for c in range(columns)
            ]
            for r in range(rows)
        ]

    # None -> str
    # Purpose: Print-friendly representation of a board
    def __repr__(self) -> str:
        """Compact board representation for debugging."""
        return "\n".join(" ".join(str(tile.fish) for tile in row) for row in self.tiles)

    # int int str -> Tuple[int, int]
    # Purpose: Return the new coords of the reachable tile in the specified direction from the given tile coordinates.
    @staticmethod
    def determine_offset(row: int, col: int, direction: str) -> Tuple[int, int]:
        EVEN_DIRS = {
            "NW": (-1, -1),
            "N": (-1, 0),
            "NE": (-1, 1),
            "SW": (0, -1),
            "S": (1, 0),
            "SE": (0, 1),
        }
        ODD_DIRS = {
            "NW": (0, -1),
            "N": (-1, 0),
            "NE": (0, 1),
            "SW": (1, -1),
            "S": (1, 0),
            "SE": (1, 1),
        }
        dirs = EVEN_DIRS if col % 2 == 0 else ODD_DIRS
        dr, dc = dirs[direction]
        return row + dr, col + dc

    # int int -> bool
    # Purpose: check if the given coords are in the board
    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.columns

    # Tile -> List[Tuple[int, int]]
    # Purpose: Determine the coordinates of reachable tiles from the given tiles.
    def reachable_tiles(self, current_tile: Tile) -> List[Tuple[int, int]]:
        reachable: List[Tuple[int, int]] = []
        row, col = current_tile.coords
        DIRECTIONS = ["NW", "N", "NE", "SW", "S", "SE"]

        for d in DIRECTIONS:
            r, c = self.determine_offset(row, col, d)
            while self.in_bounds(r, c):
                tile = self.tiles[r][c]
                if not tile.active or tile.occupied is not None:
                    break
                reachable.append((r, c))
                r, c = self.determine_offset(r, c, d)

        return reachable

    # List[Tuple[int, int]], int -> GameBoard
    # Purpose: Return a board with specific holes and a minimum amount of one fish tiles.
    def with_holes_one_fish(
        self, holes: List[Tuple[int, int]], min: int
    ) -> "GameBoard":
        """Return a new GameBoard with the given holes removed and at least `min` one-fish tiles."""

        # Filter out invalid hole coordinates (out of bounds)
        valid_holes = [
            (r, c) for (r, c) in holes if 0 <= r < self.rows and 0 <= c < self.columns
        ]

        new_tiles = [
            [
                (
                    replace(tile, fish=0, active=False)
                    if (r, c) in valid_holes
                    else replace(tile)
                )
                for c, tile in enumerate(row_tiles)
            ]
            for r, row_tiles in enumerate(self.tiles)
        ]

        available = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.columns)
            if (r, c) not in valid_holes
        ]

        if min > len(available):
            raise ValueError(
                f"Not enough available tiles ({len(available)}) to assign {min} one-fish tiles."
            )

        one_fish_positions = random.sample(available, min)

        for r, c in one_fish_positions:
            tile = new_tiles[r][c]
            new_tiles[r][c] = replace(tile, fish=1, active=True)

        for r, c in available:
            if (r, c) not in one_fish_positions:
                tile = new_tiles[r][c]
                if tile.active:
                    new_tiles[r][c] = replace(
                        tile, fish=random.randint(2, 5), active=True
                    )

        new_board = GameBoard(self.rows, self.columns)
        new_board.tiles = new_tiles
        return new_board

    # int -> Gameboard
    # Purpose: Return a GameBoard with a uniform fish count.
    def with_uniform_fish(self, fish_count: int) -> "GameBoard":
        """Return a new GameBoard where all active tiles have the same fish count."""
        if fish_count <= 5 and fish_count >= 1:
            new_tiles = [
                [replace(tile, fish=fish_count, active=True) for tile in row_tiles]
                for row_tiles in self.tiles
            ]
            new_board = GameBoard(self.rows, self.columns)
            new_board.tiles = new_tiles
            return new_board
        else:
            raise ValueError(
                f"{fish_count} is not a valid fish amount. Please provide an integer between 1 and 5."
            )

    def clear_highlights(self) -> "GameBoard":
        new_tiles = [
            [replace(tile, highlighted=False) for tile in row] for row in self.tiles
        ]
        new_board = GameBoard(self.rows, self.columns)
        new_board.tiles = new_tiles
        return new_board

    def highlight_tiles(self, coords_list: List[Tuple[int, int]]) -> "GameBoard":
        new_tiles = []
        for r, row in enumerate(self.tiles):
            new_row = []
            for c, tile in enumerate(row):
                new_row.append(replace(tile, highlighted=(r, c) in coords_list))
            new_tiles.append(new_row)
        new_board = GameBoard(self.rows, self.columns)
        new_board.tiles = new_tiles
        return new_board

    def with_occupant(
        self, row: int, col: int, penguin: Optional[object]
    ) -> "GameBoard":
        if not self.in_bounds(row, col):
            raise ValueError(
                f"Position ({row}, {col}) is out of bounds for board of size {self.rows}x{self.columns}."
            )
        new_tiles = [
            [
                replace(
                    tile, occupied=penguin if (r == row and c == col) else tile.occupied
                )
                for c, tile in enumerate(row_tiles)
            ]
            for r, row_tiles in enumerate(self.tiles)
        ]
        new_board = GameBoard(self.rows, self.columns)
        new_board.tiles = new_tiles
        return new_board

    def clear_occupant(self, row: int, col: int) -> "GameBoard":
        if not self.in_bounds(row, col):
            raise ValueError(
                f"Position ({row}, {col}) is out of bounds for board of size {self.rows}x{self.columns}."
            )
        new_tiles = [
            [
                replace(
                    tile, occupied=None if (r == row and c == col) else tile.occupied
                )
                for c, tile in enumerate(row_tiles)
            ]
            for r, row_tiles in enumerate(self.tiles)
        ]
        new_board = GameBoard(self.rows, self.columns)
        new_board.tiles = new_tiles
        return new_board

    # GameState -> None
    # Purpose: draw the board
    def draw_board(self, game_state):
        """Launch the PyQt5 board visualization for this GameBoard and the current game state."""
        begin_app(self, game_state)


board = GameBoard(rows=5, columns=5)
holes_board = board.with_holes_one_fish([(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)], 12)
equal_board = board.with_uniform_fish(4)
