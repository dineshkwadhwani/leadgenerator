"""
Generic Selenium-based lead scraper.

Input columns expected (case-insensitive):
- Location
- Org name
- Org Type

Output columns:
- Exact Match
- Closest Match
- Source
- Address
- Google Map Link
- Contact Person Name
- Phone Number
- Website
- Email Address
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"selenium_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


INPUT_ALIASES = {
    "location": ["location", "city", "city_name", "taluka_name", "_taluka_name"],
    "org_name": ["org name", "organization name", "school_name", "org_name", "name"],
    "org_type": ["org type", "org_type", "type"],
}

OUTPUT_ALIASES = {
    "Exact Match": ["exact match"],
    "Closest Match": ["closest match"],
    "Source": ["source", "sour ce"],
    "Address": ["address"],
    "Google Map Link": ["google map link", "gmaps link", "gmaps_link"],
    "Contact Person Name": ["contact person name", "contact person"],
    "Phone Number": ["phone number", "contact number", "phone"],
    "Website": ["website"],
    "Email Address": ["email address", "email"],
    "Hours of Operation": ["hours of operation", "hours_of_operation"],
}

STOPWORDS = {
    "the",
    "and",
    "of",
    "for",
    "in",
    "at",
    "public",
    "private",
    "ltd",
    "limited",
    "pvt",
    "pune",
}

INVALID_PHONE_VALUES = {
    "9999999999",
    "9999999976",
    "9999999776",
    "9876543210",
    "9123456789",
    "1234567890",
    "9138075055",
}


@dataclass
class Candidate:
    name: str
    link: str
    score: float


class GenericLeadScraper:
    def __init__(self) -> None:
        self.driver = None
        self.wait = None
        self.progress_file = "selenium_progress.json"
        self.cache_version = 6
        self.progress = self._load_progress()

    def setup_driver(self) -> None:
        logger.info("Setting up Chrome driver...")
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 12)
        logger.info("Chrome driver ready")

    def close(self) -> None:
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
            self.wait = None
            logger.info("Browser closed")

    def _ensure_driver(self) -> None:
        if self.driver is None:
            self.setup_driver()
            return
        try:
            _ = self.driver.current_url
        except Exception:
            logger.warning("WebDriver session dropped. Reinitializing browser.")
            self.close()
            self.setup_driver()

    def _load_progress(self) -> Dict[str, Dict[str, str]]:
        path = Path(self.progress_file)
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}

    def _save_progress(self) -> None:
        Path(self.progress_file).write_text(json.dumps(self.progress, indent=2))

    @staticmethod
    def _norm_space(value: str) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()

    @staticmethod
    def _tokens(value: str) -> List[str]:
        return [
            t
            for t in re.findall(r"[a-z0-9]+", value.lower())
            if len(t) >= 2 and t not in STOPWORDS
        ]

    def _location_tokens(self, location: str) -> List[str]:
        """Build meaningful location tokens for strict local filtering."""
        drop = {"mnp", "municipal", "corporation", "city"}
        return [t for t in self._tokens(location) if t not in drop and len(t) >= 3]

    def _is_location_match(self, location: str, text: str) -> bool:
        """Accept a candidate only when location hints are present in evidence text."""
        loc_tokens = self._location_tokens(location)
        if not loc_tokens:
            return True
        haystack = (text or "").lower()
        hits = sum(1 for token in loc_tokens if token in haystack)
        required = 1 if len(loc_tokens) <= 2 else 2
        return hits >= required

    def _expand_abbrev(self, name: str) -> str:
        s = f" {self._norm_space(name).lower()} "
        repl = {
            " pri ": " primary ",
            " pri. ": " primary ",
            " sec ": " secondary ",
            " sec. ": " secondary ",
            " sch ": " school ",
            " sch. ": " school ",
            " eng ": " english ",
            " med ": " medium ",
            " clg ": " college ",
            " inst ": " institute ",
        }
        for k, v in repl.items():
            s = s.replace(k, v)
        return self._norm_space(s)

    def _trim_address_terms(self, org_name: str, location: str) -> str:
        s = f" {self._expand_abbrev(org_name).lower()} "
        drop = set(self._tokens(location) + ["pune", "district", "taluka", "mnp", "municipal"])
        for token in drop:
            s = re.sub(rf"\b{re.escape(token)}\b", " ", s)
        s = re.sub(r"\b\d{1,4}\b", " ", s)
        return self._norm_space(s)

    def _search_queries(self, org_name: str, location: str, org_type: str) -> List[str]:
        base_variants = []
        full = self._norm_space(org_name)
        if full:
            base_variants.append(full)
        expanded = self._expand_abbrev(full)
        if expanded and expanded.lower() != full.lower():
            base_variants.append(expanded)
        trimmed = self._trim_address_terms(full, location)
        if trimmed and trimmed.lower() not in {b.lower() for b in base_variants}:
            base_variants.append(trimmed)

        q = []
        for b in base_variants:
            q.append(f"{b} {location} {org_type}")
            q.append(f"{b} {location}")
            q.append(f"{b} {org_type} pune")
        out = []
        seen = set()
        for item in q:
            key = item.lower().strip()
            if key and key not in seen:
                seen.add(key)
                out.append(item)
        return out

    def _name_similarity(self, target: str, candidate: str) -> float:
        t = set(self._tokens(self._expand_abbrev(target)))
        c = set(self._tokens(self._expand_abbrev(candidate)))
        if not t or not c:
            return 0.0
        inter = len(t & c)
        return (2.0 * inter) / (len(t) + len(c))

    def _is_valid_phone(self, value: str) -> bool:
        if not value or value == "Not Found":
            return False
        digits = re.sub(r"\D", "", value)
        if len(digits) < 10:
            return False
        last10 = digits[-10:]
        if last10 in INVALID_PHONE_VALUES:
            return False
        if len(set(last10)) == 1:
            return False
        return True

    def _extract_phone(self, text: str) -> str:
        if not text:
            return "Not Found"
        patterns = [
            r"(?:\+91[\s\-]?)?[6-9]\d{9}",
            r"(?:\+91[\s\-]?)?0\d{2,4}[\s\-]?\d{6,8}",
            r"\+?\d[\d\s\-\.]{7,16}\d",
        ]
        for pat in patterns:
            for raw in re.findall(pat, text):
                d = re.sub(r"\D", "", raw)
                if len(d) >= 10:
                    # Keep Indian landline numbers with leading STD code 0.
                    if len(d) == 11 and d.startswith("0"):
                        val = d
                    elif len(d) == 12 and d.startswith("910"):
                        val = d[2:]
                    else:
                        val = d[-10:]
                    if self._is_valid_phone(val):
                        return val
        return "Not Found"

    def _normalize_url(self, url: str) -> str:
        if not url:
            return ""
        cleaned = str(url).strip().replace("&amp;", "&").replace("\\u003d", "=")
        parsed = urlparse(cleaned)
        if "google." in parsed.netloc:
            q = parse_qs(parsed.query)
            redirect = q.get("q", q.get("url", [""]))[0]
            if redirect:
                cleaned = unquote(redirect)
        if "&" in cleaned:
            cleaned = cleaned.split("&", 1)[0]
        cleaned = cleaned.rstrip('.,);]"\'\\')
        p2 = urlparse(cleaned)
        if p2.scheme and p2.netloc:
            return f"{p2.scheme}://{p2.netloc}{p2.path}".rstrip("/")
        return cleaned

    def _is_valid_site(self, url: str) -> bool:
        u = self._normalize_url(url)
        if not u:
            return False
        l = u.lower()
        host = (urlparse(l).netloc or "").lower()
        blocked = [
            "schema.org",
            "google.",
            "gstatic.com",
            "googleapis.com",
            "googleusercontent.com",
            "ggpht.com",
            "jdmagicbox.com",
            "taboola.com",
            "maps.app.goo.gl",
            "facebook.com",
            "twitter.com",
            "instagram.com",
            "youtube.com",
            "linkedin.com",
            "whatsapp.com",
            "justdial.com",
            "bing.com",
        ]
        return l.startswith(("http://", "https://")) and host and not any(b in l for b in blocked)

    def _extract_email(self, text: str) -> str:
        if not text:
            return "Not Found"
        for m in re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text):
            ml = m.lower()
            if "noreply" in ml:
                continue
            return m
        return "Not Found"

    def _extract_site(self, text: str) -> str:
        if not text:
            return "Not Found"
        for u in re.findall(r"https?://[^\s\"\'<>\)]+", text):
            n = self._normalize_url(u)
            if self._is_valid_site(n):
                return n
        return "Not Found"

    def _extract_contact_person(self, text: str) -> str:
        if not text:
            return "Not Found"
        patterns = [
            r"(?:Principal|Headmaster|Headmistress|Director|Chairman|Owner|Founder)\s*[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
            r"\b(Mr|Mrs|Ms|Dr)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                if len(m.groups()) >= 2 and m.group(1) in ["Mr", "Mrs", "Ms", "Dr"]:
                    return f"{m.group(1)} {m.group(2)}"
                return m.group(1)
        return "Not Found"

    def _text_match_fraction(self, target: str, text: str) -> float:
        target_tokens = set(self._tokens(self._expand_abbrev(target)))
        if not target_tokens:
            return 0.0
        lowered = (text or "").lower()
        hits = sum(1 for token in target_tokens if token in lowered)
        return hits / len(target_tokens)

    def _extract_address(self) -> str:
        selectors = [
            '[data-item-id="address"]',
            'button[data-item-id="address"]',
            '[aria-label*="Address"]',
            '[aria-label*="address"]',
            'button[jsaction*="address"]',
            '[data-section-id="adr_adr"]',
        ]
        for s in selectors:
            try:
                elems = self.driver.find_elements(By.CSS_SELECTOR, s)
                for e in elems:
                    txt = self._norm_space(f"{e.text} {e.get_attribute('aria-label') or ''}")
                    # Strip icon characters and the word "Address" from the label
                    txt = re.sub(r"[\ue000-\uf8ff]", "", txt).strip()
                    txt = re.sub(r"(?i)\baddress\b[:\s]*", "", txt).strip()
                    if txt and len(txt) > 5:
                        return txt
            except Exception:
                continue
        # Fallback: scan visible text for address-like patterns (PIN code or city names)
        try:
            visible = self.driver.execute_script("return document.body ? document.body.innerText : ''; ") or ""
            pin = re.search(r"[A-Za-z ,.-]+(?:Maharashtra|Gujarat|Karnataka|Tamil Nadu|Delhi)[A-Za-z ,.-]*\d{6}", visible)
            if pin:
                raw = pin.group(0).strip().strip(",")
                if len(raw) > 10:
                    return self._norm_space(raw)
        except Exception:
            pass
        return "Not Found"

    def _extract_hours(self) -> str:
        selectors = [
            'button[data-item-id="oh"]',
            '[aria-label*="Hours"]',
            '[aria-label*="Open"]',
            '[aria-label*="Closes"]',
        ]
        for s in selectors:
            try:
                elems = self.driver.find_elements(By.CSS_SELECTOR, s)
                for e in elems:
                    txt = self._norm_space(f"{e.text} {e.get_attribute('aria-label') or ''}")
                    if txt and txt.lower() not in {"hours", "open", "opens"}:
                        return txt
            except Exception:
                continue
        return "Not Found"

    def _collect_map_candidates(self, org_name: str, location: str, org_type: str) -> Tuple[List[Candidate], str]:
        last_url = ""
        for query in self._search_queries(org_name, location, org_type):
            url = f"https://www.google.com/maps/search/{quote_plus(query)}"
            try:
                self._ensure_driver()
                self.driver.get(url)
                time.sleep(2.5)
                last_url = self.driver.current_url or url
            except (InvalidSessionIdException, WebDriverException):
                logger.warning("WebDriver disconnected during maps search; retrying next query.")
                self.close()
                continue

            candidates: List[Candidate] = []
            try:
                nodes = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
                for node in nodes[:20]:
                    label = self._norm_space(node.text or node.get_attribute("aria-label") or "")
                    link = node.get_attribute("href") or ""
                    if label and "/maps/place/" in link:
                        score = self._name_similarity(org_name, label)
                        candidates.append(Candidate(label, link, score))
            except Exception:
                pass

            if "/maps/place/" in (self.driver.current_url or ""):
                title = self._norm_space((self.driver.title or "").replace(" - Google Maps", ""))
                if title:
                    candidates.append(Candidate(title, self.driver.current_url, self._name_similarity(org_name, title)))

            uniq = {}
            for c in candidates:
                key = c.link or c.name
                if key not in uniq or c.score > uniq[key].score:
                    uniq[key] = c
            deduped = sorted(uniq.values(), key=lambda x: x.score, reverse=True)
            if deduped:
                return deduped, last_url

        return [], last_url

    def _extract_from_current_page(self) -> Dict[str, str]:
        page = self.driver.page_source or ""
        try:
            visible = self.driver.execute_script("return document.body ? document.body.innerText : ''; ") or ""
        except Exception:
            visible = ""
        blob = f"{visible}\n{page}"

        phone = "Not Found"
        selectors = [
            '[data-item-id="phone"]',
            'button[aria-label*="Phone"]',
            'button[aria-label*="Call"]',
            '[aria-label*="Phone:"]',
        ]
        for s in selectors:
            try:
                elems = self.driver.find_elements(By.CSS_SELECTOR, s)
                for e in elems:
                    txt = f"{e.text} {e.get_attribute('aria-label') or ''}"
                    phone = self._extract_phone(txt)
                    if phone != "Not Found":
                        break
            except Exception:
                pass
            if phone != "Not Found":
                break

        if phone == "Not Found":
            phone = self._extract_phone(blob)

        return {
            "Address": self._extract_address(),
            "Contact Person Name": self._extract_contact_person(blob),
            "Phone Number": phone,
            "Website": self._extract_site(blob),
            "Email Address": self._extract_email(blob),
            "Hours of Operation": self._extract_hours(),
        }

    def _search_google_maps(self, org_name: str, location: str, org_type: str) -> Dict[str, str]:
        candidates, last_url = self._collect_map_candidates(org_name, location, org_type)
        base = {
            "Exact Match": "Not Found",
            "Closest Match": "Not Found",
            "Source": "Not Found",
            "Address": "Not Found",
            "Google Map Link": "Not Found",
            "Contact Person Name": "Not Found",
            "Phone Number": "Not Found",
            "Website": "Not Found",
            "Email Address": "Not Found",
            "Hours of Operation": "Not Found",
        }

        if not candidates:
            # Some Maps pages render place details directly in the side panel but
            # expose no /maps/place/ anchors. In that case, extract from the
            # current page instead of failing hard.
            try:
                if last_url:
                    self.driver.get(last_url)
                    time.sleep(2.5)
                visible = self.driver.execute_script(
                    "return document.body ? document.body.innerText : ''; "
                ) or ""
                name_score = self._text_match_fraction(org_name, visible)
                if name_score >= 0.80 and self._is_location_match(location, visible):
                    details = self._extract_from_current_page()
                    base["Exact Match"] = "Yes" if name_score >= 0.95 else "No"
                    base["Closest Match"] = org_name
                    base["Source"] = "Google Maps"
                    base["Google Map Link"] = self.driver.current_url or last_url or "Not Found"
                    base.update(details)
                    if not self._is_valid_phone(base["Phone Number"]):
                        base["Phone Number"] = "Not Found"
                    if not self._is_valid_site(base["Website"]):
                        base["Website"] = "Not Found"
            except Exception:
                pass
            return base

        exact = [c for c in candidates if c.score >= 0.90]
        ranked = exact + [c for c in candidates if c not in exact]

        for idx, chosen in enumerate(ranked):
            # Reject low-confidence map matches to avoid wrong businesses.
            if chosen.score < 0.55:
                continue

            try:
                self.driver.get(chosen.link)
                time.sleep(3.0)
                current_link = self.driver.current_url or chosen.link
                details = self._extract_from_current_page()

                # Build evidence for location matching; also include raw visible page
                # text so the check works even when CSS selectors miss the address.
                try:
                    page_visible = self.driver.execute_script(
                        "return document.body ? document.body.innerText : ''; "
                    ) or ""
                except Exception:
                    page_visible = ""

                evidence = " ".join([
                    chosen.name,
                    details.get("Address", ""),
                    current_link,
                    page_visible[:3000],
                ])
                # For near-exact name matches (score >= 0.85) that have landed on a
                # real place page, skip the location filter — the name alone is
                # strong enough signal and the address may not have been extracted.
                if chosen.score < 0.85 and not self._is_location_match(location, evidence):
                    continue

                base["Exact Match"] = "Yes" if chosen in exact else "No"
                base["Closest Match"] = chosen.name
                base["Source"] = "Google Maps"
                base["Google Map Link"] = current_link
                base.update(details)

                if not self._is_valid_phone(base["Phone Number"]):
                    base["Phone Number"] = "Not Found"
                if not self._is_valid_site(base["Website"]):
                    base["Website"] = "Not Found"

                if len(ranked) > 1 and idx > 0 and base["Exact Match"] != "Yes":
                    base["Exact Match"] = "No"

                return base
            except Exception:
                continue

        # No location-valid candidate found.
        return base

    def _search_justdial(self, org_name: str, location: str, org_type: str) -> Dict[str, str]:
        out = {
            "Source": "Not Found",
            "Address": "Not Found",
            "Contact Person Name": "Not Found",
            "Phone Number": "Not Found",
            "Website": "Not Found",
            "Email Address": "Not Found",
        }
        try:
            self._ensure_driver()
            q = quote_plus(f"{org_name} {location} {org_type}")
            self.driver.get(f"https://www.justdial.com/search?kw={q}")
            time.sleep(2.5)
            visible = self.driver.execute_script("return document.body ? document.body.innerText : ''; ") or ""
            blob = f"{self.driver.page_source}\n{visible}"

            # Only accept fallback if page content substantially matches org name.
            if self._text_match_fraction(org_name, blob) < 0.7:
                return out

            out["Phone Number"] = self._extract_phone(blob)
            out["Website"] = self._extract_site(blob)
            out["Email Address"] = self._extract_email(blob)
            out["Contact Person Name"] = self._extract_contact_person(blob)
            if out["Phone Number"] != "Not Found" or out["Website"] != "Not Found" or out["Email Address"] != "Not Found":
                out["Source"] = "JustDial"
            if not self._is_valid_phone(out["Phone Number"]):
                out["Phone Number"] = "Not Found"
            if not self._is_valid_site(out["Website"]):
                out["Website"] = "Not Found"
            if out["Phone Number"] == "Not Found" and out["Website"] == "Not Found" and out["Email Address"] == "Not Found":
                out["Source"] = "Not Found"
        except Exception:
            pass
        return out

    def process_one(self, location: str, org_name: str, org_type: str) -> Dict[str, str]:
        key = f"{location}||{org_name}||{org_type}".lower()
        if key in self.progress:
            cached = self.progress[key]
            if cached.get("cache_version") == self.cache_version:
                return cached

        result = self._search_google_maps(org_name, location, org_type)

        if (
            result["Phone Number"] == "Not Found"
            and result["Website"] == "Not Found"
            and result["Email Address"] == "Not Found"
        ):
            fb = self._search_justdial(org_name, location, org_type)
            for k in ["Phone Number", "Website", "Email Address", "Contact Person Name", "Address"]:
                if result.get(k, "Not Found") == "Not Found" and fb.get(k, "Not Found") != "Not Found":
                    result[k] = fb[k]
            if fb.get("Source") != "Not Found":
                result["Source"] = fb["Source"]

            if result["Google Map Link"] == "Not Found":
                retry_name = result.get("Closest Match", "")
                if not retry_name or retry_name == "Not Found":
                    retry_name = org_name
                maps_retry = self._search_google_maps(retry_name, location, org_type)
                if maps_retry["Google Map Link"] != "Not Found":
                    result["Google Map Link"] = maps_retry["Google Map Link"]
                    if result["Address"] == "Not Found":
                        result["Address"] = maps_retry["Address"]

        for k in [
            "Exact Match",
            "Closest Match",
            "Source",
            "Address",
            "Google Map Link",
            "Contact Person Name",
            "Phone Number",
            "Website",
            "Email Address",
            "Hours of Operation",
        ]:
            if not result.get(k):
                result[k] = "Not Found"

        result["cache_version"] = self.cache_version
        self.progress[key] = result
        self._save_progress()
        return result


def _resolve_col(df: pd.DataFrame, choices: List[str]) -> Optional[str]:
    lowered = {c.lower().strip(): c for c in df.columns}
    for choice in choices:
        key = choice.lower().strip()
        if key in lowered:
            return lowered[key]
    return None


def _resolve_or_create_output_cols(df: pd.DataFrame) -> Dict[str, str]:
    resolved: Dict[str, str] = {}
    lowered = {c.lower().strip(): c for c in df.columns}

    for logical_name, aliases in OUTPUT_ALIASES.items():
        found = None
        for alias in aliases:
            key = alias.lower().strip()
            if key in lowered:
                found = lowered[key]
                break
        if not found:
            found = logical_name
            df[found] = "Not Found"
            lowered[found.lower().strip()] = found
        resolved[logical_name] = found

    # Ensure assignment is dtype-safe for mixed text output values.
    for col in set(resolved.values()):
        df[col] = df[col].astype("object")

    return resolved


def _prepare_input(df: pd.DataFrame) -> Tuple[pd.DataFrame, str, str, str]:
    loc_col = _resolve_col(df, INPUT_ALIASES["location"])
    name_col = _resolve_col(df, INPUT_ALIASES["org_name"])
    type_col = _resolve_col(df, INPUT_ALIASES["org_type"])

    if not loc_col or not name_col or not type_col:
        raise ValueError("Input sheet must include columns for Location, Org name, and Org Type")

    return df, loc_col, name_col, type_col


def main() -> None:
    print(
        """
