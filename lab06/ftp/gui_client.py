import tkinter as tk
from tkinter import messagebox, Toplevel, Text
import socket


class FTPClient:
    def __init__(self, host, port=21):
        self.host = host
        self.port = port
        self.sock = None
        self.data_sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        response = self.sock.recv(1024).decode()
        if not response.startswith("220"):
            raise Exception(f"Connection failed: {response}")
        return response

    def authenticate(self, username, password):
        self.sock.sendall(f"USER {username}\r\n".encode())
        response = self.sock.recv(1024).decode()
        if not response.startswith("331"):
            raise Exception(f"USER error: {response}")
        self.sock.sendall(f"PASS {password}\r\n".encode())
        response = self.sock.recv(1024).decode()
        if not response.startswith("230"):
            raise Exception(f"PASS error: {response}")
        return response

    def enter_passive_mode(self):
        self.sock.sendall(b"PASV\r\n")
        response = self.sock.recv(1024).decode()
        if not response.startswith("227"):
            raise Exception(f"PASV error: {response}")
        start = response.find('(') + 1
        end = response.find(')')
        parts = response[start:end].split(',')
        ip = '.'.join(parts[:4])
        port = int(parts[4]) * 256 + int(parts[5])
        return ip, port

    def list_files(self):
        ip, port = self.enter_passive_mode()
        self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_sock.connect((ip, port))
        self.sock.sendall(b"LIST\r\n")
        response = self.sock.recv(1024).decode()
        if not response.startswith("150"):
            raise Exception(f"LIST error: {response}")
        file_list = ""
        while True:
            data = self.data_sock.recv(1024).decode()
            if not data:
                break
            file_list += data
        self.data_sock.close()
        self.data_sock = None
        response = self.sock.recv(1024).decode()
        if not response.startswith("226"):
            raise Exception(f"LIST completion error: {response}")
        return file_list

    def retrieve_file(self, remote_file):
        ip, port = self.enter_passive_mode()
        self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_sock.connect((ip, port))
        self.sock.sendall(f"RETR {remote_file}\r\n".encode())
        response = self.sock.recv(1024).decode()
        if not response.startswith("150"):
            raise Exception(f"RETR error: {response}")
        file_content = b""
        while True:
            data = self.data_sock.recv(1024)
            if not data:
                break
            file_content += data
        self.data_sock.close()
        self.data_sock = None
        response = self.sock.recv(1024).decode()
        if not response.startswith("226"):
            raise Exception(f"RETR completion error: {response}")
        return file_content.decode()

    def store_file(self, remote_file, content):
        ip, port = self.enter_passive_mode()
        self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_sock.connect((ip, port))
        self.sock.sendall(f"STOR {remote_file}\r\n".encode())
        response = self.sock.recv(1024).decode()
        if not response.startswith("150"):
            raise Exception(f"STOR error: {response}")
        self.data_sock.sendall(content.encode())
        self.data_sock.close()
        self.data_sock = None
        response = self.sock.recv(1024).decode()
        if not response.startswith("226"):
            raise Exception(f"STOR completion error: {response}")

    def delete_file(self, remote_file):
        self.sock.sendall(f"DELE {remote_file}\r\n".encode())
        response = self.sock.recv(1024).decode()
        if not response.startswith("250"):
            raise Exception(f"DELE error: {response}")
        return response

    def quit(self):
        self.sock.sendall(b"QUIT\r\n")
        response = self.sock.recv(1024).decode()
        self.sock.close()
        return response


class FTPClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("FTP Client")
        self.ftp_client = None
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.master, text="Server (host:port):").grid(row=0, column=0, sticky="e")
        self.server_entry = tk.Entry(self.master, width=30)
        self.server_entry.grid(row=0, column=1)
        tk.Label(self.master, text="Username:").grid(row=1, column=0, sticky="e")
        self.username_entry = tk.Entry(self.master, width=30)
        self.username_entry.grid(row=1, column=1)
        tk.Label(self.master, text="Password:").grid(row=2, column=0, sticky="e")
        self.password_entry = tk.Entry(self.master, width=30, show="*")
        self.password_entry.grid(row=2, column=1)
        tk.Button(self.master, text="Connect", command=self.connect_to_server).grid(row=3, column=1, sticky="e")
        self.display_text = Text(self.master, height=20, width=60, state=tk.DISABLED)
        self.display_text.grid(row=4, column=0, columnspan=2, padx=10, pady=10)
        tk.Label(self.master, text="File Name:").grid(row=5, column=0, sticky="e")
        self.file_name_entry = tk.Entry(self.master, width=30)
        self.file_name_entry.grid(row=5, column=1)
        tk.Button(self.master, text="Create", command=self.create_file).grid(row=6, column=0, sticky="e")
        tk.Button(self.master, text="Retrieve", command=self.retrieve_file).grid(row=6, column=1, sticky="w")
        tk.Button(self.master, text="Update", command=self.update_file).grid(row=7, column=0, sticky="e")
        tk.Button(self.master, text="Delete", command=self.delete_file).grid(row=7, column=1, sticky="w")

    def connect_to_server(self):
        server = self.server_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        try:
            host, port = server.split(":")
            port = int(port)
            self.ftp_client = FTPClient(host, port)
            self.ftp_client.connect()
            self.ftp_client.authenticate(username, password)
            messagebox.showinfo("Success", "Connected to FTP server")
            file_list = self.ftp_client.list_files()
            self.display_text.config(state=tk.NORMAL)
            self.display_text.delete(1.0, tk.END)
            self.display_text.insert(tk.END, file_list)
            self.display_text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def create_file(self):
        file_name = self.file_name_entry.get()
        if not file_name:
            messagebox.showerror("Error", "Please enter a file name")
            return
        edit_window = Toplevel(self.master)
        edit_window.title(f"Create File: {file_name}")
        text_area = Text(edit_window, height=20, width=60)
        text_area.pack(padx=10, pady=10)
        tk.Button(edit_window, text="Save",
                  command=lambda: self.save_new_file(file_name, text_area.get(1.0, tk.END), edit_window)).pack(pady=10)

    def save_new_file(self, file_name, content, window):
        try:
            self.ftp_client.store_file(file_name, content)
            messagebox.showinfo("Success", f"File {file_name} created successfully")
            window.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def retrieve_file(self):
        file_name = self.file_name_entry.get()
        if not file_name:
            messagebox.showerror("Error", "Please enter a file name")
            return
        try:
            content = self.ftp_client.retrieve_file(file_name)
            self.display_text.config(state=tk.NORMAL)
            self.display_text.delete(1.0, tk.END)
            self.display_text.insert(tk.END, content)
            self.display_text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_file(self):
        file_name = self.file_name_entry.get()
        if not file_name:
            messagebox.showerror("Error", "Please enter a file name")
            return
        try:
            content = self.ftp_client.retrieve_file(file_name)
            edit_window = Toplevel(self.master)
            edit_window.title(f"Update File: {file_name}")
            text_area = Text(edit_window, height=20, width=60)
            text_area.insert(tk.END, content)
            text_area.pack(padx=10, pady=10)
            tk.Button(edit_window, text="Save",
                      command=lambda: self.save_updated_file(file_name, text_area.get(1.0, tk.END), edit_window)).pack(
                pady=10)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def save_updated_file(self, file_name, content, window):
        try:
            self.ftp_client.store_file(file_name, content)
            messagebox.showinfo("Success", f"File {file_name} updated successfully")
            window.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_file(self):
        file_name = self.file_name_entry.get()
        if not file_name:
            messagebox.showerror("Error", "Please enter a file name")
            return
        try:
            self.ftp_client.delete_file(file_name)
            messagebox.showinfo("Success", f"File {file_name} deleted successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = FTPClientGUI(root)
    root.mainloop()
