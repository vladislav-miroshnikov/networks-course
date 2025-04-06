import socket
import os
import threading


class FTPSession:
    def __init__(self, root_dir):
        self.root_dir = os.path.abspath(root_dir)
        self.authenticated = False
        self.username_input = None
        self.current_dir = "/"
        self.data_host = None
        self.data_port = None
        self.data_sock = None

    def resolve_path(self, path):
        if os.path.isabs(path):
            new_path = os.path.join(self.root_dir, path.lstrip("/"))
        else:
            new_path = os.path.join(self.root_dir, self.current_dir.lstrip("/"), path)
        norm_path = os.path.abspath(new_path)
        if os.path.commonpath([norm_path, self.root_dir]) != self.root_dir:
            return None
        return norm_path


class FTPServer:
    def __init__(self, host="127.0.0.1", port=21, root_dir="."):
        self.host = host
        self.port = port
        self.root_dir = root_dir

    def start(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((self.host, self.port))
        server_sock.listen(5)
        print(f"FTP is launched on {self.host}:{self.port}")
        try:
            while True:
                client_sock, addr = server_sock.accept()
                print(f"Connection from {addr}")
                threading.Thread(target=self.handle_client, args=(client_sock,), daemon=True).start()
        except KeyboardInterrupt:
            print("Stopping server...")
        finally:
            server_sock.close()

    def handle_client(self, client_sock):
        session = FTPSession(self.root_dir)
        try:
            client_sock.sendall("220 Welcome to the FTP server\r\n".encode('utf-8'))
            while True:
                data = client_sock.recv(1024)
                if not data:
                    break
                command_line = data.decode().strip()
                if not command_line:
                    continue
                print(f"Command received: {command_line}")
                parts = command_line.split()
                cmd = parts[0].upper()
                args = parts[1:]
                if cmd == "USER":
                    self.handle_user(client_sock, session, args)
                elif cmd == "PASS":
                    self.handle_pass(client_sock, session, args)
                elif cmd == "CWD":
                    self.handle_cwd(client_sock, session, args)
                elif cmd in ("PWD", "XPWD"):
                    self.handle_pwd(client_sock, session)
                elif cmd == "PORT":
                    self.handle_port(client_sock, session, args)
                elif cmd == "NLST":
                    self.handle_nlst(client_sock, session)
                elif cmd == "RETR":
                    self.handle_retr(client_sock, session, args)
                elif cmd == "STOR":
                    self.handle_stor(client_sock, session, args)
                elif cmd == "QUIT":
                    self.handle_quit(client_sock)
                    break
                elif cmd == "OPTS":
                    client_sock.sendall("200 OPTS received\r\n".encode('utf-8'))
                else:
                    client_sock.sendall("500 Unknown command\r\n".encode('utf-8'))
        except Exception as e:
            print(f"Failed processing command: {e}")
        finally:
            try:
                client_sock.close()
            except Exception:
                pass

    def handle_user(self, sock, session, args):
        if len(args) != 1:
            sock.sendall("501 Syntax error in parameters\r\n".encode('utf-8'))
            return
        session.username_input = args[0]
        sock.sendall("331 Please specify the password\r\n".encode('utf-8'))

    def handle_pass(self, sock, session, args):
        if len(args) != 1:
            sock.sendall("501 Syntax error in parameters\r\n".encode('utf-8'))
            return
        if session.username_input == "Test_User" and args[0] == "123456":
            session.authenticated = True
            sock.sendall("230 Login successful\r\n".encode('utf-8'))
        else:
            sock.sendall("530 Invalid username or password\r\n".encode('utf-8'))

    def handle_cwd(self, sock, session, args):
        if not session.authenticated:
            sock.sendall("530 Not logged in\r\n".encode('utf-8'))
            return
        if len(args) != 1:
            sock.sendall("501 Syntax error in parameters\r\n".encode('utf-8'))
            return
        requested_path = args[0]
        new_abs_path = session.resolve_path(requested_path)
        if new_abs_path is None or not os.path.isdir(new_abs_path):
            sock.sendall("550 Failed to change directory\r\n".encode('utf-8'))
            return
        session.current_dir = os.path.relpath(new_abs_path, session.root_dir).replace("\\", "/")
        if session.current_dir == ".":
            session.current_dir = "/"
        else:
            session.current_dir = "/" + session.current_dir
        sock.sendall("250 Directory successfully changed\r\n".encode('utf-8'))

    def handle_pwd(self, sock, session):
        if not session.authenticated:
            sock.sendall("530 Not logged in\r\n".encode('utf-8'))
            return
        sock.sendall(f"257 \"{session.current_dir}\"\r\n".encode('utf-8'))

    def handle_port(self, sock, session, args):
        if not session.authenticated:
            sock.sendall("530 Not logged in\r\n".encode('utf-8'))
            return
        if len(args) != 1:
            sock.sendall("501 Syntax error in parameters\r\n".encode('utf-8'))
            return
        parts = args[0].split(",")
        if len(parts) != 6:
            sock.sendall("501 Syntax error in parameters\r\n".encode('utf-8'))
            return
        session.data_host = ".".join(parts[:4])
        try:
            session.data_port = int(parts[4]) * 256 + int(parts[5])
        except ValueError:
            sock.sendall("501 Syntax error in parameters\r\n".encode('utf-8'))
            return
        sock.sendall("200 PORT command successful\r\n".encode('utf-8'))

    def handle_nlst(self, sock, session):
        if not session.authenticated:
            sock.sendall("530 Not logged in\r\n".encode('utf-8'))
            return
        if not session.data_host or not session.data_port:
            sock.sendall("425 Use PORT or PASV first\r\n".encode('utf-8'))
            return
        sock.sendall("150 Starting directory listing transfer\r\n".encode('utf-8'))
        try:
            session.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            session.data_sock.connect((session.data_host, session.data_port))
            dir_path = session.resolve_path(session.current_dir)
            if dir_path is None or not os.path.isdir(dir_path):
                sock.sendall("550 Directory not found\r\n".encode('utf-8'))
                return
            files = os.listdir(dir_path)
            for file in files:
                session.data_sock.sendall(f"{file}\r\n".encode('utf-8'))
            sock.sendall("226 Directory listing transfer completed\r\n".encode('utf-8'))
        except Exception as e:
            print(f"NLST error: {e}")
            sock.sendall("426 Connection closed; transfer aborted\r\n".encode('utf-8'))
        finally:
            if session.data_sock:
                session.data_sock.close()
                session.data_sock = None

    def handle_retr(self, sock, session, args):
        if not session.authenticated:
            sock.sendall("530 Not logged in\r\n".encode('utf-8'))
            return
        if len(args) != 1:
            sock.sendall("501 Syntax error in parameters\r\n".encode('utf-8'))
            return
        file_name = args[0]
        file_path = session.resolve_path(os.path.join(session.current_dir, file_name))
        if file_path is None or not os.path.isfile(file_path):
            sock.sendall("550 File not found\r\n".encode('utf-8'))
            return
        sock.sendall("150 Opening data connection for transfer\r\n".encode('utf-8'))
        try:
            session.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            session.data_sock.connect((session.data_host, session.data_port))
            with open(file_path, "rb") as f:
                while (data := f.read(1024)):
                    session.data_sock.sendall(data)
            sock.sendall("226 Transfer completed\r\n".encode('utf-8'))
        except Exception as e:
            print(f"RETR error: {e}")
            sock.sendall("426 Connection closed; transfer aborted\r\n".encode('utf-8'))
        finally:
            if session.data_sock:
                session.data_sock.close()
                session.data_sock = None

    def handle_stor(self, sock, session, args):
        if not session.authenticated:
            sock.sendall("530 Not logged in\r\n".encode('utf-8'))
            return
        if len(args) != 1:
            sock.sendall("501 Syntax error in parameters\r\n".encode('utf-8'))
            return
        file_name = args[0]
        file_path = session.resolve_path(os.path.join(session.current_dir, file_name))
        if file_path is None:
            sock.sendall("550 Cannot create file\r\n".encode('utf-8'))
            return
        sock.sendall("150 Opening data connection for transfer\r\n".encode('utf-8'))
        try:
            session.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            session.data_sock.connect((session.data_host, session.data_port))
            with open(file_path, "wb") as f:
                while (data := session.data_sock.recv(1024)):
                    f.write(data)
            sock.sendall("226 Transfer completed\r\n".encode('utf-8'))
        except Exception as e:
            print(f"STOR error: {e}")
            sock.sendall("426 Connection closed; transfer aborted\r\n".encode('utf-8'))
        finally:
            if session.data_sock:
                session.data_sock.close()
                session.data_sock = None

    def handle_quit(self, sock):
        sock.sendall("221 Goodbye\r\n".encode('utf-8'))


if __name__ == "__main__":
    server = FTPServer(root_dir=".")
    server.start()
