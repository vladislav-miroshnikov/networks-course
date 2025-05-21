import tkinter as tk
from tkinter import messagebox
import socket
import struct
import time
import threading


class TCPServerApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Получатель TCP")
        tk.Label(self.window, text="Введите IP").pack()
        self.ip_entry = tk.Entry(self.window)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack()
        tk.Label(self.window, text="Введите порт для получения").pack()
        self.port_entry = tk.Entry(self.window)
        self.port_entry.insert(0, "8080")
        self.port_entry.pack()
        tk.Label(self.window, text="Скорость передачи").pack()
        self.speed_label = tk.Label(self.window, text="0 B/s")
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
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((ip, port))
                s.listen()
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(4)
                    N = struct.unpack('>I', data)[0]
                    start_time = time.time()
                    total_bytes = 0
                    for _ in range(N):
                        packet = conn.recv(1024)
                        if not packet:
                            break
                        total_bytes += len(packet)
                    end_time = time.time()
                    time_elapsed = end_time - start_time
                    speed = total_bytes / time_elapsed if time_elapsed > 0 else 0
                    self.update_results(f"{speed:.2f} B/s", f"{N} of {N}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            self.receive_button.config(state="normal")

    def update_results(self, speed, packets):
        self.speed_label.config(text=speed)
        self.packets_label.config(text=packets)


if __name__ == "__main__":
    TCPServerApp()
