#!/usr/bin/python3
from socket import socket, AF_INET, SOCK_DGRAM
import random
import os
import json

SERVER_PORT = 7777
SERVER_IP = '192.168.3.6'


def shuffle_cards():
    pars = {}

    cards_obj = [f'img{i + 1}' for i in range(30)]

    imgs = os.listdir('imgs/')

    for _ in range(15):
        c1 = cards_obj.pop(random.randint(0, len(cards_obj) - 1))
        c2 = cards_obj.pop(random.randint(0, len(cards_obj) - 1))
        img = imgs.pop(random.randint(0, len(imgs) - 1))

        pars[c1] = (c2, img)
        pars[c2] = (c1, img)

    return pars


class Server:
    def __init__(self):
        self.waiting_clients = {}
        self.playing_clients = {}
        self.games = {}
        self.game_state = {}
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((SERVER_IP, SERVER_PORT))
        print('Server is on...')

    def start(self):
        while True:
            client_msg, client_addr = self.socket.recvfrom(1500)
            decod_client_msg = client_msg.decode().split('|')

            if decod_client_msg[0] == 'ADD_USER':
                msg = 'ERR|This username already exists. Try another one.'
                if decod_client_msg[1] not in self.waiting_clients \
                        and decod_client_msg[1] not in self.playing_clients:
                    self.waiting_clients[decod_client_msg[1]] = client_addr
                    msg = f'SUCC|Welcome {decod_client_msg[1]}. Finding an opponent...'
                print(f'{client_addr} - {decod_client_msg[1]} joined the game.')
                self.socket.sendto(msg.encode(), client_addr)
            if len(self.waiting_clients) > 1:
                player_1 = random.choice(list(self.waiting_clients.keys()))
                player_1_addr = self.waiting_clients.pop(player_1)
                player_2 = random.choice(list(self.waiting_clients.keys()))
                player_2_addr = self.waiting_clients.pop(player_2)

                self.playing_clients[player_1] = player_1_addr
                self.playing_clients[player_2] = player_2_addr

                cards = shuffle_cards()
                self.games[(player_1, player_2)] = cards

                msg = f'START_GAME|{player_1}|{player_2}|{json.dumps(cards)}'
                self.socket.sendto(msg.encode(), player_1_addr)
                self.socket.sendto(msg.encode(), player_2_addr)


if __name__ == '__main__':
    server = Server()
    server.start()
