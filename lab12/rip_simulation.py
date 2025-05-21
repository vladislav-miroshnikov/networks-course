import random
import threading
import socket
import time
import json


def transmit_to_adjacent(adj_address, adj_port, table_data):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            sock.connect((adj_address, adj_port))
            sock.sendall(json.dumps(table_data).encode())
    except Exception:
        pass


class NetworkNode(threading.Thread):
    def __init__(self, node_id, address, port_number, adjacent_nodes, topology):
        super().__init__()
        self.node_id = node_id
        self.address = address
        self.port_number = port_number
        self.adjacent_nodes = adjacent_nodes
        self.topology = topology
        self.path_table = {}
        self.incoming_messages = []
        self.sync_lock = threading.Lock()
        self.active = True
        self.table_updated = False
        self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.listener_socket.bind((self.address, self.port_number))
            self.listener_socket.listen(5)
        except Exception as e:
            print(f"[{self.node_id}] Binding failed on {self.address}:{self.port_number}: {e}")
            raise
        self.listener_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.listener_thread.start()

    def setup_initial_paths(self):
        self.path_table[self.node_id] = (self.node_id, 0)
        for adj_id, _, _ in self.adjacent_nodes:
            self.path_table[adj_id] = (adj_id, 1)

    def receive_messages(self):
        while self.active:
            try:
                connection, _ = self.listener_socket.accept()
                message = connection.recv(4096)
                if message:
                    with self.sync_lock:
                        self.incoming_messages.append(json.loads(message.decode()))
                connection.close()
            except Exception:
                if self.active:
                    continue
                break

    def broadcast_paths(self):
        for _, adj_address, adj_port in self.adjacent_nodes:
            transmit_to_adjacent(adj_address, adj_port, self.path_table)

    def update_paths(self):
        self.table_updated = False
        with self.sync_lock:
            for message in self.incoming_messages:
                for target, (next_node, hops) in message.items():
                    new_hops = hops + 1
                    if new_hops >= 16:
                        continue
                    if target not in self.path_table:
                        self.path_table[target] = (next_node, new_hops)
                        self.table_updated = True
                    elif new_hops < self.path_table[target][1]:
                        self.path_table[target] = (next_node, new_hops)
                        self.table_updated = True
            self.incoming_messages = []
        return self.table_updated

    def print_table(self, step=None):
        if step is not None:
            print(f"Simulation step {step} of router {self.node_id}")
        else:
            print(f"Final state of router {self.node_id} table:")
        print(f"[Source IP]      [Destination IP]    [Next Hop]       [Metric]")
        for dest, (nh, hops) in sorted(self.path_table.items()):
            print(f"{self.node_id:<16} {dest:<19} {nh:<19} {hops}")

    def run(self):
        while self.active:
            time.sleep(0.1)

    def shutdown(self):
        self.active = False
        self.listener_socket.close()
        self.listener_thread.join(timeout=1)


def generate_random_ip():
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"


def create_random_topology(node_count=5):
    topology = {}
    node_ids = [generate_random_ip() for _ in range(node_count)]
    addresses = ["127.0.0.1"] * node_count  # Use localhost for socket binding
    ports = random.sample(range(20000, 50000), node_count)
    for nid, addr, port in zip(node_ids, addresses, ports):
        topology[nid] = {
            "id": nid,
            "address": addr,
            "port": port,
            "adjacent": []
        }
    nodes = list(topology.values())
    for i in range(len(nodes) - 1):
        current = nodes[i]
        next_node = nodes[i + 1]
        current["adjacent"].append((next_node["id"], next_node["address"], next_node["port"]))
        next_node["adjacent"].append((current["id"], current["address"], current["port"]))

    extra_links = node_count // 2
    links_added = 0
    while links_added < extra_links:
        node_a, node_b = random.sample(nodes, 2)
        link_a = (node_b["id"], node_b["address"], node_b["port"])
        link_b = (node_a["id"], node_a["address"], node_a["port"])
        if not any(n[0] == node_b["id"] for n in node_a["adjacent"]):
            node_a["adjacent"].append(link_a)
            node_b["adjacent"].append(link_b)
            links_added += 1

    return topology


def run_simulation():
    topology = create_random_topology()
    if not topology:
        print("No nodes in topology.")
        return
    nodes = {}
    for nid, data in topology.items():
        node = NetworkNode(nid, data["address"], data["port"], data["adjacent"], topology)
        node.setup_initial_paths()
        node.start()
        nodes[nid] = node
    iteration = 0
    updates_exist = True
    try:
        while updates_exist:
            iteration += 1
            print(f"\n{'-' * 60}")
            print(f"Simulation step {iteration}")
            print(f"{'-' * 60}")
            broadcast_threads = []
            for node in nodes.values():
                t = threading.Thread(target=node.broadcast_paths)
                broadcast_threads.append(t)
                t.start()
            for t in broadcast_threads:
                t.join()
            time.sleep(0.5)
            any_updates = False
            for node in nodes.values():
                if node.update_paths():
                    any_updates = True
                node.print_table(step=iteration)
            updates_exist = any_updates
        print(f"\n{'-' * 60}")
        print("Final Routing Tables")
        print(f"{'-' * 60}")
        for nid, node in sorted(nodes.items()):
            node.print_table()
    except KeyboardInterrupt:
        print("\nTerminating simulation...")
    finally:
        for node in nodes.values():
            node.shutdown()
        for node in nodes.values():
            node.join(timeout=1)


if __name__ == "__main__":
    run_simulation()