======================================================================
Generic Org Lead Scraper (Google Maps First)
======================================================================
"""
    )

    if len(sys.argv) < 2:
        print("Usage: python selenium_scraper.py INPUT.xlsx")
        sys.exit(1)

    input_file = sys.argv[1]
    try:
        df = pd.read_excel(input_file)
    except Exception as exc:
        logger.error("Failed to read input file: %s", exc)
        sys.exit(1)

    try:
        df, loc_col, name_col, type_col = _prepare_input(df)
    except ValueError as exc:
        logger.error(str(exc))
        sys.exit(1)

    logger.info("Using columns -> Location: %s, Org name: %s, Org Type: %s", loc_col, name_col, type_col)

    scraper = GenericLeadScraper()
    try:
        scraper.setup_driver()
        total = len(df)
        output_cols = _resolve_or_create_output_cols(df)
        output_file = input_file.replace(".xlsx", "_SELENIUM_LEADS.xlsx")
        checkpoint_every = 25

        for i, row in df.iterrows():
            location = GenericLeadScraper._norm_space(row.get(loc_col, ""))
            org_name = GenericLeadScraper._norm_space(row.get(name_col, ""))
            org_type = GenericLeadScraper._norm_space(row.get(type_col, ""))

            if not location or not org_name or not org_type:
                result = {
                    "Exact Match": "Not Found",
                    "Closest Match": "Not Found",
                    "Source": "Not Found",
                    "Address": "Not Found",
                    "Google Map Link": "Not Found",
                    "Contact Person Name": "Not Found",
                    "Phone Number": "Not Found",
                    "Website": "Not Found",
                    "Email Address": "Not Found",
                    "Hours of Operation": "Not Found",
                }
            else:
                logger.info("[%s/%s] %s | %s | %s", i + 1, total, org_name, location, org_type)
                try:
                    result = scraper.process_one(location, org_name, org_type)
                except Exception as exc:
                    logger.error("Row failed (%s): %s", org_name, exc)
                    result = {
                        "Exact Match": "Not Found",
                        "Closest Match": "Not Found",
                        "Source": "Not Found",
                        "Address": "Not Found",
                        "Google Map Link": "Not Found",
                        "Contact Person Name": "Not Found",
                        "Phone Number": "Not Found",
                        "Website": "Not Found",
                        "Email Address": "Not Found",
                        "Hours of Operation": "Not Found",
                    }

            for logical_name, actual_col in output_cols.items():
                df.at[i, actual_col] = result.get(logical_name, "Not Found")

            if (i + 1) % checkpoint_every == 0:
                df.to_excel(output_file, index=False, engine="openpyxl")
                logger.info("Checkpoint saved: %s (%s/%s rows)", output_file, i + 1, total)
            time.sleep(0.5)

        df.to_excel(output_file, index=False, engine="openpyxl")

        print("\n======================================================================")
        print("SUMMARY")
        print("======================================================================")
        print(f"Rows processed: {len(df)}")
        print(f"Exact matches: {(df[output_cols['Exact Match']] == 'Yes').sum()}")
        print(f"Phones found: {(df[output_cols['Phone Number']] != 'Not Found').sum()}")
        print(f"Websites found: {(df[output_cols['Website']] != 'Not Found').sum()}")
        print(f"Emails found: {(df[output_cols['Email Address']] != 'Not Found').sum()}")
        print(f"Saved: {output_file}")
        print("======================================================================")

    finally:
        scraper.close()


if __name__ == "__main__":
    main()
