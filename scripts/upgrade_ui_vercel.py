# -*- coding: utf-8 -*-
"""
Upgrade CounterVerse Dashboard to Vercel-grade UI/UX Design System.
Ensures UTF-8 encoding without BOM, preserving all emojis and test compatibility.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_PATH = ROOT / "app" / "dashboard.py"

VERCEL_INLINE_CSS = """st.markdown(\"\"\"
<style>
/* ── Vercel Typography & Font Imports: Geist + Inter + Geist Mono ── */
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700;800&family=Geist+Mono:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Vercel Pure Monochrome & High-Contrast Design Tokens ── */
:root {
    --canvas-bg: #000000;
    --canvas-radial: radial-gradient(ellipse 80% 50% at 50% -20%, rgba(120, 119, 198, 0.15), transparent 80%),
                     linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                     linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
    --surface-glass: #0a0a0a;
    --surface-glass-hover: #121212;
    --surface-elevated: #111111;
    --surface-card: #0a0a0a;

    --border-subtle: #222222;
    --border-hover: rgba(255, 255, 255, 0.22);
    --border-glow: 0 0 0 1px rgba(255, 255, 255, 0.15);

    --text-primary: #ededed;
    --text-secondary: #a1a1a1;
    --text-muted: #707070;
    --text-highlight: #ffffff;

    --neon-cyan: #0070f3;
    --neon-cyan-glow: 0 0 16px rgba(0, 112, 243, 0.25);
    --neon-red: #ee0000;
    --neon-red-glow: 0 0 16px rgba(238, 0, 0, 0.25);
    --neon-emerald: #00df8f;
    --neon-emerald-glow: 0 0 16px rgba(0, 223, 143, 0.25);
    --neon-amber: #f5a623;
    --neon-amber-glow: 0 0 16px rgba(245, 166, 35, 0.25);

    --sidebar-bg: #050505;
    --sidebar-active-indicator: #ffffff;

    --radius-standard: 8px;
    --radius-sm: 6px;
    --shadow-glass: 0 0 0 1px rgba(255, 255, 255, 0.05), 0 4px 20px rgba(0, 0, 0, 0.7);
    --shadow-card: 0 0 0 1px rgba(255, 255, 255, 0.04), 0 2px 8px rgba(0, 0, 0, 0.6);
}

/* ── Global Canvas Overrides ── */
.stApp {
    background-color: #000000 !important;
    background-image: var(--canvas-radial) !important;
    background-size: 100% 100%, 32px 32px, 32px 32px !important;
    background-attachment: fixed !important;
    font-family: 'Geist', 'Inter', -apple-system, sans-serif !important;
    color: var(--text-primary) !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Geist', 'Inter', sans-serif !important;
    letter-spacing: -0.03em !important;
    color: #ededed !important;
    font-weight: 700 !important;
}

/* ── Hide Default Streamlit Clutter ── */
header[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer, .stDeployButton { display: none !important; }

/* ── Sidebar: Vercel Sleek Panel ── */
section[data-testid="stSidebar"] {
    background-color: var(--sidebar-bg) !important;
    border-right: 1px solid #1a1a1a !important;
}
section[data-testid="stSidebar"] * {
    font-family: 'Geist', 'Inter', sans-serif !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #1a1a1a !important;
}
section[data-testid="stSidebar"] .stRadio label {
    color: #888888 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 8px 12px !important;
    border-radius: var(--radius-sm) !important;
    transition: all 0.15s ease !important;
    border: 1px solid transparent !important;
    margin-bottom: 2px !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: #111111 !important;
    color: #ffffff !important;
    border-color: #222222 !important;
}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"],
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) {
    background: #171717 !important;
    border: 1px solid #333333 !important;
    border-left: 2px solid #ffffff !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.08) !important;
}
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div > div {
    background: #0a0a0a !important;
    border: 1px solid #222222 !important;
    color: #ffffff !important;
    border-radius: var(--radius-sm) !important;
}
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label,
section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
    color: #888888 !important;
}

