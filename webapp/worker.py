"""Background scraper worker thread."""
import sys
import logging
import threading
import time
from pathlib import Path

import pandas as pd

# Allow importing the root-level selenium_scraper
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import update_job  # noqa: E402 – relative within webapp

logger = logging.getLogger(__name__)


def _headless_setup(scraper):
    """Patch Chrome options to add headless flag for server deployments."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36"
    )
    scraper.driver = webdriver.Chrome(options=options)
    scraper.wait = WebDriverWait(scraper.driver, 12)


def run_job(job_id: str, input_path: str, output_path: str):
    """Entry point run in a daemon thread."""
    try:
        from selenium_scraper import (
            GenericLeadScraper,
            _prepare_input,
            _resolve_or_create_output_cols,
        )

        update_job(job_id, status="processing", message="Starting browser...")

        df = pd.read_excel(input_path)
        df, loc_col, name_col, type_col = _prepare_input(df)
        output_cols = _resolve_or_create_output_cols(df)
        total = len(df)

        scraper = GenericLeadScraper()
        _headless_setup(scraper)

        EMPTY = {k: "Not Found" for k in [
            "Exact Match", "Closest Match", "Source", "Address",
            "Google Map Link", "Contact Person Name", "Phone Number",
            "Website", "Email Address", "Hours of Operation",
        ]}

        try:
            for i, row in df.iterrows():
                location = GenericLeadScraper._norm_space(row.get(loc_col, ""))
                org_name = GenericLeadScraper._norm_space(row.get(name_col, ""))
                org_type = GenericLeadScraper._norm_space(row.get(type_col, ""))

                update_job(job_id,
                           message=f"Processing {i + 1} of {total}...",
                           processed=i + 1)

                if location and org_name and org_type:
                    try:
                        result = scraper.process_one(location, org_name, org_type)
                    except Exception as exc:
                        logger.warning("Row %s failed: %s", i + 1, exc)
                        result = EMPTY.copy()
                else:
                    result = EMPTY.copy()

                for logical, actual_col in output_cols.items():
                    df.at[i, actual_col] = result.get(logical, "Not Found")
        finally:
            scraper.close()

        note_row = {c: "" for c in df.columns}
        first_col = df.columns[0]
        note_row[first_col] = "Please fill only first three columns."
        out_df = pd.concat([pd.DataFrame([note_row]), df], ignore_index=True)

        out_df.to_excel(output_path, index=False, engine="openpyxl")
        update_job(job_id, status="complete",
                   message=f"Done — {total} rows processed.",
                   processed=total)
        logger.info("Job %s complete → %s", job_id, output_path)

    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        update_job(job_id, status="failed", message=str(exc))


def start(job_id: str, input_path: str, output_path: str):
    """Spawn a daemon thread for the scraper job."""
    t = threading.Thread(target=run_job,
                         args=(job_id, input_path, output_path),
                         daemon=True)
    t.start()
    return t
