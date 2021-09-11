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
    def __init__(self, p1, p2, cards, action):
        super().__init__()
        self.w1 = GameWindow()
        self.addWidget(self.w1)

        self.w1.p1_pts.setText(p1)
        self.w1.p2_pts.setText(p2)
        self.pars = cards
        self.server_action = action

        self.w1.mouseReleaseEvent = self.card_click

        self.cards_turned = []
        self.is_player_1 = True
        self.w1.p1_pts.setStyleSheet("color: red")

    @pyqtSlot()
    def card_click(self, event):
        pos = event.pos()
        card = self.childAt(pos)
        card_name = card.objectName()

        if (len(self.cards_turned) > 0 and card_name in self.cards_turned[0]) \
                or card_name not in self.pars:
            return

        img = self.pars[card_name][1]

        if len(self.cards_turned) < 2:
            card.setStyleSheet(f"""
                #{card_name} {{
                    background-image: url(imgs/{img});
                    background-repeat: no-repeat;
                    background-position: center;
                }}
            """)

            self.cards_turned.append((card_name, card), )

            QtTest.QTest.qWait(800)

            self.is_match()

    @pyqtSlot()
    def is_match(self):
        if len(self.cards_turned) == 2:
            if self.pars[self.cards_turned[0][0]][0] == self.cards_turned[1][0]:
                # add points
                if self.is_player_1:
                    p1 = self.w1.p1_pts.text().split(': ')
                    self.w1.p1_pts.setText(f'{p1[0]}: {int(p1[1]) + 1}')
                else:
                    p2 = self.w1.p2_pts.text().split(': ')
                    self.w1.p2_pts.setText(f'{p2[0]}: {int(p2[1]) + 1}')

                # remove pars from dict
                self.pars.pop(self.cards_turned[0][0])
                self.pars.pop(self.cards_turned[1][0])
            else:  # return image and next player
                self.is_player_1 = not self.is_player_1
                if self.is_player_1:
                    self.w1.p1_pts.setStyleSheet("color: red")
                    self.w1.p2_pts.setStyleSheet("color: white")
                else:
                    self.w1.p2_pts.setStyleSheet("color: red")
                    self.w1.p1_pts.setStyleSheet("color: white")

                for name, obj in self.cards_turned:
                    obj.setStyleSheet(f"""
                        #{name} {{
                            background-image: url(cards.png);
                            background-repeat: no-repeat;
                            background-position: center;
                        }}
                    """)
            self.cards_turned = []
