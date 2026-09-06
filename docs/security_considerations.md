# Security Considerations — CounterVerse

## Covered in This Implementation

### 1. Prompt Injection Mitigation
- All GDELT headlines pass through `sanitize_headline()` in 
  `src/data_sources.py` before SLM ingestion
- 12 injection pattern regexes detect instruction-override attempts
- Headlines truncated to 500 chars max to prevent context flooding
- Flagged headlines logged server-side; sanitized version passed to SLM
- Limitation: Regex patterns catch known attack formats; novel 
  adversarial prompts may evade detection

### 2. Zero-Credential Architecture
- No API keys required: UN Comtrade public preview + GDELT free tier
- HuggingFace model (Qwen2.5-0.5B) is open-weights, no token needed
- `.env.example` provided for future extensibility without exposing secrets

### 3. User-Facing Error Sanitization
- All dashboard exceptions caught and logged server-side
- Users see generic "An error occurred" message, not raw stack traces
- Internal file paths and exception details never exposed to UI

### 4. Grounding Graph Integrity
- SHA-256 hash check on graph structure at load time
- Detects accidental or unauthorized modification to the 30-node/69-edge 
  static knowledge graph
- Hash mismatch logged as ERROR before any verification runs

### 5. Dependency Pinning
- `requirements.txt` pins all cloud dependencies to exact versions
- Reduces risk of compromised package updates on Streamlit Cloud

## Explicitly Out of Scope (with Rationale)

| Item | Why Out of Scope |
|---|---|
| Authentication / User Login | Single-user academic demo — no PII collected |
| Rate limiting on dashboard | Streamlit Cloud handles infra-level rate limits |
| Full adversarial robustness | Beyond scope of 0.5B model academic project |
| CVE scanning pipeline | Manual review appropriate for academic project scale |
| Data encryption at rest | No sensitive data stored — only public trade statistics |

## Residual Risks (Acknowledged)

1. Novel prompt injection formats not covered by regex patterns
2. GDELT public API has no SLA — malformed responses handled by fallback
3. Static grounding graph does not auto-update on supply chain changes
