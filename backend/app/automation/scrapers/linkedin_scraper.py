"""LinkedIn job scraper."""
import asyncio
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


class LinkedInScraper:
    """Scrape job listings from LinkedIn."""

    BASE_URL = "https://www.linkedin.com"
    JOBS_SEARCH_URL = f"{BASE_URL}/jobs/search"

    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize LinkedIn scraper.

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
        experience_level: Optional[str] = None,
        max_results: int = 25,
    ) -> List[dict]:
        """
        Search for jobs on LinkedIn.

        Args:
            keywords: Job title or keywords to search
            location: Location filter
            remote: Filter for remote jobs only
            experience_level: Experience level filter (entry, mid, senior, etc.)
            max_results: Maximum number of jobs to return

        Returns:
            List of job dictionaries
        """
        page = await self.browser.new_page()

        try:
            # Build search URL
            params = {
                "keywords": keywords,
                "location": location,
            }

            if remote:
                params["f_WT"] = "2"  # Remote filter

            # Navigate to search page
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{self.JOBS_SEARCH_URL}?{query_string}"

            await page.goto(url, wait_until="networkidle")

            # Wait for job listings to load
            await page.wait_for_selector("ul.jobs-search__results-list", timeout=10000)

            # Extract job cards
            jobs = []
            job_cards = await page.query_selector_all(
                "li.jobs-search-results__list-item"
            )

            for idx, card in enumerate(job_cards[:max_results]):
                try:
                    job_data = await self._extract_job_card_data(card, page)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    print(f"Error extracting job card {idx}: {e}")
                    continue

            return jobs

        finally:
            await page.close()

    async def _extract_job_card_data(self, card, page: Page) -> Optional[dict]:
        """
        Extract data from a job card element.

        Args:
            card: Job card element
            page: Page instance

        Returns:
            Job data dictionary or None
        """
        try:
            # Click card to load details
            await card.click()
            await asyncio.sleep(1)  # Wait for details to load

            # Extract basic info from card
            title_elem = await card.query_selector(".job-card-list__title")
            title = await title_elem.inner_text() if title_elem else ""

            company_elem = await card.query_selector(".job-card-container__company-name")
            company = await company_elem.inner_text() if company_elem else ""

            location_elem = await card.query_selector(".job-card-container__metadata-item")
            location = await location_elem.inner_text() if location_elem else ""

            # Extract job ID from data attribute or URL
            job_link = await card.query_selector("a.job-card-list__title")
            job_url = await job_link.get_attribute("href") if job_link else ""
            job_id = self._extract_job_id_from_url(job_url)

            # Extract description from details panel
            description = ""
            description_elem = await page.query_selector(
                ".jobs-description__content"
            )
            if description_elem:
                description = await description_elem.inner_text()

            # Determine if remote
            is_remote = "remote" in location.lower() or "remote" in title.lower()

            return {
                "external_id": job_id,
                "platform": "linkedin",
                "url": f"{self.BASE_URL}/jobs/view/{job_id}" if job_id else job_url,
                "title": title.strip(),
                "company": company.strip(),
                "location": location.strip(),
                "is_remote": is_remote,
                "description": description.strip(),
                "scraped_at": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error extracting job card data: {e}")
            return None

    @staticmethod
    def _extract_job_id_from_url(url: str) -> Optional[str]:
        """Extract job ID from LinkedIn job URL."""
        match = re.search(r"/jobs/view/(\d+)", url)
        return match.group(1) if match else None

    async def save_jobs_to_db(self, jobs: List[dict]) -> int:
        """
        Save scraped jobs to database with deduplication.

        Args:
            jobs: List of job dictionaries

        Returns:
            Number of new jobs saved
        """
        db = SessionLocal()
        new_jobs_count = 0

        try:
            for job_data in jobs:
                # Check if job already exists
                existing = (
                    db.query(Job)
                    .filter(
                        Job.external_id == job_data["external_id"],
                        Job.platform == job_data["platform"],
                    )
                    .first()
                )

                if not existing:
                    # Create new job
                    job = Job(**job_data)
                    db.add(job)
                    new_jobs_count += 1
                else:
                    # Update existing job
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

    async def authenticate(self, email: str, password: str) -> bool:
        """
        Authenticate with LinkedIn and save session.

        Args:
            email: LinkedIn email
            password: LinkedIn password

        Returns:
            True if authentication successful
        """
        page = await self.browser.new_page()

        try:
            # Navigate to login page
            await page.goto(f"{self.BASE_URL}/login", wait_until="networkidle")

            # Wait for login form to be visible
            await page.wait_for_selector('input[name="session_key"]', timeout=10000)

            # Fill login form
            await page.fill('input[name="session_key"]', email)
            await page.fill('input[name="session_password"]', password)

            # Click sign in button and wait for navigation
            await page.click('button[type="submit"]')

            # Wait for successful login (either feed or checkpoint)
            try:
                # Wait for either feed URL or checkpoint
                await page.wait_for_url(f"{self.BASE_URL}/feed/**", timeout=30000)
            except:
                # Check if we're on checkpoint/challenge page
                current_url = page.url
                if "checkpoint" in current_url or "challenge" in current_url:
                    print("LinkedIn requires additional verification. Please complete it in the browser.")
                    print("Press Enter after completing verification...")
                    input()
                    # Wait again after manual verification
                    await page.wait_for_url(f"{self.BASE_URL}/feed/**", timeout=60000)

            # Save session
            await self.browser.save_session("linkedin")

            return True

        except Exception as e:
            print(f"LinkedIn authentication failed: {e}")
            return False
        finally:
            await page.close()
