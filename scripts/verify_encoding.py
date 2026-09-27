"""Verify the dashboard.py encoding fix."""
with open("app/dashboard.py", encoding="utf-8") as f:
    text = f.read()

remaining = text.count("use_container_width")
stretch_count = text.count("width='stretch'")
bom_bytes = open("app/dashboard.py", "rb").read(3).hex()

print("Remaining use_container_width:", remaining)
print("width=stretch count:", stretch_count)
print("BOM bytes:", bom_bytes, "(ok if not efbbbf)")

# Check key Unicode chars
checks = {
    "lightning emoji U+26A1": chr(0x26A1),
    "em-dash U+2014": chr(0x2014),
    "right-arrow U+2192": chr(0x2192),
    "bullet U+2022": chr(0x2022),
    "check-mark U+2713": chr(0x2713),
}
for name, ch in checks.items():
    print(f"  {name} present: {ch in text}")
