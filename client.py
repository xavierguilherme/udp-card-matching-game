#!/usr/bin/python3
from socket import socket, AF_INET, SOCK_DGRAM
from app import MemoryGame
import json

SERVER_PORT = 7777
SERVER_IP = '192.168.3.6'


class Client:
    def __init__(self):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.username = ''

    def start(self):
        self.set_username()
        while True:
            msg, server_addr = self.socket.recvfrom(1500)
            decod_msg = msg.decode().split('|')
            if decod_msg[0] == 'START_GAME':
                print(f'Memory Game started: {decod_msg[1]} vs {decod_msg[2]}')
                game = MemoryGame(decod_msg[1], decod_msg[2], json.loads(decod_msg[3]), self.click_action)

    def set_username(self):
        username = input('Enter your username: ')
        while True:
            self.socket.sendto(f'ADD_USER|{username}'.encode(), (SERVER_IP, SERVER_PORT))
            msg, server_addr = self.socket.recvfrom(1500)
            decod_msg = msg.decode().split('|')
            if decod_msg[0] == 'ERR':
                print('Username already exists. Try again.')
                username = input('Enter your username: ')
            else:
                self.username = username
                print(decod_msg[1])
                return

    def click_action(self, teste):
        print(self.username)
        print(teste)

    def close(self):
        self.socket.close()


if __name__ == '__main__':
    client = Client()
    client.start()