/* ── Live Incident HUD Banner (Vercel Style) ── */
.active-incident-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    padding: 12px 20px;
    background: #0d0606;
    border: 1px solid rgba(238, 0, 0, 0.3);
    border-left: 3px solid #ee0000;
    border-radius: var(--radius-standard);
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.04), 0 4px 16px rgba(0, 0, 0, 0.5);
    margin-bottom: 20px;
}
.incident-badge-group {
    display: flex;
    align-items: center;
    gap: 10px;
}
.incident-shock-badge {
    background: #ee0000;
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 3px 8px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.incident-headline-text {
    font-size: 0.92rem;
    font-weight: 500;
    color: #ededed;
}
.incident-meta-group {
    display: flex;
    align-items: center;
    gap: 16px;
    font-size: 0.82rem;
    color: var(--text-secondary);
}
.incident-meta-item strong {
    color: #ffffff;
}

/* ── Causal Decision Ribbon (Vercel Modular HUD) ── */
.decision-ribbon {
    display: flex;
    align-items: stretch;
    background: var(--surface-glass);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-standard);
    box-shadow: var(--shadow-glass);
    margin-bottom: 24px;
    overflow: hidden;
}
.ribbon-tier {
    flex: 1;
    padding: 14px 18px;
    border-right: 1px solid var(--border-subtle);
    background: transparent;
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
    transition: all 0.15s ease;
}
.ribbon-tier:last-child {
    border-right: none;
}
.ribbon-tier:hover {
    background: #111111;
}
.ribbon-tier.active-shock {
    background: #100808;
    border-left: 2px solid #ee0000;
}
.ribbon-tier-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.ribbon-tier-val {
    font-size: 1.05rem;
    font-weight: 600;
    font-family: 'Geist', 'Inter', sans-serif;
    color: #ffffff;
    line-height: 1.25;
}
.ribbon-tier-sub {
    font-size: 12px;
    color: var(--text-secondary);
    margin-top: 4px;
    line-height: 1.35;
}
.ribbon-pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ee0000;
    display: inline-block;
    box-shadow: 0 0 0 rgba(238, 0, 0, 0.6);
    animation: ribbonPulse 2s infinite ease-in-out;
}
.ribbon-dot-teal {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #00df8f;
    display: inline-block;
}
.ribbon-dot-amber {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #f5a623;
    display: inline-block;
}
.ribbon-dot-blue {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #0070f3;
    display: inline-block;
}
@keyframes ribbonPulse {
    0% { transform: scale(0.92); box-shadow: 0 0 0 0 rgba(238, 0, 0, 0.8); }
    70% { transform: scale(1.15); box-shadow: 0 0 0 6px rgba(238, 0, 0, 0); }
    100% { transform: scale(0.92); box-shadow: 0 0 0 0 rgba(238, 0, 0, 0); }
}

/* ── Executive Directive Card ── */
.recommended-action-card {
    background: #090e0c;
    border: 1px solid rgba(0, 223, 143, 0.25);
    border-left: 3px solid #00df8f;
    border-radius: var(--radius-standard);
    padding: 16px 20px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
    margin-top: 16px;
}
.action-kicker {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #00df8f;
}
.action-title {
    font-size: 1.10rem;
    font-weight: 600;
    font-family: 'Geist', 'Inter', sans-serif;
    color: #ffffff;
    margin: 4px 0 6px 0;
}
.action-sub {
    font-size: 0.84rem;
    color: #a1a1a1;
    line-height: 1.45;
}

/* ── Vercel Panels (.glass-card) ── */
.glass-card {
    background: var(--surface-glass);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-standard);
    box-shadow: var(--shadow-glass);
    padding: 24px;
    margin-bottom: 20px;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.glass-card:hover {
    border-color: var(--border-hover);
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.12), 0 8px 30px rgba(0, 0, 0, 0.8);
}
.glass-card h3 {
    font-size: 0.95rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
}

/* ── Section Header ── */
.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 14px;
    margin-bottom: 16px;
}
.section-header h3 {
    font-size: 1.10rem;
    font-weight: 700;
    font-family: 'Geist', 'Inter', sans-serif;
    color: #ffffff;
    margin: 0;
}
.section-badge {
    font-size: 11px;
    font-weight: 500;
    color: #a1a1a1;
    background: #111111;
    padding: 3px 10px;
    border-radius: 9999px;
    border: 1px solid #262626;
}

