import socket
import argparse


def check_free_ports(ip_address, start_port, end_port):
    free_ports = []
    for port in range(start_port, end_port + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.bind((ip_address, port))
            free_ports.append(port)
        except socket.error:
            pass
        finally:
            sock.close()
    return free_ports


def main():
    parser = argparse.ArgumentParser(description="Check free ports for an IP address")
    parser.add_argument("ip_address", type=str, help="IP address to check")
    parser.add_argument("start_port", type=int, help="Start of port range")
    parser.add_argument("end_port", type=int, help="End of port range")
    args = parser.parse_args()
    if not (0 <= args.start_port <= 65535 and 0 <= args.end_port <= 65535):
        print("Error: Ports must be in the range 0 to 65535")
        return
    if args.start_port > args.end_port:
        print("Error: Start port must be less than or equal to end port")
        return
    try:
        socket.inet_aton(args.ip_address)
    except socket.error:
        print("Error: Invalid IP address format")
        return
    print(f"Checking free ports for {args.ip_address} in range {args.start_port}-{args.end_port}...")
    free_ports = check_free_ports(args.ip_address, args.start_port, args.end_port)
    if free_ports:
        print("Free ports:")
        for port in free_ports:
            print(f"Port {port}")
        print(f"Total free ports: {len(free_ports)}")
    else:
        print("No free ports found in the specified range.")


if __name__ == "__main__":
    main()
