# -*- coding: utf-8 -*-
"""
Refine CounterVerse dashboard components with Vercel aesthetic touches:
- Vercel brand mark (▲ / minimalist monochrome mark)
- Clean Vercel scope bar
- Streamlined Plotly theme backgrounds to match #000000 canvas
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_PATH = ROOT / "app" / "dashboard.py"

def refine():
    text = DASHBOARD_PATH.read_text(encoding="utf-8")

    # 1. Update sidebar header to Vercel branding
    old_sidebar_header = """    st.markdown(\"\"\"
    <div style="padding: 10px 4px 16px 4px; border-bottom: 1px solid #1f2937; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: #f97316; font-size: 1.4rem;">⚡</span>
            <div>
                <div style="color: #ffffff; font-weight: 800; font-size: 1.15rem; letter-spacing: -0.02em;">CounterVerse</div>
                <div style="color: #94a3b8; font-size: 0.70rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em;">Decision Intelligence</div>
            </div>
        </div>
        <div style="margin-top: 10px; display: inline-flex; align-items: center; gap: 6px; background: #1e293b; border: 1px solid #334155; border-radius: 4px; padding: 3px 8px; font-size: 0.72rem; color: #38bdf8; font-weight: 600;">
            <span>🔒 Scope: HS 8112 ➔ HS 8542</span>
        </div>
    </div>
    \"\"\", unsafe_allow_html=True)"""

    new_sidebar_header = """    st.markdown(\"\"\"
    <div style="padding: 10px 4px 16px 4px; border-bottom: 1px solid #1a1a1a; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 28px; height: 28px; background: #ffffff; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: #000000; font-weight: 900; font-size: 14px; box-shadow: 0 0 14px rgba(255,255,255,0.25);">▲</div>
            <div>
                <div style="color: #ededed; font-weight: 700; font-size: 1.05rem; letter-spacing: -0.03em;">CounterVerse</div>
                <div style="color: #707070; font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em;">Supply Chain Intelligence</div>
            </div>
        </div>
        <div style="margin-top: 12px; display: inline-flex; align-items: center; gap: 6px; background: #0e0e0e; border: 1px solid #222222; border-radius: 4px; padding: 3px 8px; font-size: 0.72rem; color: #a1a1a1; font-weight: 500;">
            <span style="color: #00df8f; font-size: 8px;">●</span>
            <span>Locked Scope: HS 8112 ➔ HS 8542</span>
        </div>
    </div>
    \"\"\", unsafe_allow_html=True)"""

    if old_sidebar_header in text:
        text = text.replace(old_sidebar_header, new_sidebar_header)
        print("Updated sidebar header to Vercel brand styling.")
    else:
        print("Sidebar header pattern not matched, skipping sidebar header replace.")

    # 2. Update Global Scope Metadata Bar to Vercel card
    old_scope_bar = """<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:16px; padding:8px 18px; background:rgba(15, 23, 42, 0.7); backdrop-filter:blur(12px); border:1px solid rgba(255, 255, 255, 0.08); border-radius:10px; font-size:0.80rem; box-shadow:0 4px 16px rgba(0,0,0,0.3);">"""
    new_scope_bar = """<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:16px; padding:10px 18px; background:#0a0a0a; border:1px solid #222222; border-radius:8px; font-size:0.80rem; box-shadow:0 0 0 1px rgba(255, 255, 255, 0.05), 0 2px 8px rgba(0,0,0,0.6);">"""

    if old_scope_bar in text:
        text = text.replace(old_scope_bar, new_scope_bar)
        print("Updated global scope metadata bar.")

    # 3. Clean up any leftover cyan text in base_html
    text = text.replace(
        "Macro Exposure: <strong style='color:#38bdf8;",
        "Macro Exposure: <strong style='color:#ffffff;"
    )
    text = text.replace(
        "Allocated Base: <strong style='color:#38bdf8;",
        "Allocated Base: <strong style='color:#ffffff;"
    )

    DASHBOARD_PATH.write_text(text, encoding="utf-8")
    print("Refinements applied successfully.")

if __name__ == "__main__":
    refine()
