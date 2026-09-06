import urllib.request
import json
import time
from pathlib import Path

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

def fetch_year_data(hs_code, year):
    url = f"https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode=699&period={year}&cmdCode={hs_code}&flowCode=M"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CounterVerse/1.0"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("data", [])
    except Exception as e:
        print(f"Error fetching HS {hs_code} ({year}): {e}")
        return None

def main():
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "metadata": {
            "source": "UN Comtrade API (v1 preview)",
            "reporter": "India (699)",
            "flow": "Imports (M)",
            "commodities": {
                "8542": "Electronic integrated circuits (Semiconductors)",
                "8112": "Gallium, germanium, hafnium, indium, niobium, rhenium, thallium"
            },
            "exchange_rate_usd_inr": 83.0,
            "access_date": "2026-09-05"
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
            rows = fetch_year_data(hs, y)
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
                    "usd_value": world_val,
                    "inr_crore": round(world_val * 83.0 / 1e7, 2),
                    "partners_usd": partners,
                    "partners_inr_crore": {p: round(v * 83.0 / 1e7, 2) for p, v in partners.items()}
                }
            else:
                print(f"  Warning: No data or rate limit for {hs} ({y})")
                results["yearly_totals"][hs][y] = {"status": "Rate Limited / No Data"}
            time.sleep(2.0) # Be polite to API
            
    out_file = out_dir / "comtrade_india_baseline.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Successfully saved UN Comtrade baseline to: {out_file}")

if __name__ == "__main__":
    main()
