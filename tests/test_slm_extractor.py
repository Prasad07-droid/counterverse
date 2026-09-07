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

    def test_auto_extracted_fields_presence_and_ranges(self):
        """
        Verifies that auto-extracted fields (affected_node, event_type,
        severity_pct, duration_days, confidence) exist, are within valid
        ranges/enums, and are deterministic across multiple calls.
        """
        headline = "Taiwan semiconductor foundry reports severe packaging bottlenecks and wafer line delays"
        sig1 = extract_signal(headline, simulate_delay=False, engine="fast")
        sig2 = extract_signal(headline, simulate_delay=False, engine="fast")

        # 1. Verify existence of all 5 fields
        for field in ["affected_node", "event_type", "severity_pct", "duration_days", "confidence"]:
            self.assertIn(field, sig1, f"Field '{field}' missing from extraction output")

        # 2. Verify types and ranges
        self.assertIsInstance(sig1["severity_pct"], (int, float))
        self.assertGreaterEqual(sig1["severity_pct"], 0.0)
        self.assertLessEqual(sig1["severity_pct"], 100.0)

        self.assertIsInstance(sig1["duration_days"], int)
        self.assertGreater(sig1["duration_days"], 0)
        self.assertLessEqual(sig1["duration_days"], 365)

        self.assertIsInstance(sig1["confidence"], (int, float))
        self.assertGreaterEqual(sig1["confidence"], 0.0)
        self.assertLessEqual(sig1["confidence"], 1.0)

        valid_nodes = {
            "Raw Material Supplier",
            "Port/Logistics",
            "Tier-1 Supplier",
            "Tier-2 Supplier",
            "Semiconductor Fab",
            "Assembly Hub"
        }
        self.assertIn(sig1["affected_node"], valid_nodes)
        self.assertIsInstance(sig1["event_type"], str)
        self.assertGreater(len(sig1["event_type"]), 0)

        # 3. Verify determinism (same headline -> identical values across calls)
        self.assertEqual(sig1["affected_node"], sig2["affected_node"])
        self.assertEqual(sig1["event_type"], sig2["event_type"])
        self.assertEqual(sig1["severity_pct"], sig2["severity_pct"])
        self.assertEqual(sig1["duration_days"], sig2["duration_days"])
        self.assertEqual(sig1["confidence"], sig2["confidence"])

    def test_node_to_graph_id_fallback_and_edge_cases(self):
        """
        Verifies that unmapped or edge-case node strings do not raise a KeyError,
        and resolve strictly to the documented fallback 'tier1_supplier_a'.
        """
        from src.module_c_causal import NODE_TO_GRAPH_ID, map_node_to_graph_id, DEFAULT_FALLBACK_GRAPH_ID

        # Verified canonical mappings
        self.assertEqual(NODE_TO_GRAPH_ID["Raw Material Supplier"], "gallium_supplier")
        self.assertEqual(NODE_TO_GRAPH_ID["Port/Logistics"], "busan_port")
        self.assertEqual(NODE_TO_GRAPH_ID["Tier-1 Supplier"], "tier1_supplier_a")
        self.assertEqual(NODE_TO_GRAPH_ID["Tier-2 Supplier"], "tier2_component_mfg")
        self.assertEqual(NODE_TO_GRAPH_ID["Semiconductor Fab"], "tsmc_fab")
        self.assertEqual(NODE_TO_GRAPH_ID["Assembly Hub"], "assembly_hub_india")

        # Documented fallback constant
        self.assertEqual(DEFAULT_FALLBACK_GRAPH_ID, "tier1_supplier_a")

        # Edge cases: unmapped strings, empty, None, non-string
        edge_cases = [
            "Unknown Supplier Node",
            "Mysterious Fab 99",
            "",
            "   ",
            None,
            12345,
            {"not": "a string"}
        ]
        for ec in edge_cases:
            res = map_node_to_graph_id(ec)
            self.assertEqual(res, "tier1_supplier_a", f"Edge case {ec!r} failed to resolve to fallback")

        # Propagation through risk scoring without KeyError
        test_signal = {
            "headline": "Unusual disruption at unknown facility",
            "affected_node": "Completely Unmapped Sub-Tier Supplier",
            "severity": 2,
            "is_disruption": True
        }
        risk = calculate_deterministic_risk_score(test_signal)
        self.assertEqual(risk["graph_node_id"], "tier1_supplier_a")

    def test_company_level_pcar_internal_consistency(self):
        """
        Verifies calculate_pcar_by_company() across all 4 named OEMs:
        - Maruti Suzuki
        - Tata Motors
        - Mahindra
        - Hyundai India
        Confirms internal consistency with macro PCaR: company values are strictly
        bounded by the macro aggregate, and sum to the exact theoretical allocation (~33.16%).
        """
        import numpy as np
        from src.module_d_mc import run_monte_carlo
        from src.module_e_pcar import calculate_pcar, calculate_pcar_by_company, OEM_PROFILES

        test_probs = {
            "High (>15%)": 0.55,
            "Medium (5-15%)": 0.30,
            "Low (<5%)": 0.12,
            "None": 0.03,
            "_risk_meta": {"risk_score": 0.68}
        }
        mc_res = run_monte_carlo(test_probs, n_samples=5000, random_seed=42)

        # Baseline macro PCaR
        macro_pcar = calculate_pcar(mc_res, company_name="Entire Indian Automotive Industry")
        self.assertEqual(macro_pcar["company_name"], "Entire Indian Automotive Industry")
        self.assertEqual(macro_pcar["market_share_pct"], 100.0)
        self.assertGreater(macro_pcar["mean_loss_crore"], 0)

        named_oems = ["Maruti Suzuki", "Tata Motors", "Mahindra", "Hyundai India"]
        company_results = {}
        total_company_mean_loss = 0.0
        total_company_base = 0.0
        total_allocation_factor = 0.0

        for oem in named_oems:
            c_pcar = calculate_pcar_by_company(oem, macro_pcar)
            company_results[oem] = c_pcar

            # Basic assertions
            self.assertEqual(c_pcar["company_name"], oem)
            self.assertIn("pcar_95_crore", c_pcar)
            self.assertIn("pcar_99_crore", c_pcar)
            self.assertIn("mean_loss_crore", c_pcar)
            self.assertIn("effective_base_crore", c_pcar)

            # Each company loss must be strictly positive and less than macro aggregate
            self.assertGreater(c_pcar["mean_loss_crore"], 0)
            self.assertLess(c_pcar["mean_loss_crore"], macro_pcar["mean_loss_crore"])
            self.assertLess(c_pcar["pcar_95_crore"], macro_pcar["pcar_95_crore"])
            self.assertLess(c_pcar["effective_base_crore"], macro_pcar["industry_baseline_crore"])

            # Pro-rata formula checks
            alloc = OEM_PROFILES[oem]["market_share"] * OEM_PROFILES[oem]["dependency_ratio"]
            expected_mean = macro_pcar["mean_loss_crore"] * alloc
            self.assertAlmostEqual(c_pcar["mean_loss_crore"], expected_mean, delta=0.05)

            total_company_mean_loss += c_pcar["mean_loss_crore"]
            total_company_base += c_pcar["effective_base_crore"]
            total_allocation_factor += alloc

        # Aggregate bounds:
        # Sum of 4 OEM allocations: Maruti (15.8%) + Tata (6.3%) + Mahindra (4.9%) + Hyundai (6.1%) = ~33.16%
        # The sum of all 4 companies must be strictly bounded below macro industry aggregate
        self.assertLess(total_company_mean_loss, macro_pcar["mean_loss_crore"])
        self.assertLess(total_company_base, macro_pcar["industry_baseline_crore"])

        ratio = total_company_mean_loss / macro_pcar["mean_loss_crore"]
        self.assertAlmostEqual(ratio, total_allocation_factor, places=3)
        self.assertAlmostEqual(ratio, 0.33161, places=2)

    def test_monte_carlo_distribution_honesty_and_reproducibility(self):
        """
        Verifies Monte Carlo engine distribution honesty disclosures,
        reproducibility via fixed random seed, and overridable distribution_source.
        """
        import numpy as np
        from src.module_d_mc import run_monte_carlo
        import src.module_d_mc as d_mc

        # 1. Honest docstring disclosure check
        doc = d_mc.run_monte_carlo.__doc__ or ""
        self.assertIn("calibrated", doc.lower())
        self.assertIn("not fitted", doc.lower())

        # 2. Return dict distribution_source check
        test_probs = {"High (>15%)": 0.5, "Medium (5-15%)": 0.3, "Low (<5%)": 0.15, "None": 0.05}
        mc1 = run_monte_carlo(test_probs, n_samples=2000, random_seed=42)
        self.assertIsInstance(mc1, dict)
        self.assertEqual(mc1["distribution_source"], "calibrated_estimate")
        self.assertEqual(mc1["random_seed"], 42)

        # 3. Seeded reproducibility
        mc2 = run_monte_carlo(test_probs, n_samples=2000, random_seed=42)
        np.testing.assert_array_equal(mc1["samples"], mc2["samples"])

        # 4. Overridable distribution_source (future empirical fit interface)
        mc_emp = run_monte_carlo(test_probs, n_samples=500, random_seed=42, distribution_source="empirical_fit")
        self.assertEqual(mc_emp["distribution_source"], "empirical_fit")


if __name__ == "__main__":
    unittest.main()

