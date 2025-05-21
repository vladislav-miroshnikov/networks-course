import tkinter as tk
from tkinter import messagebox
import socket
import struct
import time
import threading


class UDPServerApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Получатель UDP")
        tk.Label(self.window, text="Введите IP").pack()
        self.ip_entry = tk.Entry(self.window)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack()
        tk.Label(self.window, text="Введите порт для получения").pack()
        self.port_entry = tk.Entry(self.window)
        self.port_entry.insert(0, "8888")
        self.port_entry.pack()
        tk.Label(self.window, text="Скорость соединения").pack()
        self.speed_label = tk.Label(self.window, text="0 KB/s")
        self.speed_label.pack()
        tk.Label(self.window, text="Число полученных пакетов").pack()
        self.packets_label = tk.Label(self.window, text="0 of 0")
        self.packets_label.pack()
        self.receive_button = tk.Button(self.window, text="Получить", command=self.start_receive)
        self.receive_button.pack()
        self.window.mainloop()

    def start_receive(self):
        self.receive_button.config(state="disabled")
        thread = threading.Thread(target=self.receive)
        thread.start()

    def receive(self):
        ip = self.ip_entry.get()
        port = int(self.port_entry.get())
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.bind((ip, port))
                s.settimeout(2)
                data, _ = s.recvfrom(4)
                N = struct.unpack('>I', data)[0]
                received = set()
                start_time = None
                while True:
                    try:
                        packet, _ = s.recvfrom(1024)
                        if start_time is None:
                            start_time = time.time()
                        seq = struct.unpack('>I', packet[:4])[0]
                        received.add(seq)
                    except socket.timeout:
                        break
                end_time = time.time()
                time_elapsed = end_time - start_time if start_time else 0
                total_bytes = len(received) * 1020
                speed = (total_bytes / time_elapsed) / 1000 if time_elapsed > 0 else 0
                packets_received = len(received)
                self.update_results(f"{speed:.2f} KB/s", f"{packets_received} of {N}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            self.receive_button.config(state="normal")

    def update_results(self, speed, packets):
        self.speed_label.config(text=speed)
        self.packets_label.config(text=packets)


if __name__ == "__main__":
    UDPServerApp()
