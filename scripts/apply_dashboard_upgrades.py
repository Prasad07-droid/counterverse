"""
Final clean dashboard fix:
1. Normalize line endings (remove double-CR from git stash artifact)
2. Replace use_container_width (already done, verify)
3. Inject CSS loader after set_page_config
4. Write back clean UTF-8 without BOM
"""

filepath = "app/dashboard.py"

with open(filepath, "rb") as f:
    raw = f.read()

# Strip BOM
if raw.startswith(b"\xef\xbb\xbf"):
    raw = raw[3:]

# Normalize line endings: \r\r\n -> \n, then \r\n -> \n
text = raw.replace(b"\r\r\n", b"\n").replace(b"\r\n", b"\n").replace(b"\r", b"\n").decode("utf-8")

# 1. Fix use_container_width
count_true = text.count("use_container_width=True")
count_false = text.count("use_container_width=False")
text = text.replace("use_container_width=True",  "width='stretch'")
text = text.replace("use_container_width=False", "width='content'")
print(f"Replaced {count_true} True, {count_false} False")

# 2. Inject CSS loader after set_page_config
css_loader = '''
# -- Load external CSS design system (dark-mode + glassmorphism) --
_css_path = _app_dir / "assets" / "style.css"
if _css_path.exists():
    with open(_css_path, encoding="utf-8") as _f:
        st.markdown("<style>" + _f.read() + "</style>", unsafe_allow_html=True)

'''
marker = 'initial_sidebar_state="expanded"\n)\n'
if css_loader.strip() not in text:
    if marker in text:
        text = text.replace(marker, marker + css_loader, 1)
        print("CSS loader injected.")
    else:
        print("WARNING: marker not found, CSS not injected.")
else:
    print("CSS loader already present.")

# 3. Write back
with open(filepath, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)

# 4. Verify
with open(filepath, "rb") as f:
    head = f.read(4)

checks = {
    "lightning U+26A1": chr(0x26A1),
    "em-dash U+2014":   chr(0x2014),
    "arrow U+2192":     chr(0x2192),
    "rupee U+20B9":     chr(0x20B9),
}
print("\n--- Verification ---")
_s = "OK - no BOM" if head[:3] != b"\xef\xbb\xbf" else "BAD - HAS BOM"
print("BOM:", _s)
_stretch = text.count("width='stretch'")
_ucw = text.count("use_container_width")
print("width=stretch count:", _stretch)
print("use_container_width remaining:", _ucw)
for name, ch in checks.items():
    print(f"  {name}: {ch in text}")
_sz = len(text.encode("utf-8"))
print("File size:", _sz, "bytes")
print("Done!")
