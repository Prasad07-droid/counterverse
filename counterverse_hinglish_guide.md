# 🔥 CounterVerse — Complete Hinglish Study Guide (Viva Ready!)

---

## 🏗️ SYSTEM KYA HAI? (Big Picture)

**CounterVerse** ek **Causal AI system** hai jo **Indian Automotive Semiconductor supply chain** ki disruptions predict karta hai.

> **Simple words mein:** Koi news headline aao jaise *Taiwan mein earthquake aya* — system batata hai kitna financial loss hoga aur kya karna chahiye.

---

## 📊 COMPLETE EXECUTION FLOW

`
News Headline
    ↓
[Module A] Ingestion (GDELT/RSS/SQLite)
    ↓
[Module B] Signal Extraction (Fast Rule-Parser / Qwen2.5 SLM)
    ↓
[Grounding Graph] Entity Verification (NetworkX — 30 nodes, 69 edges)
    ↓
[Module C] Risk Scoring (Deterministic 5-Factor Formula)
    ↓
[Module C] Causal Impact Simulation (4 state probabilities)
    ↓
[Module D] Monte Carlo (10,000 draws, seed=42)
    ↓
[Module E] PCaR — Procurement Cost-at-Risk
    ↓
[Module I] Report/PDF Generation
    ↓
React Dashboard (War Room / Financial Exposure / Governance)
`

---

## 📁 MODULE-BY-MODULE DEEP DIVE

---

### 🅰️ MODULE A — module_a_ingest.py (Data Ingestion)

**Kya karta hai?** News headlines ko 3 sources se laata hai:
1. **GDELT 2.0** — Global news database (real-time)
2. **RSS Feeds** — Google News RSS
3. **SQLite Cache** — headline_cache.db mein store karta hai

**Flow:**
`
GDELT API → fetch headlines (max 8 records, 3 retries, 6s timeout)
     ↓
Sanitize (HTML strip, unicode normalize, max 512 chars)
     ↓
SQLite mein cache (24-hour TTL)
     ↓
Static fallback if all fail
`

---

### 🅱️ MODULE B — module_b_slm.py (Signal Extraction) ⭐ MOST IMPORTANT

**2 engines hain:**

#### Engine 1: Fast Rule-Based Parser (Default)
Keyword matching se classify karo.
event_type: EARTHQUAKE / FIRE / STRIKE / TARIFF
affected_node: Taiwan / China / South Korea
severity_pct: 10-60%, duration_days: 7-180 days

**Output Signal Dict:**
`json
{
   is_disruption: true,
  affected_node: Taiwan,
  event_type: EARTHQUAKE,
  severity_pct: 35.0,
  duration_days: 60,
  component: IC_ADVANCED,
  region: APAC
}
`

#### Engine 2: SLM (Qwen2.5-0.5B-Instruct) — GPU mode
- Small Language Model, GPU pe chalta hai (RTX 3050 Ti)
- Zyada accurate but slow, bfloat16 precision

---

### 🕸️ GROUNDING GRAPH — grounding_graph.py

**Technology:** NetworkX library
**Graph:** 30 nodes, 69 edges
**Node types:** SUPPLIER, OEM, COUNTRY, COMPONENT

Agar entity graph mein nahi → human_review flag lagega.

---

### 🅲 MODULE C — module_c_causal.py (Risk Scoring) ⭐ MOST ASKED

#### Risk Score Formula:
`
R = 0.35·EB + 0.25·DR + 0.20·DC + 0.10·TC + 0.10·ED
`

| Factor | Weight | Matlab |
|--------|--------|--------|
| EB — Event Baseline | 0.35 | Event type kitna serious hai |
| DR — Dependency Ratio | 0.25 | India kitna depend karta hai |
| DC — Disruption Criticality | 0.20 | Component kitna critical hai |
| TC — Trade Concentration | 0.10 | HHI — single supplier dependency |
| ED — Event Duration | 0.10 | Disruption kitne din chalega |

**Risk Levels:**
`
R >= 0.60  → HIGH   → Dual-source / Replace immediately
0.45-0.60  → MEDIUM → Increase safety stock
R < 0.45   → LOW    → Monitor operations
`

