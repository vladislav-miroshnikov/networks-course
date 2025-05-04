import socket
import random


def udp_echo_server(host='0.0.0.0', port=12000):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print(f"UDP Echo Server запущен на {host}:{port}")
    while True:
        message, client_address = server_socket.recvfrom(1024)
        print(f"Получено сообщение от {client_address}")
        if random.random() < 0.2:
            print("Симуляция потери пакета. Пакет проигнорирован.")
            continue
        modified_message = message.decode().upper()
        server_socket.sendto(modified_message.encode(), client_address)
        print(f"Ответ отправлен клиенту {client_address}")


if __name__ == '__main__':
    udp_echo_server()
