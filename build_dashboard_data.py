"""Build compact JSON data for the dashboard HTML page."""
import json
import re
import os
from collections import Counter, defaultdict
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUT = os.path.join(DATA_DIR, "dashboard_data.json")

NOW = datetime(2026, 3, 14)


def parse_date(s):
    if not s:
        return None
    try:
        parts = s.strip().split("/")
        return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
    except:
        return None


def main():
    # Load data
    with open(os.path.join(DATA_DIR, "charities_full.json")) as f:
        all_c = json.load(f)
    profiles = {}
    with open(os.path.join(DATA_DIR, "charities_profiles.jsonl")) as f:
        for line in f:
            p = json.loads(line)
            profiles[p.get("_uen")] = p
    financials = []
    with open(os.path.join(DATA_DIR, "charities_financials.jsonl")) as f:
        for line in f:
            financials.append(json.loads(line))

    active = [c for c in all_c if c.get("CharityStatus") not in ("Deregistered", "De-Exempted")]
    dereg = [c for c in all_c if c.get("CharityStatus") == "Deregistered"]
    charities_map = {c["UENNo"]: c for c in all_c}

    # === 1. Overview stats ===
    total_active = len(active)
    total_ipc = sum(1 for c in active if c.get("IPCStatus") == "Live")

    # === 2. Sector distribution ===
    sector_data = defaultdict(lambda: {"total": 0, "ipc": 0})
    for c in active:
        s = c.get("PrimarySector", "Unknown")
        sector_data[s]["total"] += 1
        if c.get("IPCStatus") == "Live":
            sector_data[s]["ipc"] += 1
    sectors = []
    for s in sorted(sector_data.keys(), key=lambda x: -sector_data[x]["total"]):
        d = sector_data[s]
        sectors.append({
            "name": s,
            "count": d["total"],
            "ipc": d["ipc"],
            "ipc_rate": round(d["ipc"] / d["total"] * 100, 1) if d["total"] else 0,
        })

    # === 3. Registration timeline ===
    reg_active = Counter()
    reg_dereg = Counter()
    for c in active:
        dt = parse_date(c.get("RegistrationDate"))
        if dt:
            reg_active[dt.year] += 1
    for c in dereg:
        dt = parse_date(c.get("RegistrationDate"))
        if dt:
            reg_dereg[dt.year] += 1

    years = sorted(set(list(reg_active.keys()) + list(reg_dereg.keys())))
    timeline = [{"year": y, "active": reg_active.get(y, 0), "dereg": reg_dereg.get(y, 0)} for y in years]

    # === 4. IPC expiry ===
    ipc_quarterly = Counter()
    ipc_urgent = []
    ipc_expired = 0
    for c in active:
        till = c.get("IPCValidTill")
        if not till:
            continue
        dt = parse_date(till)
        if not dt:
            continue
        qtr = f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"
        ipc_quarterly[qtr] += 1
        if dt < NOW:
            ipc_expired += 1
        elif dt <= datetime(2026, 6, 14):
            ipc_urgent.append({
                "name": c["CharityIPCName"],
                "sector": c.get("PrimarySector", ""),
                "expiry": dt.strftime("%Y-%m-%d"),
            })

    ipc_urgent.sort(key=lambda x: x["expiry"])
    ipc_quarters = [{"quarter": q, "count": ipc_quarterly[q]}
                    for q in sorted(ipc_quarterly.keys()) if q >= "2026"]

    # === 5. Financials ===
    latest_fin = {}
    for fin in financials:
        uen = fin.get("_uen", "")
        for fi in fin.get("FinancialInfos", []):
            inc = fi.get("Income", "N.A")
            spend = fi.get("Spending", "N.A")
            if inc != "N.A" and spend != "N.A":
                try:
                    income = float(inc)
                    spending = float(spend)
                    period = fi.get("FYPeriod", "")
                    if uen not in latest_fin or period > latest_fin[uen]["period"]:
                        charity = charities_map.get(uen, {})
                        latest_fin[uen] = {
                            "name": fin.get("CharityName", ""),
                            "income": income,
                            "spending": spending,
                            "period": period,
                            "sector": charity.get("PrimarySector", ""),
                        }
                except:
                    pass

    fin_list = list(latest_fin.values())
    total_income = sum(f["income"] for f in fin_list)

    # Income brackets
    brackets = [
        (0, 50000, "<$50K"), (50000, 250000, "$50K-250K"),
        (250000, 1000000, "$250K-1M"), (1000000, 5000000, "$1M-5M"),
        (5000000, 10000000, "$5M-10M"), (10000000, float("inf"), ">$10M"),
    ]
    income_dist = []
    for lo, hi, label in brackets:
        orgs = [f for f in fin_list if lo <= f["income"] < hi]
        income_dist.append({
            "label": label,
            "count": len(orgs),
            "total_income": round(sum(f["income"] for f in orgs) / 1e6, 1),
        })

    # Top 10 by income
    top_income = sorted(fin_list, key=lambda x: -x["income"])[:10]
    top_income_list = [{
        "name": f["name"],
        "income": round(f["income"] / 1e6, 1),
        "efficiency": round(f["spending"] / f["income"] * 100) if f["income"] > 0 else 0,
        "sector": f["sector"],
    } for f in top_income]

    # Sector financials
    sector_fin = defaultdict(lambda: {"count": 0, "income": 0, "spending": 0})
    for f in fin_list:
        s = f["sector"]
        sector_fin[s]["count"] += 1
        sector_fin[s]["income"] += f["income"]
        sector_fin[s]["spending"] += f["spending"]
    sector_financials = []
    for s in sorted(sector_fin.keys(), key=lambda x: -sector_fin[x]["income"]):
        d = sector_fin[s]
        sector_financials.append({
            "name": s,
            "count": d["count"],
            "income": round(d["income"] / 1e6, 1),
            "spending": round(d["spending"] / 1e6, 1),
            "avg_income": round(d["income"] / d["count"] / 1e6, 2) if d["count"] else 0,
            "efficiency": round(d["spending"] / d["income"] * 100) if d["income"] else 0,
        })

    # === 6. Geography ===
    region_map = {
        "01": "Central", "02": "Central", "03": "Central", "04": "Central", "05": "Central",
        "06": "Central", "07": "Central", "08": "Central", "09": "Central", "10": "Central",
        "11": "Central", "12": "Central", "48": "Central",
        "13": "East", "14": "East", "15": "East", "16": "East", "17": "East", "18": "East",
        "30": "East", "38": "East", "39": "East", "40": "East", "41": "East", "42": "East",
        "43": "East", "44": "East", "45": "East", "46": "East", "47": "East",
        "50": "East", "51": "East", "52": "East",
        "19": "North East", "20": "North East", "27": "North East", "28": "North East",
        "29": "North East", "31": "North East", "32": "North East", "33": "North East",
        "34": "North East", "49": "North East", "53": "North East", "54": "North East",
        "55": "North East", "56": "North East", "57": "North East", "82": "North East",
        "21": "West", "22": "West", "23": "West", "58": "West", "59": "West",
        "60": "West", "61": "West", "62": "West", "63": "West", "64": "West",
        "65": "West", "66": "West", "67": "West", "68": "West", "69": "West", "71": "West",
        "24": "North", "25": "North", "26": "North", "70": "North", "72": "North",
        "73": "North", "75": "North", "76": "North", "77": "North", "78": "North",
        "79": "North", "80": "North", "81": "North",
    }
    geo_region = Counter()
    geo_region_sector = defaultdict(Counter)
    for p in profiles.values():
        addr = p.get("Address") or ""
        postal = re.findall(r"(\d{6})\s*$", addr.strip())
        if postal:
            pc2 = postal[0][:2]
            region = region_map.get(pc2, "Other")
            geo_region[region] += 1
            uen = p.get("_uen", "")
            sector = charities_map.get(uen, {}).get("PrimarySector", "")
            geo_region_sector[region][sector] += 1

    geo_data = []
    for r in ["Central", "East", "West", "North", "North East"]:
        sectors_in_region = dict(geo_region_sector.get(r, {}))
        geo_data.append({"region": r, "count": geo_region.get(r, 0), "sectors": sectors_in_region})

    # === 7. Governance ===
    board_dist = Counter()
    for p in profiles.values():
        size = len(p.get("GoverningMembers", []))
        if size < 5:
            board_dist["<5"] += 1
        elif size < 10:
            board_dist["5-9"] += 1
        elif size < 15:
            board_dist["10-14"] += 1
        elif size < 20:
            board_dist["15-19"] += 1
        else:
            board_dist["20+"] += 1

    # Digital presence
    has_website = sum(1 for p in profiles.values()
                      if p.get("Website") and p["Website"] != "Not Applicable")
    has_email = sum(1 for p in profiles.values() if p.get("Email"))

    # === 8. Org list for search ===
    org_list = []
    for c in active:
        uen = c.get("UENNo", "")
        p = profiles.get(uen, {})
        obj = p.get("Objective") or p.get("VisionMission") or ""
        org_list.append({
            "n": c["CharityIPCName"],
            "u": uen,
            "s": c.get("PrimarySector", ""),
            "c": "|".join(c.get("PrimaryClassification", [])),
            "i": 1 if c.get("IPCStatus") == "Live" else 0,
            "y": parse_date(c.get("RegistrationDate")).year if parse_date(c.get("RegistrationDate")) else 0,
            "t": c.get("CharitySetup", ""),
            "d": obj[:150] if obj else "",
        })

    # === Assemble ===
    dashboard = {
        "stats": {
            "total": len(all_c),
            "active": total_active,
            "ipc": total_ipc,
            "dereg": len(dereg),
            "with_financials": len(fin_list),
            "total_income_m": round(total_income / 1e6, 0),
            "total_employees": 84264,
            "avg_age": 24.1,
        },
        "sectors": sectors,
        "timeline": timeline,
        "ipc": {
            "quarters": ipc_quarters,
            "urgent": ipc_urgent[:30],
            "expired_count": ipc_expired,
        },
        "financials": {
            "income_dist": income_dist,
            "top_income": top_income_list,
            "by_sector": sector_financials,
        },
        "geo": geo_data,
        "governance": {
            "board_dist": dict(board_dist),
            "has_website": has_website,
            "has_email": has_email,
            "total_profiles": len(profiles),
        },
        "orgs": org_list,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, ensure_ascii=False)
    size_kb = os.path.getsize(OUT) / 1024
    print(f"Dashboard data: {OUT} ({size_kb:.0f} KB)")
    print(f"  {len(org_list)} orgs, {len(sectors)} sectors, {len(timeline)} years")


if __name__ == "__main__":
    main()
