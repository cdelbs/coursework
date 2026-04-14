from typing import List, Optional, Tuple, Set

# from dataclasses import replace
from Fish.Common.gameboard import GameBoard

PENGUIN_COUNT_RULE = {2: 4, 3: 3, 4: 2}
PHASES = ["Initialization", "Placement", "Move", "GameOver"]
COLORS = ["red", "white", "brown", "black"]


def replace(obj, **changes):
    """
    Python 3.6-compatible replacement for dataclasses.replace().
    Works for frozen classes by reconstructing the instance.
    """
    # Copy all current attributes
    attrs = obj.__dict__.copy()
    # Apply the changes
    attrs.update(changes)
    # Create a new instance of the same class
    return obj.__class__(**attrs)


class Penguin:
    def __init__(
        self,
        id: int,
        owner: "Player",
        coords: Tuple[int, int] = (-1, -1),
        placed: bool = False,
        fallen: bool = False,
    ):
        """A penguin belongs to a player and can occupy a tile (immutable)."""
        self.id = id
        self.owner = owner
        self.coords = coords
        self.placed = placed
        self.fallen = fallen

    def __repr__(self) -> str:
        return f"<Penguin {self.id} ({self.owner.color}) at {self.coords}, placed={self.placed}, fallen={self.fallen}>"


class Player:
    def __init__(
        self,
        pid: str,
        score: int = 0,
        color: Optional[str] = None,
        penguins: Optional[List[Penguin]] = None,
    ):
        """Represents one player in the game (immutable)."""
        self.pid = pid
        self.score = score
        self.color = color
        self.penguins = penguins if penguins is not None else []

    def __repr__(self) -> str:
        return f"<Player {self.pid} ({self.color}) score={self.score} penguins={len(self.penguins)}>"

    def has_unplaced_penguins(self) -> bool:
        return any(not p.placed for p in self.penguins)

    def active_penguins(self) -> List["Penguin"]:
        # Only penguins already on the board should be considered for moves
        return [p for p in self.penguins if p.placed and not p.fallen]


# ------------------------------
# GAME STATE LOGIC
# ------------------------------


