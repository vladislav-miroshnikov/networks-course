import socket
import zlib
import random
import threading


def make_ack_packet(seq):
    return b'A' + bytes([seq])


def make_data_packet(seq, is_last, data):
    checksum = zlib.crc32(data)
    packet = b'D' + bytes([seq]) + bytes([is_last]) + checksum.to_bytes(4, 'big') + data
    return packet


# We send a file from server to client in sedner thread
def sender(sock, client_address, filename='file_to_send_from_server'):
    with open(filename, 'rb') as f:
        data = f.read()
    chunk_size = 1000
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    seq = 0

    for i, chunk in enumerate(chunks):
        is_last = 1 if i == len(chunks) - 1 else 0
        packet = make_data_packet(seq, is_last, chunk)
        while True:
            if random.random() > 0.3:  # imitate 70% chance to send (30% loss)
                sock.sendto(packet, client_address)
                print(f"Server sent packet {seq}")
            else:
                print(f"Server packet {seq} lost")
            try:
                ack, addr = sock.recvfrom(2048)
                if len(ack) >= 2 and ack[0:1] == b'A' and ack[1] == seq:
                    print(f"Server received ACK {seq}")
                    break
                else:
                    print("Server received invalid ACK")
            except socket.timeout:
                print(f"Server timeout for packet {seq}")
            except ConnectionResetError:
                print(f"Server: Client disconnected, stopping sender thread")
                return
        seq = 1 - seq
    print("Server finished sending file")


def receiver(sock):
    with open('received_from_client', 'wb') as f:
        expected_seq = 0
        while True:
            try:
                packet, addr = sock.recvfrom(2048)
                if len(packet) < 7:
                    continue
                packet_type = packet[0:1]
                if packet_type == b'D':
                    seq = packet[1]
                    is_last = packet[2]
                    checksum = int.from_bytes(packet[3:7], 'big')
                    data = packet[7:]
                    print(f"Server received packet with seq {seq}")
                    if zlib.crc32(data) == checksum:
                        if seq == expected_seq:
                            f.write(data)
                            print(f"Server accepted packet {seq}")
                            ack_packet = make_ack_packet(seq)
                            if random.random() > 0.3:
                                sock.sendto(ack_packet, addr)
                                print(f"Server sent ACK {seq}")
                            else:
                                print(f"Server ACK {seq} lost")
                            if is_last:
                                break
                            expected_seq = 1 - expected_seq
                        else:
                            print(f"Server got duplicate packet {seq}")
                            ack_packet = make_ack_packet(1 - expected_seq)
                            if random.random() > 0.3:
                                sock.sendto(ack_packet, addr)
                                print(f"Server sent ACK {1 - expected_seq}")
                            else:
                                print(f"Server ACK {1 - expected_seq} lost")
                    else:
                        print(f"Server checksum failed for packet {seq}")
            except socket.timeout:
                continue


def main():
    server_address = ('localhost', 12345)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)
    sock.bind(server_address)
    print("Server started")

    while True:
        try:
            packet, client_address = sock.recvfrom(2048)
            if packet[0:1] == b'D':
                break
        except socket.timeout:
            continue

    send_thread = threading.Thread(target=sender, args=(sock, client_address))
    recv_thread = threading.Thread(target=receiver, args=(sock,))

    send_thread.start()
    recv_thread.start()

    send_thread.join()
    recv_thread.join()

    print("Server finished")


if __name__ == "__main__":
    main()
