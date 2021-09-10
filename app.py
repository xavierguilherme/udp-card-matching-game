#!/usr/bin/env python

# pyuic5 -x main_window.ui -o design.py

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from control import MainWindow

def run():
    conn_window = QApplication(sys.argv)
    w = MainWindow()
    w.setWindowTitle('Memory Game')
    w.resize(1031, 653)
    w.show()
    sys.exit(conn_window.exec_())
