# Environment record

Verification date: 2026-09-04  
Machine: Windows (ASUS TUF F15), NVIDIA GeForce RTX 3050 Ti Laptop GPU, 4096 MiB VRAM

## Commands run

```
nvidia-smi
nvcc --version
python --version
```

## Recorded output (this laptop)

| Item | Value |
|------|--------|
| nvidia-smi driver | 581.29 |
| nvidia-smi CUDA Version (max supported by driver) | 13.0 |
| GPU | NVIDIA GeForce RTX 3050 Ti Laptop GPU (WDDM) |
| VRAM | 4096 MiB |
| nvcc | Cuda compilation tools, release 11.2, V11.2.152 |
| System Python | 3.9.13 |

## How to read these numbers

- `nvidia-smi` “CUDA Version” is the **highest** CUDA the **driver** can run. It is not the CUDA toolkit used by a PyTorch wheel.
- Local `nvcc` 11.2 is an old toolkit install. **Do not compile PyTorch from source against it.** Use official pip wheels.
- Official PyTorch stable (checked 2026-07-27 get-started page): **Stable 2.7.0**, CUDA options include **12.6 and 12.8**, and **Python 3.10–3.14 is required** on Windows.

## RESOLVED — Python venv (decided 2026-09-04, updated same day)

System Python is **3.9.13**. Current Windows CUDA PyTorch wheels need **Python >= 3.10**.

**Original plan:** Python 3.11 venv. **Actual:** Python 3.11 was **not installed** on this machine (only 3.9 and 3.14). Tried Python **3.14.7** — torch installed clean.

**Second change:** `torch==2.7.0` has **no wheel for Python 3.14**. Available cu128 versions: 2.9.0, 2.9.1, 2.10.0, 2.11.0. Installed **latest stable**.

### Actual installed stack (pip-tested 2026-09-04)

| Package | Version | Note |
|---------|---------|------|
| Python | 3.14.7 | venv via `py -3.14 -m venv .venv` |
| torch | 2.11.0+cu128 | `--index-url https://download.pytorch.org/whl/cu128` |
| torchvision | 0.26.0+cu128 | matched by pip |
| torchaudio | 2.11.0+cu128 | matched by pip |
| numpy | 2.5.2 | installed by torch |
| networkx | 3.6.1 | installed by torch |
| pillow | 12.3.0 | installed by torch |

Driver CUDA 13.0 can load a cu128 runtime ✓

### Setup commands (copy-paste for teammates)

```
py -3.14 -m venv .venv
.venv\Scripts\activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements-local.txt
python scripts/check_gpu.py
```

## Comtrade API key (decided 2026-09-04)

✅ **Free Comtrade registration is acceptable.** API key is used only in data download scripts (`scripts/`), **never** as a runtime dependency of the Streamlit dashboard.

## Colab

Colab supplies its own CUDA + torch. Use `requirements-colab.txt` only after a fresh Colab `!nvidia-smi` and `import torch; print(torch.__version__, torch.version.cuda)` and pin what Colab actually installed.

## Phase 0 status

Venv created and torch installed. `scripts/check_gpu.py` and `scripts/smoke_test_slm.py` outputs should be pasted below.

### Laptop smoke-test log

**`check_gpu.py` output (2026-09-04):**
```
============================================================
Phase 0 — GPU smoke test
============================================================

Python:      3.14.7 (tags/v3.14.7:823f032, Aug  5 2026, 10:51:32) [MSC v.1944 64 bit (AMD64)]
Platform:    Windows-11-10.0.26200-SP0

torch:       2.11.0+cu128
CUDA avail:  True
CUDA ver:    12.8
cuDNN ver:   91900
Device name: NVIDIA GeForce RTX 3050 Ti Laptop GPU
Total VRAM:  4096 MiB
Compute cap: 8.6
bf16 native: ✓

--- Small tensor test (bf16 matmul on GPU) ---
Result shape: torch.Size([256, 256]), dtype: torch.bfloat16, device: cuda:0
✓ bf16 matmul on GPU succeeded.

VRAM allocated: 8.5 MiB
VRAM reserved:  22.0 MiB

============================================================
✓ GPU smoke test PASSED. Ready for Phase 0 SLM smoke test.
============================================================
```

**`smoke_test_slm.py` output (2026-09-04):**
```
============================================================
Phase 0 — SLM smoke test (5 headlines)
============================================================

torch 2.11.0+cu128, CUDA 12.8
GPU: NVIDIA GeForce RTX 3050 Ti Laptop GPU
VRAM: 4096 MiB

Loading Qwen/Qwen2.5-0.5B-Instruct in bf16...

Load time:   1323.5s
VRAM in use: 942 MiB

--- Running 5 headlines ---

  [1] ✓ parsed | 2.26s | Maruti Suzuki halts production at Gurugram plant due to semi...
       → {"component": "semiconductor", "region": "Gurugram", "severity": 3, "lead_time_weeks": 0}
  [2] ✓ parsed | 1.56s | India semiconductor imports surge 23% as chip crisis deepens...
       → {"component": "semiconductor", "region": "India", "severity": 3, "lead_time_weeks": 6}
  [3] ✓ parsed | 1.54s | Shanghai lockdown disrupts auto parts supply chain across As...
       → {"component": "auto parts", "region": "Asia", "severity": 3, "lead_time_weeks": 0}
  [4] ✓ parsed | 1.70s | China restricts gallium and germanium exports citing nationa...
       → {"component": "gallium and germanium", "region": "China", "severity": 3, "lead_time_weeks": 0}
  [5] ✓ parsed | 1.82s | Red Sea shipping crisis forces Indian automakers to reroute ...
       → {"component": "automobile components", "region": "Indian automotive component supply chain", "severity": 3, "lead_time_weeks": 6}

--- Summary ---
Parsed OK:     5/5
Peak VRAM:     958 MiB
Model load:    1323.5s

✓ SLM smoke test PASSED. Ready for Phase 1.
```

### Colab smoke-test log

_Pending._

---

## Data Freshness Matrix

| Data Source | Current Vintage | Update Frequency | Staleness Risk |
|---|---|---|---|
| GDELT Live Feed | Real-time (~15 min rolling) | Continuous | Low — auto-refreshes |
| UN Comtrade Baseline (HS 8542) | 2022 calendar year | Annual (12-18 month lag) | Medium — 2023-24 not reflected |
| UN Comtrade Baseline (HS 8112) | 2022 calendar year | Annual (12-18 month lag) | Medium — China gallium ban (Aug 2023) post-dates baseline |
| Grounding Graph (NetworkX) | 2023–2024 disclosures | Manual update required | Medium — static snapshot |
| SIAM Benchmark | FY2021-22 (Sep 2021 peak) | N/A — historical fixed point | Low — historical reference, not live |
| SLM Model Weights | Qwen2.5-0.5B-Instruct (2024) | Manual retrain required | Low for current scope |

**Critical Note:** The China Gallium/Germanium export restriction (August 2023) post-dates the 2022 UN Comtrade baseline. The DR formula for HS 8112 therefore uses pre-restriction trade shares. This underestimates current Chinese dependency for gallium. This limitation is acknowledged and documented.

