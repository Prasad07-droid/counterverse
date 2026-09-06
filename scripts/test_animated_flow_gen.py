# Test script to generate and validate the HTML for render_animated_flow_graph
import html

def build_animated_flow_html(disrupted_node="Shanghai Port", severity_pct=75, event_type="Port closure"):
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

    nodes_info = {
        "Busan Port": {"x": 100, "y": 95, "icon": "🚢", "tier": "Port Origin (SK)"},
        "Shanghai Port": {"x": 100, "y": 345, "icon": "🚢", "tier": "Port Origin (CN)"},
        "Tier-1 Supplier A": {"x": 305, "y": 140, "icon": "🏭", "tier": "Wafer Fab (Asia)"},
        "Tier-1 Supplier B": {"x": 305, "y": 345, "icon": "🏭", "tier": "Substrate Plant (Asia)"},
        "Tier-2 Component Mfg": {"x": 510, "y": 240, "icon": "⚙️", "tier": "Microelectronics (Global)"},
        "Assembly Hub": {"x": 690, "y": 240, "icon": "🔧", "tier": "Assembly Hub (India)"},
        "Distribution Center": {"x": 845, "y": 110, "icon": "📦", "tier": "Logistics Hub (Global)"},
        "OE Retailer": {"x": 845, "y": 345, "icon": "🏪", "tier": "OEM Retail (India)"},
    }

    edges = [
        {"id": "e1", "src": "Busan Port", "dst": "Tier-1 Supplier A", "flow": flow_busan_to_supA,
         "path": "M 100 95 C 205 95, 205 140, 305 140", "mx": 202, "my": 105},
        {"id": "e2", "src": "Shanghai Port", "dst": "Tier-1 Supplier A", "flow": flow_shanghai_to_supA,
         "path": "M 100 345 C 205 345, 205 140, 305 140", "mx": 202, "my": 225},
        {"id": "e3", "src": "Shanghai Port", "dst": "Tier-1 Supplier B", "flow": flow_shanghai_to_supB,
         "path": "M 100 345 L 305 345", "mx": 202, "my": 345},
        {"id": "e4", "src": "Tier-1 Supplier A", "dst": "Tier-2 Component Mfg", "flow": flow_supA_to_mfg,
         "path": "M 305 140 C 410 140, 410 240, 510 240", "mx": 408, "my": 180},
        {"id": "e5", "src": "Tier-1 Supplier B", "dst": "Tier-2 Component Mfg", "flow": flow_supB_to_mfg,
         "path": "M 305 345 C 410 345, 410 240, 510 240", "mx": 408, "my": 300},
        {"id": "e6", "src": "Tier-2 Component Mfg", "dst": "Assembly Hub", "flow": flow_mfg_to_assembly,
         "path": "M 510 240 L 690 240", "mx": 600, "my": 240},
        {"id": "e7", "src": "Assembly Hub", "dst": "Distribution Center", "flow": flow_assembly_to_dist,
         "path": "M 690 240 C 768 240, 768 110, 845 110", "mx": 768, "my": 165},
        {"id": "e8", "src": "Assembly Hub", "dst": "OE Retailer", "flow": flow_assembly_to_retail,
         "path": "M 690 240 C 768 240, 768 345, 845 345", "mx": 768, "my": 300},
        {"id": "e9", "src": "Distribution Center", "dst": "OE Retailer", "flow": flow_dist_to_retail,
         "path": "M 845 110 L 845 345", "mx": 845, "my": 228},
    ]

    throughput = cap_retail
    blocked_count = sum(1 for e in edges if e["flow"] <= 20)
    throttled_count = sum(1 for e in edges if 20 < e["flow"] < 80)

    # Build SVG content
    edge_elements = []
    particle_elements = []
    badge_elements = []

    for e in edges:
        eid = e["id"]
        flow = e["flow"]
        path = e["path"]
        mx = e["mx"]
        my = e["my"]

        # Background track
        edge_elements.append(f'<path d="{path}" fill="none" stroke="#e5e7eb" stroke-width="5" stroke-linecap="round"/>')

        if flow <= 20:
            # BLOCKED / SEVERED CONDUIT - NO PARTICLES (FLOW STOPPED)
            edge_elements.append(
                f'<path id="{eid}" d="{path}" fill="none" stroke="#ef4444" stroke-width="3" '
                f'stroke-dasharray="6,6" stroke-linecap="round" marker-end="url(#arrow-blocked)" class="conduit-blocked"/>'
            )
            # Floating badge
            badge_elements.append(
                f'<g transform="translate({mx - 46}, {my - 11})" class="flow-badge">'
                f'<rect width="92" height="22" rx="11" fill="#fef2f2" stroke="#fca5a5" stroke-width="1.5"/>'
                f'<text x="46" y="15" text-anchor="middle" fill="#dc2626" font-family="Inter,sans-serif" font-size="10" font-weight="700">🚫 0% BLOCKED</text>'
                f'</g>'
            )
        elif flow < 80:
            # THROTTLED / CONSTRAINED CONDUIT - SLUGGISH FLOW
            edge_elements.append(
                f'<path id="{eid}" d="{path}" fill="none" stroke="#f59e0b" stroke-width="3" '
                f'stroke-dasharray="8,8" stroke-linecap="round" marker-end="url(#arrow-throttled)" class="conduit-throttled"/>'
            )
            # Slow particle
            particle_elements.append(
                f'<circle r="4" fill="#f59e0b" class="flow-particle">'
                f'<animateMotion dur="4.2s" repeatCount="indefinite"><mpath href="#{eid}"/></animateMotion>'
                f'</circle>'
            )
            badge_elements.append(
                f'<g transform="translate({mx - 42}, {my - 11})" class="flow-badge">'
                f'<rect width="84" height="22" rx="11" fill="#fffbeb" stroke="#fde68a" stroke-width="1.5"/>'
                f'<text x="42" y="15" text-anchor="middle" fill="#d97706" font-family="Inter,sans-serif" font-size="10" font-weight="600">⚠️ {flow}% FLOW</text>'
                f'</g>'
            )
        else:
            # ACTIVE OPTIMAL FLOW - VIBRANT PARTICLES
            edge_elements.append(
                f'<path id="{eid}" d="{path}" fill="none" stroke="#3b82f6" stroke-width="3.5" '
                f'stroke-linecap="round" marker-end="url(#arrow-active)" class="conduit-active"/>'
            )
            # Fast particles
            particle_elements.append(
                f'<circle r="4.5" fill="#10b981" filter="url(#glow)" class="flow-particle">'
                f'<animateMotion dur="1.8s" repeatCount="indefinite"><mpath href="#{eid}"/></animateMotion>'
                f'</circle>'
            )
            particle_elements.append(
                f'<circle r="4.5" fill="#10b981" filter="url(#glow)" class="flow-particle">'
                f'<animateMotion dur="1.8s" begin="0.9s" repeatCount="indefinite"><mpath href="#{eid}"/></animateMotion>'
                f'</circle>'
            )
            badge_elements.append(
                f'<g transform="translate({mx - 38}, {my - 10})" class="flow-badge">'
                f'<rect width="76" height="20" rx="10" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1"/>'
                f'<text x="38" y="14" text-anchor="middle" fill="#059669" font-family="Inter,sans-serif" font-size="9.5" font-weight="600">100% FLOW</text>'
                f'</g>'
            )

    # Build Node elements
    node_elements = []
    for name, info in nodes_info.items():
        x = info["x"]
        y = info["y"]
        icon = info["icon"]
        tier = info["tier"]
        cap = node_caps[name]
        is_disrupted = (name == disrupted_node)

        beacon_html = ""
        if is_disrupted:
            # Hazard pulse rings
            beacon_html = (
                f'<circle cx="{x}" cy="{y}" r="32" fill="none" stroke="#ef4444" stroke-width="2.5" opacity="0.8">'
                f'<animate attributeName="r" values="30;60" dur="1.6s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0.8;0" dur="1.6s" repeatCount="indefinite"/>'
                f'</circle>'
                f'<circle cx="{x}" cy="{y}" r="26" fill="none" stroke="#dc2626" stroke-width="1.5" opacity="0.6">'
                f'<animate attributeName="r" values="24;50" dur="1.6s" begin="0.8s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0.6;0" dur="1.6s" begin="0.8s" repeatCount="indefinite"/>'
                f'</circle>'
            )
            card_border = "#ef4444"
            card_border_w = "2.5"
            card_bg = "#ffffff"
            badge_bg = "#fef2f2"
            badge_border = "#fecaca"
            badge_text_color = "#dc2626"
            badge_label = f"🚫 DISRUPTED ({cap}%)"
        elif cap < 40:
            card_border = "#f97316"
            card_border_w = "2"
            card_bg = "#ffffff"
            badge_bg = "#fff7ed"
            badge_border = "#fed7aa"
            badge_text_color = "#ea580c"
            badge_label = f"❌ STARVED ({cap}%)"
        elif cap < 80:
            card_border = "#f59e0b"
            card_border_w = "2"
            card_bg = "#ffffff"
            badge_bg = "#fffbeb"
            badge_border = "#fde68a"
            badge_text_color = "#d97706"
            badge_label = f"⚠️ CONSTRAINED ({cap}%)"
        else:
            card_border = "#e5e7eb"
            card_border_w = "1.5"
            card_bg = "#ffffff"
            badge_bg = "#ecfdf5"
            badge_border = "#a7f3d0"
            badge_text_color = "#059669"
            badge_label = f"✅ OPTIMAL ({cap}%)"

        node_card = (
            f'<g class="node-group" data-node="{name}" transform="translate({x - 70}, {y - 32})">'
            f'<rect width="140" height="64" rx="12" fill="{card_bg}" stroke="{card_border}" stroke-width="{card_border_w}" '
            f'filter="url(#shadow-card)" class="node-rect"/>'
            f'<text x="70" y="20" text-anchor="middle" fill="#111827" font-family="Inter,sans-serif" font-size="11.5" font-weight="700">{icon} {name}</text>'
            f'<text x="70" y="34" text-anchor="middle" fill="#6b7280" font-family="Inter,sans-serif" font-size="9" font-weight="500">{tier}</text>'
            f'<g transform="translate(18, 41)">'
            f'<rect width="104" height="17" rx="8.5" fill="{badge_bg}" stroke="{badge_border}" stroke-width="1"/>'
            f'<text x="52" y="12" text-anchor="middle" fill="{badge_text_color}" font-family="Inter,sans-serif" font-size="9" font-weight="700">{badge_label}</text>'
            f'</g>'
            f'</g>'
        )

        node_elements.append(f'<g id="node-wrap-{name.replace(" ", "_")}">{beacon_html}{node_card}</g>')

    edges_svg = "\n".join(edge_elements)
    particles_svg = "\n".join(particle_elements)
    badges_svg = "\n".join(badge_elements)
    nodes_svg = "\n".join(node_elements)

    html_code = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', -apple-system, sans-serif; }}