#### Causal Impact Simulation:
Bayesian Network (pgmpy library) → 4 states: HIGH/MEDIUM/LOW/NONE probabilities

---

### 🅳 MODULE D — module_d_mc.py (Monte Carlo) ⭐

10,000 baar random simulation, seed=42 (reproducibility ke liye)

**Output:**
- mean_drop_pct: average production drop
- p95_drop_pct: 95th percentile
- p99_drop_pct: 99th percentile (worst case)

---

### 🅴 MODULE E — module_e_pcar.py (PCaR) ⭐⭐ FINANCIAL CORE

**PCaR = Procurement Cost-at-Risk**
`
PCaR = Drop% × Baseline × Share × Dependency × Premium[1.3,2.8]
`

| Variable | Matlab |
|----------|--------|
| Drop% | Monte Carlo se production drop |
| Baseline | UN Comtrade 2022 (Rs 1,33,814 Cr for ICs) |
| Share | Company ka market share |
| Dependency | Component pe dependency ratio |
| Premium | Spot market premium Uniform(1.3, 2.8) |

**4 OEMs:** Maruti Suzuki, Hyundai India, Tata Motors, Mahindra

---

### 📄 MODULE I — module_i_report.py

HTML → WeasyPrint → PDF → /static/reports/ mein save
Trigger: POST /api/v1/generate-report

---

## 🔌 FASTAPI — api/main.py (Orchestrator)

| Endpoint | Method | Kya karta hai |
|----------|--------|---------------|
| /api/v1/health | GET | Server alive? |
| /api/v1/analyze-headline | POST | Full pipeline |
| /api/v1/signal | POST | Signal extract only |
| /api/v1/simulate | POST | Risk + Monte Carlo |
| /api/v1/calculate-pcar | POST | PCaR only |
| /api/v1/backtest/siam | GET | SIAM backtest |
| /api/v1/generate-report | POST | PDF banao |
| /api/v1/currencies | GET | USD/INR rate |
| /token | POST | JWT auth token |

---

## 🎨 FRONTEND — React + TypeScript + Vite

**Tech:** React 18, Vite bundler, TailwindCSS, Lucide React

**3 views:**
1. **War Room** (ExecutiveWarRoom.tsx) — Real-time dashboard, headline input
2. **Financial Exposure** (FinancialExposureView.tsx) — 4 OEM PCaR charts
3. **Governance** (GovernanceView.tsx) — Risk policies, compliance

---

## 📊 DATA SOURCES

| Source | Data | Use |
|--------|------|-----|
| UN Comtrade 2022 | Import/Export | Baseline values |
| SIAM | Indian auto production | OEM market shares |
| GDELT 2.0 | Global news | Real-time headlines |
| FRED DEXINUS | USD/INR rate | Currency conversion |
| GSCPI | Supply chain pressure | Macro calibration |

---

## 🔒 SECURITY

- JWT Authentication (python-jose)
- Rate Limiting: 100 req/min (slowapi)
- Input Validation: sanitize_headline() — XSS, injection prevent

---

## 📈 SIAM BACKTEST

2021 chip crisis actual drop: ~37.46%
System prediction: ~35-40%
→ Calibration proof, bona fide validation nahi (N=1)

---

## ❓ CROSS QUESTIONS & ANSWERS (Viva Ready!)

**Q1: System ka naam CounterVerse kyun?**
Counter = disruption counter karna. Verse = universe of scenarios — multiple what-if scenarios simulate karta hai.

**Q2: Monte Carlo mein seed=42 kyun?**
Reproducibility ke liye. Same input → same output every time. ML best practice hai.

**Q3: Risk formula weights kaise decide kiye?**
Domain expert assumptions. EB = 0.35 highest kyunki event type sabse direct indicator. Limitation: real data se fit nahi kiya.

**Q4: PCaR mein Uniform(1.3, 2.8) kyun?**
Supply chain crisis mein spot premium 1.3x-2.8x jaata hai (ACMA/SIAM reports). Uniform isliye kyunki exact distribution unknown hai.

**Q5: Grounding Graph — 30 nodes, 69 edges kyun?**
Indian auto semiconductor ecosystem ke key players: TSMC, Samsung, SK Hynix, + Indian OEMs (Maruti, Hyundai, Tata, M&M). 69 edges = supply relationships.

