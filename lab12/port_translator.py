import json
import os
import socket
import threading
import time
import tkinter as tk
from tkinter import ttk

CONFIG_FILE = 'config.json'
rules = []
active_connections = {}
listeners = {}
config_mtime = 0
is_running = False


# Функция загрузки правил из конфигурационного файла
def load_rules():
    global rules, config_mtime
    try:
        with open(CONFIG_FILE, 'r') as f:
            rules = json.load(f)
        config_mtime = os.path.getmtime(CONFIG_FILE)
    except Exception as e:
        print(f"Ошибка загрузки конфигурации: {e}")


# Функция управления слушателями портов
def manage_listeners():
    global listeners
    if is_running:
        required_ports = {rule['internal_port'] for rule in rules}
        # Закрыть слушатели для портов, которые больше не нужны
        for port in list(listeners.keys()):
            if port not in required_ports:
                listeners[port].close()
                del listeners[port]
        # Запустить слушатели для новых портов
        for rule in rules:
            port = rule['internal_port']
            if port not in listeners:
                try:
                    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    listener.bind((rule['internal_ip'], port))
                    listener.listen(5)
                    listeners[port] = listener
                    threading.Thread(target=listen_port, args=(listener, rule), daemon=True).start()
                except Exception as e:
                    print(f"Ошибка запуска слушателя на порту {port}: {e}")
    else:
        # Закрыть все слушатели, если транслятор остановлен
        for listener in listeners.values():
            listener.close()
        listeners.clear()


# Функция прослушивания порта
def listen_port(listener, rule):
    while True:
        try:
            client_socket, addr = listener.accept()
            dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dest_socket.connect((rule['external_ip'], rule['external_port']))
            active_connections[client_socket] = (rule, dest_socket)
            threading.Thread(target=forward_data, args=(client_socket, dest_socket), daemon=True).start()
            threading.Thread(target=forward_data, args=(dest_socket, client_socket), daemon=True).start()
        except Exception as e:
            print(f"Ошибка в listen_port: {e}")
            break


# Функция пересылки данных
def forward_data(src, dest):
    while True:
        try:
            data = src.recv(4096)
            if not data:
                break
            dest.sendall(data)
        except Exception as e:
            print(f"Ошибка пересылки данных: {e}")
            break
    src.close()
    dest.close()
    if src in active_connections:
        del active_connections[src]


# Функция мониторинга конфигурации
def monitor_config():
    while True:
        time.sleep(5)
        try:
            mtime = os.path.getmtime(CONFIG_FILE)
            if mtime != config_mtime:
                load_rules()
                manage_listeners()
        except Exception as e:
            print(f"Ошибка мониторинга конфигурации: {e}")


# Функция создания GUI
def create_gui():
    root = tk.Tk()
    root.title("Транслятор портов")
    tree = ttk.Treeview(root, columns=("Name", "Internal IP", "Internal Port", "External IP", "External Port"),
                        show="headings")
    tree.heading("Name", text="Название")
    tree.heading("Internal IP", text="Внутренний IP")
    tree.heading("Internal Port", text="Внутренний порт")
    tree.heading("External IP", text="Внешний IP")
    tree.heading("External Port", text="Внешний порт")
    tree.pack(fill=tk.BOTH, expand=True)

    def update_table():
        for i in tree.get_children():
            tree.delete(i)
        for rule in rules:
            tree.insert("", "end", values=(
                rule['name'], rule['internal_ip'], rule['internal_port'], rule['external_ip'], rule['external_port']))

    frame = tk.Frame(root)
    frame.pack(pady=10)
    tk.Label(frame, text="Название:").grid(row=0, column=0)
    name_entry = tk.Entry(frame)
    name_entry.grid(row=0, column=1)
    tk.Label(frame, text="Внутренний IP:").grid(row=1, column=0)
    int_ip_entry = tk.Entry(frame)
    int_ip_entry.grid(row=1, column=1)
    tk.Label(frame, text="Внутренний порт:").grid(row=2, column=0)
    int_port_entry = tk.Entry(frame)
    int_port_entry.grid(row=2, column=1)
    tk.Label(frame, text="Внешний IP:").grid(row=3, column=0)
    ext_ip_entry = tk.Entry(frame)
    ext_ip_entry.grid(row=3, column=1)
    tk.Label(frame, text="Внешний порт:").grid(row=4, column=0)
    ext_port_entry = tk.Entry(frame)
    ext_port_entry.grid(row=4, column=1)

    def add_rule():
        new_rule = {
            "name": name_entry.get(),
            "internal_ip": int_ip_entry.get(),
            "internal_port": int(int_port_entry.get()),
            "external_ip": ext_ip_entry.get(),
            "external_port": int(ext_port_entry.get())
        }
        rules.append(new_rule)
        save_config()
        manage_listeners()
        update_table()
        clear_entries()

    def remove_rule():
        selected = tree.selection()
        if selected:
            item = tree.item(selected[0])['values']
            for i, rule in enumerate(rules):
                if rule['name'] == item[0] and rule['internal_port'] == item[2]:
                    del rules[i]
                    save_config()
                    manage_listeners()
                    update_table()
                    break

    def edit_rule():
        selected = tree.selection()
        if selected:
            item = tree.item(selected[0])['values']
            name_entry.delete(0, tk.END)
            name_entry.insert(0, item[0])
            int_ip_entry.delete(0, tk.END)
            int_ip_entry.insert(0, item[1])
            int_port_entry.delete(0, tk.END)
            int_port_entry.insert(0, item[2])
            ext_ip_entry.delete(0, tk.END)
            ext_ip_entry.insert(0, item[3])
            ext_port_entry.delete(0, tk.END)
            ext_port_entry.insert(0, item[4])

    def save_config():
        with open(CONFIG_FILE, 'w') as f:
            json.dump(rules, f, indent=2)

    def clear_entries():
        name_entry.delete(0, tk.END)
        int_ip_entry.delete(0, tk.END)
        int_port_entry.delete(0, tk.END)
        ext_ip_entry.delete(0, tk.END)
        ext_port_entry.delete(0, tk.END)

    tk.Button(frame, text="Добавить", command=add_rule).grid(row=5, column=0, pady=5)
    tk.Button(frame, text="Удалить", command=remove_rule).grid(row=5, column=1, pady=5)
    tk.Button(frame, text="Редактировать", command=edit_rule).grid(row=5, column=2, pady=5)
    control_frame = tk.Frame(root)
    control_frame.pack(pady=10)
    start_button = tk.Button(control_frame, text="Запустить транслятор", command=lambda: start_translator())
    start_button.pack(side=tk.LEFT, padx=5)
    stop_button = tk.Button(control_frame, text="Остановить транслятор", command=lambda: stop_translator(),
                            state=tk.DISABLED)
    stop_button.pack(side=tk.LEFT, padx=5)

    def start_translator():
        global is_running
        is_running = True
        start_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
        manage_listeners()

    def stop_translator():
        global is_running
        is_running = False
        stop_button.config(state=tk.DISABLED)
        start_button.config(state=tk.NORMAL)
        manage_listeners()

    def periodic_update():
        update_table()
        root.after(5000, periodic_update)

    periodic_update()
    root.mainloop()


def main():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump([], f)
    load_rules()
    threading.Thread(target=monitor_config, daemon=True).start()
    create_gui()


if __name__ == "__main__":
    main()
