"""Scrape all Singapore registered charities from charities.gov.sg"""
import json
import urllib.request
import time
import os

BASE_URL = "https://www.charities.gov.sg/_layouts/15/CPInternet/AdvanceSearchHandler.ashx"
DETAIL_URL = "https://www.charities.gov.sg/_layouts/15/CPInternet/SearchOrgProfileHandler.ashx"
OUTPUT_DIR = os.path.expanduser("~/.openclaw/workspace/projects/sg-charity/data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_all_charities():
    """Fetch the full list from the search API"""
    url = f"{BASE_URL}?query=&sortColumn=&sortDirection=&reqType=charityInfo&filterColumn="
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    
    total = data.get("recordsTotal", 0)
    charities = data.get("charityInfosData", [])
    print(f"Total records: {total}, fetched: {len(charities)}")
    return charities

def fetch_charity_detail(crm_id):
    """Fetch detailed info for a single charity"""
    url = f"{DETAIL_URL}?q={crm_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  Error fetching {crm_id}: {e}")
        return None

def main():
    print("=== Fetching charity list ===")
    charities = fetch_all_charities()
    
    # Save the raw list
    list_path = os.path.join(OUTPUT_DIR, "charities_list.json")
    with open(list_path, "w", encoding="utf-8") as f:
        json.dump(charities, f, ensure_ascii=False, indent=2)
    print(f"Saved list to {list_path}")
    
    # Quick stats
    sectors = {}
    statuses = {}
    activities_count = {}
    ipc_count = 0
    
    for c in charities:
        sector = c.get("PrimarySector", "Unknown")
        sectors[sector] = sectors.get(sector, 0) + 1
        
        status = c.get("CharityStatus", "Unknown")
        statuses[status] = statuses.get(status, 0) + 1
        
        if c.get("IPCStatus") == "Live":
            ipc_count += 1
        
        for act in c.get("Activities", []):
            activities_count[act] = activities_count.get(act, 0) + 1
    
    stats = {
        "total": len(charities),
        "ipc_live": ipc_count,
        "by_sector": dict(sorted(sectors.items(), key=lambda x: -x[1])),
        "by_status": dict(sorted(statuses.items(), key=lambda x: -x[1])),
        "by_activity": dict(sorted(activities_count.items(), key=lambda x: -x[1])),
    }
    
    stats_path = os.path.join(OUTPUT_DIR, "charities_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"\nSaved stats to {stats_path}")
    
    print(f"\n=== Stats ===")
    print(f"Total charities: {len(charities)}")
    print(f"Active IPC: {ipc_count}")
    print(f"\nBy Sector:")
    for k, v in sorted(sectors.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print(f"\nBy Status:")
    for k, v in sorted(statuses.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print(f"\nBy Activity:")
    for k, v in sorted(activities_count.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    
    # Fetch details for a sample (first 10) to understand data structure
    print(f"\n=== Fetching sample details (10 charities) ===")
    details = []
    sample = charities[:10]
    for i, c in enumerate(sample):
        crm_id = c.get("CharityAccountCRMRecordID")
        name = c.get("CharityIPCName", "?")
        if crm_id:
            print(f"  [{i+1}/10] {name}...")
            detail = fetch_charity_detail(crm_id)
            if detail:
                details.append(detail)
            time.sleep(0.5)
    
    detail_path = os.path.join(OUTPUT_DIR, "charities_detail_sample.json")
    with open(detail_path, "w", encoding="utf-8") as f:
        json.dump(details, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(details)} detail records to {detail_path}")

if __name__ == "__main__":
    main()
