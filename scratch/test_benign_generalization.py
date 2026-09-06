import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.module_b_slm import extract_signal
from src.module_c_causal import calculate_deterministic_risk_score

headlines = [
    "Company announces routine quarterly earnings call, no supply chain concerns raised",
    "Automotive plant completes scheduled annual maintenance shutdown ahead of production restart",
    "Trade ministry renews standard bilateral cooperation agreement with no policy changes"
]

print("=== FAST MODE ===")
for h in headlines:
    sig = extract_signal(h, simulate_delay=False, engine="fast")
    sig["headline"] = h
    risk = calculate_deterministic_risk_score(sig)
    print(f"H: {h[:55]}... | is_disr={sig.get('is_disruption')} | pred_type={sig.get('disruption_type')} | risk={risk.get('risk_score')} | level={risk.get('risk_level')}")

print("\n=== SLM MODE ===")
for h in headlines:
    sig = extract_signal(h, simulate_delay=False, engine="slm")
    sig["headline"] = h
    risk = calculate_deterministic_risk_score(sig)
    print(f"H: {h[:55]}... | is_disr={sig.get('is_disruption')} | pred_type={sig.get('disruption_type')} | risk={risk.get('risk_score')} | level={risk.get('risk_level')}")
