#!/usr/bin/python3
import threading
from socket import socket, AF_INET, SOCK_DGRAM

from PyQt5 import QtTest
from PyQt5.QtWidgets import QApplication

from cryptography.fernet import Fernet

from app import MainWindow

KEY = 'VWllRVh4TE5nb3hDenVxWUFCVHpmdGZWUFZLZ2dTa1k='

SERVER_PORT = 7766
# SERVER_IP = '25.102.154.225'
SERVER_IP = '192.168.3.6'

# SGM -- USED TO THE START THE GAME BETWEEN TWO PLAYERS
# UAE -- USED WHEN AN USERNAME THAT ALREADY EXISTS IS TYPED
# SUC -- USED TO INDICATE IT'S A VALID USERNAME
# FLC -- USED TO FLIP THE CARDS WHEN A PLAYER MAKE A PLAY
# UPS -- USED TO UPDATE THE SCORE OF A GAME
# NRD -- USED WHEN A NEW ROUND IS ABOUT TO START
# GFN -- USED WHEN THE PAIRS WERE FLIPPED AND THE GAME IS FINISHED
# NWU -- USED TO CREATE A NEW USER IN THE SERVER
# CKE -- USED WHEN AN EVENT (CLICK) HAPPENS IN THE GAME UI
# WCL -- USED TO TELL THE SERVER THE GAME WINDOW WAS CLOSED BY THE PLAYER
# WCM -- TELLS THE PLAYERS OF A GAME THAT ONE OF THE PLAYERS CLOSED THE WINDOW, SO THEY ARE BACK TO THE LOBBY


class Client:
    def __init__(self):
        self.conn_window = QApplication([])
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.username = ''
        self.game_id = ''
        self.game_window = None
        self.closed_window = True
        self.exit_game = False

        self.fern = Fernet(KEY)

        self.set_username()

    def start(self):
        while True:
            print('Welcome to the lobby. Looking for an opponent...')
            server_msg, server_addr = self.socket.recvfrom(1500)
            decod_msg = self.fern.decrypt(server_msg).decode().split('|')
            if decod_msg[0] == 'SGM':
                self.game_id = decod_msg[1]
                print(f'Game started: {decod_msg[2]} vs {decod_msg[3]}')
                self.game_window = MainWindow(decod_msg[2], decod_msg[3], self.click_event)
                self.game_window.show()
                thread = threading.Thread(target=self.listen_server)
                thread.start()
                self.conn_window.exec_()
                if self.closed_window:
                    self.socket.sendto(self.fern.encrypt(f'WCL|{self.game_id}|{self.username}'.encode()),
                                       (SERVER_IP, SERVER_PORT))
                thread.join()
                self.closed_window = True
                if self.exit_game:
                    self.socket.close()
                    exit()

    def listen_server(self):
        while True:
            msg, server_addr = self.socket.recvfrom(1500)
            decod_msg = self.fern.decrypt(msg).decode().split('|')

            if decod_msg[0] == 'FLC':
                self.handle_flc(decod_msg[1], decod_msg[2], decod_msg[3])
            elif decod_msg[0] == 'UPS':
                self.handle_ups(decod_msg[1], decod_msg[2], decod_msg[3])
            elif decod_msg[0] == 'NRD':
                self.handle_nrd(decod_msg[1], decod_msg[2], decod_msg[3],
                                decod_msg[4], decod_msg[5])
            elif decod_msg[0] == 'GFN':
                print(f'Game is finished. Final score: {self.game_window.w1.p1_pts.text()} vs '
                      f'{self.game_window.w1.p2_pts.text()}')
                self.closed_window = False
                self.game_window.close()
                break
            elif decod_msg[0] == 'WCM':
                print(f'The game was closed by one of the players. You\'re back to the lobby')
                if self.username != decod_msg[1]:
                    self.closed_window = False
                    self.game_window.close()
                else:
                    self.exit_game = True
                break

    def handle_flc(self, pos_x, pos_y, img_file):
        card = self.game_window.childAt(int(pos_x),
                                        int(pos_y))
        card_name = card.objectName()
        card.setStyleSheet(f"""
                            #{card_name} {{
                                background-image: url(imgs/{img_file});
                                background-repeat: no-repeat;
                                background-position: center;
                            }}
                        """)
        QtTest.QTest.qWait(800)

    def handle_ups(self, player, player_score, prev_play):
        if int(prev_play) == 1:
            self.game_window.w1.p1_pts.setText(f'{player} : {player_score}')
        else:
            self.game_window.w1.p2_pts.setText(f'{player} : {player_score}')

    def handle_nrd(self, prev_play, c1_pos_x, c1_pos_y, c2_pos_x, c2_pos_y):
        if int(prev_play) == 1:
            self.game_window.w1.p2_pts.setStyleSheet("color: red")
            self.game_window.w1.p1_pts.setStyleSheet("color: white")
        else:
            self.game_window.w1.p1_pts.setStyleSheet("color: red")
            self.game_window.w1.p2_pts.setStyleSheet("color: white")

        for pos_x, pos_y in [(c1_pos_x, c1_pos_y), (c2_pos_x, c2_pos_y)]:
            card = self.game_window.childAt(int(pos_x),
                                            int(pos_y))
            card_name = card.objectName()
            card.setStyleSheet(f"""
                    #{card_name} {{
                        background-image: url(cards.png);
                        background-repeat: no-repeat;
                        background-position: center;
                    }}
                """)

    def set_username(self):
        username = input('Enter your username: ')
        while True:
            self.socket.sendto(self.fern.encrypt(f'NWU|{username.strip()}'.encode()),
                               (SERVER_IP, SERVER_PORT))
            msg, server_addr = self.socket.recvfrom(1500)
            decod_msg = self.fern.decrypt(msg).decode().split('|')
            if decod_msg[0] == 'UAE':
                print(decod_msg[1])
                username = input('Enter your username: ')
            else:
                self.username = username
                print(decod_msg[1])
                break

    def click_event(self, click):
        pos = click.pos()
        card = self.game_window.childAt(pos)
        card_name = card.objectName()
        self.socket.sendto(self.fern.encrypt(f'CKE|{self.game_id}|{self.username}|{card_name}|'
                                             f'{pos.x()}|{pos.y()}'.encode()),
                           (SERVER_IP, SERVER_PORT))


if __name__ == '__main__':
    client = Client()
    client.start()
