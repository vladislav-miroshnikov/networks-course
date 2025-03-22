import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.bind(('', 9999))
print("Client is launched and waiting for new messages...")
while True:
    data, addr = client_socket.recvfrom(1024)
    message = data.decode('utf-8')
    print(f"Received from {addr}: {message}")