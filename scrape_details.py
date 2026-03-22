"""Scrape detailed profile + financial data for all active charities"""
import json
import urllib.request
import urllib.parse
import base64
import time
import os
import sys

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/projects/sg-charity/data")
HANDLER_URL = "https://www.charities.gov.sg/_layouts/15/CPInternet/SearchResultHandler.ashx"

# Load charity list
with open(os.path.join(DATA_DIR, "charities_full.json"), "r") as f:
    all_charities = json.load(f)

# Filter active only
active = [c for c in all_charities if c.get("CharityStatus") not in ("Deregistered", "De-Exempted")]
print(f"Total active charities to scrape: {len(active)}")

# Resume support - check existing progress
PROFILE_FILE = os.path.join(DATA_DIR, "charities_profiles.jsonl")
FINANCE_FILE = os.path.join(DATA_DIR, "charities_financials.jsonl")

done_ids = set()
if os.path.exists(PROFILE_FILE):
    with open(PROFILE_FILE, "r") as f:
        for line in f:
            try:
                d = json.loads(line)
                done_ids.add(d.get("_crm_id"))
            except: pass
    print(f"Resuming: {len(done_ids)} already done")

def fetch_detail(crm_id, data_type):
    b64 = base64.b64encode(crm_id.encode()).decode()
    url = f"{HANDLER_URL}?query={urllib.parse.quote(b64)}&type={urllib.parse.quote(data_type)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            if data.get("Error") == "1":
                return None
            return data
    except Exception as e:
        return {"_error": str(e)}

# Open files in append mode
prof_f = open(PROFILE_FILE, "a", encoding="utf-8")
fin_f = open(FINANCE_FILE, "a", encoding="utf-8")

try:
    total = len(active)
    skipped = 0
    errors = 0
    for i, c in enumerate(active):
        crm_id = c.get("CharityAccountCRMRecordID")
        if not crm_id:
            continue
        if crm_id in done_ids:
            skipped += 1
            continue
        
        name = c.get("CharityIPCName", "?")
        
        # Fetch profile
        profile = fetch_detail(crm_id, "Organisation Profile")
        if profile and "_error" not in profile:
            profile["_crm_id"] = crm_id
            profile["_uen"] = c.get("UENNo")
            prof_f.write(json.dumps(profile, ensure_ascii=False) + "\n")
        else:
            errors += 1
        
        # Fetch financials
        finance = fetch_detail(crm_id, "Financial Information")
        if finance and "_error" not in finance:
            finance["_crm_id"] = crm_id
            finance["_uen"] = c.get("UENNo")
            fin_f.write(json.dumps(finance, ensure_ascii=False) + "\n")
        
        done = i + 1 - skipped + len(done_ids) - skipped
        if (i + 1) % 50 == 0:
            prof_f.flush()
            fin_f.flush()
            elapsed = i + 1
            print(f"  [{elapsed}/{total}] {name[:40]}... (errors: {errors})")
        
        # Be polite - 200ms between requests  
        time.sleep(0.2)
        
finally:
    prof_f.close()
    fin_f.close()

# Count results
prof_count = 0
fin_count = 0
if os.path.exists(PROFILE_FILE):
    with open(PROFILE_FILE) as f:
        prof_count = sum(1 for _ in f)
if os.path.exists(FINANCE_FILE):
    with open(FINANCE_FILE) as f:
        fin_count = sum(1 for _ in f)

print(f"\nDone! Profiles: {prof_count}, Financials: {fin_count}, Errors: {errors}")
print(f"Files: {PROFILE_FILE}")
print(f"       {FINANCE_FILE}")
