import socket
import app

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('25.102.60.208', 1234)
print('Conectando ao servidor {} na porta {}'.format(server_address[0], server_address[1]))
sock.connect(server_address)
app.run()