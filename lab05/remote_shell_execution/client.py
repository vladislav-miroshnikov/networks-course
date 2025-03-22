import platform
import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 9999))
command = input("Enter command to execute remote on server: ")
client_socket.send(command.encode('utf-8'))

result = b""
while True:
    part = client_socket.recv(1024)
    if not part:
        break
    result += part

if platform.system() == "Windows":
    encoding = 'cp866'
else:
    encoding = 'utf-8'

decoded_result = result.decode(encoding)
print("Result of command execution:")
print(decoded_result)
client_socket.close()
