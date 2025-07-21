import networkx as nx
import matplotlib.pyplot as plt
import random
import time
import json


def visualize_network(graph, paths=None, title="Network Topology"):
    """Visualizes the network graph with optional paths highlighted."""
    pos = nx.spring_layout(graph, seed=42)
    plt.figure(figsize=(12, 8))
    nx.draw_networkx_nodes(graph, pos, node_size=700, node_color='skyblue')
    nx.draw_networkx_labels(graph, pos, font_size=10, font_family='sans-serif')
    edge_labels = nx.get_edge_attributes(graph, 'cost')
    nx.draw_networkx_edges(graph, pos, width=1.5, alpha=0.5, edge_color='gray')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)
    if paths:
        for path_edges in paths:
            nx.draw_networkx_edges(graph, pos, edgelist=path_edges, width=2.5, edge_color='red')
    plt.title(title)
    plt.axis('off')
    plt.show()

def load_config(filepath):
    """Loads configuration data from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

# Load configuration and topology from JSON
config = load_config('config.json')
topology_data = load_config('topology.json')

# Assign config values
PUBLIC_KEYS = config['public_keys']
METRIC_WEIGHTS = config['metric_weights']

# Build network topology
G = nx.Graph()
G.add_nodes_from(topology_data['nodes'])

for edge in topology_data['edges']:
    G.add_edge(edge['source'], edge['target'],
               base_latency=edge['base_latency'],
               bandwidth=edge['bandwidth'])

# Signature Simulation
def sign_message(message, source_id):
    return hash(str(message) + PUBLIC_KEYS[source_id])

def verify_signature(message, signature, source_id):
    return signature == sign_message(message, source_id)



class Router:
    def __init__(self, router_id, graph):
        self.id = router_id
        self.graph = graph
        self.topology = nx.Graph()
        self.sequence_number = 0
        self.routing_table = {}
        self.w1 = METRIC_WEIGHTS['w1_latency']
        self.w2 = METRIC_WEIGHTS['w2_bandwidth']
        self.lsu_timestamps = []
        self.lsu_rate_limit = 10 
        self.lsu_window = 1

    def calculate_link_cost(self, neighbor_id):
        link_data = self.graph.edges[self.id, neighbor_id]
        latency = link_data['base_latency'] + random.uniform(-2, 2)
        normalized_latency = latency / 50
        normalized_bandwidth = link_data['bandwidth'] / 200
        cost = self.w1 * normalized_latency + self.w2 * (1 / (normalized_bandwidth + 0.01))
        return round(cost, 2)

    def create_lsu(self):
        self.sequence_number += 1
        links_data = {}
        for neighbor in self.graph.neighbors(self.id):
            cost = self.calculate_link_cost(neighbor)
            links_data[neighbor] = {'cost': cost}
        lsu_data = {
            "source_id": self.id,
            "sequence_number": self.sequence_number,
            "links": links_data
        }
        signature = sign_message(lsu_data, self.id)
        return {"data": lsu_data, "signature": signature}

    def process_lsu(self, lsu):
        current_time = time.time()
        self.lsu_timestamps = [t for t in self.lsu_timestamps if current_time - t <= self.lsu_window]
        if len(self.lsu_timestamps) >= self.lsu_rate_limit:
            print(f"{self.id}: Rate limit exceeded. LSU from {lsu['data']['source_id']} ignored.")
            return False

        data = lsu['data']
        source_id = data['source_id']
        if not verify_signature(data, lsu['signature'], source_id):
            print(f"{self.id}: Discarded LSU from {source_id}. Invalid signature.")
            return False
        if source_id in self.topology and self.topology.nodes[source_id].get('seq', 0) >= data['sequence_number']:
            return False

        self.lsu_timestamps.append(current_time)
        self.topology.add_node(source_id, seq=data['sequence_number'])

        old_edges = list(self.topology.edges(source_id))
        self.topology.remove_edges_from(old_edges)
        for neighbor, props in data['links'].items():
            self.topology.add_edge(source_id, neighbor, cost=props['cost'])

        print(f"{self.id}: Processed new LSU from {source_id} (Seq: {data['sequence_number']}).")
        return True

    def calculate_routes(self):
        if self.id not in self.topology:
            return
        self.routing_table = {}
        for target_node in self.topology.nodes:
            if target_node == self.id:
                continue
            try:
                primary_path = nx.dijkstra_path(self.topology, self.id, target_node, weight='cost')
                primary_cost = nx.dijkstra_path_length(self.topology, self.id, target_node, weight='cost')

                topology_copy = self.topology.copy()
                path_edges = list(zip(primary_path, primary_path[1:]))
                topology_copy.remove_edges_from(path_edges)

                try:
                    backup_path = nx.dijkstra_path(topology_copy, self.id, target_node, weight='cost')
                    backup_cost = nx.dijkstra_path_length(topology_copy, self.id, target_node, weight='cost')
                except nx.NetworkXNoPath:
                    backup_path = None
                    backup_cost = None

                self.routing_table[target_node] = {
                    "next_hop": primary_path[1],
                    "total_cost": round(primary_cost, 2),
                    "path": primary_path,
                    "backup_path": backup_path,
                    "backup_cost": round(backup_cost, 2) if backup_cost else None
                }
            except nx.NetworkXNoPath:
                pass
        print(f"--- {self.id} updated its routing table with backup paths. ---")


def break_n_random_links(graph, n):
    edges = list(graph.edges())
    if n > len(edges):
        n = len(edges)
    links_to_remove = random.sample(edges, n)
    for edge in links_to_remove:
        graph.remove_edge(*edge)
    print(f"Random links broken: {links_to_remove}")
    return links_to_remove




# Simulation

def run_simulation():
    routers = {node_id: Router(node_id, G) for node_id in G.nodes()}

    print("--- Initial Network Convergence ---")
    for _ in range(len(routers)):
        for router_id, router in routers.items():
            lsu = router.create_lsu()
            for neighbor_router in routers.values():
                if neighbor_router.id != router_id:
                    if neighbor_router.process_lsu(lsu):
                        neighbor_router.calculate_routes()

    for router in routers.values():
        router.calculate_routes()

    print("\n--- Initial Routing Table for R0 ---")
    print(routers['R0'].routing_table)
    all_paths = []
    for dest, route_info in routers['R0'].routing_table.items():
        if 'path' in route_info and route_info['path']:
            path = route_info['path']
            path_edges = list(zip(path, path[1:]))
            all_paths.append(path_edges)

    visualize_network(routers['R0'].topology, all_paths, title="R0's View: All Routes (Initial)")


    print("\n" + "="*50)
    print("!!! SIMULATING LINK FAILURE !!!")
    print("="*50 + "\n")

    failed_links = break_n_random_links(G, 2) # No of Breaking Link
    failed_originators = [u for u, v in failed_links] + [v for u, v in failed_links]


    start_time = time.time()
    for _ in range(2):
        for router_id in failed_originators:
            router = routers[router_id]
            lsu = router.create_lsu()
            print(f"\n{router_id} creates new LSU due to failure.")
            for other_router in routers.values():
                if other_router.id != router_id:
                    if other_router.process_lsu(lsu):
                        other_router.calculate_routes()

    convergence_time = time.time() - start_time
    print(f"\nNetwork re-converged in ~{convergence_time:.4f} seconds.")
    print("\n--- Final Routing Table for R0 ---")
    print(routers['R0'].routing_table)
    all_paths_after_failure = []
    for dest, route_info in routers['R0'].routing_table.items():
        if 'path' in route_info and route_info['path']:
            path = route_info['path']
            path_edges = list(zip(path, path[1:]))
            all_paths_after_failure.append(path_edges)

    visualize_network(routers['R0'].topology, all_paths_after_failure, title="R0's View: All Routes After Failure")

if __name__ == "__main__":
    run_simulation()
