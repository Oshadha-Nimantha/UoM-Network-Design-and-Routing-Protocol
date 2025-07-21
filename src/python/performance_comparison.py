import time
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

# Import the necessary components from your existing OSDRP simulation
from osdrp_simulation import Router as OSDRPRouter, G as base_graph

# OSPF Simulation Class
# We'll create a simplified OSPF router for comparison.
# Its key difference is the STATIC metric calculation.

class OSPFRouter(OSDRPRouter):
    def __init__(self, router_id, graph):
        super().__init__(router_id, graph)

    def calculate_link_cost(self, neighbor_id):
        """
        Overrides the OSDRP cost calculation with a simplified, static OSPF-like metric.
        OSPF cost is typically inverse of bandwidth.
        """
        link_data = self.graph.edges[self.id, neighbor_id]
        bandwidth = link_data['bandwidth']
        
        # OSPF formula: reference_bandwidth / interface_bandwidth
        # We'll use a reference of 1000 Mbps for this simulation
        reference_bandwidth = 1000
        cost = reference_bandwidth / bandwidth
        
        # Ensure cost is at least 1
        return max(1, round(cost))

# Simulation Runner Function

def run_protocol_simulation(protocol_class, graph, failure_edge=None):
    sim_graph = graph.copy()
    
    # 1. Initial Convergence
    routers = {node_id: protocol_class(node_id, sim_graph) for node_id in sim_graph.nodes()}
    for _ in range(len(routers)):
        lsus = [router.create_lsu() for router in routers.values()]
        for router in routers.values():
            for lsu in lsus:
                if router.process_lsu(lsu):
                    router.calculate_routes()

    initial_path_cost = routers['R0'].routing_table.get('R5', {}).get('total_cost', float('inf'))

    if not failure_edge:
        return {'initial_path_cost': initial_path_cost}

    # 2. Simulate Link Failure and Measure Convergence Time
    u, v = failure_edge
    sim_graph.remove_edge(u, v)
    failed_link_originators = [u, v]
    
    start_time = time.perf_counter() # Use a high-precision counter
    
    # Re-convergence loop
    for _ in range(3): # A few rounds to ensure convergence
        lsus_from_failed = [routers[router_id].create_lsu() for router_id in failed_link_originators]
        for router in routers.values():
            topology_changed = False
            for lsu in lsus_from_failed:
                if router.process_lsu(lsu):
                    topology_changed = True
            if topology_changed:
                router.calculate_routes()

    convergence_time = (time.perf_counter() - start_time) * 1000 # in milliseconds
    
    final_path_cost = routers['R0'].routing_table.get('R5', {}).get('total_cost', float('inf'))

    return {
        'convergence_time_ms': convergence_time,
        'final_path_cost': final_path_cost,
        'initial_path_cost': initial_path_cost
    }

# Plotting Function

def plot_comparison_chart(metrics_ospf, metrics_osdrp, title, y_label):
    """Generates a bar chart comparing OSPF and SARP metrics."""
    labels = list(metrics_ospf.keys())
    ospf_values = list(metrics_ospf.values())
    osdrp_values = list(metrics_osdrp.values())
    
    x = np.arange(len(labels)) 
    width = 0.35  

    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x - width/2, ospf_values, width, label='OSPF (Static Metric)', color='royalblue')
    rects2 = ax.bar(x + width/2, osdrp_values, width, label='OSDRP (Dynamic Metric)', color='seagreen')

    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    ax.bar_label(rects1, padding=3, fmt='%.2f')
    ax.bar_label(rects2, padding=3, fmt='%.2f')

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Scenario 1: Baseline Path Quality 
    scenario1_graph = base_graph.copy()
    scenario1_graph.edges['R1', 'R2']['base_latency'] = 40 
    
    print("--- Running Scenario 1: Baseline Path Quality ---")
    results_ospf_s1 = run_protocol_simulation(OSPFRouter, scenario1_graph)
    results_sarp_s1 = run_protocol_simulation(OSDRPRouter, scenario1_graph)
    
    path_cost_metrics_ospf = {'Path Cost (R0 to R5)': results_ospf_s1['initial_path_cost']}
    path_cost_metrics_sarp = {'Path Cost (R0 to R5)': results_sarp_s1['initial_path_cost']}
    
    plot_comparison_chart(path_cost_metrics_ospf, path_cost_metrics_sarp, 
                          'Scenario 1: Path Cost Comparison (High Latency on Fastest Link)', 
                          'Total Path Cost (Lower is Better)')

    # Scenario 2: Convergence Time After Link Failure
    print("\n--- Running Scenario 2: Convergence Time ---")
    failure_link = ('R1', 'R3')
    
    runs = 5
    ospf_conv_times = []
    osdrp_conv_times = []

    for i in range(runs):
        print(f"Convergence Run {i+1}/{runs}...")
        results_ospf_s2 = run_protocol_simulation(OSPFRouter, base_graph, failure_edge=failure_link)
        results_sarp_s2 = run_protocol_simulation(OSDRPRouter, base_graph, failure_edge=failure_link)
        ospf_conv_times.append(results_ospf_s2['convergence_time_ms'])
        osdrp_conv_times.append(results_sarp_s2['convergence_time_ms'])
    
    avg_ospf_conv = np.mean(ospf_conv_times)
    avg_osdrp_conv = np.mean(osdrp_conv_times)

    convergence_metrics_ospf = {'Convergence Time': avg_ospf_conv}
    convergence_metrics_osdrp = {'Convergence Time': avg_osdrp_conv}

    plot_comparison_chart(convergence_metrics_ospf, convergence_metrics_osdrp,
                          f'Scenario 2: Average Convergence Time after Link Failure (over {runs} runs)',
                          'Time (milliseconds) (Lower is Better)')