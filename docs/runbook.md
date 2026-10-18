# CounterVerse Operational Runbook
====================================

This document establishes operational procedures, mitigation workflows, and disaster-recovery runbooks for the CounterVerse automotive semiconductor disruption simulation platform.

---

## 1. GDELT / RSS News Ingestion Outage

### Incident Symptom
- Live headline ingestion fails due to upstream API rate limits, HTTP 500s, or DNS timeout from `api.gdeltproject.org`.

### Automated System Behavior
CounterVerse executes a resilient 4-tier fallback hierarchy ([`src/data_sources.py`](file:///c:/Users/Dattaprasad/Videos/sem%207/src/data_sources.py)):
1. **Tier 1 (GDELT 2.0 API):** Primary live query with 6-second timeout.
2. **Tier 2 (Google News RSS):** Automatically triggered on Tier 1 failure (`RSS_LIVE`).
3. **Tier 3 (SQLite Cache):** Pulls cached headlines from `data/processed/headline_cache.db` with an explicit `is_stale: true` flag and human-readable staleness warning.
4. **Tier 4 (Static Fallback):** Read-only immutable headlines with explicit `OFFLINE DEMO DATA` badge.

### Operator Actions
1. Check source health via `GET /api/v1/headlines`.
2. Inspect `sources_status` in response payload (`gdelt`, `rss`, `sqlite`, `twitter`).
3. If SQLite cache requires manual refresh, run:
   ```bash
   python -c "from src.data_sources import fetch_headlines_resilient; print(fetch_headlines_resilient(force_refresh=True))"
   ```
4. Verify the frontend displays the amber **Stale Cache / Offline Demo** indicator.

---

## 2. Stale UN Comtrade Trade Cache

### Incident Symptom
- `GET /api/v1/health` reports status `degraded` with reason `"Comtrade baseline cache is stale"`.

### Automated System Behavior
- The PCaR financial engine falls back to the audited 2022 annual baseline:
  - HS 8542 (Semiconductor ICs): ₹133,814.34 Crore
  - HS 8112 (Upstream Rare Metals): ₹552.84 Crore
- Responses clearly carry `data_provenance: {"status": "sourced_from_comtrade", "vintage": "2022 Full Year"}`.

### Operator Actions
1. Verify network access to UN Comtrade API v1.
2. If new annual data is available, update `data/processed/comtrade_india_baseline.json`:
   ```bash
   python scripts/fetch_comtrade_data.py
   ```
3. Restart the API to refresh in-memory baselines.

---

## 3. SLM / GPU Unavailable (CPU Fast Mode Fallback)

### Incident Symptom
- `GET /api/v1/health` indicates `gpu_available: false` and `slm_available: false`.

### Automated System Behavior
- The system automatically engages `extract_signal_fast()` ([`src/module_b_slm.py`](file:///c:/Users/Dattaprasad/Videos/sem%207/src/module_b_slm.py)), a deterministic keyword-and-rule heuristic that parses disruption events, components, severity, and durations in <5 milliseconds without GPU or VRAM requirements.
- The UI and API response header `engine_used` flags `"fast"` or `"fast (fallback)"`.

### Operator Actions
- If running in Docker or cloud environment without NVIDIA drivers, CPU fast mode is the expected, verified configuration.
- To re-enable SLM on machines with NVIDIA GPUs:
  ```bash
  python scripts/check_gpu.py
  # Ensure CUDA 12.x and PyTorch with CUDA are installed
  pip install torch --index-url https://download.pytorch.org/whl/cu128
  ```

---

## 4. Malicious or Prompt-Injected Headlines

### Incident Symptom
- An untrusted user inputs adversarial prompts or script tags into `/api/v1/analyze-headline` or the War Room headline input.

### Automated System Behavior
- Input is sanitized by `sanitize_headline()` ([`src/data_sources.py`](file:///c:/Users/Dattaprasad/Videos/sem%207/src/data_sources.py)):
  - Enforces length limits (minimum 5, maximum 500 characters).
  - Strips HTML tags (`<script>`, `<img>`, etc.).
  - Strips prompt-injection phrases (`"ignore previous instructions"`, `"system prompt"`, `"reveal secret"`).
  - Normalizes non-ASCII characters.

### Operator Actions
- Check application logs for sanitized inputs:
  ```bash
  # Search structured logs for sanitize warnings
  grep "Sanitized" data/logs/api.log
  ```

---

## 5. Grounding Graph Hash Mismatch / Corruption

### Incident Symptom
- `GET /api/v1/health` returns status `unhealthy` with reason `"Graph hash mismatch: expected 31f67108669b9208"`.

### Automated System Behavior
- GraphRAG grounding requires strict topological integrity. If custom overlays corrupt the canonical 30-node bipartite structure, the healthcheck transitions to `unhealthy`.

### Operator Actions
1. Verify current graph state against golden tests:
   ```bash
   pytest tests/test_golden.py -v
   ```
2. If disk overlay was corrupted, delete or reset the custom overlay:
   ```bash
   rm data/processed/grounding_graph_custom.json
   ```
3. Re-run `test_golden.py` to confirm hash `31f67108669b9208` is restored.

---

## 6. Failed PDF Report Generation

### Incident Symptom
- `POST /api/v1/generate-report` returns HTTP 500 or report URL fails to download.

### Automated System Behavior
- The pure ReportLab raw PDF 1.4 renderer in `src/module_i_report.py` formats A4 executive dossiers without external GTK/system binaries.

### Operator Actions
1. Verify write permissions on `static/reports/`:
   ```bash
   mkdir -p static/reports
   ```
2. Verify disk space on the host machine.
3. Test report generation standalone:
   ```bash
   python -c "from src.module_i_report import generate_report; print(generate_report({'headline': 'Test disruption'}))"
   ```
4. Verify PDF retention cleanup has not purged active reports:
   ```bash
   python -c "from src.module_i_report import cleanup_old_reports; print(cleanup_old_reports())"
   ```

---

## 7. Rotating JWT Signing Secret & Passwords

### Procedure
1. Generate a cryptographically secure 256-bit secret:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
2. Update environment variables on host or `.env`:
   ```bash
   COUNTERVERSE_JWT_SECRET="<new_secure_secret>"
   COUNTERVERSE_ADMIN_PASSWORD="<new_admin_password>"
   COUNTERVERSE_OFFICER_PASSWORD="<new_officer_password>"
   COUNTERVERSE_ANALYST_PASSWORD="<new_analyst_password>"
   ```
3. Restart the FastAPI service:
   ```bash
   # Existing tokens signed with the old secret will automatically be invalidated (401)
   docker compose restart api
   ```
4. Re-issue tokens via `POST /api/v1/token`.

---

## 8. Frontend Rebuild & Redeployment

### Procedure
1. Navigate to the project root:
   ```bash
   cd "c:\Users\Dattaprasad\Videos\sem 7"
   ```
2. Recompile TypeScript and bundle assets with Vite:
   ```bash
   npm run build
   ```
3. Verify that `dist/index.html` and bundled JavaScript (`dist/assets/*.js`) were generated with 0 errors.
4. If testing in development mode with live API:
   ```bash
   # Ensure .env has VITE_API_URL pointing to the backend
   echo "VITE_API_URL=http://localhost:8000" > .env
   npm run dev
   ```

---

## 9. Backup & Restore Procedures

### Creating a Timestamped Backup
Run the backup script to archive SQLite headline caches, graph overlays, decision audit logs, and PDF dossiers:
```bash
python scripts/backup.py
# Output archive saved to: data/backups/counterverse_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Restoring from Backup
To restore the platform to the state of the latest backup archive:
```bash
python scripts/restore.py
# Or specify a specific archive:
python scripts/restore.py --archive data/backups/counterverse_backup_20261018_220000.tar.gz
```

### Automated Round-Trip Verification
Verify backup integrity via automated test:
```bash
pytest tests/test_phase8_operations.py -k test_backup_restore_roundtrip -v
```

---

## 10. Rollback to Previous Version

### Code Rollback
```bash
git checkout <previous_commit_or_tag>
npm run build
pytest tests/ -v
```

### State Rollback
1. Stop running API and dashboard processes.
2. Restore data archive matching the previous version tag:
   ```bash
   python scripts/restore.py --archive data/backups/<matching_backup>.tar.gz
   ```
3. Start the application services and verify `/api/v1/health`.
