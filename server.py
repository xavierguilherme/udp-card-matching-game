#!/usr/bin/python3
from socket import socket, AF_INET, SOCK_DGRAM
import random
import os
import uuid

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
        self.lobby = {}
        self.games = {}

        self.cards = {}
        self.cards_turned = {}

        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((SERVER_IP, SERVER_PORT))
        print('Server is on...')

    def start(self):
        while True:
            client_msg, client_addr = self.socket.recvfrom(1500)
            decod_client_msg = client_msg.decode().split('|')

            if decod_client_msg[0] == 'NEW_USER':
                msg = 'ERR|This username already exists. Try another one.'
                if decod_client_msg[1] not in self.lobby \
                        and decod_client_msg[1] not in self.games:
                    self.lobby[decod_client_msg[1]] = client_addr
                    msg = f'SUCC|Welcome {decod_client_msg[1]}. Finding an opponent...'
                    print(f'{client_addr} - {decod_client_msg[1]} joined the game.')
                self.socket.sendto(msg.encode(), client_addr)
            elif decod_client_msg[0] == 'CLICK_EVENT':
                self.click_event(decod_client_msg[1], decod_client_msg[2], decod_client_msg[3],
                                 decod_client_msg[4], decod_client_msg[5])

            if len(self.lobby) > 1:
                player_1 = random.choice(list(self.lobby.keys()))
                player_1_addr = self.lobby.pop(player_1)
                player_2 = random.choice(list(self.lobby.keys()))
                player_2_addr = self.lobby.pop(player_2)

                cards = shuffle_cards()
                game_id = str(uuid.uuid1())

                self.games[game_id] = {player_1: [player_1_addr, 0, True], player_2: [player_2_addr, 0, False]}
                self.cards[game_id] = cards
                self.cards_turned[game_id] = []

                msg = f'START_GAME|{game_id}|{player_1}: 0|{player_2}: 0'
                self.socket.sendto(msg.encode(), player_1_addr)
                self.socket.sendto(msg.encode(), player_2_addr)

    def click_event(self, game_id, player, card, pos_x, pos_y):
        if not card.startswith('img'): return

        img = self.cards[game_id][card][1]

        if (len(self.cards_turned[game_id]) > 0 and card in self.cards_turned[game_id][0]) \
                or card not in self.cards[game_id] or not self.games[game_id][player][2]:
            return

        if len(self.cards_turned[game_id]) < 2:
            for _, values in self.games[game_id].items():
                self.socket.sendto(f'FLIP_CARD|{pos_x}|{pos_y}|{img}'.encode(), values[0])

            self.cards_turned[game_id].append((card, (pos_x, pos_y)))

            self.is_match(game_id, player, self.cards_turned[game_id])

        players = list(self.games[game_id].keys())
        if len(self.cards[game_id]) == 0:
            for _, values in self.games[game_id].items():
                self.socket.sendto(f'GAME_FINISHED|{players[0]}|{self.games[game_id][players[0]][1]}|'
                                   f'{players[1]}|{self.games[game_id][players[1]][1]}'.encode(), values[0])

            self.cards.pop(game_id)
            self.cards_turned.pop(game_id)
            self.lobby[players[0]] = self.games[game_id][players[0]][0]
            self.lobby[players[1]] = self.games[game_id][players[1]][0]

            for player, values in self.games[game_id].items():
                self.socket.sendto(f'LOBBY|Welcome back to the lobby {player}. '
                                   f'We\'re trying to find another opponent.'.encode(), values[0])

            self.games.pop(game_id)

    def is_match(self, game_id, player, cards_turned):
        players = list(self.games[game_id].keys())
        pos = 1 if players[0] == player else 2
        if len(self.cards_turned[game_id]) == 2:
            if self.cards[game_id][cards_turned[0][0]][0] == cards_turned[1][0]:
                # remove pars from dict
                self.cards[game_id].pop(cards_turned[0][0])
                self.cards[game_id].pop(cards_turned[1][0])
                # add points
                self.games[game_id][player][1] = self.games[game_id][player][1] + 1
                for _, values in self.games[game_id].items():
                    self.socket.sendto(f'UPDATE_SCORE|{player}|{self.games[game_id][player][1]}|'
                                       f'{pos}'.encode(), values[0])
            else:  # return image and next player
                self.games[game_id][players[0]][2] = not self.games[game_id][players[0]][2]
                self.games[game_id][players[1]][2] = not self.games[game_id][players[1]][2]

                for _, values in self.games[game_id].items():
                    self.socket.sendto(f'NEW_ROUND|{pos}|{cards_turned[0][1][0]}|{cards_turned[0][1][1]}|'
                                       f'{cards_turned[1][1][0]}|{cards_turned[1][1][1]}'.encode(), values[0])

            self.cards_turned[game_id] = []


if __name__ == '__main__':
    server = Server()
    server.start()
