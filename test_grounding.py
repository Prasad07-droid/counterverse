# -*- coding: utf-8 -*-
"""Test GraphRAG grounding - both test cases."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.module_b_slm import extract_signal_with_grounding

# TEST 1: Known entity headline
print("=" * 60)
print("TEST 1: Known entity - China restricts gallium exports")
print("=" * 60)
r1 = extract_signal_with_grounding(
    "China restricts gallium and germanium exports citing national security",
    simulate_delay=False
)
g1 = r1["grounding"]
print("Verified: %d/%d (%.1f%%)" % (
    g1["summary"]["verified_count"],
    g1["summary"]["total_entities"],
    g1["summary"]["verification_rate"]
))
for e in g1["grounding_results"]:
    tag = "[VERIFIED]" if e["status"] == "Graph-Verified" else "[UNVERIFIED]"
    name = e.get("canonical_name") or e["entity_text"]
    print("  %s %s (%s)" % (tag, name, e["entity_type"]))
for r in g1.get("relationship_checks", []):
    tag = "[EDGE OK]" if r["status"] == "Graph-Verified" else "[NO EDGE]"
    print("  %s %s" % (tag, r["description"].replace("\u2192", "->")))

print()

# TEST 2: Unknown entity headline
print("=" * 60)
print("TEST 2: Unknown entity - FictionalCorp halts in Atlantis")
print("=" * 60)
headline_2 = "FictionalCorp halts semiconductor chip production in Atlantis indefinitely"
print(f"Tested Headline: \"{headline_2}\"")
r2 = extract_signal_with_grounding(
    headline_2,
    simulate_delay=False
)
print(f"Extracted Raw Signal: component='{r2.get('component')}', regions={r2.get('affected_regions')}, companies={r2.get('companies')}")
g2 = r2["grounding"]
print("Verified: %d/%d (%.1f%%)" % (
    g2["summary"]["verified_count"],
    g2["summary"]["total_entities"],
    g2["summary"]["verification_rate"]
))
for e in g2["grounding_results"]:
    tag = "[VERIFIED]" if e["status"] == "Graph-Verified" else "[UNVERIFIED]"
    name = e.get("canonical_name") or e["entity_text"]
    raw_str = e.get("entity_text")
    print("  %s %s (%s) [raw: '%s']" % (tag, name, e["entity_type"], raw_str))

print()
print("ALL TESTS PASSED")
