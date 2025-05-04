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
            print(f"Ответ: {response.decode()}   RTT = {rtt:.4f} сек")
        except socket.timeout:
            print("Request timed out")
    received = len(rtts)
    packet_loss = (num_packets - received) / num_packets * 100
    if rtts:
        min_rtt = min(rtts)
        max_rtt = max(rtts)
        avg_rtt = sum(rtts) / len(rtts)
    else:
        min_rtt = max_rtt = avg_rtt = 0.0

    print("\n--- Ping statistics ---")
    print(f"{num_packets} packets transmitted, {received} packets received, {packet_loss:.2f}% packet loss")
    print(f"RTT min/avg/max = {min_rtt:.4f}/{avg_rtt:.4f}/{max_rtt:.4f} sec")

    client_socket.close()


if __name__ == '__main__':
    udp_echo_client()
