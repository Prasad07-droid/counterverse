"""
Script: generate_architecture_viva_pdf.py
Generates a complete, beautifully formatted PDF Guide for CounterVerse Architecture
and Viva Q&A in Hinglish. Uses pure Python PDF generation (no external libraries).
"""

import os
import sys

def build_pdf():
    output_dir = os.path.join(os.getcwd(), "static", "reports")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "CounterVerse_Architecture_Viva_Guide.pdf")

    # Content structure
    pages_data = [
        # PAGE 1: Architecture Flow & Code Walkthrough
        {
            "title": "COUNTERVERSE: ARCHITECTURE & CODE WALKTHROUGH",
            "subtitle": "Comprehensive Technical Guide (Hinglish) - Page 1",
            "sections": [
                {
                    "heading": "1. Pipeline Overview & Orchestrator (api/main.py)",
                    "lines": [
                        "Input: Unstructured news text -> Output: Financial PCaR in INR Crore + 3-Page PDF Report.",
                        "Core Flow: Ingestion -> SLM/Fast Parser -> Graph Verification -> Causal Risk -> Monte Carlo -> PCaR.",
                        "Orchestrator Endpoints: /api/v1/analyze-headline, /api/v1/simulate, /api/v1/generate-report.",
                        "AI Safety Rule: LLM handles text extraction only; 100% of math/risk calculations are deterministic Python."
                    ]
                },
                {
                    "heading": "2. Ingestion (Module A) & Signal Extraction (Module B)",
                    "lines": [
                        "Module A (data_sources.py): 4-tier failover: GDELT 2.0 API -> Google News RSS -> SQLite Cache -> Static Cache.",
                        "Sanitization: sanitize_headline() scrubs prompt injection keywords and control characters.",
                        "Module B (module_b_slm.py): Two engines: 'fast' (default regex/keyword parser) and 'slm' (local Qwen2.5-0.5B bf16).",
                        "Extracts: disruption_type, affected_node, severity_pct (0-100), duration_days, component, region."
                    ]
                },
                {
                    "heading": "3. Grounding Graph (src/grounding_graph.py)",
                    "lines": [
                        "30 Nodes (7 Countries, 7 Components, 12 Companies, 4 Industries) and 69 Directed Edges in NetworkX DiGraph.",
                        "Integrity Hash: '31f67108669b9208' verified on startup to ensure topological consistency.",
                        "Grounding Logic: Extracted entities must exist in graph. Unverified entities flagged for review, not dropped."
                    ]
                },
                {
                    "heading": "4. Deterministic Risk Engine (Module C: module_c_causal.py)",
                    "lines": [
                        "Formula: Risk = 0.35*EB + 0.25*DR + 0.20*DC + 0.10*TC + 0.10*ED (Score: 0.000 to 1.000).",
                        "EB (Exposure Breadth: 35%): Component lookup; DR (Dependency Ratio: 25%): UN Comtrade import shares + choke points.",
                        "DC (Downstream Criticality: 20%), TC (Tier-1 Centrality: 10%), ED (Exposure Depth: 10% tier hierarchy).",
                        "Bands: HIGH >= 0.60 (Dual-source/replace), MEDIUM 0.45-0.59 (Buffer stock), LOW < 0.45 (Standard watch)."
                    ]
                }
            ]
        },
        # PAGE 2: Monte Carlo, PCaR, and Decisions
        {
            "title": "MONTE CARLO, PCAR ENGINE & REPORT GENERATION",
            "subtitle": "Mathematical & Financial Core (Hinglish) - Page 2",
            "sections": [
                {
                    "heading": "5. Monte Carlo Simulation (Module D: module_d_mc.py)",
                    "lines": [
                        "Runs 10,000 draws with fixed seed=42 (np.random.RandomState(42)) for complete reproducibility.",
                        "Maps risk score to 4 states: High (>15%), Medium (5-15%), Low (<5%), None (0%).",
                        "Samples from calibrated normal distributions, clipped to [0, 100]%.",
                        "Generates production drop percentiles: Mean, Median, P95 Tail, and P99 Worst-case."
                    ]
                },
                {
                    "heading": "6. Procurement Cost at Risk (Module E: module_e_pcar.py)",
                    "lines": [
                        "Macro Baseline: INR 133,814.34 Cr ($16.12B USD at 83.0 INR/USD) from UN Comtrade 2022 HS 8542.",
                        "Company Base Spend = Macro Baseline * Market Share (Maruti 41.7%, Tata 13.9%) * BOM Dependency Ratio.",
                        "PCaR Exposure = (Drop% / 100) * Company Base Spend * Spot Premium Multiplier U[1.3, 2.8].",
                        "Additive Extra Procurement Cost = (Drop% / 100) * Base Spend * (Multiplier - 1.0)."
                    ]
                },
                {
                    "heading": "7. Decision Directives & PDF Generator (Module I: module_i_report.py)",
                    "lines": [
                        "Cost-Adjusted Action: Evaluates Net Benefit = (Mean PCaR * Risk Reduction) - Implementation Cost.",
                        "Action choices: Monitor (0 Cr, 0%), Buffer (15 Cr, 40%, 4 wks), Dual Source (45 Cr, 70%, 12 wks).",
                        "Disagreement Reconciliation: Explicit statement when risk band directive differs from cost-benefit action.",
                        "Pure PDF Compiler: Generates 3-page A4 PDF directly in memory without wkhtmltopdf or heavy binaries."
                    ]
                },
                {
                    "heading": "8. SIAM 2021 Chip Crisis Empirical Calibration",
                    "lines": [
                        "Historical Event: Sept 2021 passenger vehicle production dropped -37.46% YoY (SIAM audited report).",
                        "CounterVerse Model: Posterior Mean drop = -28.24%, P95 tail drop = -41.24%.",
                        "Ground truth falls squarely between Mean and P95 tail (-9.22% vs Mean, +3.78% vs P95)."
                    ]
                }
            ]
        },
        # PAGE 3: Viva & Technical Q&A
        {
            "title": "COUNTERVERSE: VIVA & TECHNICAL Q&A (HINGLISH)",
            "subtitle": "Essential Questions & Answers - Page 3",
            "sections": [
                {
                    "heading": "Q1: CounterVerse traditional tools se alag kaise hai?",
                    "lines": [
                        "Ans: Traditional alerts sirf news dete hain. CounterVerse use NetworkX graph se verify karta hai,",
                        "5-factor deterministic formula se risk score nikalta hai, aur Monte Carlo se real balance-sheet",
                        "PCaR (INR Crore me loss) quantify karta hai specific automakers (Maruti, Tata, etc.) ke liye."
                    ]
                },
                {
                    "heading": "Q2: Risk calculation me LLM kyu use nahi kiya?",
                    "lines": [
                        "Ans: AlMahri et al. (2026) AI Safety Separation principle: LLMs numbers me hallucinate karte hain.",
                        "Isliye SLM sirf text parsing karta hai; 100% mathematical scoring deterministic Python code karta hai."
                    ]
                },
                {
                    "heading": "Q3: 15 Scenarios benchmark aur adversarial test me kya farak hai?",
                    "lines": [
                        "Ans: 15-Scenario benchmark pe fast parser ka Macro F1 0.945 hai (100% benign control specificity).",
                        "Held-out adversarial benchmark (30 scenarios) pe F1 drop hokar 0.631 hota hai, showing model limits."
                    ]
                },
                {
                    "heading": "Q4: Report generator me fake number bug kya tha aur kaise fix hua?",
                    "lines": [
                        "Ans: Purane code me 'mean_drop * 0.5' fake formula tha jo hamesha Monitor ko jitata tha.",
                        "Fix me real OEM financial exposure (mean_loss_crore) pass kiya gaya, jisse high risk me Dual Source jeetta hai."
                    ]
                },
                {
                    "heading": "Q5: System ki 3 sabse badi limitations kya hain?",
                    "lines": [
                        "1. Heuristic OEM BOM dependency ratios (38-45% domain proxies hain, audited company secrets nahi).",
                        "2. Single-event calibration: SIAM 2021 match calibration check hai, out-of-sample statistical validation nahi.",
                        "3. No MILP optimization: Directives stylized guidelines hain, contractually binding procurement schedules nahi."
                    ]
                }
            ]
        }
    ]

    # Render PDF bytes manually
    def escape_pdf(text: str) -> str:
        return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    pdf_objects = []

    def add_obj(content: str) -> int:
        pdf_objects.append(content)
        return len(pdf_objects)

    # 1: Catalog, 2: Outlines
    add_obj("<< /Type /Catalog /Pages 3 0 R >>")
    add_obj("<< /Type /Outlines /Count 0 >>")

    # 3: Pages object (placeholder, will be updated)
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
        stream_lines.append("/F2 14 Tf")
        stream_lines.append(f"50 800 Td ({escape_pdf(pdata['title'])}) Tj")

        # Subtitle
        stream_lines.append("/F1 9 Tf")
        stream_lines.append(f"0 -15 Td ({escape_pdf(pdata['subtitle'])}) Tj")

        # Line separator
        stream_lines.append("ET")
        stream_lines.append("0.2 w")
        stream_lines.append("50 775 m 545 775 l S")
        stream_lines.append("BT")

        current_y = 755
        stream_lines.append(f"50 {current_y} Td")

        for sec in pdata["sections"]:
            # Heading
            stream_lines.append("/F2 10 Tf")
            stream_lines.append(f"({escape_pdf(sec['heading'])}) Tj")
            stream_lines.append("0 -14 Td")
            current_y -= 14

            # Body lines
            stream_lines.append("/F1 8.5 Tf")
            for line in sec["lines"]:
                stream_lines.append(f"({escape_pdf(line)}) Tj")
                stream_lines.append("0 -12 Td")
                current_y -= 12

            # Space between sections
            stream_lines.append("0 -8 Td")
            current_y -= 8

        # Footer
        footer_text = f"CounterVerse Architecture & Viva Guide | Page {page_idx} of 3 | Pure Python Rendered"
        stream_lines.append("ET")
        stream_lines.append("0.2 w")
        stream_lines.append("50 45 m 545 45 l S")
        stream_lines.append("BT")
        stream_lines.append("/F1 8 Tf")
        stream_lines.append(f"50 32 Td ({escape_pdf(footer_text)}) Tj")
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

    # Now update Pages object (obj 3)
    kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    pdf_objects[pages_obj_index] = f"<< /Type /Pages /Kids [{kids_str}] /Count {len(page_obj_ids)} >>"

    # Assemble complete PDF file
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

    print(f"Successfully generated PDF: {output_path} ({len(full_pdf_bytes)} bytes)")

if __name__ == "__main__":
    build_pdf()
