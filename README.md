# Causal simulation for Indian automotive-component sourcing (BE mini project)

**Vidyavardhini's College of Engineering & Technology, Vasai**  
Department of Computer Science & Engineering (Data Science)  
Team of 4 — module owners below (fill names before the panel)

This repository is a **scenario-based causal simulation**: a small language model extracts disruption signals from public headlines, a **pgmpy Bayesian network** encodes a fixed expert DAG, Monte Carlo produces a **distribution** of production-drop outcomes, and a Streamlit app shows **Procurement Cost at Risk** under labeled **assumptions**.

It is **not** a real-time trained forecast, **not** connected to any company’s procurement system, and **not** a source of audited financials.

## Current phase

**Phase -1 (data source verification) is in progress.**  
`data/raw/*/SOURCE.md` records PRIMARY vs FALLBACK decisions.  
**Do not start Phase 2 downloads or Phase 3 fine-tuning until Phase 0 GPU smoke tests pass.**  
**Do not start Phase 1 dummy dashboard until the blockers below are answered.**

## Blockers (all resolved 2026-09-04)

1. ~~**GDELT DOC 2.0 ArtList is not a 2017–present headline dump.**~~ → **Option C**: ArtList for ~90-day rolling window + hand-collected ~140–210 headlines around 7 calendar events. See [SOURCE.md](data/raw/gdelt_headlines/SOURCE.md).
2. ~~**System Python is 3.9.13.**~~ → **Python 3.11 venv** confirmed. See [environment.md](docs/environment.md).
3. ~~**HS 8541/8542 bulk: Comtrade needs registration.**~~ → **Free Comtrade key** is acceptable (data scripts only, not dashboard runtime).
4. Several "sample rows" are schemas or press tables; CSV binaries were not committed (and must not be). Phase 2 pastes a live row into each SOURCE.md after download.

**Next step: Phase 0** — create Python 3.11 venv, run `check_gpu.py`, then `smoke_test_slm.py`.

## Hardware

Laptop: Windows, RTX **3050 Ti 4 GB**. Use `torch.bfloat16`. Cap **Qwen2.5-0.5B-Instruct**. No flash-attn. CPU for pgmpy, Monte Carlo, Streamlit.

Recorded 2026-09-04: driver CUDA **13.0**, `nvcc` **11.2** (ignore for pip), VRAM 4096 MiB. See `docs/environment.md`.

## Pipeline (fixed)

Module A data → B SLM (GPU) → C Bayesian network (CPU) → D Monte Carlo (CPU) → E PCaR (CPU) → F Streamlit (`app/dashboard.py`).

## Module owners (fill in)

| Module | Branch | Owner |
|--------|--------|--------|
| A Data | `feat/module-a-data` | TBD |
| B SLM | `feat/module-b-slm` | TBD |
| C Causal | `feat/module-c-causal` | TBD |
| D–E Monte Carlo + PCaR | `feat/module-d-mc` / `feat/module-e-pcar` | TBD |
| F Dashboard | `feat/module-f-dashboard` | TBD |

No direct pushes to `main`. Merge a module only when its `tests/test_*.py` passes.

## Setup (after blockers)

```text
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements-local.txt
python scripts/check_gpu.py
```

Colab: use `requirements-colab.txt` and pin whatever torch Colab already installed.

Raw CSVs, PDFs, and model weights are **gitignored**. Regeneration steps live in each `SOURCE.md`.

## Honesty for the viva

- Sensitivity ±20% on CPTs is a **robustness check on assumptions**, not a confidence interval.
- PCaR numbers are **simulated under documented assumptions**.
- Small number of well-documented precedent events (chip shortage, Shanghai, Red Sea, …) — say this before you are asked.
