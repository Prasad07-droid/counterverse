"""
Script: generate_complete_viva_pdf.py
Generates the Complete Master Viva Q&A Guide for CounterVerse in Hinglish.
Covers every single possible viva/interview question across 6 structured A4 pages.
Uses pure Python PDF 1.4 compiler (Zero external dependencies).
"""

import os
import sys

def build_complete_viva_pdf():
    output_dir = os.path.join(os.getcwd(), "static", "reports")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "CounterVerse_Complete_Viva_Master_Guide.pdf")

    # 6 Full Pages of Structured Viva Content in Hinglish
    pages_data = [
        # PAGE 1: Intro, Scope & Problem Statement
        {
            "title": "COUNTERVERSE: MASTER VIVA Q&A GUIDE (HINGLISH)",
            "subtitle": "Part 1: Project Overview, Problem Statement & Industry Scope",
            "sections": [
                {
                    "q": "Q1: Project ka 1-line elevator pitch kya hai?",
                    "ans": [
                        "Ans: CounterVerse ek AI-powered supply chain risk quantification system hai jo unstructured news",
                        "headlines ko graph verification, deterministic 5-factor scoring, aur Monte Carlo simulation ke",
                        "through specific Indian automotive OEMs (Maruti, Tata, etc.) ke Procurement Cost at Risk (PCaR in Cr) me convert karta hai."
                    ]
                },
                {
                    "q": "Q2: System ka exact input aur output kya hai?",
                    "ans": [
                        "Ans: Exact Input: News headline (string 5-500 chars), Target OEM (string), Inference Engine ('fast' ya 'slm').",
                        "Exact Output: Disruption signal dictionary, Graph entity verification report, Deterministic Risk Score (0-1),",
                        "Monte Carlo production drop percentiles (Mean, P95, P99), Financial PCaR in INR Cr, aur 3-Page Executive PDF Report."
                    ]
                },
                {
                    "q": "Q3: Scope me konsa sector, components aur OEMs covered hain?",
                    "ans": [
                        "Ans: Sector: Indian Automotive Industry (Passenger Vehicles primary).",
                        "Corridor: Gallium/Germanium (HS 8112) -> Silicon Wafers/ICs (HS 8542) -> Microcontrollers -> ECUs & Sensors.",
                        "OEMs: Maruti Suzuki (41.7%), Hyundai (14.6%), Tata Motors (13.9%), Mahindra (11.2%), Entire Industry (100%)."
                    ]
                },
                {
                    "q": "Q4: CounterVerse Google Alerts ya traditional NLP tools se alag kaise hai?",
                    "ans": [
                        "Ans: Traditional NLP sirf keyword alert deta hai ('China export ban'). Usse ye pata nahi chalta ki kya sach me",
                        "Indian auto supply chain hit hogi aur kitna financial loss hoga. CounterVerse entity grounding karta hai,",
                        "real UN Comtrade trade flows model karta hai, aur CFO/CSCO ko balance-sheet Value-at-Risk (INR Cr) deta hai."
                    ]
                },
                {
                    "q": "Q5: System explicitly kya cheezein exclude karta hai (Out of Scope)?",
                    "ans": [
                        "Ans: 1. IIP macroeconomic time-series forecasting nahi karta. 2. Proprietary OEM ERP/BOM access nahi karta.",
                        "3. Pearl's do-calculus causal discovery observational data se nahi karta (asserted expert graph hai).",
                        "4. Conventional silicon MCUs gallium se nahi bante - Ga/Ge compound semiconductors ke liye benchmarked hai."
                    ]
                },
                {
                    "q": "Q6: Target users kaun hain aur unhe kya decision support milta hai?",
                    "ans": [
                        "Ans: Target: Chief Supply Chain Officers (CSCO), Chief Procurement Officers (CPO), Automotive Risk Managers.",
                        "Decision: Strategic buffer stock badhana (15 Cr holding cost) vs Alternate supplier qualify karna (45 Cr cost)."
                    ]
                }
            ]
        },
        # PAGE 2: Architecture & Pipeline Mechanics
        {
            "title": "COUNTERVERSE: MASTER VIVA Q&A GUIDE (HINGLISH)",
            "subtitle": "Part 2: Architecture, AI Safety & Graph Verification Mechanics",
            "sections": [
                {
                    "q": "Q7: End-to-end pipeline architecture ka flow samjhao.",
                    "ans": [
                        "Ans: 1. News Ingestion (GDELT/RSS/SQLite) -> 2. Sanitization (regex against prompt injection) ->",
                        "3. Signal Extraction (Fast parser/SLM Qwen) -> 4. Graph Grounding (NetworkX 30-node DiGraph) ->",
                        "5. Deterministic 5-Factor Risk Scoring -> 6. Monte Carlo Simulation (10,000 draws) ->",
                        "7. PCaR Financial Allocation Engine -> 8. Decision Support Directive & 3-Page A4 PDF Generation."
                    ]
                },
                {
                    "q": "Q8: 'AI Safety Architectural Separation Principle' kya hai?",
                    "ans": [
                        "Ans: AlMahri et al. (2026) paper se inspired: SLM ka role sirf unstructured English text parsing tak restricted hai.",
                        "Zero percent risk scores ya rupee values LLM se calculate hoti hain. 100% mathematical scoring,",
                        "graph checks, Monte Carlo draws, aur financial allocations deterministic Python code me execute hote hain."
                    ]
                },
                {
                    "q": "Q9: Fast Parser aur SLM Qwen2.5-0.5B me kya difference hai? Default konsa hai?",
                    "ans": [
                        "Ans: Fast Parser: Deterministic regex/keyword taxonomy parser. CPU pe ~1ms leta hai, zero GPU required.",
                        "SLM: Local Qwen2.5-0.5B-Instruct running on GPU via PyTorch bfloat16. High semantic understanding.",
                        "Default 'fast' rakha gaya hai taaki pura system lightweight server ya CPU-only environment me bina crash ke chale."
                    ]
                },
                {
                    "q": "Q10: Grounding Graph me kitne nodes aur edges hain? Inka purpose kya hai?",
                    "ans": [
                        "Ans: NetworkX DiGraph me 30 Nodes aur 69 Edges hain. 7 Countries, 7 Components, 12 Companies, 4 Industries.",
                        "Purpose: Extracted entities ko verify karna taaki LLM fake supply connections na banaye.",
                        "Agar node graph me hai toh verified=True, nahi toh unverified flag hota hai for human review (signal drop nahi hota)."
                    ]
                },
                {
                    "q": "Q11: Graph Integrity Hash '31f67108669b9208' ka kya role hai?",
                    "ans": [
                        "Ans: Ye graph topology ka SHA-256 fingerprint hai. App launch pe graph initialize hone par calculate hota hai.",
                        "Agar koi graph definition file tamper kare ya edge missing ho, hash mismatch ho jayega aur /health error dega."
                    ]
                },
                {
                    "q": "Q12: Ingestion layer me news sources fail ho jayein toh system kaise handle karta hai?",
                    "ans": [
                        "Ans: 4-tier resilient hierarchy: 1. Live GDELT 2.0 API -> 2. Agar fail/429 rate limit ho toh Google News RSS ->",
                        "3. Agar offline ho toh SQLite local cache (headline_cache.db) -> 4. Static curated fallback headlines in code."
                    ]
                }
            ]
        },
        # PAGE 3: Mathematical Modeling & Risk Scoring
        {
            "title": "COUNTERVERSE: MASTER VIVA Q&A GUIDE (HINGLISH)",
            "subtitle": "Part 3: 5-Factor Deterministic Risk Engine & Trade Baselines",
            "sections": [
                {
                    "q": "Q13: Deterministic Risk Formula kya hai aur iske weights kya hain?",
                    "ans": [
                        "Ans: Formula: Risk Score = 0.35*EB + 0.25*DR + 0.20*DC + 0.10*TC + 0.10*ED (Range: 0.000 to 1.000).",
                        "EB (Exposure Breadth: 35%), DR (Dependency Ratio: 25%), DC (Downstream Criticality: 20%),",
                        "TC (Tier-1 Centrality: 10%), ED (Exposure Depth: 10%). Weights expert-asserted engineering constants hain."
                    ]
                },
                {
                    "q": "Q14: Dependency Ratio (DR) me UN Comtrade trade data kaise use hota hai?",
                    "ans": [
                        "Ans: Formula: DR = (S_direct + S_transit) + C_upstream * [1.0 - (S_direct + S_transit)] * W_unhedged.",
                        "S_direct: Direct import share (China to India ICs = 31.4%). S_transit: Hong Kong transit route (24.6%).",
                        "C_upstream: Monopoly concentration penalty (China Ga/Ge = 0.90, Taiwan = 0.70). W_unhedged = 0.75."
                    ]
                },
                {
                    "q": "Q15: Exposure Breadth (EB) aur Downstream Criticality (DC) kaise calculate hote hain?",
                    "ans": [
                        "Ans: EB: Component lookup (Ga/Ge = 0.90, ICs = 0.85, Sensors = 0.55), modulated by headline severity factor.",
                        "DC: Production halt hone ki criticality (Ga/Ge/IC/ECU = 0.95, Sensors = 0.65), also modulated by severity."
                    ]
                },
                {
                    "q": "Q16: Exposure Depth (ED) ka tier-based lookup kya hai?",
                    "ans": [
                        "Ans: Upstream choke points ko penalize karta hai: Tier-3 Raw Materials (Gallium/Germanium) = 1.00,",
                        "Tier-2 Semiconductors/Wafers/MCUs/ECUs = 0.75, Tier-1 Assemblies/Sensors = 0.25, Fallback = 0.50."
                    ]
                },
                {
                    "q": "Q17: Risk bands aur directives kya hain?",
                    "ans": [
                        "Ans: Score >= 0.60: HIGH Risk -> 'Replace Supplier / Qualify Dual-Sourcing Immediately'.",
                        "Score 0.45 - 0.59: MEDIUM Risk -> 'Increase Safety Stock & Active Weekly Monitoring'.",
                        "Score < 0.45: LOW Risk -> 'Maintain Standard Operations & Routine Watch'."
                    ]
                },
                {
                    "q": "Q18: Posterior probability mapping (simulate_causal_impact) kya karta hai?",
                    "ans": [
                        "Ans: Risk score ko 4 categorical states me convert karta hai: High (>15% drop), Medium (5-15%), Low (<5%), None (0%).",
                        "Ye 4 state probabilities Monte Carlo simulation ke sampling distribution ke liye prior banati hain."
                    ]
                }
            ]
        },
        # PAGE 4: Stochastic Simulation & Financial PCaR
        {
            "title": "COUNTERVERSE: MASTER VIVA Q&A GUIDE (HINGLISH)",
            "subtitle": "Part 4: Monte Carlo Simulation & Financial PCaR Engine",
            "sections": [
                {
                    "q": "Q19: Monte Carlo Simulation me kitne draws aur seed use hote hain?",
                    "ans": [
                        "Ans: Default 10,000 draws use hote hain (configurable 100 to 1,000,000) with fixed seed = 42.",
                        "np.random.RandomState(42) ensure karta hai ki same headline pe hamesha identical, reproducible distribution aaye."
                    ]
                },
                {
                    "q": "Q20: Monte Carlo ka sampling logic kya hai?",
                    "ans": [
                        "Ans: Har draw me pehle posterior probabilities se 1 state pick hoti hai, fir us state ke Normal distribution se",
                        "production drop percentage draw hota hai: High (mean 20-36%, std 3.5), Medium (mean 10%, std 2.0),",
                        "Low (mean 2%, std 1.0), None (0%). Sabhi samples ko [0, 100]% range me clip kiya jata hai."
                    ]
                },
                {
                    "q": "Q21: Procurement Cost at Risk (PCaR) ka exact formula kya hai?",
                    "ans": [
                        "Ans: Company Base Spend = Macro Baseline * Market Share * BOM Dependency Ratio.",
                        "Company PCaR = (Drop% / 100) * Company Base Spend * Uniform[1.3, 2.8] (Spot Multiplier).",
                        "Extra Procurement Cost (Additive) = (Drop% / 100) * Base Spend * (Multiplier - 1.0)."
                    ]
                },
                {
                    "q": "Q22: Macro Baseline INR 133,814.34 Crore kahan se aaya?",
                    "ans": [
                        "Ans: UN Comtrade 2022 Full Year India trade records for HS 8542 (Electronic Integrated Circuits).",
                        "Dollar value: $16.12 Billion USD converted at 83.0 INR/USD. Upstream Gallium HS 8112 baseline: 552.84 Cr."
                    ]
                },
                {
                    "q": "Q23: 4 OEMs ke market shares aur BOM dependency ratios kya hain?",
                    "ans": [
                        "Ans: Market Share (SIAM FY24): Maruti (41.7%), Hyundai (14.6%), Tata (13.9%), Mahindra (11.2%).",
                        "Dependency Ratios: Maruti (38%), Hyundai (42%), Tata (45%), Mahindra (44%).",
                        "Honesty Disclosure: Dependency ratios heuristic proxies hain (electronics intensity), audited BOM filings nahi."
                    ]
                },
                {
                    "q": "Q24: Spot Multiplier Uniform[1.3, 2.8] kyu use kiya gaya hai?",
                    "ans": [
                        "Ans: Supply chain shock ke time broker spot market me microcontrollers 30% se 180% premium pe trade hote hain.",
                        "Uniform[1.3, 2.8] range is extreme short-term cost volatility ko capture karti hai."
                    ]
                }
            ]
        },
        # PAGE 5: Decisions, Benchmarking & SIAM Backtest
        {
            "title": "COUNTERVERSE: MASTER VIVA Q&A GUIDE (HINGLISH)",
            "subtitle": "Part 5: Decision Support, Model Evaluation & Empirical Backtest",
            "sections": [
                {
                    "q": "Q25: Cost-Adjusted Recommendation (compute_cost_adjusted_recommendation) kaise work karti hai?",
                    "ans": [
                        "Ans: 3 actions ka Net Financial Benefit compare karta hai: Net Benefit = (Mean PCaR * Risk Reduction) - Cost.",
                        "1. Monitor & Maintain: Cost 0 Cr, 0% reduction. 2. Buffer Inventory: Cost 15 Cr, 40% reduction, 4 wks lead time.",
                        "3. Qualify Dual Source: Cost 45 Cr, 70% reduction, 12 wks lead time. Maximum net benefit wala option select hota hai."
                    ]
                },
                {
                    "q": "Q26: Agar Risk Band Directive aur Cost-Adjusted Action differ karein toh report kya karti hai?",
                    "ans": [
                        "Ans: Report dono decisions print karti hai aur explicit Reconciliation Sentence deti hai:",
                        "'The risk band indicates <directive>. The cost-adjusted comparison selects <action> because its net benefit is",
                        "<X> Cr versus <Y> Cr for <other>. Costs and reductions are illustrative model assumptions.'"
                    ]
                },
                {
                    "q": "Q27: Synthesized Benchmark (15 scenarios) ke evaluation results kya hain?",
                    "ans": [
                        "Ans: 15 scenarios (11 Disruptions, 4 Benign Controls):",
                        "Fast Parser: Precision 0.900, Recall 1.000, Macro F1 0.945 (100% Specificity on benign news).",
                        "SLM Qwen: Precision 0.877, Recall 1.000, Macro F1 0.933 (100% Specificity on benign news)."
                    ]
                },
                {
                    "q": "Q28: Held-out Adversarial Benchmark (30 scenarios) pe F1 kyu drop hua?",
                    "ans": [
                        "Ans: Adversarial benchmark pe Fast Parser ka Macro F1 drop hokar 0.631 (Precision 0.486) ho jata hai.",
                        "Reason: Complex syntaxes, ambiguous double negatives aur unseen phrasing pe rule parser false alarms deta hai.",
                        "Ye honest engineering validation hai jo model ke genuine real-world limitations ko demonstrate karta hai."
                    ]
                },
                {
                    "q": "Q29: SIAM September 2021 Chip Crisis backtest me model ne kaisa perform kiya?",
                    "ans": [
                        "Ans: SIAM Historical Ground Truth: Sept 2021 passenger vehicle production dropped -37.46% YoY.",
                        "Model Estimate: Posterior Mean drop was -28.24%, P95 tail drop was -41.24%.",
                        "Ground truth (-37.46%) model ke confidence interval [Mean, P95] ke andar capture hua (-9.22% vs Mean, +3.78% vs P95)."
                    ]
                },
                {
                    "q": "Q30: Global Sensitivity Analysis (10,000 draws) ka kya result raha?",
                    "ans": [
                        "Ans: Formula constants (EB, DC, TC, ED) ko +/-20% perturb karne par baseline score 0.752 tha.",
                        "10,000 runs me se 100% runs HIGH risk band (>= 0.60) me hi rahe (min perturbed score = 0.693).",
                        "Isse prove hota hai ki ranking noise aur weight perturbations ke against robust hai."
                    ]
                }
            ]
        },
        # PAGE 6: Code Upgrades, Limitations & Examiner Traps
        {
            "title": "COUNTERVERSE: MASTER VIVA Q&A GUIDE (HINGLISH)",
            "subtitle": "Part 6: Recent Code Fixes, Core Limitations & Examiner Traps",
            "sections": [
                {
                    "q": "Q31: module_i_report.py me hal hi me kya bug fix kiya gaya?",
                    "ans": [
                        "Ans: Bug: Purane code me 'pcar_mean_crore = mean_drop * 0.5' hardcoded tha. Drop % ko 0.5 se multiply karke fake Cr",
                        "bana diya tha, jisse Buffer (-9 Cr) aur Dual Source (-34.5 Cr) hamesha Monitor (0 Cr) se haar jaate the.",
                        "Fix: Fake formula delete karke actual OEM exposure mean_loss_crore pass kiya. Ab high risk me Dual Source jeetta hai."
                    ]
                },
                {
                    "q": "Q32: PDF report generation pure in-memory kyu design ki gayi?",
                    "ans": [
                        "Ans: wkhtmltopdf ya Headless Chrome binaries deployment me fail ho jaate hain. Custom pure Python PDF 1.4",
                        "compiler likha gaya hai jo raw byte buffers likhta hai. Zero external binary dependency, instant generation."
                    ]
                },
                {
                    "q": "Q33: Model ki top 5 genuine limitations kya hain (Honest Disclosure)?",
                    "ans": [
                        "Ans: 1. No physical inventory depletion: shocks graph hops pe instantaneously propagate hote hain (no SimPy buffer delay).",
                        "2. Closed-system fallacy: aerospace ya defense se cross-industry chip bidding ignore karta hai.",
                        "3. Heuristic OEM BOM dependency ratios (38-45%): audited contracts nahi hain.",
                        "4. UN Comtrade trade data 2022 vintage hai (lagged by 12-24 months).",
                        "5. Single-event calibration: SIAM 2021 match parameter calibration hai, out-of-sample prediction nahi."
                    ]
                },
                {
                    "q": "Q34: Examiner Trap: 'Kya aapka system causal inference Pearl's do-calculus use karta hai?'",
                    "ans": [
                        "Ans: Defense: 'Nahi Sir. Hum observational data se DAG discover nahi karte. Hamara graph ek expert-curated",
                        "domain dependency graph hai. Causal term hum interventional shock propagation (what-if shock) ke sense me use karte hain.'"
                    ]
                },
                {
                    "q": "Q35: Examiner Trap: 'Gallium ban hone se Silicon MCUs kaise affect ho sakte hain?'",
                    "ans": [
                        "Ans: Defense: 'Conventional silicon MCUs gallium se nahi bante. But automotive power electronics, radar sensors,",
                        "aur EV fast chargers Gallium Nitride (GaN) pe depend karte hain. System compound semiconductor corridor test karta hai.'"
                    ]
                },
                {
                    "q": "Q36: Examiner Trap: 'Aapka 94.5% F1 real-world market news pe valid hai?'",
                    "ans": [
                        "Ans: Defense: 'Sir, 94.5% F1 hamare 15-scenario primary benchmark pe hai. Lekin humne adversarial 30-scenario test",
                        "bhi kiya jahan F1 63.1% par drop hota hai. Humne actively document kiya hai ki complex syntaxes pe rule parser degrade hota hai.'"
                    ]
                }
            ]
        }
    ]

    def escape_pdf(text: str) -> str:
        return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    pdf_objects = []

    def add_obj(content: str) -> int:
        pdf_objects.append(content)
        return len(pdf_objects)

    # 1: Catalog, 2: Outlines
    add_obj("<< /Type /Catalog /Pages 3 0 R >>")
    add_obj("<< /Type /Outlines /Count 0 >>")

    pages_obj_index = len(pdf_objects)
    add_obj("")

    # Fonts: 4: Helvetica, 5: Helvetica-Bold, 6: Courier
    add_obj("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    add_obj("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    add_obj("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    page_obj_ids = []

    for page_idx, pdata in enumerate(pages_data, start=1):
        stream_lines = []
        stream_lines.append("BT")

        # Header Title
        stream_lines.append("/F2 13 Tf")
        stream_lines.append(f"45 802 Td ({escape_pdf(pdata['title'])}) Tj")

        # Subtitle
        stream_lines.append("/F1 8.5 Tf")
        stream_lines.append(f"0 -14 Td ({escape_pdf(pdata['subtitle'])}) Tj")

        # Line separator
        stream_lines.append("ET")
        stream_lines.append("0.3 w")
        stream_lines.append("45 778 m 550 778 l S")
        stream_lines.append("BT")

        current_y = 760
        stream_lines.append(f"45 {current_y} Td")

        for sec in pdata["sections"]:
            # Question in Bold
            stream_lines.append("/F2 9 Tf")
            stream_lines.append(f"({escape_pdf(sec['q'])}) Tj")
            stream_lines.append("0 -12 Td")
            current_y -= 12

            # Answer in Regular Helvetica
            stream_lines.append("/F1 8 Tf")
            for line in sec["ans"]:
                stream_lines.append(f"({escape_pdf(line)}) Tj")
                stream_lines.append("0 -10.5 Td")
                current_y -= 10.5

            # Gap between questions
            stream_lines.append("0 -6 Td")
            current_y -= 6

        # Footer
        footer_text = f"CounterVerse Complete Viva Master Guide | Page {page_idx} of 6 | Academic Defense Ready"
        stream_lines.append("ET")
        stream_lines.append("0.3 w")
        stream_lines.append("45 42 m 550 42 l S")
        stream_lines.append("BT")
        stream_lines.append("/F1 7.5 Tf")
        stream_lines.append(f"45 30 Td ({escape_pdf(footer_text)}) Tj")
        stream_lines.append("ET")

        content_stream = "\n".join(stream_lines)
        stream_len = len(content_stream.encode('latin1', errors='replace'))
        stream_obj = f"<< /Length {stream_len} >>\nstream\n{content_stream}\nendstream"
        content_obj_id = add_obj(stream_obj)

        page_obj = (
            f"<< /Type /Page /Parent 3 0 R /MediaBox [0 0 595.28 841.89] "
            f"/Resources << /Font << /F1 4 0 R /F2 5 0 R /F3 6 0 R >> >> "
            f"/Contents {content_obj_id} 0 R >>"
        )
        page_obj_id = add_obj(page_obj)
        page_obj_ids.append(page_obj_id)

    # Update Pages object
    kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    pdf_objects[pages_obj_index] = f"<< /Type /Pages /Kids [{kids_str}] /Count {len(page_obj_ids)} >>"

    header = "%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body_parts = []
    offsets = [0]
    current_offset = len(header.encode('latin1'))

    for i, obj_str in enumerate(pdf_objects, start=1):
        offsets.append(current_offset)
        obj_bytes = f"{i} 0 obj\n{obj_str}\nendobj\n".encode('latin1', errors='replace')
        body_parts.append(obj_bytes)
        current_offset += len(obj_bytes)

    xref_offset = current_offset
    xref = [f"xref\n0 {len(pdf_objects) + 1}\n0000000000 65535 f \n"]
    for off in offsets[1:]:
        xref.append(f"{off:010d} 00000 n \n")
    xref_str = "".join(xref)

    trailer = f"trailer\n<< /Size {len(pdf_objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"

    full_pdf_bytes = header.encode('latin1') + b"".join(body_parts) + xref_str.encode('latin1') + trailer.encode('latin1')

    with open(output_path, "wb") as f:
        f.write(full_pdf_bytes)

    print(f"Successfully generated Master Viva Guide PDF: {output_path} ({len(full_pdf_bytes)} bytes, 6 Pages)")

if __name__ == "__main__":
    build_complete_viva_pdf()
