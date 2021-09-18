#!/usr/bin/python3
from socket import socket, AF_INET, SOCK_DGRAM
import random
import os
import uuid

SERVER_PORT = 7788
# SERVER_IP = '25.102.154.225'
SERVER_IP = '192.168.3.6'


# NRD -- USED WHEN A NEW ROUND IS ABOUT TO START
# SGM -- USED TO THE START THE GAME BETWEEN TWO PLAYERS
# UAE -- USED WHEN AN USERNAME THAT ALREADY EXISTS IS TYPED
# UPS -- USED TO UPDATE THE SCORE OF A GAME
# FLC -- USED TO FLIP THE CARDS WHEN A PLAYER MISSES A PAIR
# GFN -- USED WHEN THE PAIRS WERE FLIPPED AND THE GAME IS FINISHED
# NWU -- USED TO CREATE A NEW USER IN THE SERVER
# CKE -- USED WHEN AN EVENT (CLICK) HAPPENS IN THE GAME UI
# LOB -- USED TO TELL THE PLAYER IS BACK IN THE LOBBY

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
        self.players = []  # MAINTAIN INFORMATION ABOUT ALL THE PLAYERS IN THE SERVER

        self.lobby = {}  # HOLD ALL THE PLAYERS THAT ARE WAITING FOR A GAME TO START
        self.games = {}  # {GAME_ID: P1: {ADDR, SCORE, TURN}, P2: {ADDR, SCORE, TURN}}
        self.cards = {}  # MAINTAIN INFORMATION ABOUT THE CARDS WITHIN EACH GAME
        self.cards_turned = {}  # MAINTAIN INFORMATION ABOUT THE TWO CARDS TURNED IN A ROUND

        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((SERVER_IP, SERVER_PORT))
        print('$-- SERVER ONLINE --$')

    def start(self):
        while True:
            client_msg, client_addr = self.socket.recvfrom(1500)
            decod_msg = client_msg.decode().split('|')

            if decod_msg[0] == 'NWU':
                msg = 'UAE|This username already exists. Try another one.'
                if decod_msg[1] not in self.players:
                    self.lobby[decod_msg[1]] = client_addr
                    self.players.append(decod_msg[1])
                    msg = f'SUC|Welcome {decod_msg[1]}. Finding an opponent...'
                    print(f'{client_addr} - {decod_msg[1]} joined the game.')
                self.socket.sendto(msg.encode(), client_addr)
            elif decod_msg[0] == 'CKE':
                self.click_event(decod_msg[1], decod_msg[2], decod_msg[3],
                                 decod_msg[4], decod_msg[5])

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

                msg = f'SGM|{game_id}|{player_1}|{player_2}'
                print(f'Game started: {player_1} vs {player_2}')
                self.socket.sendto(msg.encode(), player_1_addr)
                self.socket.sendto(msg.encode(), player_2_addr)

    def click_event(self, game_id, player, card, pos_x, pos_y):
        if not card.startswith('img'):
            return

        img = self.cards[game_id][card][1]

        if (len(self.cards_turned[game_id]) > 0 and card in self.cards_turned[game_id][0]) \
                or card not in self.cards[game_id] or not self.games[game_id][player][2]:
            return

        if len(self.cards_turned[game_id]) < 2:

            for player_info in self.games[game_id].values():
                self.socket.sendto(f'FLC|{pos_x}|{pos_y}|{img}|'.encode(), player_info[0])

            self.cards_turned[game_id].append((card, (pos_x, pos_y)))

            if len(self.cards_turned[game_id]) == 2:
                self.is_match(game_id, player, self.cards_turned[game_id])

        if len(self.cards[game_id]) == 0:
            for player, player_info in self.games[game_id].items():
                self.socket.sendto(f'GFN|{game_id}'.encode(), player_info[0])
                self.lobby[player] = self.games[game_id][player][0]
            self.cards.pop(game_id)
            self.cards_turned.pop(game_id)

            for player, player_info in self.games[game_id].items():
                self.socket.sendto(f'LOB|Welcome back to the lobby {player}. '
                                   f'We\'re trying to find another opponent.'.encode(), player_info[0])
            self.games.pop(game_id)

    def is_match(self, game_id, player, cards_turned):
        players = list(self.games[game_id].keys())
        pos = 1 if players[0] == player else 2

        if self.cards[game_id][cards_turned[0][0]][0] == cards_turned[1][0]:  # MATCHED
            self.cards[game_id].pop(cards_turned[0][0])
            self.cards[game_id].pop(cards_turned[1][0])
            self.games[game_id][player][1] = self.games[game_id][player][1] + 1
            for player_info in self.games[game_id].values():
                self.socket.sendto(f'UPS|{player}|{self.games[game_id][player][1]}|'
                                   f'{pos}'.encode(), player_info[0])
        else:  # UNMATCHED
            self.games[game_id][players[0]][2] = not self.games[game_id][players[0]][2]
            self.games[game_id][players[1]][2] = not self.games[game_id][players[1]][2]

            for player_info in self.games[game_id].values():
                self.socket.sendto(f'NRD|{pos}|{cards_turned[0][1][0]}|{cards_turned[0][1][1]}|'
                                   f'{cards_turned[1][1][0]}|{cards_turned[1][1][1]}'.encode(), player_info[0])

        self.cards_turned[game_id] = []


if __name__ == '__main__':
    server = Server()
    server.start()
