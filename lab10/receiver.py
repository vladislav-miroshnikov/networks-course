import socket

SEQ_NUM_RANGE = 16


def print_receiver_state(expected_seq_num):
    state = [str(i) if i == expected_seq_num else f"({i})" for i in range(SEQ_NUM_RANGE)]
    print("Receiver window state:", " ".join(state))


def main():
    server_addr = ('localhost', 12345)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(server_addr)
    expected_seq_num = 0
    while True:
        data, addr = sock.recvfrom(1024)
        seq_num, packet_data = data.decode().split('|', 1)
        seq_num = int(seq_num)
        print_receiver_state(expected_seq_num)
        if seq_num == expected_seq_num:
            print(f"Received frame {seq_num} Same as Rn, send ACK{seq_num + 1}")
            sock.sendto(str(seq_num).encode(), addr)
            expected_seq_num = (expected_seq_num + 1) % SEQ_NUM_RANGE
        else:
            print(f"Received packet out of order {seq_num}, expected {expected_seq_num}")
            sock.sendto(str(expected_seq_num - 1).encode(), addr)


if __name__ == '__main__':
    main()
