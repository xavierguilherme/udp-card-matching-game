#!/usr/bin/python3
from socket import socket, AF_INET, SOCK_DGRAM

from PyQt5 import QtTest
from PyQt5.QtWidgets import QApplication

from app import MainWindow
import sys
import threading

SERVER_PORT = 7788
# SERVER_IP = '25.102.154.225'
SERVER_IP = '192.168.3.6'


# NRD -- USED WHEN A NEW ROUND IS ABOUT TO START
# SGM -- USED TO THE START THE GAME BETWEEN TWO PLAYERS
# UAE -- USED WHEN AN USERNAME THAT ALREADY EXISTS IS TYPED
# UPS -- USED TO UPDATE THE SCORE OF A GAME
# FLC -- USED TO FLIP THE CARDS WHEN A PLAYER MAKE A PLAY
# GFN -- USED WHEN THE PAIRS WERE FLIPPED AND THE GAME IS FINISHED
# NWU -- USED TO CREATE A NEW USER IN THE SERVER
# CKE -- USED WHEN AN EVENT (CLICK) HAPPENS IN THE GAME UI
# LOB -- USED TO TELL THE PLAYER IS BACK IN THE LOBBY


class Client:
    def __init__(self):
        self.conn_window = QApplication([])
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.username = ''
        self.game_id = ''
        self.game_window = None
        self.process = None

        self.set_username()

    def start(self):
        while True:
            server_msg, server_addr = self.socket.recvfrom(1500)
            decod_msg = server_msg.decode().split('|')
            if decod_msg[0] == 'SGM':
                self.game_id = decod_msg[1]
                print(f'Game started: {decod_msg[2]} vs {decod_msg[3]}')
                self.game_window = MainWindow(decod_msg[2], decod_msg[3], self.click_event)
                self.game_window.show()
                thread = threading.Thread(target=self.listen_server)
                thread.start()
                # sys.exit(self.conn_window.exec_())
                self.conn_window.exec_()
                thread.join()

    def listen_server(self):
        while True:
            msg, server_addr = self.socket.recvfrom(1500)
            decod_msg = msg.decode().split('|')

            if decod_msg[0] == 'FLC':
                card = self.game_window.childAt(int(decod_msg[1]),
                                                int(decod_msg[2]))
                card_name = card.objectName()
                card.setStyleSheet(f"""
                    #{card_name} {{
                        background-image: url(imgs/{decod_msg[3]});
                        background-repeat: no-repeat;
                        background-position: center;
                    }}
                """)
                QtTest.QTest.qWait(800)
            elif decod_msg[0] == 'UPS':
                if int(decod_msg[3]) == 1:
                    self.game_window.w1.p1_pts.setText(f'{decod_msg[1]} : {decod_msg[2]}')
                else:
                    self.game_window.w1.p2_pts.setText(f'{decod_msg[1]} : {decod_msg[2]}')
            elif decod_msg[0] == 'NRD':
                if int(decod_msg[1]) == 1:
                    self.game_window.w1.p2_pts.setStyleSheet("color: red")
                    self.game_window.w1.p1_pts.setStyleSheet("color: white")
                else:
                    self.game_window.w1.p1_pts.setStyleSheet("color: red")
                    self.game_window.w1.p2_pts.setStyleSheet("color: white")

                for i in range(0, 4, 2):
                    card = self.game_window.childAt(int(decod_msg[i + 2]),
                                                    int(decod_msg[i + 3]))
                    card_name = card.objectName()
                    card.setStyleSheet(f"""
                            #{card_name} {{
                                background-image: url(cards.png);
                                background-repeat: no-repeat;
                                background-position: center;
                            }}
                        """)
            elif decod_msg[0] == 'GFN':
                print(f'Game is finished. Final score: {self.game_window.w1.p1_pts.text()} vs '
                      f'{self.game_window.w1.p2_pts.text()}')
                self.game_window.close()
            elif decod_msg[0] == 'LOB':
                print(decod_msg[1])
                break

    def set_username(self):
        username = input('Enter your username: ')
        while True:
            self.socket.sendto(f'NWU|{username}'.encode(), (SERVER_IP, SERVER_PORT))
            msg, server_addr = self.socket.recvfrom(1500)
            decod_msg = msg.decode().split('|')
            if decod_msg[0] == 'UAE':
                print('Username already exists. Try again.')
                username = input('Enter your username: ')
            else:
                self.username = username
                print(decod_msg[1])
                break

    def click_event(self, click):
        pos = click.pos()
        card = self.game_window.childAt(pos)
        card_name = card.objectName()
        self.socket.sendto(f'CKE|{self.game_id}|{self.username}|{card_name}|{pos.x()}|{pos.y()}'.encode(),
                           (SERVER_IP, SERVER_PORT))

    def close(self):
        self.socket.close()


if __name__ == '__main__':
    client = Client()
    client.start()
