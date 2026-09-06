# Quick validation test for render_animated_flow_graph logic
import html

def calculate_network_flow(disrupted_node="Shanghai Port", severity_pct=75):
    # Root Port capacities
    cap_busan = max(0, 100 - severity_pct) if disrupted_node == "Busan Port" else 100
    cap_shanghai = max(0, 100 - severity_pct) if disrupted_node == "Shanghai Port" else 100

    flow_busan_to_supA = cap_busan
    flow_shanghai_to_supA = cap_shanghai
    flow_shanghai_to_supB = cap_shanghai

    if disrupted_node == "Tier-1 Supplier A":
        cap_supA = max(0, 100 - severity_pct)
    else:
        cap_supA = int(round(0.45 * flow_busan_to_supA + 0.55 * flow_shanghai_to_supA))

    if disrupted_node == "Tier-1 Supplier B":
        cap_supB = max(0, 100 - severity_pct)
    else:
        cap_supB = int(round(flow_shanghai_to_supB))

    flow_supA_to_mfg = cap_supA
    flow_supB_to_mfg = cap_supB

    if disrupted_node == "Tier-2 Component Mfg":
        cap_mfg = max(0, 100 - severity_pct)
    else:
        cap_mfg = int(round(0.50 * flow_supA_to_mfg + 0.50 * flow_supB_to_mfg))

    flow_mfg_to_assembly = cap_mfg

    if disrupted_node == "Assembly Hub":
        cap_assembly = max(0, 100 - severity_pct)
    else:
        cap_assembly = cap_mfg

    flow_assembly_to_dist = cap_assembly
    flow_assembly_to_retail = cap_assembly

    if disrupted_node == "Distribution Center":
        cap_dist = max(0, 100 - severity_pct)
    else:
        cap_dist = cap_assembly

    flow_dist_to_retail = cap_dist

    if disrupted_node == "OE Retailer":
        cap_retail = max(0, 100 - severity_pct)
    else:
        cap_retail = int(round(0.60 * flow_assembly_to_retail + 0.40 * flow_dist_to_retail))

    node_caps = {
        "Busan Port": cap_busan,
        "Shanghai Port": cap_shanghai,
        "Tier-1 Supplier A": cap_supA,
        "Tier-1 Supplier B": cap_supB,
        "Tier-2 Component Mfg": cap_mfg,
        "Assembly Hub": cap_assembly,
        "Distribution Center": cap_dist,
        "OE Retailer": cap_retail,
    }

    edges = [
        {"id": "e1", "src": "Busan Port", "dst": "Tier-1 Supplier A", "flow": flow_busan_to_supA,
         "path": "M 110 95 C 205 95, 205 140, 300 140", "mx": 205, "my": 105},
        {"id": "e2", "src": "Shanghai Port", "dst": "Tier-1 Supplier A", "flow": flow_shanghai_to_supA,
         "path": "M 110 345 C 205 345, 205 140, 300 140", "mx": 205, "my": 225},
        {"id": "e3", "src": "Shanghai Port", "dst": "Tier-1 Supplier B", "flow": flow_shanghai_to_supB,
         "path": "M 110 345 L 300 345", "mx": 205, "my": 345},
        {"id": "e4", "src": "Tier-1 Supplier A", "dst": "Tier-2 Component Mfg", "flow": flow_supA_to_mfg,
         "path": "M 300 140 C 405 140, 405 240, 510 240", "mx": 405, "my": 180},
        {"id": "e5", "src": "Tier-1 Supplier B", "dst": "Tier-2 Component Mfg", "flow": flow_supB_to_mfg,
         "path": "M 300 345 C 405 345, 405 240, 510 240", "mx": 405, "my": 300},
        {"id": "e6", "src": "Tier-2 Component Mfg", "dst": "Assembly Hub", "flow": flow_mfg_to_assembly,
         "path": "M 510 240 L 690 240", "mx": 600, "my": 240},
        {"id": "e7", "src": "Assembly Hub", "dst": "Distribution Center", "flow": flow_assembly_to_dist,
         "path": "M 690 240 C 765 240, 765 110, 840 110", "mx": 765, "my": 165},
        {"id": "e8", "src": "Assembly Hub", "dst": "OE Retailer", "flow": flow_assembly_to_retail,
         "path": "M 690 240 C 765 240, 765 345, 840 345", "mx": 765, "my": 300},
        {"id": "e9", "src": "Distribution Center", "dst": "OE Retailer", "flow": flow_dist_to_retail,
         "path": "M 840 110 L 840 345", "mx": 840, "my": 228},
    ]

    throughput = cap_retail
    return node_caps, edges, throughput

if __name__ == "__main__":
    for test_node in ["Shanghai Port", "Busan Port", "Tier-2 Component Mfg"]:
        nc, ed, tp = calculate_network_flow(test_node, 80)
        print(f"=== Disrupted: {test_node} (80% shock) ===")
        print(f"  Overall System Throughput: {tp}%")
        for e in ed:
            status = "BLOCKED" if e["flow"] <= 20 else ("THROTTLED" if e["flow"] < 80 else "ACTIVE")
            print(f"    {e['src']} -> {e['dst']}: Flow={e['flow']}% ({status})")
