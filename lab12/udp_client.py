import tkinter as tk
from tkinter import messagebox
import socket
import struct
import os
import threading


class UDPClientApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Отправитель UDP")
        tk.Label(self.window, text="Введите IP адрес получателя").pack()
        self.ip_entry = tk.Entry(self.window)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack()
        tk.Label(self.window, text="Введите порт получателя").pack()
        self.port_entry = tk.Entry(self.window)
        self.port_entry.insert(0, "8888")
        self.port_entry.pack()
        tk.Label(self.window, text="Введите число пакетов для отправки").pack()
        self.packets_entry = tk.Entry(self.window)
        self.packets_entry.insert(0, "5")
        self.packets_entry.pack()
        self.send_button = tk.Button(self.window, text="Отправить", command=self.start_send)
        self.send_button.pack()
        self.window.mainloop()

    def start_send(self):
        self.send_button.config(state="disabled")
        thread = threading.Thread(target=self.send)
        thread.start()

    def send(self):
        ip = self.ip_entry.get()
        port = int(self.port_entry.get())
        N = int(self.packets_entry.get())
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(struct.pack('>I', N), (ip, port))
                for i in range(N):
                    seq = struct.pack('>I', i)
                    data = os.urandom(1020)
                    packet = seq + data
                    s.sendto(packet, (ip, port))
            messagebox.showinfo("Успех", "Пакеты успешно отправлены!")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            self.send_button.config(state="normal")


if __name__ == "__main__":
    UDPClientApp()
