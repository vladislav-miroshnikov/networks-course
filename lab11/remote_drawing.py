import pygame
import socket
import threading
import sys
import asyncio
import platform

HOST = '127.0.0.1'
PORT = 5000
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BUFFER_SIZE = 1024


def start_server():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Сервер: Удаленное рисование")
    clock = pygame.time.Clock()
    drawing_sessions = []
    current_session = []
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"Сервер запущен на {HOST}:{PORT}, ожидание клиента...")
    client_socket, addr = server_socket.accept()
    print(f"Подключен клиент: {addr}")

    def receive_points():
        nonlocal current_session
        while True:
            try:
                data = client_socket.recv(BUFFER_SIZE).decode('utf-8')
                if not data:
                    break
                if data == "NEW":
                    if current_session:
                        drawing_sessions.append(current_session)
                    current_session = []
                else:
                    x, y = map(int, data.split(','))
                    current_session.append((x, y))
            except:
                break
        if current_session:
            drawing_sessions.append(current_session)
        client_socket.close()

    threading.Thread(target=receive_points, daemon=True).start()

    async def main():
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            screen.fill((255, 255, 255))
            for session in drawing_sessions:
                for i in range(1, len(session)):
                    pygame.draw.line(screen, (0, 0, 0), session[i - 1], session[i], 2)
            for i in range(1, len(current_session)):
                pygame.draw.line(screen, (0, 0, 0), current_session[i - 1], current_session[i], 2)
            pygame.display.flip()
            clock.tick(FPS)
            await asyncio.sleep(1.0 / FPS)
        pygame.quit()
        client_socket.close()
        server_socket.close()

    if platform.system() == "Emscripten":
        asyncio.ensure_future(main())
    else:
        asyncio.run(main())


def start_client():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Клиент: Удаленное рисование")
    clock = pygame.time.Clock()
    drawing_sessions = []
    current_session = []
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT))
        print(f"Подключено к серверу {HOST}:{PORT}")
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        pygame.quit()
        return

    async def main():
        nonlocal drawing_sessions, current_session
        running = True
        drawing = False
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # ЛКМ
                        drawing = True
                        if current_session:
                            drawing_sessions.append(current_session)
                        current_session = []
                        try:
                            client_socket.send("NEW".encode('utf-8'))
                        except:
                            running = False
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        drawing = False
                        if current_session:
                            drawing_sessions.append(current_session)
                        current_session = []
            if drawing:
                x, y = pygame.mouse.get_pos()
                current_session.append((x, y))
                try:
                    client_socket.send(f"{x},{y}".encode('utf-8'))
                except:
                    running = False

            screen.fill((255, 255, 255))
            for session in drawing_sessions:
                for i in range(1, len(session)):
                    pygame.draw.line(screen, (0, 0, 0), session[i - 1], session[i], 2)
            for i in range(1, len(current_session)):
                pygame.draw.line(screen, (0, 0, 0), current_session[i - 1], current_session[i], 2)
            pygame.display.flip()
            clock.tick(FPS)
            await asyncio.sleep(1.0 / FPS)
        pygame.quit()
        client_socket.close()

    if platform.system() == "Emscripten":
        asyncio.ensure_future(main())
    else:
        asyncio.run(main())


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ['server', 'client']:
        print("Использование: python remote_drawing.py [server|client]")
        sys.exit(1)

    if sys.argv[1] == 'server':
        start_server()
    else:
        start_client()