/* ── Vercel Minimalist KPI Cards ── */
.metric-card {
    background: var(--surface-glass);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-standard);
    box-shadow: var(--shadow-card);
    padding: 18px 20px;
    text-align: left;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 120px;
    position: relative;
    overflow: hidden;
}
.metric-card:hover {
    border-color: var(--border-hover);
    transform: translateY(-2px);
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1), 0 8px 24px rgba(0, 0, 0, 0.7);
}
.metric-card.critical {
    border-color: rgba(238, 0, 0, 0.35);
    background: linear-gradient(180deg, rgba(238, 0, 0, 0.08) 0%, #0a0a0a 100%);
}
.metric-card .metric-label {
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.metric-card .metric-value {
    font-size: 1.85rem;
    font-weight: 700;
    font-family: 'Geist', 'Inter', sans-serif;
    color: #ededed;
    line-height: 1.15;
    letter-spacing: -0.03em;
}
.metric-card .metric-sub {
    font-size: 12px;
    font-weight: 400;
    color: var(--text-secondary);
    margin-top: 6px;
}

/* ── Semantic Status Badges ── */
.status-badge-critical {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    background: rgba(238, 0, 0, 0.1);
    color: #ff4d4d;
    border: 1px solid rgba(238, 0, 0, 0.35);
    padding: 2px 8px;
    border-radius: 9999px;
}
.status-badge-warning {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    background: rgba(245, 166, 35, 0.1);
    color: #f5a623;
    border: 1px solid rgba(245, 166, 35, 0.35);
    padding: 2px 8px;
    border-radius: 9999px;
}
.status-badge-optimal {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    background: rgba(0, 223, 143, 0.1);
    color: #00df8f;
    border: 1px solid rgba(0, 223, 143, 0.35);
    padding: 2px 8px;
    border-radius: 9999px;
}

/* ── Form Controls & Widget Overrides ── */
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stSelectbox"] label p,
div[data-testid="stSlider"] label p,
div[data-testid="stNumberInput"] label p,
div[data-testid="stTextArea"] label p {
    font-size: 11px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    color: var(--text-muted) !important;
    margin-bottom: 6px !important;
}

div[data-testid="stSelectbox"] > div > div {
    background: #0a0a0a !important;
    border: 1px solid #222222 !important;
    color: #ffffff !important;
    border-radius: var(--radius-sm) !important;
    font-size: 13.5px !important;
    transition: all 0.15s ease;
}
div[data-testid="stSelectbox"] > div > div:hover,
div[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: rgba(255, 255, 255, 0.25) !important;
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.18) !important;
}
div[data-testid="stSelectbox"] [data-baseweb="select"] {
    background-color: transparent !important;
}
div[data-testid="stSelectbox"] [data-baseweb="select"] * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
ul[data-testid="stSelectboxVirtualDropdown"],
div[data-baseweb="popover"],
div[data-baseweb="menu"] {
    background-color: #0a0a0a !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.8) !important;
    border: 1px solid #222222 !important;
}
li[role="option"] {
    color: #ededed !important;
    font-size: 13.5px !important;
    transition: background-color 0.15s ease !important;
}
li[role="option"]:hover, li[aria-selected="true"] {
    background-color: #171717 !important;
    color: #ffffff !important;
}

div[data-testid="stTextArea"] textarea {
    background: #0a0a0a !important;
    border: 1px solid #222222 !important;
    color: #ededed !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Geist', 'Inter', sans-serif !important;
    font-size: 13.5px !important;
    line-height: 1.5 !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(255, 255, 255, 0.25) !important;
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.18) !important;
}
div[data-testid="stTextArea"] textarea::placeholder {
    color: #555555 !important;
}

div[data-testid="stNumberInput"] > div > div > input {
    background: #0a0a0a !important;
    border: 1px solid #222222 !important;
    color: #ffffff !important;
    border-radius: var(--radius-sm) !important;
}

/* ── Sliders ── */
div[data-testid="stSlider"] > div > div > div {
    background: #1e1e1e !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
    background-color: #ffffff !important;
    border: 2px solid #ffffff !important;
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.5) !important;
}

