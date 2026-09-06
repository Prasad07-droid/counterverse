import urllib.request
import urllib.parse
import json

def test_gdelt():
    query = '(semiconductor OR gallium OR germanium OR "chip shortage" OR "integrated circuit") AND (China OR India OR Taiwan OR "South Korea")'
    params = {
        'query': query,
        'mode': 'artlist',
        'maxrecords': '10',
        'format': 'json',
        'sort': 'datedesc'
    }
    url = 'https://api.gdeltproject.org/api/v2/doc/doc?' + urllib.parse.urlencode(params)
    print('Testing GDELT API...')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            articles = data.get('articles', [])
            print(f'GDELT SUCCESS! Returned {len(articles)} live articles.')
            for i, a in enumerate(articles[:3]):
                print(f"  [{i+1}] {a.get('title')} ({a.get('seendate')})")
            return articles
    except Exception as e:
        print('GDELT Error:', e)
        return []

def test_comtrade():
    print('\nTesting UN Comtrade API for India (699) HS 8542 & HS 8112...')
    # Fetch 2022 and 2023 imports
    results = {}
    for hs in ['8542', '8112']:
        for year in ['2021', '2022', '2023']:
            url = f'https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode=699&period={year}&cmdCode={hs}&flowCode=M'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    payload = json.loads(resp.read().decode('utf-8'))
                    rows = payload.get('data', [])
                    # Total world import for this commodity (partnerCode 0 is World)
                    world_rows = [r for r in rows if r.get('partnerCode') == 0]
                    partner_rows = [r for r in rows if r.get('partnerCode') in [156, 490, 410]] # China, Taiwan, Korea
                    print(f"  HS {hs} ({year}): {len(rows)} rows. World rows: {len(world_rows)}, Key partners: {len(partner_rows)}")
                    if world_rows:
                        val_usd = world_rows[0].get('primaryValue', 0)
                        print(f"    -> Total World Import: ${val_usd:,.0f} USD")
            except Exception as e:
                print(f"  HS {hs} ({year}) Error:", e)

if __name__ == '__main__':
    test_gdelt()
    test_comtrade()
