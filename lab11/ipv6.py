import socket
import sys
import threading

HOST = '::1'
PORT = 5000
BUFFER_SIZE = 1024


def start_server():
    try:
        server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT, 0, 0))
        server_socket.listen(5)
        print(f"Сервер запущен на {HOST}:{PORT}")
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Подключен клиент: {addr}")
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.start()
    except Exception as e:
        print(f"Ошибка сервера: {e}")
    finally:
        server_socket.close()


def handle_client(client_socket, addr):
    try:
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
            message = data.decode('utf-8')
            print(f"Получено от {addr}: {message}")
            response = message.upper()
            client_socket.send(response.encode('utf-8'))
            print(f"Отправлено клиенту {addr}: {response}")
    except Exception as e:
        print(f"Ошибка при обработке клиента {addr}: {e}")
    finally:
        client_socket.close()
        print(f"Клиент {addr} отключен")


def start_client():
    try:
        client_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT, 0, 0))
        print(f"Подключено к серверу {HOST}:{PORT}")

        while True:
            message = input("Введите сообщение (или 'exit' для выхода): ")
            if message.lower() == 'exit':
                break
            client_socket.send(message.encode('utf-8'))
            response = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            print(f"Ответ от сервера: {response}")
    except Exception as e:
        print(f"Ошибка клиента: {e}")
    finally:
        client_socket.close()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print("Использование: python ipv6_echo_app.py [server|client]")
        sys.exit(1)

    if sys.argv[1] == 'server':
        start_server()
    else:
        start_client()
