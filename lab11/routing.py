import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - Node %(node_id)s - %(message)s')


class Node:
    def __init__(self, node_id, neighbors, initial_costs):
        self.node_id = node_id
        self.neighbors = neighbors
        self.routing_table = {node_id: (0, node_id)}
        for neighbor, cost in initial_costs.items():
            self.routing_table[neighbor] = (cost, neighbor)
        self.logger = logging.getLogger(__name__)
        self.logger = logging.LoggerAdapter(self.logger, {'node_id': self.node_id})
        # self.logger.debug(f"Инициализация узла: routing_table={self.routing_table}")

    def send_vector(self):
        vector = {dest: cost for dest, (cost, _) in self.routing_table.items()}
        # self.logger.debug(f"Вектор для отправки: vector={vector}")
        return vector

    def process_vector(self, sender_id, vector, sender_cost):
        # self.logger.debug(f"Получен вектор от узла {sender_id}: vector={vector}")
        updated = False
        for dest, cost in vector.items():
            if cost == float('inf'):
                continue
            total_cost = cost + sender_cost
            if dest not in self.routing_table or self.routing_table[dest][0] > total_cost:
                self.routing_table[dest] = (total_cost, sender_id)
                updated = True
                # self.logger.debug(f"Обновлен маршрут до {dest}: cost={total_cost}, next_hop={sender_id}")
        if updated:
            ...
            # self.logger.debug(f"Таблица маршрутизации обновлена: routing_table={self.routing_table}")
        return updated

    def update_cost(self, neighbor_id, new_cost):
        if neighbor_id in self.routing_table:
            old_cost = self.routing_table[neighbor_id][0]
            self.routing_table[neighbor_id] = (new_cost, neighbor_id)
            # self.logger.debug(
            #     f"Обновлена стоимость до узла {neighbor_id}: new_cost={new_cost}, routing_table={self.routing_table}")
            return old_cost != new_cost
        return False


def run_routing(nodes, max_iterations=10):
    for iteration in range(max_iterations):
        updated = False
        for node_id, node in nodes.items():
            vector = node.send_vector()
            for neighbor in node.neighbors:
                sender_cost = node.routing_table[neighbor.node_id][0]
                if neighbor.process_vector(node_id, vector, sender_cost):
                    updated = True
        if not updated:
            print(f"Таблицы маршрутизации стабилизировались на итерации {iteration + 1}")
            break
    else:
        print("Максимальное количество итераций достигнуто")


def print_routing_tables(nodes):
    for node_id, node in nodes.items():
        print(f"\nТаблица маршрутизации узла {node_id}:")
        for dest, (cost, next_hop) in node.routing_table.items():
            print(f"  До {dest}: стоимость {cost}, следующий узел {next_hop}")


# Инициализация сети
nodes = {
    0: Node(0, [], {}),
    1: Node(1, [], {}),
    2: Node(2, [], {}),
    3: Node(3, [], {})
}

neighbors = {
    0: [1, 3],
    1: [0, 2, 3],
    2: [1, 3],
    3: [0, 1, 2]
}

initial_costs = {
    0: {1: 1, 3: 7},
    1: {0: 1, 2: 1, 3: 3},
    2: {1: 1, 3: 2},
    3: {0: 7, 1: 3, 2: 2}
}

for node_id, node in nodes.items():
    node.neighbors = [nodes[neighbor_id] for neighbor_id in neighbors[node_id]]
    node.routing_table.update({neighbor_id: (cost, neighbor_id)
                               for neighbor_id, cost in initial_costs[node_id].items()})

print("Запускаем начальный обмен векторами...")
run_routing(nodes)
print("\nНачальные таблицы маршрутизации:")
print_routing_tables(nodes)
print("\nИзменим стоимость канала между узлами 0 и 3 с 7 до 10...")
initial_costs[0][3] = 10
initial_costs[3][0] = 10
nodes[0].update_cost(3, 10)
nodes[3].update_cost(0, 10)
print("\nЗапускаем обмен векторами после изменения стоимости...")
run_routing(nodes)
print("\nТаблицы маршрутизации после изменения стоимости:")
print_routing_tables(nodes)
