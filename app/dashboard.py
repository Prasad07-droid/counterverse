import streamlit as st

# ── Page config: wide layout, no sidebar ──
st.set_page_config(
    page_title="CounterVerse — Supply Chain Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Hide Streamlit header, footer, menu & all padding ──
st.markdown(
    """
    <style>
        /* Hide the Streamlit header / toolbar */
        header[data-testid="stHeader"] { display: none !important; }
        /* Hide hamburger menu */
        #MainMenu { display: none !important; }
        /* Hide footer */
        footer { display: none !important; }
        /* Hide deploy button */
        .stDeployButton { display: none !important; }
        /* Remove ALL padding from the main block */
        .block-container {
            padding: 0 !important;
            max-width: 100% !important;
        }
        /* Remove top padding from the app view */
        .appview-container .main .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
        }
        /* Make the app view fill the screen */
        .stApp {
            margin: 0;
            padding: 0;
        }
        /* Hide sidebar collapse button */
        [data-testid="collapsedControl"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── URL of the Vite front-end (GitHub Pages) ──
VITE_URL = "https://prasad07-droid.github.io/counterverse/"

# ── Full-viewport iframe ──
st.markdown(
    f"""
    <iframe
        src="{VITE_URL}"
        style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            border: none;
            margin: 0;
            padding: 0;
            overflow: hidden;
            z-index: 999999;
        "
        allowfullscreen
    ></iframe>
    """,
    unsafe_allow_html=True,
)
