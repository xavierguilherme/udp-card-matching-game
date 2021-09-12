#!/usr/bin/python3
from socket import socket, AF_INET, SOCK_DGRAM

from PyQt5 import QtTest
from PyQt5.QtWidgets import QApplication

from app import MainWindow
import sys
import threading

SERVER_PORT = 7777
SERVER_IP = '192.168.3.6'


class Client:
    def __init__(self):
        self.conn_window = QApplication([])
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.username = ''
        self.game_id = ''
        self.game_window = None

        self.set_username()

    def start(self):
        msg, server_addr = self.socket.recvfrom(1500)
        decod_msg = msg.decode().split('|')
        if decod_msg[0] == 'START_GAME':
            self.game_id = decod_msg[1]
            # print(f'Memory Game started: {decod_msg[2]} vs {decod_msg[3]}')
            self.game_window = MainWindow(decod_msg[2], decod_msg[3], self.click_event)
            self.game_window.show()
            th = threading.Thread(target=self.listen_server)
            th.start()
            sys.exit(self.conn_window.exec_())

    def listen_server(self):
        while True:
            msg, server_addr = self.socket.recvfrom(1500)
            decod_msg = msg.decode().split('|')
            if decod_msg[0] == 'FLIP_CARD':
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
            elif decod_msg[0] == 'UPDATE_SCORE':
                if int(decod_msg[3]) == 1:
                    self.game_window.w1.p1_pts.setText(f'{decod_msg[1]}: {decod_msg[2]}')
                else:
                    self.game_window.w1.p2_pts.setText(f'{decod_msg[1]}: {decod_msg[2]}')
            elif decod_msg[0] == 'NEW_ROUND':
                if int(decod_msg[1]) == 1:
                    self.game_window.w1.p2_pts.setStyleSheet("color: red")
                    self.game_window.w1.p1_pts.setStyleSheet("color: white")
                else:
                    self.game_window.w1.p1_pts.setStyleSheet("color: red")
                    self.game_window.w1.p2_pts.setStyleSheet("color: white")

                for i in range(0, 4, 2):
                    card = self.game_window.childAt(int(decod_msg[i+2]),
                                                    int(decod_msg[i+3]))
                    card_name = card.objectName()
                    card.setStyleSheet(f"""
                            #{card_name} {{
                                background-image: url(cards.png);
                                background-repeat: no-repeat;
                                background-position: center;
                            }}
                        """)
            elif decod_msg[0] == 'GAME_FINISHED':
                print(f'Game is finished. Final score: {decod_msg[1]} {decod_msg[2]} vs '
                      f'{decod_msg[4]} {decod_msg[3]}')
                self.game_window.close()
            elif decod_msg[0] == 'LOBBY':
                print(decod_msg[1])
                self.start()

    def set_username(self):
        username = input('Enter your username: ')
        while True:
            self.socket.sendto(f'NEW_USER|{username}'.encode(), (SERVER_IP, SERVER_PORT))
            msg, server_addr = self.socket.recvfrom(1500)
            decod_msg = msg.decode().split('|')
            if decod_msg[0] == 'ERR':
                print('Username already exists. Try again.')
                username = input('Enter your username: ')
            else:
                self.username = username
                print(decod_msg[1])
                return

    def click_event(self, click):
        pos = click.pos()
        card = self.game_window.childAt(pos)
        card_name = card.objectName()
        self.socket.sendto(f'CLICK_EVENT|{self.game_id}|{self.username}|{card_name}|{pos.x()}|{pos.y()}'.encode(),
                           (SERVER_IP, SERVER_PORT))

    def close(self):
        self.socket.close()


if __name__ == '__main__':
    client = Client()
    client.start()
