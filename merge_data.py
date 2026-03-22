#!/usr/bin/env python3
"""
Merge all charity data sources into a unified JSON.

Sources:
1. charities_full.json       — 3,173 records (registry)
2. charities_profiles.jsonl   — 2,635 records (details)
3. charities_financials.jsonl — 860 records (financials, needs ETL)
4. ncss_agencies.json         — 908 records (GPS coordinates)
5. givingsg_organisations.json — 1,707 records (descriptions/causes)

Output: data/charities_unified.json
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path("data")


# ──────────────────────────────────────────────
# 1. Financial ETL — parse nested JSON strings
# ──────────────────────────────────────────────

def parse_financial_table(raw_json_str):
    """Parse the pivot-table-style financial data into structured dict.

    Input format (each row):
    [
        {"Key": "Receipts", "Value": "Tax-Deductible"},   # category + line item
        {"Key": "May 2024 - Apr 2025", "Value": "96242"}, # period values...
        {"Key": "May 2023 - Apr 2024", "Value": "62525"},
    ]

    Output: {
        "May 2024 - Apr 2025": {"Tax-Deductible": 96242.0, ...},
        "May 2023 - Apr 2024": {...},
    }
    """
    if not raw_json_str:
        return {}

    try:
        rows = json.loads(raw_json_str)
    except (json.JSONDecodeError, TypeError):
        return {}

    result = {}

    for row in rows:
        if not isinstance(row, list) or len(row) < 2:
            continue

        # First element: category header (e.g. "Receipts") + line item name
        header = row[0]
        line_item = header.get("Value", "").strip()

        if not line_item:
            continue

        # Skip section headers (e.g. "Donations in Cash" with no values)
        # These are parent categories — we want the detail lines

        # Remaining elements: period values
        for entry in row[1:]:
            period = entry.get("Key", "").strip()
            value_str = entry.get("Value", "").strip()

            if not period or period in ("Receipts", "Expenses", "Balance Sheet"):
                continue

            if period not in result:
                result[period] = {}

            # Parse numeric value
            if value_str:
                try:
                    value = float(value_str)
                    result[period][line_item] = value
                except ValueError:
                    result[period][line_item] = value_str

    return result


def parse_financials(record):
    """Parse all financial data for one charity into structured format."""
    # Summary info (already structured)
    summaries = []
    for info in record.get("FinancialInfos", []):
        summaries.append({
            "period": info.get("FYPeriod", ""),
            "income": safe_float(info.get("Income")),
            "spending": safe_float(info.get("Spending")),
            "status": info.get("Status", ""),
        })

    # Detailed breakdowns (need ETL)
    receipts = parse_financial_table(record.get("FinancialInfoReceipts", ""))
    expenses = parse_financial_table(record.get("FinancialInfoExpenses", ""))
    balance_sheet = parse_financial_table(record.get("FinancialInfoBalanceSheet", ""))
    other_info = parse_financial_table(record.get("FinancialInfoOtherInformation", ""))

    return {
        "summaries": summaries,
        "receipts": receipts,
        "expenses": expenses,
        "balance_sheet": balance_sheet,
        "other_info": other_info,
    }


def safe_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ──────────────────────────────────────────────
# 2. Name normalization for fuzzy matching
# ──────────────────────────────────────────────

def normalize_name(name):
    """Normalize org name for matching."""
    if not name:
        return ""
    name = name.upper().strip()
    # Remove common suffixes
    for suffix in [" LTD", " LTD.", " PTE", " PTE.", " CO.", " LIMITED",
                   " ASSOCIATION", " SOCIETY", " FOUNDATION", " FUND",
                   " ORGANISATION", " ORGANIZATION"]:
        name = name.replace(suffix, "")
    # Remove punctuation
    name = re.sub(r'[^\w\s]', '', name)
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def parse_address_postal(address_str):
    """Extract postal code from address string like '817 Bukit Batok West Ave 5, 659086'."""
    if not address_str:
        return address_str, None
    match = re.search(r'(\d{6})\s*$', address_str)
    if match:
        postal = match.group(1)
        addr = address_str[:match.start()].rstrip(', ')
        return addr, postal
    return address_str, None


def parse_date(date_str):
    """Convert DD/M/YYYY to YYYY-MM-DD."""
    if not date_str:
        return None
    try:
        parts = date_str.split('/')
        if len(parts) == 3:
            day, month, year = parts
            return f"{year}-{int(month):02d}-{int(day):02d}"
    except (ValueError, IndexError):
        pass
    return date_str


# ──────────────────────────────────────────────
# 3. Main merge logic
# ──────────────────────────────────────────────

def main():
    print("Loading data sources...")

    # --- Source 1: charities_full.json (master list) ---
    with open(DATA_DIR / "charities_full.json") as f:
        charities_full = json.load(f)
    print(f"  charities_full.json: {len(charities_full)} records")

    # --- Source 2: charities_profiles.jsonl ---
    profiles = {}
    with open(DATA_DIR / "charities_profiles.jsonl") as f:
        for line in f:
            record = json.loads(line)
            uen = record.get("_uen") or record.get("UENNo")
            if uen:
                profiles[uen] = record
    print(f"  charities_profiles.jsonl: {len(profiles)} records")

    # --- Source 3: charities_financials.jsonl ---
    financials = {}
    with open(DATA_DIR / "charities_financials.jsonl") as f:
        for line in f:
            record = json.loads(line)
            uen = record.get("_uen")
            if uen:
                financials[uen] = record
    print(f"  charities_financials.jsonl: {len(financials)} records")

    # --- Source 4: ncss_agencies.json ---
    with open(DATA_DIR / "ncss_agencies.json") as f:
        ncss_list = json.load(f)
    # Build UEN lookup and name lookup
    ncss_by_uen = {}
    ncss_by_name = {}
    for agency in ncss_list:
        uen = agency.get("matched_uen")
        if uen:
            ncss_by_uen[uen] = agency
        norm = normalize_name(agency.get("name", ""))
        if norm:
            ncss_by_name[norm] = agency
    print(f"  ncss_agencies.json: {len(ncss_list)} records ({len(ncss_by_uen)} UEN-matched)")

    # --- Source 5: givingsg_organisations.json ---
    with open(DATA_DIR / "givingsg_organisations.json") as f:
        givingsg_list = json.load(f)
    givingsg_by_name = {}
    for org in givingsg_list:
        norm = normalize_name(org.get("name", ""))
        if norm:
            givingsg_by_name[norm] = org
    print(f"  givingsg_organisations.json: {len(givingsg_list)} records")

    # --- Merge ---
    print("\nMerging...")
    unified = []
    stats = {
        "total": 0,
        "with_profile": 0,
        "with_financials": 0,
        "with_geo": 0,
        "with_givingsg": 0,
        "active": 0,
        "deregistered": 0,
    }

    for charity in charities_full:
        uen = (charity.get("UENNo") or "").strip()
        name = (charity.get("CharityIPCName") or "").strip()
        norm_name = normalize_name(name)
        status = charity.get("CharityStatus", "")
        is_active = "Deregistered" not in (status or "")

        # --- Base record ---
        record = {
            "uen": uen,
            "name": name,
            "status": status,
            "is_active": is_active,
            "ipc_status": charity.get("IPCStatus"),
            "ipc_valid_from": parse_date(charity.get("IPCValidFrom")),
            "ipc_valid_till": parse_date(charity.get("IPCValidTill")),
            "sector": charity.get("PrimarySector"),
            "classifications": charity.get("PrimaryClassification", []),
            "activities": charity.get("Activities", []),
            "setup": charity.get("CharitySetup"),
            "administrator": charity.get("SectorAdministrato"),
            "registration_date": parse_date(charity.get("RegistrationDate")),
            "deregistration_date": parse_date(charity.get("DeRegistrationDate")),
        }

        # --- Merge profile ---
        profile = profiles.get(uen)
        if profile:
            stats["with_profile"] += 1
            address, postal = parse_address_postal(profile.get("Address"))
            record.update({
                "contact_person": profile.get("ContactPerson"),
                "phone": profile.get("OfficeNo"),
                "fax": profile.get("FaxNo"),
                "email": profile.get("Email"),
                "website": profile.get("Website") if profile.get("Website") != "Not Applicable" else None,
                "address": address,
                "postal_code": postal,
                "objective": profile.get("Objective"),
                "vision_mission": profile.get("VisionMission"),
                "org_activities": profile.get("OrganisationActivities", []),
                "governing_members_count": len(profile.get("GoverningMembers", [])),
                "key_officers_count": len(profile.get("KeyOfficers", [])),
                "governing_members": [
                    {
                        "name": m.get("Name", ""),
                        "designation": m.get("Designation", ""),
                    }
                    for m in profile.get("GoverningMembers", [])[:5]  # Top 5 to save space
                ],
                "key_officers": [
                    {
                        "name": m.get("Name", ""),
                        "designation": m.get("Designation", ""),
                    }
                    for m in profile.get("KeyOfficers", [])[:5]
                ],
                "has_public_financials": not profile.get("requiresLogin", True),
            })
        else:
            record.update({
                "contact_person": None, "phone": None, "fax": None,
                "email": None, "website": None, "address": None,
                "postal_code": None, "objective": None, "vision_mission": None,
                "org_activities": [], "governing_members_count": 0,
                "key_officers_count": 0, "governing_members": [],
                "key_officers": [], "has_public_financials": False,
            })

        # --- Merge financials (ETL) ---
        fin = financials.get(uen)
        if fin:
            stats["with_financials"] += 1
            record["financials"] = parse_financials(fin)
        else:
            record["financials"] = None

        # --- Merge NCSS (GPS) ---
        ncss = ncss_by_uen.get(uen) or ncss_by_name.get(norm_name)
        if ncss:
            stats["with_geo"] += 1
            record["latitude"] = ncss.get("latitude")
            record["longitude"] = ncss.get("longitude")
            # Prefer NCSS address if charity has none
            if not record.get("address") and ncss.get("address"):
                record["address"] = ncss.get("address")
            if not record.get("postal_code") and ncss.get("postal_code"):
                record["postal_code"] = ncss.get("postal_code")
        else:
            record["latitude"] = None
            record["longitude"] = None

        # --- Merge giving.sg ---
        givingsg = givingsg_by_name.get(norm_name)
        if givingsg:
            stats["with_givingsg"] += 1
            record["givingsg_description"] = givingsg.get("description")
            record["givingsg_causes"] = givingsg.get("causes", [])
            record["givingsg_image"] = givingsg.get("image_url")
            record["givingsg_url"] = givingsg.get("profile_url")
            record["givingsg_tab"] = givingsg.get("tab")
        else:
            record["givingsg_description"] = None
            record["givingsg_causes"] = []
            record["givingsg_image"] = None
            record["givingsg_url"] = None
            record["givingsg_tab"] = None

        # --- Generate slug ---
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[\s_]+', '-', slug).strip('-')
        record["slug"] = f"{slug}-{uen.lower()}" if uen else slug

        if is_active:
            stats["active"] += 1
        else:
            stats["deregistered"] += 1
        stats["total"] += 1

        unified.append(record)

    # Sort: active first, then by name
    unified.sort(key=lambda x: (not x["is_active"], x["name"]))

    # --- Write output ---
    output_path = DATA_DIR / "charities_unified.json"
    with open(output_path, "w") as f:
        json.dump(unified, f, ensure_ascii=False, indent=None)

    file_size = output_path.stat().st_size / (1024 * 1024)

    print(f"\n{'='*50}")
    print(f"Output: {output_path} ({file_size:.1f} MB)")
    print(f"{'='*50}")
    print(f"Total records:     {stats['total']}")
    print(f"  Active:          {stats['active']}")
    print(f"  Deregistered:    {stats['deregistered']}")
    print(f"  With profile:    {stats['with_profile']}")
    print(f"  With financials: {stats['with_financials']}")
    print(f"  With GPS coords: {stats['with_geo']}")
    print(f"  With giving.sg:  {stats['with_givingsg']}")

    # --- Also write a lightweight version for search index ---
    search_index = []
    for r in unified:
        if not r["is_active"]:
            continue
        search_index.append({
            "uen": r["uen"],
            "name": r["name"],
            "slug": r["slug"],
            "sector": r["sector"],
            "classifications": r["classifications"],
            "activities": r["activities"],
            "ipc_status": r["ipc_status"],
            "setup": r["setup"],
            "postal_code": r["postal_code"],
            "has_financials": r["financials"] is not None,
            "has_geo": r["latitude"] is not None,
            "causes": r.get("givingsg_causes", []),
            # For search: combine searchable text
            "search_text": " ".join(filter(None, [
                r["name"],
                r.get("objective", ""),
                r.get("vision_mission", ""),
                r.get("givingsg_description", ""),
                " ".join(r.get("classifications", [])),
                " ".join(r.get("givingsg_causes", [])),
            ])),
        })

    search_path = DATA_DIR / "charities_search_index.json"
    with open(search_path, "w") as f:
        json.dump(search_index, f, ensure_ascii=False, indent=None)

    search_size = search_path.stat().st_size / (1024 * 1024)
    print(f"\nSearch index: {search_path} ({search_size:.1f} MB, {len(search_index)} active records)")

    # --- Write stats summary ---
    stats_summary = {
        "total": stats["total"],
        "active": stats["active"],
        "deregistered": stats["deregistered"],
        "with_profile": stats["with_profile"],
        "with_financials": stats["with_financials"],
        "with_geo": stats["with_geo"],
        "with_givingsg": stats["with_givingsg"],
        "sectors": defaultdict(int),
        "ipc_active": 0,
        "ipc_expiring_2026": 0,
    }

    for r in unified:
        if r["is_active"]:
            sector = r["sector"] or "Unknown"
            stats_summary["sectors"][sector] += 1
            if r["ipc_status"] == "Live":
                stats_summary["ipc_active"] += 1
            if r.get("ipc_valid_till") and r["ipc_valid_till"].startswith("2026"):
                stats_summary["ipc_expiring_2026"] += 1

    stats_summary["sectors"] = dict(stats_summary["sectors"])

    stats_path = DATA_DIR / "charities_unified_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats_summary, f, ensure_ascii=False, indent=2)

    print(f"Stats: {stats_path}")
    print(f"\nSector breakdown (active):")
    for sector, count in sorted(stats_summary["sectors"].items(), key=lambda x: -x[1]):
        print(f"  {sector}: {count}")
    print(f"\nIPC active: {stats_summary['ipc_active']}")
    print(f"IPC expiring 2026: {stats_summary['ipc_expiring_2026']}")


if __name__ == "__main__":
    main()
