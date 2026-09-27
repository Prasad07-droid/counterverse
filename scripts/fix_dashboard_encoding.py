"""Fix UTF-8 BOM and use_container_width deprecation in dashboard.py."""
import re

filepath = "app/dashboard.py"

with open(filepath, "rb") as f:
    raw = f.read()

# Strip BOM if present
if raw.startswith(b"\xef\xbb\xbf"):
    raw = raw[3:]
    print("UTF-8 BOM stripped.")
else:
    print("No BOM found.")

text = raw.decode("utf-8")
original_len = len(text)

# Replace all remaining use_container_width= occurrences
count_true = text.count("use_container_width=True")
count_false = text.count("use_container_width=False")
text = text.replace("use_container_width=True", "width='stretch'")
text = text.replace("use_container_width=False", "width='content'")
print(f"Replaced {count_true} use_container_width=True -> width='stretch'")
print(f"Replaced {count_false} use_container_width=False -> width='content'")

# Write back WITHOUT BOM
with open(filepath, "w", encoding="utf-8") as f:
    f.write(text)

print(f"File rewritten: {original_len} -> {len(text)} chars, UTF-8 no BOM.")

# Verify
with open(filepath, "rb") as f:
    check = f.read(4)
print(f"First 4 bytes: {check.hex()} (should NOT start with efbbbf)")
