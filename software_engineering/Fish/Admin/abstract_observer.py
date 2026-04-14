from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QWidget

from Fish.Common.state import GameState


class Observer(QWidget):
    def set_state(self, state: GameState):
        raise NotImplementedError("Observer subclasses must implement set_state()")