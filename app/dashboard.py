import streamlit as st

# Set page configuration
st.set_page_config(page_title="CounterVerse", layout="wide")

# URL of the Vite front‑end (GitHub Pages)
vite_url = "https://prasad07-droid.github.io/counterverse/"

# Embed the Vite app in an iframe – fills most of the viewport
st.markdown(
    f"<iframe src='{vite_url}' style='border:none;width:100%;height:90vh;'></iframe>",
    unsafe_allow_html=True,
)

st.caption("Embedded CounterVerse UI (served from GitHub Pages)")
