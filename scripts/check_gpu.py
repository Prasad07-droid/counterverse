"""
Phase 0 — GPU smoke test.

Run this AFTER creating the Python 3.11 venv and installing torch from cu128.
Paste the full output into docs/environment.md under "Laptop smoke-test log".

Usage:
    python scripts/check_gpu.py
"""

import sys
import platform


def main():
    print("=" * 60)
    print("Phase 0 — GPU smoke test")
    print("=" * 60)

    # System info
    print(f"\nPython:      {sys.version}")
    print(f"Platform:    {platform.platform()}")

    # PyTorch check
    try:
        import torch
    except ImportError:
        print("\n❌ torch is NOT installed. Install with:")
        print("   pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cu128")
        sys.exit(1)

    print(f"\ntorch:       {torch.__version__}")
    print(f"CUDA avail:  {torch.cuda.is_available()}")

    if not torch.cuda.is_available():
        print("\n❌ CUDA is NOT available to PyTorch.")
        print("   Check: is the cu128 wheel installed? Does nvidia-smi work?")
        sys.exit(1)

    print(f"CUDA ver:    {torch.version.cuda}")
    print(f"cuDNN ver:   {torch.backends.cudnn.version()}")
    print(f"Device name: {torch.cuda.get_device_name(0)}")

    total_vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 2)
    print(f"Total VRAM:  {total_vram:.0f} MiB")

    # bf16 support (Ampere = compute capability >= 8.0)
    cc_major, cc_minor = torch.cuda.get_device_capability(0)
    print(f"Compute cap: {cc_major}.{cc_minor}")
    bf16_ok = cc_major >= 8
    print(f"bf16 native: {'✓' if bf16_ok else '✗ (need Ampere+ for bf16)'}")

    if not bf16_ok:
        print("\n⚠ RTX 3050 Ti should be Ampere (cc 8.6). Something is wrong.")

    # Small tensor operation on GPU
    print("\n--- Small tensor test (bf16 matmul on GPU) ---")
    try:
        a = torch.randn(256, 256, dtype=torch.bfloat16, device="cuda")
        b = torch.randn(256, 256, dtype=torch.bfloat16, device="cuda")
        c = a @ b
        torch.cuda.synchronize()
        print(f"Result shape: {c.shape}, dtype: {c.dtype}, device: {c.device}")
        print("✓ bf16 matmul on GPU succeeded.")
    except torch.cuda.OutOfMemoryError:
        print("❌ OOM on a 256x256 bf16 matmul — something is very wrong with VRAM.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

    # VRAM after test
    allocated = torch.cuda.memory_allocated(0) / (1024 ** 2)
    reserved = torch.cuda.memory_reserved(0) / (1024 ** 2)
    print(f"\nVRAM allocated: {allocated:.1f} MiB")
    print(f"VRAM reserved:  {reserved:.1f} MiB")

    # Cleanup
    del a, b, c
    torch.cuda.empty_cache()

    print("\n" + "=" * 60)
    print("✓ GPU smoke test PASSED. Ready for Phase 0 SLM smoke test.")
    print("=" * 60)


if __name__ == "__main__":
    main()
