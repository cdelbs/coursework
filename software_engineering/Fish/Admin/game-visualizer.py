#!/usr/bin/env python3
import math

import sys
from pathlib import Path

HERE = Path(__file__).resolve()

# Find the Fish package root
for parent in HERE.parents:
    if (parent / "Fish").is_dir():
        sys.path.insert(0, str(parent))
        break

from PyQt5.QtCore import QEvent, QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt5.QtWidgets import QApplication, QWidget

from Fish.Admin.abstract_observer import Observer
from Fish.Admin.referee import Referee
from Fish.Common.drawboard import BoardWidget


from Fish.Player.player import LocalPlayer
from Fish.Common.gameboard import GameBoard
from PyQt5.QtCore import QTimer

def main():
    app = QApplication([])

    test_players = [LocalPlayer(name='hello'), LocalPlayer(name='world'), 
                    LocalPlayer(name='collin'), LocalPlayer(name='joseph')]
    
    board = GameBoard()

    ref = Referee(board, test_players)

    widget = BoardWidget(board, ref.state, ref)

    widget.show()
    QTimer.singleShot(0, ref.run)
    app.exec_()


if __name__ == "__main__":
    main()