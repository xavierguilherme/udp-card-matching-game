# pyuic5 -x main_window.ui -o design.py

import sys
from PyQt5.QtWidgets import QApplication
from control import MainWindow


class MemoryGame:
    def __init__(self, p1, p2, cards, action):
        self.conn_window = QApplication(sys.argv)
        self.w = MainWindow(p1, p2, cards, action)
        self.w.setWindowTitle('Memory Game')
        self.w.resize(1031, 653)
        self.w.show()
        sys.exit(self.conn_window.exec_())
