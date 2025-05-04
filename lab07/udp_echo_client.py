import socket
import time


def udp_echo_client(server_ip='127.0.0.1', server_port=12000):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(1)
    num_packets = 10
    rtts = []
    for seq in range(1, num_packets + 1):
        send_time = time.time()
        message = f"Ping {seq} {send_time}"
        try:
            client_socket.sendto(message.encode(), (server_ip, server_port))
            print(f"Отправлено: {message}")
            response, _ = client_socket.recvfrom(1024)
            rtt = time.time() - send_time
            rtts.append(rtt)
            print(f"Получено: {response.decode()} | RTT: {rtt:.4f} сек")
        except socket.timeout:
            print("Request timed out")
    client_socket.close()


if __name__ == '__main__':
    udp_echo_client()
