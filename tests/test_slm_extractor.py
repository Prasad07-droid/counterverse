import unittest
from src.module_b_slm import extract_signal
from src.module_c_causal import compute_dependency_ratio, calculate_deterministic_risk_score

class TestSLMExtractor(unittest.TestCase):
    def test_region_is_origin_not_target(self):
        headline = "China restricts gallium and germanium exports, sparking chip shortage fears in India"
        result = extract_signal(headline, simulate_delay=False, engine="fast")
        self.assertNotEqual(result["region"], "India", "Region should not be the target market (India)")
        self.assertIn("china", result["region"].lower(), "Region should capture the origin of the disruption (China)")

    def test_red_sea_region(self):
        headline = "Red Sea shipping crisis forces Indian automakers to reroute"
        result = extract_signal(headline, simulate_delay=False, engine="fast")
        self.assertEqual(result["region"], "Red Sea")

    def test_dependency_ratio_uniform_weight(self):
        # Gallium: 0.362 direct, 0.90 upstream -> DR=0.793
        ga_res = compute_dependency_ratio(0.362, upstream_concentration_penalty=0.900)
        self.assertEqual(ga_res["dependency_ratio"], 0.793)

        # China IC: 0.314 direct, 0.246 transit -> DR=0.560
        cn_res = compute_dependency_ratio(0.314, transit_corridor_share=0.246)
        self.assertEqual(cn_res["dependency_ratio"], 0.560)

        # Taiwan IC: 0.063 direct, 0.70 upstream -> DR=0.555
        tw_res = compute_dependency_ratio(0.063, upstream_concentration_penalty=0.700)
        self.assertEqual(tw_res["dependency_ratio"], 0.555)

        # South Korea IC: 0.140 direct, 0.45 upstream -> DR=0.430
        kr_res = compute_dependency_ratio(0.140, upstream_concentration_penalty=0.450)
        self.assertEqual(kr_res["dependency_ratio"], 0.430)

    def test_scen12_control_scenario_low_risk(self):
        signal = {
            "is_disruption": True,
            "disruption_type": "Logistics Disruption",
            "impacted_industries": ["Automotive", "Semiconductors"],
            "component": "Transportation",
            "severity": 3,
            "summary": "Automotive supplier union successfully concluded an annual wage agreement without work stoppages.",
            "headline": "Automotive supplier union successfully concludes annual wage agreement without work stoppage"
        }
        risk = calculate_deterministic_risk_score(signal)
        self.assertEqual(risk["risk_level"], "LOW")
        self.assertEqual(risk["risk_score"], 0.0)

    def test_generalized_benign_headlines(self):
        headlines = [
            "Company announces routine quarterly earnings call, no supply chain concerns raised",
            "Automotive plant completes scheduled annual maintenance shutdown ahead of production restart",
            "Trade ministry renews standard bilateral cooperation agreement with no policy changes"
        ]
        for h in headlines:
            # Fast mode extraction
            sig = extract_signal(h, simulate_delay=False, engine="fast")
            sig["headline"] = h
            risk = calculate_deterministic_risk_score(sig)
            self.assertEqual(risk["risk_level"], "LOW", f"Failed for headline: {h}")
            self.assertEqual(risk["risk_score"], 0.0, f"Failed for headline: {h}")
            self.assertFalse(sig["is_disruption"], f"Fast mode should filter benign headline: {h}")

if __name__ == "__main__":
    unittest.main()
