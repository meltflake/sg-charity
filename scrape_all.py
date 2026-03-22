"""Scrape all Singapore registered charities - full dataset"""
import json
import urllib.request
import os

EXPORT_URL = "https://www.charities.gov.sg/_layouts/15/CPInternet/AdvanceExportSearchHandler.ashx"
PROFILE_URL = "https://www.charities.gov.sg/_layouts/15/CPInternet/SearchOrgProfileHandler.ashx"
OUTPUT_DIR = os.path.expanduser("~/.openclaw/workspace/projects/sg-charity/data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_all():
    """Fetch all charities via the export endpoint"""
    data = urllib.parse.urlencode({
        "query": "",
        "sortColumn": "",
        "sortDirection": "",
        "reqType": "charityInfo",
        "filterColumn": ""
    }).encode()
    req = urllib.request.Request(EXPORT_URL, data=data, headers={
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded"
    })
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode())
    
    charities = result.get("charityInfosData", [])
    print(f"Fetched {len(charities)} charities (total: {result.get('recordsTotal')})")
    return charities

def analyze(charities):
    """Generate comprehensive stats"""
    sectors = {}
    statuses = {}
    activities = {}
    classifications = {}
    setup_types = {}
    sector_admins = {}
    ipc_count = 0
    yearly_reg = {}
    
    for c in charities:
        # Sector
        s = c.get("PrimarySector", "Unknown")
        sectors[s] = sectors.get(s, 0) + 1
        
        # Status
        st = c.get("CharityStatus", "Unknown")
        statuses[st] = statuses.get(st, 0) + 1
        
        # IPC
        if c.get("IPCStatus") == "Live":
            ipc_count += 1
        
        # Activities
        for a in c.get("Activities", []):
            activities[a] = activities.get(a, 0) + 1
        
        # Classification
        for cl in c.get("PrimaryClassification", []):
            classifications[cl] = classifications.get(cl, 0) + 1
        
        # Setup type
        setup = c.get("CharitySetup", "Unknown")
        setup_types[setup] = setup_types.get(setup, 0) + 1
        
        # Sector admin
        admin = c.get("SectorAdministrato", "Unknown")
        sector_admins[admin] = sector_admins.get(admin, 0) + 1
        
        # Registration year
        reg_date = c.get("RegistrationDate", "")
        if reg_date:
            parts = reg_date.split("/")
            if len(parts) == 3:
                year = parts[2]
                yearly_reg[year] = yearly_reg.get(year, 0) + 1
    
    return {
        "total": len(charities),
        "ipc_live": ipc_count,
        "by_sector": dict(sorted(sectors.items(), key=lambda x: -x[1])),
        "by_status": dict(sorted(statuses.items(), key=lambda x: -x[1])),
        "by_activity": dict(sorted(activities.items(), key=lambda x: -x[1])),
        "by_classification": dict(sorted(classifications.items(), key=lambda x: -x[1])),
        "by_setup_type": dict(sorted(setup_types.items(), key=lambda x: -x[1])),
        "by_sector_admin": dict(sorted(sector_admins.items(), key=lambda x: -x[1])),
        "by_registration_year": dict(sorted(yearly_reg.items())),
    }

def main():
    print("=== Fetching all charities ===")
    charities = fetch_all()
    
    # Save full list
    list_path = os.path.join(OUTPUT_DIR, "charities_full.json")
    with open(list_path, "w", encoding="utf-8") as f:
        json.dump(charities, f, ensure_ascii=False, indent=2)
    size_mb = os.path.getsize(list_path) / 1024 / 1024
    print(f"Saved full list: {list_path} ({size_mb:.1f} MB)")
    
    # Analyze
    print("\n=== Analyzing ===")
    stats = analyze(charities)
    
    stats_path = os.path.join(OUTPUT_DIR, "charities_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"Saved stats: {stats_path}")
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Total charities: {stats['total']}")
    print(f"Active IPC: {stats['ipc_live']}")
    
    print(f"\nBy Sector:")
    for k, v in stats['by_sector'].items():
        pct = v/stats['total']*100
        print(f"  {k}: {v} ({pct:.1f}%)")
    
    print(f"\nBy Status:")
    for k, v in stats['by_status'].items():
        print(f"  {k}: {v}")
    
    print(f"\nBy Classification (top 15):")
    for i, (k, v) in enumerate(stats['by_classification'].items()):
        if i >= 15: break
        print(f"  {k}: {v}")
    
    print(f"\nBy Activity:")
    for k, v in stats['by_activity'].items():
        print(f"  {k}: {v}")
    
    print(f"\nBy Setup Type:")
    for k, v in stats['by_setup_type'].items():
        print(f"  {k}: {v}")
    
    print(f"\nBy Sector Administrator:")
    for k, v in stats['by_sector_admin'].items():
        print(f"  {k}: {v}")
    
    # Registration trend (recent decades)
    print(f"\nRegistration by Decade:")
    decades = {}
    for y, c in stats['by_registration_year'].items():
        try:
            decade = f"{int(y)//10*10}s"
            decades[decade] = decades.get(decade, 0) + c
        except: pass
    for d in sorted(decades.keys()):
        print(f"  {d}: {decades[d]}")

    # Also save a CSV for easy viewing
    import csv
    csv_path = os.path.join(OUTPUT_DIR, "charities_full.csv")
    fields = ["CharityIPCName", "UEN", "CharityStatus", "IPCStatus", "IPCValidFrom", "IPCValidTill",
              "PrimarySector", "Classification", "Activities", "SectorAdmin", "CharitySetup", "RegistrationDate"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for c in charities:
            w.writerow([
                c.get("CharityIPCName", ""),
                c.get("UENNo", ""),
                c.get("CharityStatus", ""),
                c.get("IPCStatus", ""),
                c.get("IPCValidFrom", ""),
                c.get("IPCValidTill", ""),
                c.get("PrimarySector", ""),
                "|".join(c.get("PrimaryClassification", [])),
                "|".join(c.get("Activities", [])),
                c.get("SectorAdministrato", ""),
                c.get("CharitySetup", ""),
                c.get("RegistrationDate", ""),
            ])
    print(f"\nSaved CSV: {csv_path}")

if __name__ == "__main__":
    main()
