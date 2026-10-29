# -*- coding: utf-8 -*-
"""
scripts/backup.py
=================
Automated backup utility for Causal AI and Small Language Models for Supply Chain Disruption Forecasting and Procurement Cost at Risk Estimation for Indian Automotive Component Sourcing persistent state:
  1. data/processed/headline_cache.db (SQLite headline cache)
  2. data/processed/grounding_graph_custom.json (Graph overlay)
  3. data/decision_queue.json (Officer actions and audit log)
  4. static/reports/ (Generated executive PDF dossiers)

Produces a compressed, timestamped tar.gz archive in data/backups/.
Usage:
  python scripts/backup.py [--output <path>]
"""

import os
import sys
import argparse
import tarfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BACKUP_TARGETS = [
    Path("data/processed/headline_cache.db"),
    Path("data/processed/grounding_graph_custom.json"),
    Path("data/decision_queue.json"),
    Path("static/reports"),
]


def create_backup(output_path: str = None) -> Path:
    """Creates a tar.gz archive of existing Causal AI and Small Language Models for Supply Chain Disruption Forecasting and Procurement Cost at Risk Estimation for Indian Automotive Component Sourcing state files."""
    backup_dir = PROJECT_ROOT / "data" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    if output_path:
        dest = Path(output_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = backup_dir / f"counterverse_backup_{timestamp}.tar.gz"

    archived_count = 0
    with tarfile.open(dest, "w:gz") as tar:
        for rel_target in BACKUP_TARGETS:
            full_path = PROJECT_ROOT / rel_target
            if full_path.exists():
                tar.add(full_path, arcname=str(rel_target))
                archived_count += 1
                print(f"  [+] Archived: {rel_target}")
            else:
                print(f"  [-] Skipped (missing): {rel_target}")

    print(f"\n[OK] Backup successfully created at:\n     {dest}")
    print(f"     Total items archived: {archived_count}\n")
    return dest


def main():
    parser = argparse.ArgumentParser(description="Backup Causal AI and Small Language Models for Supply Chain Disruption Forecasting and Procurement Cost at Risk Estimation for Indian Automotive Component Sourcing persistent state.")
    parser.add_argument("--output", "-o", help="Target archive path (.tar.gz)", default=None)
    args = parser.parse_args()

    try:
        create_backup(args.output)
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Backup failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
