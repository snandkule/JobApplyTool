"""Indeed job scraper."""
import re
from datetime import datetime
from typing import List, Optional

from backend.app.automation.browser import BrowserManager
from backend.app.database.session import SessionLocal
from backend.app.models import Job

try:
    from playwright.async_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = None


class IndeedScraper:
    """Scrape job listings from Indeed."""

    BASE_URL = "https://www.indeed.com"

    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize Indeed scraper.

        Args:
            browser_manager: Browser manager instance
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required for scraping")

        self.browser = browser_manager

    async def search_jobs(
        self,
        keywords: str,
        location: str = "",
        remote: bool = False,
        max_results: int = 25,
    ) -> List[dict]:
        """
        Search for jobs on Indeed.

        Args:
            keywords: Job title or keywords
            location: Location filter
            remote: Filter for remote jobs
            max_results: Maximum results to return

        Returns:
            List of job dictionaries
        """
        page = await self.browser.new_page()

        try:
            # Build search URL
            params = {
                "q": keywords,
                "l": location,
            }

            if remote:
                params["sc"] = "0kf:attr(DSQF7);"  # Remote filter

            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{self.BASE_URL}/jobs?{query_string}"

            await page.goto(url, wait_until="networkidle")

            # Wait for results
            await page.wait_for_selector("div.job_seen_beacon", timeout=10000)

            # Extract job cards
            jobs = []
            job_cards = await page.query_selector_all("div.job_seen_beacon")

            for idx, card in enumerate(job_cards[:max_results]):
                try:
                    job_data = await self._extract_job_card_data(card, page)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    print(f"Error extracting job {idx}: {e}")
                    continue

            return jobs

        finally:
            await page.close()

    async def _extract_job_card_data(self, card, page: Page) -> Optional[dict]:
        """Extract data from Indeed job card."""
        try:
            # Extract job title
            title_elem = await card.query_selector("h2.jobTitle a")
            title = await title_elem.inner_text() if title_elem else ""

            # Extract company
            company_elem = await card.query_selector("span.companyName")
            company = await company_elem.inner_text() if company_elem else ""

            # Extract location
            location_elem = await card.query_selector("div.companyLocation")
            location = await location_elem.inner_text() if location_elem else ""

            # Extract job URL and ID
            link = await title_elem.get_attribute("href") if title_elem else ""
            job_id = self._extract_job_id_from_url(link)
            full_url = f"{self.BASE_URL}{link}" if link.startswith("/") else link

            # Extract snippet (partial description)
            snippet_elem = await card.query_selector("div.job-snippet")
            snippet = await snippet_elem.inner_text() if snippet_elem else ""

            # Determine if remote
            is_remote = "remote" in location.lower() or "remote" in title.lower()

            return {
                "external_id": job_id,
                "platform": "indeed",
                "url": full_url,
                "title": title.strip(),
                "company": company.strip(),
                "location": location.strip(),
                "is_remote": is_remote,
                "description": snippet.strip(),
                "scraped_at": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error extracting Indeed job card: {e}")
            return None

    @staticmethod
    def _extract_job_id_from_url(url: str) -> Optional[str]:
        """Extract job ID from Indeed URL."""
        match = re.search(r"jk=([a-f0-9]+)", url)
        return match.group(1) if match else None

    async def save_jobs_to_db(self, jobs: List[dict]) -> int:
        """
        Save jobs to database with deduplication.

        Args:
            jobs: List of job dictionaries

        Returns:
            Number of new jobs saved
        """
        db = SessionLocal()
        new_jobs_count = 0

        try:
            for job_data in jobs:
                # Check if exists
                existing = (
                    db.query(Job)
                    .filter(
                        Job.external_id == job_data["external_id"],
                        Job.platform == job_data["platform"],
                    )
                    .first()
                )

                if not existing:
                    job = Job(**job_data)
                    db.add(job)
                    new_jobs_count += 1
                else:
                    # Update existing
                    for key, value in job_data.items():
                        if key not in ["id", "scraped_at"]:
                            setattr(existing, key, value)

            db.commit()
            return new_jobs_count

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    async def get_full_job_description(self, job_url: str) -> str:
        """
        Get full job description by visiting job page.

        Args:
            job_url: Indeed job URL

        Returns:
            Full job description
        """
        page = await self.browser.new_page()

        try:
            await page.goto(job_url, wait_until="networkidle")

            # Extract full description
            desc_elem = await page.query_selector("#jobDescriptionText")
            if desc_elem:
                return await desc_elem.inner_text()

            return ""

        finally:
            await page.close()
