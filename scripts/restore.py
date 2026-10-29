# -*- coding: utf-8 -*-
"""
scripts/restore.py
==================
Automated restore utility for Causal AI and Small Language Models for Supply Chain Disruption Forecasting and Procurement Cost at Risk Estimation for Indian Automotive Component Sourcing persistent state archives.
Extracts:
  - data/processed/headline_cache.db
  - data/processed/grounding_graph_custom.json
  - data/decision_queue.json
  - static/reports/

Usage:
  python scripts/restore.py [--archive <path>]
  If --archive is omitted, the latest archive in data/backups/ is restored.
"""

import os
import sys
import argparse
import tarfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def find_latest_backup() -> Path:
    """Finds the most recent backup archive in data/backups/."""
    backup_dir = PROJECT_ROOT / "data" / "backups"
    if not backup_dir.exists():
        raise FileNotFoundError(f"Backup directory not found: {backup_dir}")

    archives = list(backup_dir.glob("counterverse_backup_*.tar.gz"))
    if not archives:
        raise FileNotFoundError(f"No backup archives found in {backup_dir}")

    archives.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return archives[0]


def restore_backup(archive_path: str = None) -> None:
    """Restores files from a Causal AI and Small Language Models for Supply Chain Disruption Forecasting and Procurement Cost at Risk Estimation for Indian Automotive Component Sourcing backup archive."""
    if archive_path:
        src = Path(archive_path).resolve()
        if not src.exists():
            raise FileNotFoundError(f"Specified archive does not exist: {src}")
    else:
        src = find_latest_backup()

    print(f"\n[*] Restoring Causal AI and Small Language Models for Supply Chain Disruption Forecasting and Procurement Cost at Risk Estimation for Indian Automotive Component Sourcing state from archive:\n    {src}")

    restored_count = 0
    with tarfile.open(src, "r:gz") as tar:
        # Security check: ensure no member has parent directory traversal
        for member in tar.getmembers():
            target_path = (PROJECT_ROOT / member.name).resolve()
            if not str(target_path).startswith(str(PROJECT_ROOT)):
                raise ValueError(f"Unsafe archive path detected: {member.name}")

        tar.extractall(path=PROJECT_ROOT)
        for member in tar.getmembers():
            restored_count += 1
            print(f"  [+] Restored: {member.name}")

    print(f"\n[OK] Restore complete! Total entries restored: {restored_count}\n")


def main():
    parser = argparse.ArgumentParser(description="Restore Causal AI and Small Language Models for Supply Chain Disruption Forecasting and Procurement Cost at Risk Estimation for Indian Automotive Component Sourcing persistent state.")
    parser.add_argument("--archive", "-a", help="Path to backup archive (.tar.gz)", default=None)
    args = parser.parse_args()

    try:
        restore_backup(args.archive)
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Restore failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
