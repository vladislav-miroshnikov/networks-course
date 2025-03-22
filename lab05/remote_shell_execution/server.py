import socket
import subprocess

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 9999))
server_socket.listen(1)
print("Server is launched on port 9999.")

while True:
    client_socket, addr = server_socket.accept()
    print(f"Accepted connection from: {addr}")
    command = client_socket.recv(1024).decode('utf-8')
    print(f"Received command from client: {command}")
    result = subprocess.run(command, shell=True, capture_output=True)
    if result.returncode == 0:
        response = result.stdout if result.stdout else b"Command executed successfully without stdout."
    else:
        response = result.stderr if result.stderr else b"Error during command execution."
    client_socket.send(response)
    client_socket.close()