/* ── Vercel Primary Action Button (Solid White) ── */
.stButton > button[kind="primary"], .stButton > button {
    background: #ffffff !important;
    color: #000000 !important;
    border: 1px solid #ffffff !important;
    border-radius: var(--radius-sm) !important;
    padding: 10px 24px !important;
    font-family: 'Geist', 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: -0.01em !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1), 0 2px 4px rgba(0, 0, 0, 0.4) !important;
}
.stButton > button:hover {
    background: #eaeaea !important;
    border-color: #eaeaea !important;
    color: #000000 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 0 24px rgba(255, 255, 255, 0.25) !important;
}

/* ── Tabs: Vercel Sleek Underline ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #222222 !important;
    padding: 0 !important;
    gap: 8px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    color: #888888 !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    padding: 10px 16px !important;
    transition: all 0.15s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #ffffff !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #ffffff !important;
    border-bottom: 2px solid #ffffff !important;
    background: transparent !important;
    box-shadow: none !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── Expanders ── */
.streamlit-expanderHeader {
    background: #0a0a0a !important;
    border-radius: var(--radius-sm) !important;
    color: #ededed !important;
    font-weight: 600 !important;
    border: 1px solid #222222 !important;
    transition: all 0.15s ease !important;
}
.streamlit-expanderHeader:hover {
    border-color: rgba(255, 255, 255, 0.2) !important;
    background: #111111 !important;
}

/* ── Alerts & Status Widgets ── */
.stAlert {
    border-radius: var(--radius-sm) !important;
    background: #0a0a0a !important;
    border: 1px solid #222222 !important;
    color: #ededed !important;
}
div[data-testid="stStatusWidget"] {
    background: #0a0a0a !important;
    border: 1px solid #222222 !important;
    border-radius: var(--radius-sm) !important;
    color: #ffffff !important;
}

/* ── GraphRAG Entity Badges ── */
.grounding-badge-verified {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 2px 8px; border-radius: 9999px;
    background: rgba(0, 223, 143, 0.1); color: #00df8f;
    font-size: 11px; font-weight: 600;
    border: 1px solid rgba(0, 223, 143, 0.3);
}
.grounding-badge-unverified {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 2px 8px; border-radius: 9999px;
    background: rgba(245, 166, 35, 0.1); color: #f5a623;
    font-size: 11px; font-weight: 600;
    border: 1px solid rgba(245, 166, 35, 0.3);
}

/* ── Horizontal Grid Gaps ── */
div[data-testid="stHorizontalBlock"] { gap: 16px !important; }

/* ── Animations ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
.reveal-step-1 { animation: fadeInUp 0.25s cubic-bezier(0.16, 1, 0.3, 1) 0s both; }
.reveal-step-2 { animation: fadeInUp 0.25s cubic-bezier(0.16, 1, 0.3, 1) 0.08s both; }
.reveal-step-3 { animation: fadeInUp 0.25s cubic-bezier(0.16, 1, 0.3, 1) 0.16s both; }

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
</style>
\"\"\", unsafe_allow_html=True)
"""

def main():
    content = DASHBOARD_PATH.read_text(encoding="utf-8")
    
    # Locate the block from st.markdown(\"\"\"\n<style> to </style>\n\"\"\", unsafe_allow_html=True)
    pattern = r'st\.markdown\("""\s*<style>.*?<\/style>\s*""",\s*unsafe_allow_html=True\)'
    
    match = re.search(pattern, content, flags=re.DOTALL)
    if not match:
        print("ERROR: Could not find inline style block in dashboard.py")
        return False
        
    start, end = match.span()
    new_content = content[:start] + VERCEL_INLINE_CSS.strip() + content[end:]
    
    # Also ensure page title has Vercel-like sleekness
    # e.g., CounterVerse · Enterprise Supply Chain Intelligence
    new_content = new_content.replace(
        'page_title="CounterVerse · Decision Intelligence"',
        'page_title="CounterVerse · Supply Chain Intelligence"'
    )
    
    # Save back cleanly as UTF-8
    DASHBOARD_PATH.write_text(new_content, encoding="utf-8")
    print("SUCCESS: dashboard.py updated with Vercel UI design system.")
    return True

if __name__ == "__main__":
    main()
