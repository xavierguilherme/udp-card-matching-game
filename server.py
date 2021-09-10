import socket
import app

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('25.102.60.208', 1234)
socket.bind(server_address)
socket.listen(1)

while True:
    connection, client_address = socket.accept()
    try:
        print('Alguém entrou')
    finally:
        connection.close()