body {{ background: #ffffff; overflow: hidden; }}

.sim-container {{
    width: 100%;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.03);
}}

/* Top Telemetry Header */
.sim-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 12px;
    border-bottom: 1px solid #f3f4f6;
    margin-bottom: 8px;
}}
.sim-title-group {{
    display: flex;
    align-items: center;
    gap: 10px;
}}
.sim-pulse-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #ef4444;
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
    animation: pulseRed 1.8s infinite;
}}
@keyframes pulseRed {{
    0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }}
    70% {{ box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }}
}}
.sim-title {{
    font-size: 14px;
    font-weight: 700;
    color: #111827;
}}
.sim-subtitle {{
    font-size: 11px;
    color: #6b7280;
}}
.sim-metrics-bar {{
    display: flex;
    gap: 10px;
    align-items: center;
}}
.telemetry-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    color: #374151;
}}
.telemetry-pill.shock {{
    background: #fef2f2;
    border-color: #fecaca;
    color: #dc2626;
}}
.telemetry-pill.throughput {{
    background: #eff6ff;
    border-color: #bfdbfe;
    color: #1d4ed8;
}}

/* Interactive Controls */
.sim-controls {{
    display: flex;
    gap: 6px;
}}
.control-btn {{
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
    color: #374151;
    cursor: pointer;
    transition: all 0.15s ease;
}}
.control-btn:hover {{
    background: #f3f4f6;
    border-color: #9ca3af;
}}
.control-btn.active {{
    background: #fee2e2;
    border-color: #f87171;
    color: #b91c1c;
}}

