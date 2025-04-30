import os
import socket
from scapy.all import sr1, IP, ICMP
import time
import sys


def ping(dest_addr, count=4):
    try:
        ip = dest_addr if dest_addr.replace('.', '').isdigit() else socket.gethostbyname(dest_addr)
    except:
        print(f"Cannot resolve {dest_addr}")
        return

    print(f"Pinging {dest_addr} [{ip}] with {count} packets:")
    rtt_list = []
    lost = 0
    for seq in range(1, count + 1):
        packet = IP(dst=ip) / ICMP(type=8, id=os.getpid() & 0xFFFF, seq=seq)
        start_time = time.time()
        reply = sr1(packet, timeout=1, verbose=0)
        rtt = time.time() - start_time
        if reply:
            if reply[ICMP].type == 0:
                rtt_ms = rtt * 1000
                rtt_list.append(rtt_ms)
                print(f"Reply from {reply.src}: seq={seq} time={rtt_ms:.2f}ms")
            elif reply[ICMP].type == 3:
                code = reply[ICMP].code
                if code == 0:
                    print(f"Destination Network Unreachable for seq={seq}")
                elif code == 1:
                    print(f"Destination Host Unreachable for seq={seq}")
                else:
                    print(f"Destination Unreachable (type=3, code={code}) for seq={seq}")
                lost += 1
            else:
                print(f"Unexpected ICMP packet: type={reply[ICMP].type}, code={reply[ICMP].code}")
                lost += 1
        else:
            lost += 1
            print(f"Request timed out for seq={seq}")
        time.sleep(1)

    print(f"\nPing statistics for {dest_addr} [{ip}]:")
    print(f"    Packets: Sent = {count}, Received = {count - lost}, Lost = {lost} ({(lost / count) * 100:.2f}% loss)")
    if rtt_list:
        print(f"Approximate round trip times in milli-seconds:")
        print(
            f"    Minimum = {min(rtt_list):.2f}ms, Maximum = {max(rtt_list):.2f}ms, Average = {sum(rtt_list) / len(rtt_list):.2f}ms")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ping_scapy.py <destination>")
        sys.exit(1)
    ping(sys.argv[1])
