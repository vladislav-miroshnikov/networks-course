import socket
import threading
import logging
import os
import json
import hashlib

logging.basicConfig(filename='proxy.log', level=logging.INFO, format='%(asctime)s %(message)s')

cache_dir = 'cache'
metadata_file = 'cache_metadata.json'
blacklist_file = 'blacklist.txt'
lock = threading.Lock()
cache_metadata = {}
blacklist = set()


def load_blacklist():
    global blacklist
    try:
        with open(blacklist_file, 'r') as f:
            blacklist = set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        logging.warning(f"Blacklist file {blacklist_file} not found. No domains will be blocked.")


def save_cache_metadata():
    with open(metadata_file, 'w') as f:
        json.dump(cache_metadata, f)


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

        if host in blacklist or url in blacklist:
            logging.info(f"Blocked request to {url}")
            client_socket.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\nAccess to this page is blocked.")
            client_socket.close()
            return

        if ':' in host:
            host, port = host.split(':', 1)
            port = int(port)
        else:
            port = 80

        if method == 'GET':
            hash_url = hashlib.md5(url.encode()).hexdigest()
            with lock:
                if url in cache_metadata:
                    meta = cache_metadata[url]
                    if meta.get('last_modified') or meta.get('etag'):
                        target_request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\n"
                        if meta.get('last_modified'):
                            target_request += f"If-Modified-Since: {meta['last_modified']}\r\n"
                        if meta.get('etag'):
                            target_request += f"If-None-Match: {meta['etag']}\r\n"
                        for header in headers[1:]:
                            if not header.startswith('Host:'):
                                target_request += header + '\r\n'
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

                        status_line = response.split(b'\r\n', 1)[0]
                        status_code = status_line.split(b' ')[1]
                        if status_code == b'304':
                            with open(os.path.join(cache_dir, hash_url), 'rb') as f:
                                cached_response = f.read()
                            client_socket.sendall(cached_response)
                            logging.info(f"URL: {url}, Status: 304, Served from cache")
                            target_socket.close()
                            client_socket.close()
                            return
                        else:
                            headers_end = response.index(b'\r\n\r\n') + 4
                            headers_str = response[:headers_end].decode('utf-8', errors='ignore')
                            headers_list = headers_str.split('\r\n')
                            last_modified = None
                            etag = None
                            for header in headers_list[1:]:
                                if header.lower().startswith('last-modified:'):
                                    last_modified = header.split(': ', 1)[1]
                                elif header.lower().startswith('etag:'):
                                    etag = header.split(': ', 1)[1]
                            with open(os.path.join(cache_dir, hash_url), 'wb') as f:
                                f.write(response)
                            cache_metadata[url] = {'file': hash_url, 'last_modified': last_modified, 'etag': etag}
                            save_cache_metadata()
                            client_socket.sendall(response)
                            logging.info(f"URL: {url}, Status: {status_code.decode('utf-8')}, Updated cache")
                            target_socket.close()
                            client_socket.close()
                            return

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

        if method == 'GET':
            hash_url = hashlib.md5(url.encode()).hexdigest()
            headers_end = response.index(b'\r\n\r\n') + 4
            headers_str = response[:headers_end].decode('utf-8', errors='ignore')
            headers_list = headers_str.split('\r\n')
            last_modified = None
            etag = None
            for header in headers_list[1:]:
                if header.lower().startswith('last-modified:'):
                    last_modified = header.split(': ', 1)[1]
                elif header.lower().startswith('etag:'):
                    etag = header.split(': ', 1)[1]
            with open(os.path.join(cache_dir, hash_url), 'wb') as f:
                f.write(response)
            with lock:
                cache_metadata[url] = {'file': hash_url, 'last_modified': last_modified, 'etag': etag}
                save_cache_metadata()
            status_code = response.split(b'\r\n')[0].split(b' ')[1].decode('utf-8')
            logging.info(f"URL: {url}, Status: {status_code}, Cached and served")
        else:
            status_code = response.split(b'\r\n')[0].split(b' ')[1].decode('utf-8')
            logging.info(f"URL: {url}, Status: {status_code}, Served without caching")

        client_socket.sendall(response)
    except Exception as e:
        logging.error(f"Error: {e}")
        client_socket.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
    finally:
        client_socket.close()
        if 'target_socket' in locals():
            target_socket.close()


def start_proxy(port):
    global cache_metadata
    load_blacklist()
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    try:
        with open(metadata_file, 'r') as f:
            cache_metadata = json.load(f)
    except FileNotFoundError:
        cache_metadata = {}

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', port))
    server.listen(5)
    print(f"Proxy server has been started on port {port}")

    while True:
        client_socket, addr = server.accept()
        threading.Thread(target=handle_client, args=(client_socket,)).start()


if __name__ == "__main__":
    start_proxy(8888)
