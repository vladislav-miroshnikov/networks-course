import socket
import time


def udp_heartbeat_server(host='0.0.0.0', port=13000, timeout_threshold=5):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    server_socket.settimeout(1)
    print(f"UDP Heartbeat Server запущен на {host}:{port}")
    clients = {}
    while True:
        try:
            message, client_address = server_socket.recvfrom(1024)
            message_decoded = message.decode()
            print(f"Получено от {client_address}: {message_decoded}")
            clients[client_address] = time.time()
        except socket.timeout:
            pass
        current_time = time.time()
        for client, last_time in list(clients.items()):
            if current_time - last_time > timeout_threshold:
                print(f"Потеря heartbeat от клиента {client}. Последнее сообщение: {time.ctime(last_time)}")
                del clients[client]


if __name__ == '__main__':
    udp_heartbeat_server()
