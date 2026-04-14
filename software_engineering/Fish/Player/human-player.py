#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
from typing import Tuple, Union
from threading import Event

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from Fish.Admin.referee import Referee
from Fish.Common.drawboard import BoardWidget
from Fish.Player.player import LocalPlayer
from Fish.Common.gameboard import GameBoard
from Fish.Common.state import GameState
from Fish.Common.game_tree import GameTree

SpecAction = Tuple[Tuple[int, int], Tuple[int, int]]


class HumanPlayer:
    """
    A player that waits for GUI input instead of using an AI strategy.
    Blocks in propose_placement() and propose_move() until the user
    makes a valid click on the GUI.
    """

    def __init__(self, name: str = "Human"):
        self.name = name
        self.placement_result = None
        self.move_result = None
        self.placement_event = Event()
        self.move_event = Event()

    def propose_placement(self, state: GameState) -> Tuple[int, int]:
        """
        Block and wait for the GUI to provide a placement via set_placement_choice().
        Returns (row, col) for penguin placement.
        """
        # Clear previous results
        self.placement_result = None
        self.placement_event.clear()

        # Process Qt events while waiting for human input
        app = QApplication.instance()
        while not self.placement_event.is_set():
            app.processEvents()

        return self.placement_result

    def propose_move(self, tree: GameTree) -> Union[SpecAction, bool]:
        """
        Block and wait for the GUI to provide a move via set_move_choice().
        Returns ((from_row, from_col), (to_row, to_col)) or False if no legal move.
        """
        # Clear previous results
        self.move_result = None
        self.move_event.clear()

        # Process Qt events while waiting for human input
        app = QApplication.instance()
        while not self.move_event.is_set():
            app.processEvents()

        return self.move_result

    def set_placement_choice(self, row: int, col: int):
        """Called by the GUI when the human clicks a tile during placement."""
        self.placement_result = (row, col)
        self.placement_event.set()

    def set_move_choice(self, from_row: int, from_col: int, to_row: int, to_col: int):
        """Called by the GUI when the human completes a move selection."""
        self.move_result = ((from_row, from_col), (to_row, to_col))
        self.move_event.set()

    def notify_tournament_start(self) -> bool:
        """Return True if the player acknowledges the start of the tournament."""
        return True

    def notify_tournament_result(self, won: bool) -> bool:
        """Return True if the player acknowledges the final result."""
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Play a Fish game with multiple human and AI players."
    )
    parser.add_argument(
        "num_human",
        type=int,
        help="Number of human players (1-4)",
    )
    parser.add_argument(
        "num_ai",
        type=int,
        help="Number of AI players (0-3)",
    )
    parser.add_argument(
        "--board-rows",
        type=int,
        default=5,
        help="Number of rows on the board (default: 5)",
    )
    parser.add_argument(
        "--board-cols",
        type=int,
        default=5,
        help="Number of columns on the board (default: 5)",
    )

    args = parser.parse_args()

    # Validate number of players
    if args.num_human < 1 or args.num_human > 3:
        print("Error: Number of human players must be between 1 and 3")
        sys.exit(1)

    if args.num_ai < 1 or args.num_ai > 3:
        print("Error: Number of AI players must be between 1 and 3")
        sys.exit(1)

    total_players = args.num_human + args.num_ai
    if total_players < 2 or total_players > 4:
        print("Error: Total number of players must be between 2 and 4")
        sys.exit(1)

    # Create the Qt application
    app = QApplication([])

    # Create human players
    human_players = []
    human_names = ["Human-1", "Human-2", "Human-3"]
    for i in range(args.num_human):
        human_players.append(HumanPlayer(name=human_names[i]))

    # Create AI players
    ai_players = []
    ai_names = ["AI-1", "AI-2", "AI-3"]
    for i in range(args.num_ai):
        ai_players.append(LocalPlayer(name=ai_names[i], depth_hero_turns=2))

    # Combine all players
    all_players = human_players + ai_players

    # Create the game board
    board = GameBoard(rows=args.board_rows, columns=args.board_cols)

    # Create the referee
    ref = Referee(board, all_players)

    # Create GUI widgets for ALL players
    widgets = []
    for i, player in enumerate(all_players):
        if isinstance(player, HumanPlayer):
            # Human player gets an interactive window with human_player callback
            widget = BoardWidget(
                board, ref.state, referee=ref,
                interactive=True,
                human_player=player,
                player_index=i
            )
            widget.setWindowTitle(f"Fish Game - {player.name} (Interactive)")
        else:
            # AI player gets a non-interactive view-only window
            widget = BoardWidget(
                board, ref.state, referee=ref,
                interactive=False
            )
            widget.setWindowTitle(f"Fish Game - {player.name} (View Only)")

        # Register widget as observer so it updates when game state changes
        ref.add_observer(widget)

        # Position windows in a grid layout
        window_offset_x = 50 + (i % 2) * 900
        window_offset_y = 50 + (i // 2) * 700
        widget.move(window_offset_x, window_offset_y)

        widget.show()
        widgets.append(widget)

    # Start the referee game loop
    QTimer.singleShot(0, ref.run)

    # Run the Qt event loop
    app.exec_()


if __name__ == "__main__":
    main()
