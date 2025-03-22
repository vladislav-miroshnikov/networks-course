import socket
import time
from datetime import datetime

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
broadcast_address = ('255.255.255.255', 9999)
print("Server is launched and sending time...")
while True:
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"Current time: {current_time}".encode('utf-8')
    server_socket.sendto(message, broadcast_address)
    print(f"Sent: {current_time}")
    time.sleep(1)