class GameState:
    def __init__(
        self,
        board: GameBoard,
        players: List[Player],
        phase: str = "Initialization",
        turn_num: int = 0,
    ):
        self.board = board
        self.players = players
        self.turn_order = [i for i in range(len(players))]
        self.current_turn = turn_num % len(players)
        self.phase = phase if phase in PHASES else "Initialization"
        self.eliminated: Set[int] = set()

        # --- Initialization Phase: set up penguins & assign colors ---
        if self.phase == "Initialization":
            self._initialize_penguins_and_colors()
            self.phase = "Placement"

    def _initialize_penguins_and_colors(self) -> None:
        """Assign penguins and colors based on player count (immutable update)."""
        max_penguins = PENGUIN_COUNT_RULE[len(self.players)]
        updated_players = []

        for i, player in enumerate(self.players):
            new_color = COLORS[i]
            new_penguins = [Penguin(pid, player) for pid in range(max_penguins)]
            # Create new player with color and penguins
            updated_player = replace(player, color=new_color, penguins=new_penguins)
            # Update penguin owners to point to the new player object
            updated_penguins = [replace(p, owner=updated_player) for p in new_penguins]
            updated_player = replace(updated_player, penguins=updated_penguins)
            updated_players.append(updated_player)

        self.players = updated_players
        
    def active_pids(self) -> List[int]:
        """
        Return the seat order filtered to players not in the eliminated set.
        This does not mutate state and does not reorder seats.
        """
        return [self.players[pid].pid for pid in self.turn_order if self.players[pid].pid not in self.eliminated]

    def __repr__(self) -> str:
        return (
            f"<GameState phase={self.phase}, "
            f"turn={self.turn_order[self.current_turn]}, "
            f"players={len(self.players)}>"
        )

    # ------------------------------
    # PLAYER ACTIONS
    # ------------------------------

    def place_avatar(self, player_id: str, row: int, col: int) -> "GameState":
        """Place one of the player's unplaced penguins (immutable update)."""
        if self.phase != "Placement":
            raise Exception("Not in placement phase")

        # Validate bounds
        if not self.board.in_bounds(row, col):
            raise Exception(f"Position ({row}, {col}) is out of bounds")

        player = self._get_current_player(player_id)
        penguin = next((p for p in player.penguins if not p.placed), None)
        if not penguin:
            raise Exception("No unplaced penguins left")

        tile = self.board.tiles[row][col]
        if not tile.active or tile.occupied is not None:
            raise Exception("Invalid tile for placement")

        # Update penguin immutably
        updated_penguin = replace(penguin, coords=(row, col), placed=True)

        # Update player's penguin list
        new_penguins = [
            updated_penguin if p.id == penguin.id else p for p in player.penguins
        ]
        updated_player = replace(player, penguins=new_penguins)

        # Update players list
        self.players = [
            updated_player if p.pid == player_id else p for p in self.players
        ]

        # Update board with new penguin reference
        new_tile = replace(tile, occupied=updated_penguin)
        new_tiles = [list(row_tiles) for row_tiles in self.board.tiles]
        new_tiles[row][col] = new_tile
        new_board = GameBoard(self.board.rows, self.board.columns)
        new_board.tiles = new_tiles
        self.board = new_board

        self._advance_turn_after_placement()
        return self

    def move_avatar(
        self, player_id: str, penguin_id: int, new_row: int, new_col: int
    ) -> "GameState":
        """Move a penguin to a new valid tile (immutable update)."""
        if self.phase != "Move":
            raise Exception("Not in move phase")

        # Validate bounds
        if not self.board.in_bounds(new_row, new_col):
            raise Exception(f"Destination ({new_row}, {new_col}) is out of bounds")

        player = self._get_current_player(player_id)
        penguin = next((p for p in player.penguins if p.id == penguin_id), None)
        if not penguin or penguin.fallen:
            raise Exception("Invalid penguin")
        if not penguin.placed:
            raise Exception("Penguin has not been placed yet")

        old_row, old_col = penguin.coords

        # Check for same-position move
        if (new_row, new_col) == (old_row, old_col):
            raise Exception("Cannot move penguin to its current position")

        old_tile = self.board.tiles[old_row][old_col]
        new_tile = self.board.tiles[new_row][new_col]

        reachable = self.board.reachable_tiles(old_tile)
        if (new_row, new_col) not in reachable:
            raise Exception("Destination not reachable")

        if new_tile.occupied is not None:
            raise Exception("Tile already occupied")

        # Update penguin immutably
        updated_penguin = replace(penguin, coords=(new_row, new_col))

        # Update player's penguin list and score
        new_penguins = [
            updated_penguin if p.id == penguin_id else p for p in player.penguins
        ]
        updated_player = replace(
            player, score=player.score + old_tile.fish, penguins=new_penguins
        )

        # Update players list
        self.players = [
            updated_player if p.pid == player_id else p for p in self.players
        ]

        # Update board tiles
        updated_tiles = [list(row_tiles) for row_tiles in self.board.tiles]
        updated_tiles[old_row][old_col] = replace(
            old_tile, fish=0, active=False, occupied=None
        )
        updated_tiles[new_row][new_col] = replace(new_tile, occupied=updated_penguin)

        new_board = GameBoard(self.board.rows, self.board.columns)
        new_board.tiles = updated_tiles
        self.board = new_board

        # Progress game
        self._advance_turn_after_move()
        return self

    def next_state_after_move(
        self, player_id: str, penguin_id: int, new_row: int, new_col: int
    ) -> "GameState":
        
        if self.phase != "Move":
            raise Exception("Not in move phase")

        # validate turn & penguin
        current_pid = self.players[self.turn_order[self.current_turn]].pid
        if player_id != current_pid:
            raise Exception("Not this player's turn")
        player = next(p for p in self.players if p.pid == player_id)
        penguin = next((p for p in player.penguins if p.id == penguin_id), None)
        if not penguin or penguin.fallen:
            raise Exception("Invalid penguin")

        old_row, old_col = penguin.coords
        old_tile = self.board.tiles[old_row][old_col]
        new_tile = self.board.tiles[new_row][new_col]

        # validate geometry
        if (new_row, new_col) not in self.board.reachable_tiles(old_tile):
            raise Exception("Destination not reachable")
        if new_tile.occupied is not None:
            raise Exception("Tile already occupied")

        # --- copy-on-write: players ---
        new_players = list(self.players)
        updated_penguin = replace(penguin, coords=(new_row, new_col))
        new_penguins = [
            updated_penguin if p.id == penguin_id else p for p in player.penguins
        ]
        updated_player = replace(
            player, score=player.score + old_tile.fish, penguins=new_penguins
        )
        # splice into player list
        idx_player = self.players.index(player)
        new_players[idx_player] = updated_player

        # --- copy-on-write: board tiles (only two positions + rows that contain them) ---
        tiles = self.board.tiles
        new_tiles = tiles[:]  # shallow copy of row lists

        # copy old row
        row_old_list = list(tiles[old_row])
        row_old_list[old_col] = replace(old_tile, fish=0, active=False, occupied=None)
        new_tiles[old_row] = row_old_list

        # copy new row (unless moving within same row we already copied)
        if new_row == old_row:
            row_new_list = row_old_list
        else:
            row_new_list = list(tiles[new_row])
            new_tiles[new_row] = row_new_list
        row_new_list[new_col] = replace(new_tile, occupied=updated_penguin)

        new_board = GameBoard(self.board.rows, self.board.columns)
        new_board.tiles = new_tiles

        # construct child state with same phase & current_turn, then advance like a real move
        child = GameState(new_board, new_players, self.phase, self.current_turn)
        # match normal engine post-move behavior
        child._advance_turn_after_move()
        return child

    # ------------------------------
    # INTERNAL HELPERS
    # ------------------------------

    def _get_current_player(self, player_id: int) -> Player:
        current_pid = self.players[self.turn_order[self.current_turn]].pid ###########change###############
        if player_id != current_pid:
            raise Exception("Not this player's turn")
        return next(p for p in self.players if p.pid == player_id)

    def _advance_turn_after_placement(self) -> None:
        """Advance placement phase and transition to Move or GameOver."""
        self.current_turn = (self.current_turn + 1) % len(self.turn_order)

        if all(not p.has_unplaced_penguins() for p in self.players):
            # All penguins placed, evaluate if any moves exist
            if not self._any_moves_available():
                self.phase = "GameOver"
            else:
                self.phase = "Move"
                # Skip to next player that can move
                if not self._player_can_move(self.players[self.turn_order[self.current_turn]].pid):
                    self._advance_turn_to_next_player()

    def _advance_turn_after_move(self) -> None:
        """Handle move end, check if game continues or ends."""
        if not self._any_moves_available():
            self.phase = "GameOver"
            return
        self._advance_turn_to_next_player()

    def _advance_turn_to_next_player(self) -> None:
        """Find the next player who can move. If none can move, game ends."""
        for _ in range(len(self.turn_order)):
            self.current_turn = (self.current_turn + 1) % len(self.turn_order)
            if self._player_can_move(self.players[self.turn_order[self.current_turn]].pid):
                return
        # If we've checked all players and none can move, game is over
        self.phase = "GameOver"

    def _player_can_move(self, pid: int) -> bool:
        player = next(p for p in self.players if p.pid == pid)
        b = self.board
        for penguin in player.active_penguins():
            r, c = penguin.coords
            from_tile = b.tiles[r][c]
            for rr, cc in b.reachable_tiles(from_tile):
                if b.tiles[rr][cc].occupied is None:
                    return True
        return False

    def _any_moves_available(self) -> bool:
        return any(self._player_can_move(p.pid) for p in self.players)

    def draw(self):
        """Launch GUI via drawboard."""
        self.board.draw_board(self)

# ------------------------------
# EXAMPLE USAGE
# ------------------------------

if __name__ == "__main__":
    board = GameBoard(rows=7, columns=8)
    players = [Player('1'), Player('2'), Player('3'), Player('4')]
    state = GameState(board, players, "Initialization", 0)
    state.draw()
