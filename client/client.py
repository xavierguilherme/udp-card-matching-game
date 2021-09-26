#!/usr/bin/python3
import sys
import threading

from PyQt5 import QtTest
from PyQt5.QtWidgets import QApplication

from app import MainWindow

from socket import socket, AF_INET, SOCK_DGRAM
from cryptography.fernet import Fernet

SERVER_IP = sys.argv[1]
SERVER_PORT = int(sys.argv[2])

# Application Layer Protocol:
# SGM -- START THE GAME BETWEEN TWO PLAYERS
# UAE -- THE USERNAME ALREADY EXISTS IN THE SERVER
# SUC -- INDICATES A VALID USERNAME
# FLC -- FLIP THE CARDS WHEN A PLAYER MAKE A PLAY
# UPS -- UPDATE THE SCORE OF A GAME
# NRD -- ACTION NEEDS TO BE DONE WHEN A NEW ROUND IS ABOUT TO START
# GFN -- INDICATES ALL THE PAIRS WERE FLIPPED AND THE GAME IS FINISHED
# NWU -- CREATE A NEW USER IN THE SERVER
# CKE -- AN EVENT (CLICK) HAPPENS IN THE GAME UI
# WCL -- THE GAME WINDOW WAS CLOSED BY THE PLAYER
# WCM -- ONE OF THE PLAYERS CLOSED THE WINDOW SO THE OTHER ONE SHOULD BE BACK TO THE LOBBY


class Client:
    def __init__(self):
        self.conn_window = QApplication([])
        # Creating UDP socket
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.username = ''
        self.game_id = ''
        self.game_window = None
        self.closed_window = True
        self.exit_game = False

        self.fern = None

        self.set_username()

    def start(self):
        # First function to be called when a game is about to start
        # Wait for a SGM signal from the server and start the player's game window
        # Also creates a thread to execute listen_server and perform actions between players
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
        # Receives most of the server messages and decides which operations needs to be done
        # based on the opcodes defined for the protocol
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
        # Receives a server message to flip the card choosed by player in it's turn
        # Waits a few ms so that the second card flipped appears in the UI
        card = self.game_window.childAt(int(pos_x),
                                        int(pos_y))
        card_name = card.objectName()
        card.setStyleSheet(f"""
                            #{card_name} {{
                                background-image: url(./cards/{img_file});
                                background-repeat: no-repeat;
                                background-position: center;
                            }}
                        """)
        QtTest.QTest.qWait(800)

    def handle_ups(self, player, player_score, prev_play):
        # Update the score of a player after a match
        if int(prev_play) == 1:
            self.game_window.w1.p1_pts.setText(f'{player} : {player_score}')
        else:
            self.game_window.w1.p2_pts.setText(f'{player} : {player_score}')

    def handle_nrd(self, prev_play, c1_pos_x, c1_pos_y, c2_pos_x, c2_pos_y):
        # Restart the game UI every time a player missed a pair,
        # so the cards need to be flipped again and the player turn should change
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
                        background-image: url(./client/imgs/cards.png);
                        background-repeat: no-repeat;
                        background-position: center;
                    }}
                """)

    def set_username(self):
        # Needed to make the first interaction with the server
        # This function is fully executed only when an username is validated by the server
        username = input('Enter your username: ')
        while True:
            self.socket.sendto(f'NWU|{username.strip()}'.encode(),
                               (SERVER_IP, SERVER_PORT))
            msg, server_addr = self.socket.recvfrom(1500)
            decod_msg = msg.decode().split('|')
            if decod_msg[0] == 'UAE':
                print(decod_msg[1])
                username = input('Enter your username: ')
            else:
                self.fern = Fernet(decod_msg[1])
                self.username = username
                break

    def click_event(self, click):
        # Every time a player clicks the UI, this function is called
        # A CKE message is sent to the server with the information about
        # the object clicked and it's position, so the action can be decided and done by the server
        pos = click.pos()
        card = self.game_window.childAt(pos)
        card_name = card.objectName()
        self.socket.sendto(self.fern.encrypt(f'CKE|{self.game_id}|{self.username}|{card_name}|'
                                             f'{pos.x()}|{pos.y()}'.encode()),
                           (SERVER_IP, SERVER_PORT))


if __name__ == '__main__':
    client = Client()
    client.start()
