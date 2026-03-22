"""Scrape giving.sg organisation listings using Playwright.

Scrapes all 3 tabs (Charities / Organisations / Groundups) from the listing page.
Each tab is paginated (30 per page). Data extracted from DOM card elements.

Usage:
    python3 scrape_givingsg.py              # scrape all tabs
    python3 scrape_givingsg.py --profiles   # also scrape individual profile pages
"""
import json
import os
import re
import sys
import time

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(DATA_DIR, "givingsg_organisations.json")
PROFILE_FILE = os.path.join(DATA_DIR, "givingsg_profiles.jsonl")

scrape_profiles = "--profiles" in sys.argv


def dismiss_cookie_banner(page):
    """Close the cookie consent popup if present."""
    try:
        accept = page.locator("button:has-text('Accept all')").first
        if accept.is_visible(timeout=3000):
            accept.click()
            page.wait_for_timeout(500)
            print("  Dismissed cookie banner")
    except:
        pass


def scrape_tab(page, tab_name, tab_index):
    """Scrape all pages for one tab. Returns list of org dicts."""
    orgs = []

    # Click the tab using role='tab'
    tabs = page.locator("[role='tab']").all()
    if tab_index < len(tabs):
        tabs[tab_index].click()
        page.wait_for_timeout(3000)
        print(f"  Clicked tab: {tabs[tab_index].inner_text().strip()}")

    # Get total count from "Explore N charities/organisations/groundups"
    try:
        explore_text = page.locator("text=/Explore \\d+/").first.inner_text()
        total = int(re.search(r'(\d+)', explore_text).group(1))
        print(f"  Total: {total}")
    except:
        total = 0
        print("  Could not determine total count")

    page_num = 0
    while True:
        page_num += 1

        # Extract cards from visible content
        cards = page.locator("[class*='card' i]").all()
        page_orgs = []
        seen = set()

        for card in cards:
            try:
                if not card.is_visible():
                    continue
                text = card.inner_text().strip()
                if not text or len(text) < 10:
                    continue

                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if not lines:
                    continue

                name = lines[0]
                if name in seen or len(name) < 3 or name in ("Filter by", "Sort", "Clear all", "Apply"):
                    continue
                seen.add(name)

                # Get profile link
                href = ""
                link = card.locator("a[href*='/organisation/']").first
                if link.count():
                    href = link.get_attribute("href") or ""
                if not href:
                    link = card.locator("a").first
                    if link.count():
                        href = link.get_attribute("href") or ""

                # Parse description and causes
                description = ""
                causes = []
                for line in lines[1:]:
                    # Causes are short tags, descriptions are long
                    if len(line) > 60:
                        if not description:
                            description = line
                    elif len(line) > 3 and len(line) < 50:
                        causes.append(line)

                # Get image
                image_url = ""
                img = card.locator("img").first
                if img.count():
                    image_url = img.get_attribute("src") or ""

                org = {
                    "name": name,
                    "description": description,
                    "causes": causes,
                    "profile_url": f"https://www.giving.sg{href}" if href and not href.startswith("http") else href,
                    "image_url": image_url,
                    "tab": tab_name,
                }
                page_orgs.append(org)
            except:
                continue

        if not page_orgs:
            print(f"  Page {page_num}: no orgs found, stopping.")
            break

        orgs.extend(page_orgs)
        print(f"  Page {page_num}: {len(page_orgs)} orgs (total: {len(orgs)})")

        # Check if we have all
        if total and len(orgs) >= total:
            break

        # Click next page via pagination nav buttons
        try:
            next_page_num = page_num + 1
            # Look for the next page number button in nav
            nav_btns = page.locator("nav button").all()
            clicked = False
            for btn in nav_btns:
                btn_text = btn.inner_text().strip()
                if btn_text == str(next_page_num):
                    btn.click()
                    page.wait_for_timeout(2500)
                    clicked = True
                    break

            if not clicked:
                # Try clicking a "next" arrow (usually last nav button)
                if nav_btns:
                    last_btn = nav_btns[-1]
                    last_text = last_btn.inner_text().strip()
                    if last_text in ("›", "»", ">", ""):
                        last_btn.click()
                        page.wait_for_timeout(2500)
                        clicked = True

            if not clicked:
                print("  No next page button found, stopping.")
                break
        except Exception as e:
            print(f"  Pagination error: {e}")
            break

    return orgs


