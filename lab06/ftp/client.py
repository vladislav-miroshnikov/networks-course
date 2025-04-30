import socket


def connect_to_server(host, port=21):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print(sock.recv(1024).decode())
    return sock


def authenticate(sock, username, password):
    sock.sendall(f"USER {username}\r\n".encode())
    response = sock.recv(1024).decode()
    if not response.startswith("331"):
        raise Exception(f"Ошибка USER: {response}")

    sock.sendall(f"PASS {password}\r\n".encode())
    response = sock.recv(1024).decode()
    if not response.startswith("230"):
        raise Exception(f"Ошибка PASS: {response}")
    print("Аутентификация успешна")


def enter_passive_mode(sock):
    sock.sendall(b"PASV\r\n")
    response = sock.recv(1024).decode()
    if not response.startswith("227"):
        raise Exception(f"Ошибка PASV: {response}")

    start = response.find('(') + 1
    end = response.find(')')
    parts = response[start:end].split(',')
    ip = '.'.join(parts[:4])
    port = int(parts[4]) * 256 + int(parts[5])
    return ip, port


def list_files(sock):
    ip, port = enter_passive_mode(sock)
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.connect((ip, port))

    sock.sendall(b"LIST\r\n")
    response = sock.recv(1024).decode()
    if not response.startswith("150"):
        raise Exception(f"Ошибка LIST: {response}")

    file_list = ""
    while True:
        data = data_sock.recv(1024).decode()
        if not data:
            break
        file_list += data

    data_sock.close()
    response = sock.recv(1024).decode()
    if not response.startswith("226"):
        raise Exception(f"Ошибка завершения LIST: {response}")

    return file_list


def upload_file(sock, local_file, remote_file):
    ip, port = enter_passive_mode(sock)
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.connect((ip, port))

    sock.sendall(f"STOR {remote_file}\r\n".encode())
    response = sock.recv(1024).decode()
    if not response.startswith("150"):
        raise Exception(f"Ошибка STOR: {response}")

    with open(local_file, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            data_sock.sendall(data)

    data_sock.close()
    response = sock.recv(1024).decode()
    if not response.startswith("226"):
        raise Exception(f"Ошибка завершения STOR: {response}")


def download_file(sock, remote_file, local_file):
    ip, port = enter_passive_mode(sock)
    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.connect((ip, port))

    sock.sendall(f"RETR {remote_file}\r\n".encode())
    response = sock.recv(1024).decode()
    if not response.startswith("150"):
        raise Exception(f"Ошибка RETR: {response}")

    with open(local_file, 'wb') as f:
        while True:
            data = data_sock.recv(1024)
            if not data:
                break
            f.write(data)

    data_sock.close()
    response = sock.recv(1024).decode()
    if not response.startswith("226"):
        raise Exception(f"Ошибка завершения RETR: {response}")


def main():
    host = input("Введите хост FTP-сервера (например, ftp.dlptest.com): ")
    username = input("Введите имя пользователя: ")
    password = input("Введите пароль: ")

    sock = connect_to_server(host)
    try:
        authenticate(sock, username, password)
        while True:
            command = input("\nВведите команду (list, upload, download, quit): ").strip().lower()
            if command == "list":
                try:
                    files = list_files(sock)
                    print("Список файлов и директорий:\n", files)
                except Exception as e:
                    print(f"Ошибка: {e}")

            elif command == "upload":
                local_file = input("Введите путь к локальному файлу: ")
                remote_file = input("Введите имя файла на сервере: ")
                try:
                    upload_file(sock, local_file, remote_file)
                    print(f"Файл {remote_file} успешно загружен на сервер")
                except Exception as e:
                    print(f"Ошибка: {e}")

            elif command == "download":
                remote_file = input("Введите имя файла на сервере: ")
                local_file = input("Введите путь для сохранения файла локально: ")
                try:
                    download_file(sock, remote_file, local_file)
                    print(f"Файл {remote_file} успешно скачан как {local_file}")
                except Exception as e:
                    print(f"Ошибка: {e}")

            elif command == "quit":
                sock.sendall(b"QUIT\r\n")
                print(sock.recv(1024).decode())
                break

            else:
                print("Неизвестная команда. Доступные команды: list, upload, download, quit")

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        sock.close()
        print("Соединение закрыто")


if __name__ == "__main__":
    main()
