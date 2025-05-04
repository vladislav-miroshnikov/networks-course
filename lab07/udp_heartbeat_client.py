import socket
import time


def udp_heartbeat_client(server_ip='127.0.0.1', server_port=13000):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sequence = 1
    try:
        while True:
            send_time = time.time()
            message = f"Heartbeat {sequence} {send_time}"
            client_socket.sendto(message.encode(), (server_ip, server_port))
            print(f"Отправлен heartbeat {sequence} в {time.ctime(send_time)}")
            sequence += 1
            time.sleep(1)
    except KeyboardInterrupt:
        print("Heartbeat клиент остановлен.")
    finally:
        client_socket.close()


if __name__ == '__main__':
    udp_heartbeat_client()
