# -*- coding: utf-8 -*-
"""
tests/test_phase8_operations.py
===============================
Validates Phase 8 Deployment, Backup, and Operations requirements:
1. Health & readiness diagnostics:
   - /api/v1/health distinguishes healthy / degraded / unhealthy with reasons.
   - X-Request-ID middleware assigns and preserves request IDs.
2. Automated backup and restore:
   - scripts/backup.py archives databases, overlays, queue, and PDF reports.
   - scripts/restore.py unpacks and restores state cleanly.
3. Report retention policy:
   - cleanup_old_reports() limits max report count and purges aged files.
"""

import os
import time
import shutil
import tarfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.module_i_report import cleanup_old_reports
from scripts.backup import create_backup
from scripts.restore import restore_backup


@pytest.fixture
def client():
    return TestClient(app)


# ════════════════════════════════════════════════════════════════
# 1. HEALTHCHECK & REQUEST ID OBSERVABILITY
# ════════════════════════════════════════════════════════════════

def test_health_diagnostics_and_reasons(client):
    """Verify /api/v1/health returns status, reasons, and diagnostics."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] in ("healthy", "degraded", "unhealthy")
    assert "reasons" in data
    assert isinstance(data["reasons"], list)
    assert "graph_integrity" in data
    assert "graph_hash" in data
    assert data["graph_hash"] == "31f67108669b9208"

    # Verify request ID header is returned
    assert "X-Request-ID" in resp.headers or "x-request-id" in resp.headers
    req_id = resp.headers.get("X-Request-ID") or resp.headers.get("x-request-id")
    assert len(req_id) >= 8


def test_request_id_preservation(client):
    """Verify incoming X-Request-ID header is preserved in the response."""
    custom_id = "test-custom-req-id-8899"
    resp = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert resp.status_code == 200
    returned_id = resp.headers.get("X-Request-ID") or resp.headers.get("x-request-id")
    assert returned_id == custom_id


# ════════════════════════════════════════════════════════════════
# 2. BACKUP & RESTORE ROUND-TRIP TEST
# ════════════════════════════════════════════════════════════════

def test_backup_restore_roundtrip(tmp_path):
    """
    Creates state, archives with backup script, mutates/deletes state,
    restores with restore script, and verifies identical restoration.
    """
    project_root = Path(__file__).resolve().parent.parent

    # 1. Ensure test state exists
    test_queue_file = project_root / "data" / "decision_queue.json"
    assert test_queue_file.exists(), "decision_queue.json should exist for backup test"
    with open(test_queue_file, "r", encoding="utf-8") as f:
        original_queue_content = f.read()

    # 2. Run backup to temporary archive
    archive_dest = tmp_path / "test_backup.tar.gz"
    created_path = create_backup(output_path=str(archive_dest))
    assert created_path.exists()
    assert tarfile.is_tarfile(created_path)

    try:
        # 3. Mutate file
        with open(test_queue_file, "w", encoding="utf-8") as f:
            f.write('[{"test_mutation": true}]')

        with open(test_queue_file, "r", encoding="utf-8") as f:
            assert "test_mutation" in f.read()

        # 4. Restore from archive
        restore_backup(archive_path=str(created_path))

        # 5. Verify restored content matches original
        with open(test_queue_file, "r", encoding="utf-8") as f:
            restored_content = f.read()

        assert restored_content == original_queue_content
        assert "test_mutation" not in restored_content

    finally:
        # Guarantee original content is restored in case of assertion failure
        with open(test_queue_file, "w", encoding="utf-8") as f:
            f.write(original_queue_content)


# ════════════════════════════════════════════════════════════════
# 3. REPORT RETENTION CLEANUP POLICY TEST
# ════════════════════════════════════════════════════════════════

def test_report_retention_policy(tmp_path):
    """Verify cleanup_old_reports() limits report count and removes excess files."""
    test_reports_dir = tmp_path / "reports"
    test_reports_dir.mkdir(parents=True, exist_ok=True)

    # Create 8 dummy PDF files with staggered timestamps
    now = time.time()
    for i in range(8):
        f = test_reports_dir / f"test_report_{i}.pdf"
        f.write_bytes(b"%PDF-1.4 dummy content %%EOF")
        # Set modification time: i hours ago
        os.utime(f, (now - i * 3600, now - i * 3600))

    files_before = list(test_reports_dir.glob("*.pdf"))
    assert len(files_before) == 8

    # Apply retention policy: max_count = 5
    deleted_count = cleanup_old_reports(reports_dir=test_reports_dir, max_count=5, max_age_days=30)
    assert deleted_count == 3

    files_after = list(test_reports_dir.glob("*.pdf"))
    assert len(files_after) == 5

    # Apply retention policy: max_age_days = 0 (delete anything older than 0 seconds)
    deleted_aged = cleanup_old_reports(reports_dir=test_reports_dir, max_count=10, max_age_days=0)
    assert deleted_aged == 5

    files_final = list(test_reports_dir.glob("*.pdf"))
    assert len(files_final) == 0
