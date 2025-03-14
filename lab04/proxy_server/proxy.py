import socket
import threading
import logging

logging.basicConfig(filename='proxy.log', level=logging.INFO, format='%(asctime)s %(message)s')


def handle_client(client_socket):
    try:
        request = client_socket.recv(4096)
        if not request:
            return

        request_str = request.decode('utf-8', errors='ignore')
        headers = request_str.split('\r\n')
        first_line = headers[0].split()
        method = first_line[0]
        url = first_line[1]

        if url.startswith('/'):
            url_parts = url.lstrip('/').split('/', 1)
            host = url_parts[0]
            path = '/' + url_parts[1] if len(url_parts) > 1 else '/'
        else:
            if '://' in url:
                url = url.split('://')[1]
            host_path = url.split('/', 1)
            host = host_path[0]
            path = '/' + host_path[1] if len(host_path) > 1 else '/'

        if ':' in host:
            host, port = host.split(':', 1)
            port = int(port)
        else:
            port = 80

        target_request = f"{method} {path} HTTP/1.1\r\nHost: {host}\r\n"
        for header in headers[1:]:
            if header.startswith('Host:'):
                continue
            target_request += header + '\r\n'

        if method == 'POST':
            body_start = request.find(b'\r\n\r\n') + 4
            body = request[body_start:]
            target_request = target_request.encode('utf-8') + body
        else:
            target_request += '\r\n'
            target_request = target_request.encode('utf-8')

        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.connect((host, port))
        target_socket.sendall(target_request)

        response = b''
        while True:
            data = target_socket.recv(4096)
            if not data:
                break
            response += data

            if b'\r\n\r\n' in response:
                headers_end = response.index(b'\r\n\r\n') + 4
                headers_str = response[:headers_end].decode('utf-8', errors='ignore')
                if 'Content-Length' in headers_str:
                    content_length = int(
                        [h.split(': ')[1] for h in headers_str.split('\r\n') if h.startswith('Content-Length:')][0])
                    if len(response) >= headers_end + content_length:
                        break
                elif 'Transfer-Encoding: chunked' in headers_str:
                    break
        client_socket.sendall(response)
        status_code = response.split(b'\r\n')[0].split(b' ')[1].decode('utf-8')
        logging.info(f"URL: {url}, Status: {status_code}")
    except Exception as e:
        logging.error(f"Error: {e}")
        client_socket.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
    finally:
        client_socket.close()
        if 'target_socket' in locals():
            target_socket.close()


def start_proxy(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', port))
    server.listen(5)
    print(f"Proxy server has been started on port {port}")

    while True:
        client_socket, addr = server.accept()
        threading.Thread(target=handle_client, args=(client_socket,)).start()


if __name__ == "__main__":
    start_proxy(8888)
