"""
Scraper service wrapping python-jobspy.
Returns a list of raw job dicts.
"""
from jobspy import scrape_jobs
import pandas as pd


def run_scrape(limit: int, search_term: str = "software engineer", location: str = "United States") -> list[dict]:
    """
    Scrape LinkedIn and Indeed for jobs matching search_term.
    Returns up to `limit` jobs as a list of dicts.
    """
    try:
        jobs_df: pd.DataFrame = scrape_jobs(
            site_name=["linkedin", "indeed"],
            search_term=search_term,
            location=location,
            results_wanted=limit,
            hours_old=72,          # only jobs posted in last 3 days
            country_indeed="USA",
        )
        return jobs_df.to_dict(orient="records")
    except Exception as e:
        # Log and return empty list rather than crashing the route
        print(f"[scraper] Error: {e}")
        return []
