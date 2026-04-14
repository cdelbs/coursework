from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPainter, QFont, QPen, QColor
from PyQt5.QtWidgets import QApplication, QWidget

from typing import List, Tuple
import sys
from time import sleep

from pathlib import Path

HERE = Path(__file__).resolve()

# Find the Fish package root
for parent in HERE.parents:
    if (parent / "Fish").is_dir():
        sys.path.insert(0, str(parent))
        break

from Fish.Admin.abstract_observer import Observer
from Fish.Admin.manager import TournamentManager
from Fish.Player.player import LocalPlayer







class TournamentWidget(Observer):
    def __init__(self, tournament: TournamentManager = None):
        super().__init__()

        self.resize(300, 300)

        if tournament is not None:
            self.tournament = tournament
            self.tournament.add_observer(self)
        else:
            self.tournament = None

        self.bracket: List[List[List[List[str, bool]]]] = []

    def set_state(self, bracket):
        self.bracket = bracket


    def paintEvent(self, a0):
        painter = QPainter(self)

        painter.setFont(QFont("Arial", 10))

        for i in range(len(self.bracket)):
            px = 30 + 120 * (i)
            painter.setPen(QColor("black"))
            painter.setFont(QFont("Arial", 15))
            if len(self.bracket[i][0]) == 1:
                painter.drawText(px, 30, "Tournament\nWinner")
            else:
                painter.drawText(px, 30, f"Round {i+1}")
            painter.setFont(QFont("Arial", 10))

            for j in range(len(self.bracket[i])):
                py = (150 * (j + 1))
                painter.setPen(QColor("black"))
                painter.drawText(px, py, "------------")

                for k in range(len(self.bracket[i][j])):
                    if self.bracket[i][j][k][1]:
                        painter.setPen(QColor("green"))
                    else:
                        painter.setPen(QColor("black"))
                    pyy = py + (30 * (k + 1))
                    painter.drawText(px, pyy, self.bracket[i][j][k][0])

    def closeEvent(self, event):
        if self.tournament != None:
            self.tournament.remove_observer(self)
        super().closeEvent(event)


def main():
    app = QApplication([])

    test_players = [
        LocalPlayer(name="jason"),
        LocalPlayer(name="marco"),
        LocalPlayer(name="collin"),
        LocalPlayer(name="chris"),
        LocalPlayer(name="roger"),
        LocalPlayer(name="aidan"),
        LocalPlayer(name="jonathan"),
        LocalPlayer(name="joseph")
    ]
    

    
    manager = TournamentManager(test_players)

    widget = TournamentWidget(manager)
    widget.show()

    def run_and_close():
        try:
            manager.run_tournament()
        finally:
            sleep(5)
            widget.close()   # close the window
            app.quit()       # (optional) also stop the event loop

    QTimer.singleShot(0, run_and_close)
    app.exec_()



if __name__ == "__main__":
    main()



