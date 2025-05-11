import socket
import struct
import time
import sys

ICMP_ECHO_REQUEST = 8
ICMP_TIME_EXCEEDED = 11
ICMP_ECHO_REPLY = 0
MAX_HOPS = 30
TIMEOUT = 2.0
TRIES = 3


def checksum(data):
    sum = 0
    for i in range(0, len(data) - 1, 2):
        sum += (data[i] << 8) + data[i + 1]
    if len(data) % 2:
        sum += data[-1] << 8
    sum = (sum >> 16) + (sum & 0xffff)
    sum += (sum >> 16)
    return ~sum & 0xffff


def build_icmp_packet():
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, 0, 1, 1)
    data = b''
    my_checksum = checksum(header + data)
    header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), 1, 1)
    return header + data


def get_host_name(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return None


def traceroute(dest_addr, max_hops=MAX_HOPS, tries=TRIES, timeout=TIMEOUT):
    try:
        dest_ip = socket.gethostbyname(dest_addr)
    except socket.gaierror:
        print(f"Не удалось разрешить адрес {dest_addr}")
        return
    print(f"Трассировка маршрута к {dest_addr} [{dest_ip}] с максимальным количеством прыжков {max_hops}:")
    for ttl in range(1, max_hops + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
            sock.settimeout(timeout)
            rtt_list = []
            router_ip = None
            reached_destination = False
            for _ in range(tries):
                packet = build_icmp_packet()
                start_time = time.time()
                sock.sendto(packet, (dest_ip, 0))

                try:
                    data, addr = sock.recvfrom(1024)
                    end_time = time.time()
                    rtt = (end_time - start_time) * 1000
                    rtt_list.append(rtt)

                    icmp_type, = struct.unpack('b', data[20:21])
                    router_ip = addr[0]
                    if icmp_type == ICMP_ECHO_REPLY:
                        reached_destination = True
                        break
                    elif icmp_type == ICMP_TIME_EXCEEDED:
                        break
                except socket.timeout:
                    rtt_list.append(None)
            if all(rtt is None for rtt in rtt_list):
                print(f"{ttl:<3}  * * *")
                continue
            host_name = get_host_name(router_ip) if router_ip else None
            rtt_str = '  '.join(f'{rtt:.3f} ms' if rtt is not None else '*' for rtt in rtt_list)
            if host_name:
                print(f"{ttl:<3}  {router_ip} ({host_name})  {rtt_str}")
            else:
                print(f"{ttl:<3}  {router_ip or '*'}  {rtt_str}")
            if reached_destination:
                break


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python traceroute.py <хост>")
        sys.exit(1)
    traceroute(sys.argv[1])
