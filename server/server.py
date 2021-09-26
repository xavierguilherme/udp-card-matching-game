#!/usr/bin/python3
import sys
import random
import string
import base64
import os
import uuid

from socket import socket, AF_INET, SOCK_DGRAM
from cryptography.fernet import Fernet, InvalidToken

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


def shuffle_cards():
    # Get 15 random cards from the folder imgs
    # and shuffles it for each game
    pars = {}

    cards_obj = [f'img{i + 1}' for i in range(30)]

    imgs = os.listdir('./cards/')

    for _ in range(15):
        c1 = cards_obj.pop(random.randint(0, len(cards_obj) - 1))
        c2 = cards_obj.pop(random.randint(0, len(cards_obj) - 1))
        img = imgs.pop(random.randint(0, len(imgs) - 1))

        pars[c1] = (c2, img)
        pars[c2] = (c1, img)

    return pars


class Server:
    def __init__(self):
        self.scoreboard = {}  # MAINTAIN INFORMATION ABOUT ALL THE PLAYERS AND IT'S SCORES IN THE SERVER

        self.lobby = {}  # HOLD ALL THE PLAYERS THAT ARE WAITING FOR A GAME TO START
        self.games = {}  # {GAME_ID: P1: {ADDR, SCORE, TURN}, P2: {ADDR, SCORE, TURN}}
        self.cards = {}  # MAINTAIN INFORMATION ABOUT THE CARDS WITHIN EACH GAME
        self.cards_turned = {}  # MAINTAIN INFORMATION ABOUT THE TWO CARDS TURNED IN A ROUND

        key = ''.join(random.SystemRandom().choice(string.ascii_uppercase +
                                                   string.ascii_lowercase +
                                                   string.digits) for _ in range(32))
        self.key = base64.b64encode(key.encode('ascii'))

        self.fern = Fernet(self.key)

        # Creating UDP socket
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind((SERVER_IP, SERVER_PORT))
        print('$-- SERVER ONLINE --$')

    def start(self):
        # Start to listen all the messages from the clients
        # and execute each action based on the protocol
        while True:
            client_msg, client_addr = self.socket.recvfrom(1500)
            try:
                decod_msg = self.fern.decrypt(client_msg).decode().split('|')
            except InvalidToken:
                decod_msg = client_msg.decode().split('|')

            if decod_msg[0] == 'NWU':
                self.handle_nwu(decod_msg[1], client_addr)
            elif decod_msg[0] == 'CKE':
                self.click_event(decod_msg[1], decod_msg[2], decod_msg[3],
                                 decod_msg[4], decod_msg[5])
            elif decod_msg[0] == 'WCL':
                self.handle_wcl(decod_msg[1], decod_msg[2])

            if len(self.lobby) > 1:
                self.start_game()

    def handle_nwu(self, username, user_addr):
        # Handle NWU opcode actions
        # Check if the username is valid and doesn't exists
        # If the condition is true, a new player is added to the game
        # Otherwise, asks the client to try another username
        msg = 'UAE|This username already exists or is invalid. Try another one.'.encode()
        if username not in self.scoreboard.keys() and username != '':
            self.lobby[username] = user_addr
            self.scoreboard[username] = 0
            msg = 'SUC|'.encode() + self.key
            self.update_scoreboard()
        self.socket.sendto(msg, user_addr)

    def handle_wcl(self, game_id, p_closed):
        # Handle WCL opcode actions
        # WCL is called a player force close a game window
        # So that player is disconnected from the server, the other one
        # needs to go back to the lobby and the information from the game is erased
        self.cards.pop(game_id)
        self.cards_turned.pop(game_id)
        self.scoreboard.pop(p_closed)
        for player, player_info in self.games[game_id].items():
            msg = f'WCM|{p_closed}'
            self.socket.sendto(self.fern.encrypt(msg.encode()), player_info[0])
            if player != p_closed:
                self.lobby[player] = self.games[game_id][player][0]
        self.games.pop(game_id)
        self.update_scoreboard()

    def start_game(self):
        # Called when there are at least 2 players waiting in the lobby for a game to start
        # All the data needed for a game is initialized and the players are remove from the lobby
        # Besides that, a message in sent to the players informing that they should open it's game windows
        player_1 = list(self.lobby.keys()).pop(0)
        player_1_addr = self.lobby.pop(player_1)
        player_2 = list(self.lobby.keys()).pop(0)
        player_2_addr = self.lobby.pop(player_2)

        cards = shuffle_cards()
        game_id = str(uuid.uuid1())

        self.games[game_id] = {player_1: [player_1_addr, 0, True], player_2: [player_2_addr, 0, False]}
        self.cards[game_id] = cards
        self.cards_turned[game_id] = []

        msg = f'SGM|{game_id}|{player_1}|{player_2}'
        self.socket.sendto(self.fern.encrypt(msg.encode()), player_1_addr)
        self.socket.sendto(self.fern.encrypt(msg.encode()), player_2_addr)

    def click_event(self, game_id, player, card, pos_x, pos_y):
        # Called every time a player perform a click event in it's game window
        # If it's not the player turn, nothing happens
        # Otherwise, the cards are flipped and the game data is updated
        if (len(self.cards_turned[game_id]) > 0 and card in self.cards_turned[game_id][0]) \
                or card not in self.cards[game_id] or not self.games[game_id][player][2] \
                or not card.startswith('img'):
            return

        img = self.cards[game_id][card][1]

        if len(self.cards_turned[game_id]) < 2:

            for player_info in self.games[game_id].values():
                self.socket.sendto(self.fern.encrypt(f'FLC|{pos_x}|{pos_y}|{img}|'.encode()),
                                   player_info[0])

            self.cards_turned[game_id].append((card, (pos_x, pos_y)))

            if len(self.cards_turned[game_id]) == 2:
                self.is_match(game_id, player, self.cards_turned[game_id])

        if len(self.cards[game_id]) == 0:
            game = {k: v for k, v in sorted(self.games[game_id].items(),
                                            key=lambda item: item[1], reverse=True)}
            for player, player_info in game.items():
                self.socket.sendto(self.fern.encrypt(f'GFN|{game_id}'.encode()), player_info[0])
                self.scoreboard[player] += player_info[1]
                self.lobby[player] = self.games[game_id][player][0]
            self.cards.pop(game_id)
            self.cards_turned.pop(game_id)
            self.games.pop(game_id)
            self.update_scoreboard()

    def is_match(self, game_id, player, cards_turned):
        # Function called when exactly 2 cards are flipped in the board by the current player
        # If the 2 cards are a match, a point is added to the score of the player and he keeps playing
        # Otherwise, the 2 cards are flipped again and the turn passes to the other player
        players = list(self.games[game_id].keys())
        pos = 1 if players[0] == player else 2

        if self.cards[game_id][cards_turned[0][0]][0] == cards_turned[1][0]:  # MATCHED
            self.cards[game_id].pop(cards_turned[0][0])
            self.cards[game_id].pop(cards_turned[1][0])
            self.games[game_id][player][1] = self.games[game_id][player][1] + 1
            for player_info in self.games[game_id].values():
                self.socket.sendto(self.fern.encrypt(f'UPS|{player}|{self.games[game_id][player][1]}|'
                                                     f'{pos}'.encode()), player_info[0])
        else:  # UNMATCHED
            self.games[game_id][players[0]][2] = not self.games[game_id][players[0]][2]
            self.games[game_id][players[1]][2] = not self.games[game_id][players[1]][2]

            for player_info in self.games[game_id].values():
                self.socket.sendto(self.fern.encrypt(f'NRD|{pos}|{cards_turned[0][1][0]}|{cards_turned[0][1][1]}|'
                                                     f'{cards_turned[1][1][0]}|{cards_turned[1][1][1]}'.encode()),
                                   player_info[0])

        self.cards_turned[game_id] = []

    def update_scoreboard(self):
        # Function that updates the scoreboard everytime a game is finished or
        # a player leaves or is disconnected from the server
        os.system('cls' if os.name == 'nt' else 'clear')
        self.scoreboard = {k: v for k, v in sorted(self.scoreboard.items(),
                                                   key=lambda item: item[1], reverse=True)}
        print('\t###### GAME SCOREBOARD ######')
        for player, score in self.scoreboard.items():
            print(f'\t{player} : {score}')


if __name__ == '__main__':
    server = Server()
    server.start()
