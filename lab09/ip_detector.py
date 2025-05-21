import netifaces


def get_network_info():
    interfaces = netifaces.interfaces()
    found = False
    for iface in interfaces:
        # Skip loopback interface
        if iface == 'lo' or iface.startswith('lo'):
            continue
        iface_details = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in iface_details:
            for addr_info in iface_details[netifaces.AF_INET]:
                ip_address = addr_info.get('addr')
                netmask = addr_info.get('netmask')
                # ignore loopback IP (127.0.0.1)
                if ip_address and netmask and ip_address != '127.0.0.1':
                    print(f"Interface: {iface}")
                    print(f"IP-addr: {ip_address}")
                    print(f"Subnet mask: {netmask}")
                    print("-" * 30)
                    found = True
    if not found:
        print("No active network interfaces with an IPv4 address other than loopback were found.")


if __name__ == "__main__":
    try:
        get_network_info()
    except Exception as e:
        print(f"Error when receiving network information: {e}")