**Q6: SLM kyun, GPT-4 kyun nahi?**
1. Cost — API expensive. 2. Privacy — sensitive data cloud pe nahi. 3. Latency — local faster. 4. Qwen2.5-0.5B — RTX 3050 Ti pe bhi chalti hai.

**Q7: Fast parser vs SLM accuracy?**
Fast parser ~75-80%, SLM ~85-90%. Production mein fast parser (speed ke liye).

**Q8: P95 aur P99 real-world use?**
P95 = safety stock planning. P99 = insurance/hedging, CFO ko worst-case dikhana.

**Q9: Causal AI kyun? Normal ML se fark?**
ML = correlation sikhta hai. Causal AI = causation model karta hai. Bayesian Network = causal DAG, domain knowledge encode karta hai, data se nahi sikhta.

**Q10: SIAM backtest — validated ya calibrated?**
Calibrated, validated nahi. Validated = statistically proven. N=1 event se validation nahi hoti.

**Q11: SQLite kyun, PostgreSQL nahi?**
Caching ke liye SQLite kafi. Simple, no concurrent writes. Production scale pe PostgreSQL/Redis.

**Q12: Neo4j Docker mein kyun hai jab NetworkX use karte hain?**
Future scaling ke liye. Phase 1 = NetworkX in-memory. Phase 2 = Neo4j persistent DB. Dependency injection pattern — migration easy hoga.

**Q13: HHI kya hai?**
Herfindahl-Hirschman Index = Trade Concentration.
HHI = sum(share_i squared)
Taiwan se 90% → HHI=0.81 (very concentrated = high risk).
Diverse → HHI low = lower risk.

**Q14: Rate limiting kyun?**
100 req/min — DDoS se bacha. SLM GPU-intensive, unlimited requests = server crash.

**Q15: Frontend + Backend deploy kaise?**
Backend → Render/Railway (Python). Frontend → Vercel (dist/ folder). Communication via REST + CORS middleware.

**Q16: bfloat16 kyun?**
float32 = 4 bytes → 2GB VRAM. bfloat16 = 2 bytes → 1GB VRAM. Accuracy same, memory half. RTX 3050 Ti (4GB) pe comfortably fit.

**Q17: GDELT down ho toh?**
Fallback: 1→GDELT (3 retries) 2→RSS feeds 3→SQLite cache 4→Hardcoded static headlines. Graceful degradation.

**Q18: PDF kaise generate hota hai?**
HTML template + data → WeasyPrint → PDF → /static/reports/ → API download URL return karta hai.

---

## 🎯 IMPORTANT FORMULAS

`
1. Risk Score:
   R = 0.35·EB + 0.25·DR + 0.20·DC + 0.10·TC + 0.10·ED
   HIGH >= 0.60 | MEDIUM 0.45-0.60 | LOW < 0.45

2. PCaR:
   PCaR = Drop% × Baseline × Share × Dependency × Premium[1.3,2.8]

3. HHI:
   HHI = sum(share_i squared)   [0=diverse, 1=monopoly]

4. Monte Carlo:
   mean = (1/N) × sum(drop_i)   [N=10,000, seed=42]
   P95 = 95th percentile of sorted drops
`

---

## 🏆 QUICK SUMMARY TABLE

| Module | File | Tech | Output |
|--------|------|------|--------|
| Ingestion | module_a_ingest.py | GDELT, SQLite | Clean headlines |
| Signal Extract | module_b_slm.py | Rule-parser/Qwen2.5 | Signal dict |
| Grounding | grounding_graph.py | NetworkX | Verified/Unverified |
| Risk Score | module_c_causal.py | Math formula | R score + level |
| Causal Sim | module_c_causal.py | pgmpy Bayesian | 4 probabilities |
| Monte Carlo | module_d_mc.py | NumPy random | mean/P95/P99 |
| PCaR | module_e_pcar.py | Financial math | Rs Crore per OEM |
| Report | module_i_report.py | WeasyPrint | PDF |
| API | api/main.py | FastAPI | REST endpoints |
| Frontend | src/ | React+Vite+TS | Dashboard |

---

**Ab toh viva mein full confidence ke saath jao! 🚀**
