import urllib.request
import json
import time
from pathlib import Path

from datetime import datetime, timezone
import urllib.error

# Partner codes: 0 = World, 156 = China, 490 = Taiwan, 410 = South Korea, 344 = Hong Kong, 392 = Japan, 702 = Singapore, 842 = USA
PARTNER_NAMES = {
    0: "World Total",
    156: "China",
    490: "Taiwan",
    410: "South Korea",
    344: "Hong Kong",
    392: "Japan",
    702: "Singapore",
    842: "USA"
}

def fetch_year_data(hs_code, year, max_retries=3):
    """Fetches UN Comtrade data with exponential backoff (max 3 attempts: 1s, 2s, 4s)."""
    url = f"https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode=699&period={year}&cmdCode={hs_code}&flowCode=M"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CounterVerse/1.0"}
    req = urllib.request.Request(url, headers=headers)
    backoff_delays = [1.0, 2.0, 4.0]

    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("data", []), None
        except urllib.error.HTTPError as e:
            err_msg = f"HTTP {e.code}: {e.reason}"
            print(f"  Attempt {attempt}/{max_retries} for HS {hs_code} ({year}) failed: {err_msg}")
            if attempt < max_retries:
                delay = backoff_delays[attempt - 1]
                time.sleep(delay)
            else:
                return None, err_msg
        except Exception as e:
            err_msg = str(e)
            print(f"  Attempt {attempt}/{max_retries} for HS {hs_code} ({year}) failed: {err_msg}")
            if attempt < max_retries:
                delay = backoff_delays[attempt - 1]
                time.sleep(delay)
            else:
                return None, err_msg

def main():
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    
    results = {
        "metadata": {
            "source": "UN Comtrade API (v1 preview)",
            "citation": "UN Comtrade Database (India Imports, HS 8542 & HS 8112)",
            "data_vintage": "2022 Complete Baseline (Latest Audited Annual Release)",
            "reporter": "India (699)",
            "flow": "Imports (M)",
            "commodities": {
                "8542": "Electronic integrated circuits (Semiconductors)",
                "8112": "Gallium, germanium, hafnium, indium, niobium, rhenium, thallium"
            },
            "exchange_rate_usd_inr": 83.0,
            "access_date": "2026-09-05",
            "last_fetch_utc": now_utc,
            "stale_warning": "UN Comtrade public trade data is annual and lagged by 3-12 months. 2023-2024 records may be partial or unreleased."
        },
        "yearly_totals": {},
        "partner_shares": {}
    }

    # Fetch 2019 to 2023
    years = ["2019", "2020", "2021", "2022", "2023"]
    
    for hs in ["8542", "8112"]:
        results["yearly_totals"][hs] = {}
        for y in years:
            print(f"Fetching HS {hs} for {y}...")
            rows, err = fetch_year_data(hs, y)
            if rows:
                # Find world total
                world_rows = [r for r in rows if r.get("partnerCode") == 0]
                world_val = world_rows[0].get("primaryValue", 0) if world_rows else 0
                
                # Partner breakdown
                partners = {}
                for r in rows:
                    pcode = r.get("partnerCode")
                    if pcode in PARTNER_NAMES and pcode != 0:
                        partners[PARTNER_NAMES[pcode]] = r.get("primaryValue", 0)
                
                results["yearly_totals"][hs][y] = {
                    "data_vintage": f"{y} Annual Baseline (UN Comtrade)",
                    "usd_value": world_val,
                    "inr_crore": round(world_val * 83.0 / 1e7, 2),
                    "partners_usd": partners,
                    "partners_inr_crore": {p: round(v * 83.0 / 1e7, 2) for p, v in partners.items()},
                    "status": "Complete" if world_val > 1e7 else "Partial / Incomplete"
                }
            else:
                print(f"  Warning: No data or rate limit for {hs} ({y}): {err}")
                results["yearly_totals"][hs][y] = {
                    "data_vintage": f"{y} Annual (Unavailable / Rate Limited)",
                    "status": f"Rate Limited / No Data: {err}"
                }
            time.sleep(2.0) # Be polite to API
            
    out_file = out_dir / "comtrade_india_baseline.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Successfully saved UN Comtrade baseline to: {out_file}")

if __name__ == "__main__":
    main()