def scrape_profile(page, url):
    """Scrape detailed info from an individual profile page."""
    try:
        page.goto(url, wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(2000)

        profile = {"url": url}

        # Name
        h1 = page.locator("h1").first
        if h1.count():
            profile["name"] = h1.inner_text().strip()

        # Try clicking "See more" to expand description
        try:
            see_more = page.locator("text=See more").first
            if see_more.is_visible(timeout=1000):
                see_more.click()
                page.wait_for_timeout(500)
        except:
            pass

        # Full page text for pattern extraction
        body_text = page.inner_text("body")

        # Email
        emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', body_text)
        if emails:
            profile["email"] = emails[0]

        # Phone
        phones = re.findall(r'\b(?:\+65\s?)?[689]\d{7}\b', body_text)
        if phones:
            profile["phone"] = phones[0]

        # Website (non-giving.sg, non-social links)
        ext_links = page.locator("a[href^='http']:not([href*='giving.sg']):not([href*='facebook']):not([href*='instagram']):not([href*='sentry'])").all()
        for link in ext_links[:5]:
            href = link.get_attribute("href") or ""
            if href and not any(x in href for x in ["giving.sg", "sentry", "outsystems", "google"]):
                profile["website"] = href
                break

        # Social media
        social = {}
        for platform, pattern in [("facebook", "facebook.com"), ("instagram", "instagram.com")]:
            link = page.locator(f"a[href*='{pattern}']").first
            if link.count():
                social[platform] = link.get_attribute("href")
        if social:
            profile["social"] = social

        return profile
    except Exception as e:
        return {"url": url, "_error": str(e)}


def main():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 900},
        )

        # Navigate to listing page
        print("=== Navigating to giving.sg/organisations ===")
        page.goto("https://www.giving.sg/organisations", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)
        dismiss_cookie_banner(page)

        all_orgs = []
        tabs = [("charity", 0), ("organisation", 1), ("groundup", 2)]

        for tab_name, tab_idx in tabs:
            print(f"\n=== Tab: {tab_name} ===")
            tab_orgs = scrape_tab(page, tab_name, tab_idx)
            all_orgs.extend(tab_orgs)

        # Save
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_orgs, f, ensure_ascii=False, indent=2)
        print(f"\n=== Saved {len(all_orgs)} organisations to {OUTPUT_FILE} ===")

        by_tab = {}
        for o in all_orgs:
            t = o.get("tab", "?")
            by_tab[t] = by_tab.get(t, 0) + 1
        for t, c in by_tab.items():
            print(f"  {t}: {c}")

        # Scrape profiles if requested
        if scrape_profiles:
            print(f"\n=== Scraping individual profiles ===")
            done_urls = set()
            if os.path.exists(PROFILE_FILE):
                with open(PROFILE_FILE) as f:
                    for line in f:
                        try:
                            done_urls.add(json.loads(line).get("url"))
                        except:
                            pass
                print(f"  Resuming: {len(done_urls)} already done")

            to_scrape = [o for o in all_orgs if o.get("profile_url") and o["profile_url"] not in done_urls]
            print(f"  To scrape: {len(to_scrape)}")

            pf = open(PROFILE_FILE, "a", encoding="utf-8")
            try:
                for i, org in enumerate(to_scrape):
                    profile = scrape_profile(page, org["profile_url"])
                    profile["_tab"] = org.get("tab", "")
                    pf.write(json.dumps(profile, ensure_ascii=False) + "\n")

                    if (i + 1) % 10 == 0:
                        pf.flush()
                        print(f"  [{i+1}/{len(to_scrape)}] {profile.get('name', '?')[:40]}")

                    time.sleep(1)
            finally:
                pf.close()

        browser.close()


if __name__ == "__main__":
    main()
