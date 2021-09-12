# pyuic5 -x main_window.ui -o design.py

from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtTest
from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QWidget
from design import MainWindowUI


class GameWindow(QMainWindow, MainWindowUI):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setStyleSheet("""
        #MainWindow {
            background-image: url(background.jpg);
            background-repeat: no-repeat;
            background-position: center;
        }
        """)

        self.set_init_cards_bc()

        self.show()

    def set_init_cards_bc(self):
        for i in range(30):
            self.findChild(QWidget, f'img{i + 1}').setStyleSheet(f"""
                #img{i + 1} {{
                    background-image: url(cards.png);
                    background-repeat: no-repeat;
                    background-position: center;
                }}
            """)


class MainWindow(QStackedWidget):
    def __init__(self, p1, p2, action):
        super().__init__()

        self.setWindowTitle('Memory Game')
        self.resize(1031, 653)

        self.w1 = GameWindow()
        self.addWidget(self.w1)

        self.w1.p1_pts.setText(p1)
        self.w1.p2_pts.setText(p2)
        self.w1.p1_pts.setStyleSheet("color: red")

        self.w1.mouseReleaseEvent = action


