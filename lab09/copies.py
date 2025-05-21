import socket
import threading
import time
import select
import queue
import tkinter as tk
from tkinter import ttk

BROADCAST_PORT = 5000
INTERVAL = 2.0
TIMEOUT = 3 * INTERVAL


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('255.255.255.255', BROADCAST_PORT))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def network_thread(q, shutdown_event):
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    broadcast_socket.bind(('', BROADCAST_PORT))

    unicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    unicast_socket.bind(('', 0))
    unicast_port = unicast_socket.getsockname()[1]
    unicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    local_ip = get_local_ip()
    my_addr = (local_ip, unicast_port)
    running_instances = {}
    next_here_time = time.time() + INTERVAL
    next_check_time = time.time() + 1.0

    unicast_socket.sendto("START".encode('utf-8'), ('<broadcast>', BROADCAST_PORT))
    while not shutdown_event.is_set():
        readable, _, _ = select.select([broadcast_socket, unicast_socket], [], [], 0.1)
        current_time = time.time()
        for sock in readable:
            data, (sender_ip, sender_port) = sock.recvfrom(1024)
            message = data.decode('utf-8')
            sender_addr = (sender_ip, sender_port)
            if sock == broadcast_socket:
                if message == "START":
                    unicast_socket.sendto("RUNNING".encode('utf-8'), sender_addr)
                    running_instances[sender_addr] = current_time
                elif message == "HERE":
                    running_instances[sender_addr] = current_time
            elif sock == unicast_socket:
                if message == "RUNNING":
                    running_instances[sender_addr] = current_time
                elif message == "SHUTDOWN":
                    running_instances.pop(sender_addr, None)
        if current_time >= next_here_time:
            unicast_socket.sendto("HERE".encode('utf-8'), ('<broadcast>', BROADCAST_PORT))
            next_here_time = current_time + INTERVAL
        if current_time >= next_check_time:
            to_remove = [addr for addr, last_seen in running_instances.items()
                         if current_time - last_seen > TIMEOUT]
            for addr in to_remove:
                running_instances.pop(addr, None)
            next_check_time = current_time + 1.0
        if running_instances:
            q.put(list(running_instances.keys()))
        if shutdown_event.is_set():
            for addr in running_instances:
                if addr != my_addr:
                    unicast_socket.sendto("SHUTDOWN".encode('utf-8'), addr)
            break
    broadcast_socket.close()
    unicast_socket.close()


def update_gui(q, root, count_label, listbox):
    try:
        while not q.empty():
            instances = q.get_nowait()
            listbox.delete(0, tk.END)
            for ip, port in sorted(instances):
                listbox.insert(tk.END, f"{ip}:{port}")
            count_label.config(text=str(len(instances)))
    except queue.Empty:
        pass
    root.after(100, update_gui, q, root, count_label, listbox)


def on_closing(root, shutdown_event, net_thread):
    shutdown_event.set()
    net_thread.join()
    root.destroy()


def main():
    root = tk.Tk()
    root.title("Анализ копий приложения")
    root.geometry("300x400")
    tk.Label(root, text="Количество запущено:").pack(pady=5)
    count_label = tk.Label(root, text="0")
    count_label.pack()
    tk.Label(root, text="Ожидание, мс:").pack(pady=5)
    tk.Label(root, text="2000").pack()
    listbox = tk.Listbox(root, font="Courier", height=15)
    listbox.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
    close_button = ttk.Button(root, text="Закрыть", command=lambda: on_closing(root, shutdown_event, net_thread))
    close_button.pack(pady=10)
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, shutdown_event, net_thread))

    q = queue.Queue()
    shutdown_event = threading.Event()
    net_thread = threading.Thread(target=network_thread, args=(q, shutdown_event))
    net_thread.start()

    root.after(100, update_gui, q, root, count_label, listbox)
    root.mainloop()


if __name__ == "__main__":
    main()
