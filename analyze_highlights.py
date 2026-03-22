"""Deep analysis of SG charity data - find interesting patterns"""
import json
import os
from collections import Counter, defaultdict
from datetime import datetime

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/projects/sg-charity/data")

with open(os.path.join(DATA_DIR, "charities_full.json"), "r") as f:
    charities = json.load(f)

# Filter active only (exclude deregistered)
active = [c for c in charities if c.get("CharityStatus") not in ("Deregistered", "De-Exempted")]
deregistered = [c for c in charities if c.get("CharityStatus") == "Deregistered"]

print(f"Total: {len(charities)}, Active: {len(active)}, Deregistered: {len(deregistered)}")

# === 1. Registration timeline analysis ===
print("\n" + "="*60)
print("1. REGISTRATION TIMELINE")
print("="*60)

def parse_year(date_str):
    if not date_str: return None
    parts = date_str.split("/")
    if len(parts) == 3:
        try: return int(parts[2])
        except: pass
    return None

yearly = Counter()
for c in charities:
    y = parse_year(c.get("RegistrationDate"))
    if y: yearly[y] += 1

# Show year by year from 2015
print("\nRecent registration trend:")
for y in range(2015, 2027):
    count = yearly.get(y, 0)
    bar = "█" * (count // 2)
    print(f"  {y}: {count:3d} {bar}")

# Peak year
peak_year = max(yearly, key=yearly.get)
print(f"\nPeak year: {peak_year} ({yearly[peak_year]} registrations)")

# Oldest charities
print("\nOldest active charities:")
oldest = sorted(active, key=lambda c: parse_year(c.get("RegistrationDate","")) or 9999)
for c in oldest[:10]:
    print(f"  {c.get('RegistrationDate','?'):12s} | {c.get('CharityIPCName','?')}")

# === 2. Deregistration analysis ===
print("\n" + "="*60)
print("2. DEREGISTRATION PATTERNS")
print("="*60)

dereg_sectors = Counter()
dereg_years = Counter()
for c in deregistered:
    dereg_sectors[c.get("PrimarySector", "?")] += 1
    y = parse_year(c.get("DeRegistrationDate"))
    if y: dereg_years[y] += 1

print("\nDeregistered by sector:")
for s, cnt in dereg_sectors.most_common():
    total_in_sector = sum(1 for c in charities if c.get("PrimarySector") == s)
    pct = cnt / total_in_sector * 100 if total_in_sector else 0
    print(f"  {s:25s}: {cnt:3d} / {total_in_sector} ({pct:.0f}% failure rate)")

print("\nRecent deregistrations:")
for y in range(2020, 2027):
    print(f"  {y}: {dereg_years.get(y, 0)}")

# === 3. IPC analysis ===
print("\n" + "="*60)
print("3. IPC (TAX DEDUCTIBLE) ANALYSIS")
print("="*60)

ipc_live = [c for c in active if c.get("IPCStatus") == "Live"]
print(f"\nActive IPC: {len(ipc_live)} out of {len(active)} active charities ({len(ipc_live)/len(active)*100:.1f}%)")

ipc_by_sector = Counter()
active_by_sector = Counter()
for c in active:
    s = c.get("PrimarySector", "?")
    active_by_sector[s] += 1
    if c.get("IPCStatus") == "Live":
        ipc_by_sector[s] += 1

print("\nIPC rate by sector:")
for s, total in active_by_sector.most_common():
    ipc = ipc_by_sector.get(s, 0)
    rate = ipc / total * 100 if total else 0
    bar = "█" * int(rate // 2)
    print(f"  {s:25s}: {ipc:3d}/{total:4d} ({rate:5.1f}%) {bar}")

# IPC expiring soon
print("\nIPC expiring in 2026:")
expiring_2026 = []
for c in ipc_live:
    till = c.get("IPCValidTill", "")
    if "2026" in till:
        expiring_2026.append(c)
print(f"  {len(expiring_2026)} charities with IPC expiring in 2026")

# === 4. Classification deep dive ===
print("\n" + "="*60)
print("4. CLASSIFICATION DEEP DIVE")
print("="*60)

classification_counts = Counter()
for c in active:
    for cl in c.get("PrimaryClassification", []):
        classification_counts[cl] += 1

print("\nAll classifications:")
for cl, cnt in classification_counts.most_common():
    print(f"  {cl:40s}: {cnt}")

# === 5. Cross-sector patterns ===
print("\n" + "="*60)
print("5. MULTI-ACTIVITY CHARITIES")
print("="*60)

activity_combos = Counter()
for c in active:
    acts = tuple(sorted(c.get("Activities", [])))
    if len(acts) > 1:
        activity_combos[acts] += 1

print(f"\nCharities with multiple activities: {sum(1 for c in active if len(c.get('Activities',[])) > 1)}")
print(f"Charities with no activities listed: {sum(1 for c in active if len(c.get('Activities',[])) == 0)}")
print("\nTop activity combinations:")
for combo, cnt in activity_combos.most_common(10):
    print(f"  {cnt:3d} | {' + '.join(combo)}")

# === 6. Setup type vs sector ===
print("\n" + "="*60)
print("6. ORGANIZATIONAL STRUCTURE")
print("="*60)

setup_sector = defaultdict(Counter)
for c in active:
    setup = c.get("CharitySetup", "Unknown")
    sector = c.get("PrimarySector", "Unknown")
    setup_sector[sector][setup] += 1

for sector in ["Social and Welfare", "Health", "Education", "Religious", "Arts and Heritage"]:
    if sector in setup_sector:
        print(f"\n  {sector}:")
        for setup, cnt in setup_sector[sector].most_common():
            print(f"    {setup}: {cnt}")

# === 7. Eldercare focus (Luca's interest) ===
print("\n" + "="*60)
print("7. ELDERCARE DEEP DIVE")
print("="*60)

eldercare = [c for c in active if "Eldercare" in (c.get("PrimaryClassification") or [])]
print(f"\nEldercare charities: {len(eldercare)}")
print(f"With IPC: {sum(1 for c in eldercare if c.get('IPCStatus')=='Live')}")

print("\nEldercare organizations:")
for c in sorted(eldercare, key=lambda x: x.get("CharityIPCName","")):
    ipc = "IPC" if c.get("IPCStatus") == "Live" else "   "
    setup = c.get("CharitySetup", "?")
    admin = c.get("SectorAdministrato", "?").replace("Ministry of ", "")
    print(f"  [{ipc}] {c.get('CharityIPCName','?')[:50]:50s} | {setup:20s} | {admin}")

# === 8. Name patterns (fun) ===
print("\n" + "="*60)
print("8. FUN PATTERNS")
print("="*60)

# Names containing certain keywords
keywords = {"Singapore": 0, "International": 0, "World": 0, "Global": 0, "Asia": 0, 
            "Chinese": 0, "Malay": 0, "Indian": 0, "Tamil": 0, "Muslim": 0,
            "Children": 0, "Women": 0, "Youth": 0, "Elderly": 0, "Animal": 0}
for c in active:
    name = c.get("CharityIPCName", "").upper()
    for kw in keywords:
        if kw.upper() in name:
            keywords[kw] += 1

print("\nKeyword in charity name:")
for kw, cnt in sorted(keywords.items(), key=lambda x: -x[1]):
    if cnt > 0:
        print(f"  {kw:20s}: {cnt}")

# Newest charities
print("\nNewest charities (2025-2026):")
newest = [c for c in active if parse_year(c.get("RegistrationDate")) in (2025, 2026)]
for c in sorted(newest, key=lambda x: x.get("RegistrationDate",""), reverse=True)[:15]:
    print(f"  {c.get('RegistrationDate','?'):12s} | {c.get('PrimarySector','?'):20s} | {c.get('CharityIPCName','?')}")

