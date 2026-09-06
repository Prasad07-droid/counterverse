"""
Phase 0 — SLM smoke test (5-headline inference).

Loads Qwen/Qwen2.5-0.5B-Instruct in bf16, runs 5 hardcoded headlines
through the JSON-extraction prompt, and reports:
  - Load time, peak VRAM
  - Per-headline inference time
  - JSON parse success/failure for each

Run this AFTER check_gpu.py passes.
Paste the full output into docs/environment.md under "Laptop smoke-test log".

Usage:
    python scripts/smoke_test_slm.py
"""

import json
import sys
import time
from pathlib import Path


# --- 5 real headlines for smoke test (sourced from public news) ---
SMOKE_HEADLINES = [
    "Maruti Suzuki halts production at Gurugram plant due to semiconductor shortage",
    "India semiconductor imports surge 23% as chip crisis deepens",
    "Shanghai lockdown disrupts auto parts supply chain across Asia",
    "China restricts gallium and germanium exports citing national security",
    "Red Sea shipping crisis forces Indian automakers to reroute supply chains",
]

SYSTEM_PROMPT = """You are a supply-chain disruption signal extractor.
Given a news headline about the Indian automotive component supply chain,
extract a JSON object with exactly these fields:
{
  "component": "<affected component or material>",
  "region": "<geographic region involved>",
  "severity": <integer 1-3, where 1=low, 2=medium, 3=high>,
  "lead_time_weeks": <estimated weeks of impact, integer>
}
Return ONLY the JSON object, no other text."""


def main():
    print("=" * 60)
    print("Phase 0 — SLM smoke test (5 headlines)")
    print("=" * 60)

    # Import torch and check CUDA
    try:
        import torch
    except ImportError:
        print("❌ torch not installed. Run check_gpu.py first.")
        sys.exit(1)

    if not torch.cuda.is_available():
        print("❌ CUDA not available. Run check_gpu.py first.")
        sys.exit(1)

    device = "cuda"
    print(f"\ntorch {torch.__version__}, CUDA {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    vram_total = torch.cuda.get_device_properties(0).total_memory / (1024 ** 2)
    print(f"VRAM: {vram_total:.0f} MiB")

    # Import transformers
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        print("❌ transformers not installed. pip install transformers")
        sys.exit(1)

    # Load model
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    print(f"\nLoading {model_name} in bf16...")
    t0 = time.time()

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="cuda",
            trust_remote_code=True,
        )
    except torch.cuda.OutOfMemoryError:
        print("❌ OOM loading Qwen2.5-0.5B in bf16. This should NOT happen on 4 GB.")
        print("   Close other GPU processes and retry.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        sys.exit(1)

    load_time = time.time() - t0
    vram_after_load = torch.cuda.memory_allocated(0) / (1024 ** 2)
    print(f"Load time:   {load_time:.1f}s")
    print(f"VRAM in use: {vram_after_load:.0f} MiB")

    # Inference loop
    print(f"\n--- Running {len(SMOKE_HEADLINES)} headlines ---\n")
    results = []

    for i, headline in enumerate(SMOKE_HEADLINES):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": headline},
        ]

        # Tokenize using chat template
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(text, return_tensors="pt").to(device)

        t1 = time.time()
        try:
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=150,
                    do_sample=False,
                    temperature=1.0,
                    pad_token_id=tokenizer.eos_token_id,
                )
        except torch.cuda.OutOfMemoryError:
            print(f"  [{i+1}] ❌ OOM during generation. Reduce max_new_tokens.")
            results.append({"headline": headline, "status": "OOM"})
            continue

        gen_time = time.time() - t1

        # Decode only the new tokens
        new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        raw_output = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

        # Try to parse JSON
        parsed = None
        parse_ok = False
        try:
            parsed = json.loads(raw_output)
            parse_ok = True
        except json.JSONDecodeError:
            # Try to extract JSON from the output (model might add text around it)
            try:
                start = raw_output.index("{")
                end = raw_output.rindex("}") + 1
                parsed = json.loads(raw_output[start:end])
                parse_ok = True
            except (ValueError, json.JSONDecodeError):
                pass

        status = "✓ parsed" if parse_ok else "✗ parse fail"
        print(f"  [{i+1}] {status} | {gen_time:.2f}s | {headline[:60]}...")
        if parse_ok:
            print(f"       → {json.dumps(parsed, ensure_ascii=False)}")
        else:
            print(f"       → raw: {raw_output[:120]}")

        results.append({
            "headline": headline,
            "status": status,
            "time_s": round(gen_time, 2),
            "parsed": parsed,
            "raw": raw_output,
        })

    # Summary
    peak_vram = torch.cuda.max_memory_allocated(0) / (1024 ** 2)
    parse_count = sum(1 for r in results if r.get("parsed") is not None)

    print(f"\n--- Summary ---")
    print(f"Parsed OK:     {parse_count}/{len(SMOKE_HEADLINES)}")
    print(f"Peak VRAM:     {peak_vram:.0f} MiB")
    print(f"Model load:    {load_time:.1f}s")

    if parse_count == len(SMOKE_HEADLINES):
        print("\n✓ SLM smoke test PASSED. Ready for Phase 1.")
    elif parse_count > 0:
        print(f"\n⚠ {len(SMOKE_HEADLINES) - parse_count} parse failures — acceptable for zero-shot baseline.")
        print("  Review outputs; these feed the Phase 3 zero-shot F1 evaluation.")
    else:
        print("\n❌ All headlines failed to parse. Check the prompt or model.")

    # Cleanup
    del model
    torch.cuda.empty_cache()

    print("\n" + "=" * 60)
    print("Paste everything above into docs/environment.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
