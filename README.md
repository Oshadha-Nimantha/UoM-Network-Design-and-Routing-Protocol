# UoM Network Design & Routing Protocol Suite

This repository contains two major networking projects from the Department of Electronic & Telecommunication Engineering at the University of Moratuwa:
1.  **Design of a Local Area Network (LAN)** for the entire University of Moratuwa (UoM) campus.
2.  **Design of a Novel Routing Protocol (OSDRP)**, a secure and dynamic link-state protocol.

These projects were developed by the "Network Surgeons" team for the EN2150 Communication Network Engineering course.

![University of Moratuwa Logo](img/uom_logo.png)

---

## 1. Design of Local Area Network (LAN)

This project outlines the design and simulation of a robust and scalable backbone network for the University of Moratuwa, as well as a detailed network design for the Electronics and Telecommunication (ENTC) building.

### Key Features
-   **Hierarchical Hybrid Topology**: A three-layer design (Core, Distribution, Access) combining star and mesh configurations for scalability and fault tolerance.
-   **Redundancy**: Dual exit routers and multiple interconnected core switches to ensure high availability and load balancing.
-   **Scalable IP Addressing**: Utilizes /23 subnets for major building nodes, providing ample IP space for up to 500 devices per VLAN with room for expansion.
-   **VLAN Segmentation**: Traffic is segregated by department and user type (student, staff, management) to enhance security and network efficiency.
-   **High-Speed Backbone**: A fiber optic backbone using Single-Mode Fiber (SMF) connects all major university buildings to the central CITES data center.
-   **Cost-Effective Design**: Justification for all active (switches, routers) and passive (cabling, patch panels) components is provided, balancing performance with budget.


### Simulation Files
The Cisco Packet Tracer simulation files for this design can be found in the `cisco_packet_tracer/` directory:
-   `UOM Network.pkt`: The main campus backbone simulation.
-   `ENTC Network.pkt`: The detailed network for the ENTC building.

---

## 2. Routing Protocol Design (OSDRP)

This project introduces the **OSD-Routing Protocol (OSDRP)**, a modern link-state protocol designed to overcome the limitations of existing standards like RIP and OSPF.

### Key Features
-   **Dynamic Composite Metric**: Calculates link cost using a weighted sum of real-time latency and available bandwidth, leading to more intelligent path selection.
-   **Enhanced Security**: All Link State Update (LSU) messages are digitally signed to prevent spoofing and unauthorized updates. Rate-limiting and sequence numbers protect against DoS attacks and replays.
-   **Fast Reroute**: Pre-calculates a link-disjoint backup path, allowing for instantaneous failover in the event of a primary link failure without waiting for network-wide reconvergence.
-   **Proven with Simulation**: The protocol was designed, simulated, and analyzed using Python and the NetworkX library, demonstrating its superior performance over static-metric protocols.

### Python Simulation
The Python scripts for the OSDRP simulation and its comparison with OSPF are located in the `src/python/` directory:
-   `osdrp_simulation.py`: The core implementation and simulation of the OSDRP protocol.
-   `performance_comparison.py`: A simplified OSPF-like protocol for performance comparison.

To run the simulation, you will need Python and the `networkx` library:
```bash
pip install networkx matplotlib
python src/python/osdrp_simulation.py