/* SVG Viewport */
.svg-viewport {{
    width: 100%;
    height: 380px;
    display: block;
}}

.node-group {{
    cursor: pointer;
    transition: transform 0.2s ease;
}}
.node-group:hover {{
    filter: drop-shadow(0 6px 12px rgba(0,0,0,0.12));
}}

/* Bottom Legend */
.sim-legend {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 10px;
    border-top: 1px solid #f3f4f6;
    margin-top: 6px;
    font-size: 11px;
    color: #6b7280;
}}
.legend-items {{
    display: flex;
    gap: 16px;
}}
.legend-item {{
    display: flex;
    align-items: center;
    gap: 6px;
}}
.legend-indicator {{
    width: 12px;
    height: 4px;
    border-radius: 2px;
}}
.legend-indicator.active {{ background: #3b82f6; }}
.legend-indicator.throttled {{ background: #f59e0b; }}
.legend-indicator.blocked {{ background: #ef4444; }}
.legend-particle {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #10b981;
}}
</style>
</head>
<body>

<div class="sim-container">
    <div class="sim-header">
        <div class="sim-title-group">
            <div class="sim-pulse-dot"></div>
            <div>
                <div class="sim-title">⚡ Real-Time Material & Component Flow Simulation</div>
                <div class="sim-subtitle">Simulating live discrete component pulses across 8 multi-tier network nodes</div>
            </div>
        </div>
        <div class="sim-metrics-bar">
            <div class="telemetry-pill shock">
                <span>⚠️ Choke: <b>{disrupted_node}</b> ({event_type})</span>
            </div>
            <div class="telemetry-pill throughput">
                <span>Network Throughput: <b>{throughput}%</b></span>
            </div>
            <div class="sim-controls">
                <button class="control-btn" id="btnShock" onclick="triggerShockWave()">⚡ Shock Ripple</button>
                <button class="control-btn" id="btnPause" onclick="togglePause()">⏸ Pause Flow</button>
            </div>
        </div>
    </div>

    <svg class="svg-viewport" viewBox="0 0 945 425" preserveAspectRatio="xMidYMid meet">
        <defs>
            <!-- Glowing effect -->
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="2.5" result="blur" />
                <feMerge>
                    <feMergeNode in="blur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
            <!-- Drop shadow for node cards -->
            <filter id="shadow-card" x="-10%" y="-10%" width="125%" height="125%">
                <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000000" flood-opacity="0.06"/>
            </filter>
            <!-- Arrow markers -->
            <marker id="arrow-active" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#3b82f6" />
            </marker>
            <marker id="arrow-throttled" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#f59e0b" />
            </marker>
            <marker id="arrow-blocked" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#ef4444" />
            </marker>
        </defs>

        <!-- Conduits (Base tracks & status paths) -->
        <g id="layer-edges">
            {edges_svg}
        </g>

        <!-- Moving Flow Particles -->
        <g id="layer-particles">
            {particles_svg}
        </g>

        <!-- Flow Status Badges -->
        <g id="layer-badges">
            {badges_svg}
        </g>

        <!-- Dynamic Shock Ripple Ring -->
        <circle id="shockRipple" cx="{nodes_info[disrupted_node]['x']}" cy="{nodes_info[disrupted_node]['y']}" r="0" fill="none" stroke="#ef4444" stroke-width="4" opacity="0"/>

        <!-- Nodes -->
        <g id="layer-nodes">
            {nodes_svg}
        </g>
    </svg>

    <div class="sim-legend">
        <div class="legend-items">
            <div class="legend-item">
                <div class="legend-particle"></div>
                <span>Moving Particles: Active Component Freight</span>
            </div>
            <div class="legend-item">
                <div class="legend-indicator active"></div>
                <span>Active Conduit (100% Flow)</span>
            </div>
            <div class="legend-item">
                <div class="legend-indicator throttled"></div>
                <span>Throttled/Starved ({throttled_count} paths)</span>
            </div>
            <div class="legend-item">
                <div class="legend-indicator blocked"></div>
                <span>Severed / Blocked (0% Flow · {blocked_count} severed)</span>
            </div>
        </div>
        <div>
            <span>Physics Mode: Deterministic Multi-Tier Flow · 60 FPS</span>
        </div>
    </div>
</div>

<script>
let isPaused = false;
function togglePause() {{
    isPaused = !isPaused;
    const svg = document.querySelector('.svg-viewport');
    const btn = document.getElementById('btnPause');
    if (isPaused) {{
        svg.pauseAnimations();
        btn.innerHTML = '▶ Resume Flow';
        btn.classList.add('active');
    }} else {{
        svg.unpauseAnimations();
        btn.innerHTML = '⏸ Pause Flow';
        btn.classList.remove('active');
    }}
}}

function triggerShockWave() {{
    const ripple = document.getElementById('shockRipple');
    const btn = document.getElementById('btnShock');
    btn.classList.add('active');
    ripple.setAttribute('r', '10');
    ripple.setAttribute('opacity', '0.9');
    ripple.setAttribute('stroke-width', '5');
    
    let radius = 10;
    let opacity = 0.9;
    const interval = setInterval(() => {{
        radius += 18;
        opacity -= 0.04;
        ripple.setAttribute('r', radius);
        ripple.setAttribute('opacity', Math.max(0, opacity));
        if (opacity <= 0 || radius > 700) {{
            clearInterval(interval);
            ripple.setAttribute('opacity', '0');
            btn.classList.remove('active');
        }}
    }}, 25);
}}
</script>

</body>
</html>
"""
    return html_code

if __name__ == "__main__":
    test_html = build_animated_flow_html("Shanghai Port", 80, "Port closure")
    print(f"Generated HTML successfully! Length: {len(test_html)} characters.")
