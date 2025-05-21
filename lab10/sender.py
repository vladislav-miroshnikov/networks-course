import socket
import random

WINDOW_SIZE = 4
SEQ_NUM_RANGE = 16
TIMEOUT = 2
LOSS_PROB = 0.1


class Packet:
    def __init__(self, seq_num, data):
        self.seq_num = seq_num
        self.data = data


def simulate_network(packet):
    if random.random() < LOSS_PROB:
        print(f"Packet {packet.seq_num} lost!")
        return None
    return packet


def send_packet(sock, packet, addr):
    message = f"{packet.seq_num}|{packet.data}".encode()
    sock.sendto(message, addr)
    print(f"Send packet {packet.seq_num} successfully sent")


def receive_ack(sock, base, next_seq_num):
    try:
        ack, _ = sock.recvfrom(1024)
        ack_num = int(ack.decode())
        print(f"ACK received for packet {ack_num}")
        print_window_state(base, next_seq_num, ack_num)
        return ack_num
    except socket.timeout:
        print("Timeout, resending window")
        return None


def print_window_state(base, next_seq_num, ack_num=None):
    state = [str(i) if i >= base and i < next_seq_num else f"({i})" for i in range(SEQ_NUM_RANGE)]
    if ack_num is not None:
        state[ack_num] = f"[{ack_num}]"
    print("Sender window state:", " ".join(state))


def main():
    server_addr = ('localhost', 12345)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)
    with open('file.txt', 'r', encoding='utf-8') as f:
        data = f.read()

    packets = [Packet(i % SEQ_NUM_RANGE, data[i:i + 10]) for i in range(0, len(data), 10)]
    base = 0
    next_seq_num = 0
    while base < len(packets):
        while next_seq_num < base + WINDOW_SIZE and next_seq_num < len(packets):
            packet = packets[next_seq_num]
            if simulate_network(packet):
                send_packet(sock, packet, server_addr)
            next_seq_num += 1
            print_window_state(base, next_seq_num)

        ack_num = receive_ack(sock, base, next_seq_num)
        if ack_num is not None:
            while base <= ack_num:
                base += 1
        else:
            for i in range(base, next_seq_num):
                packet = packets[i]
                if simulate_network(packet):
                    send_packet(sock, packet, server_addr)
            print_window_state(base, next_seq_num)
    print("File transfer completed!")
    sock.close()


if __name__ == '__main__':
    main()
