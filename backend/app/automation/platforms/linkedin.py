"""LinkedIn Easy Apply automation."""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.app.automation.browser import BrowserManager, FormFiller
from backend.app.database.session import SessionLocal
from backend.app.models import Application, Job, Resume, UserProfile

try:
    from playwright.async_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = None


class LinkedInApplicator:
    """Automate LinkedIn Easy Apply process."""

    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize LinkedIn applicator.

        Args:
            browser_manager: Browser manager instance
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required for automation")

        self.browser = browser_manager
        self.form_filler = FormFiller()

    async def apply_to_job(
        self,
        job_id: int,
        user_profile_id: int,
        resume_id: Optional[int] = None,
    ) -> dict:
        """
        Apply to a job using Easy Apply.

        Args:
            job_id: Database job ID
            user_profile_id: User profile ID
            resume_id: Resume ID (uses default if None)

        Returns:
            Application result dictionary
        """
        db = SessionLocal()

        try:
            # Get job and profile data
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")

            profile = db.query(UserProfile).filter(UserProfile.id == user_profile_id).first()
            if not profile:
                raise ValueError(f"User profile {user_profile_id} not found")

            # Get resume
            if resume_id:
                resume = db.query(Resume).filter(Resume.id == resume_id).first()
            else:
                resume = (
                    db.query(Resume)
                    .filter(Resume.user_id == user_profile_id, Resume.is_default == True)
                    .first()
                )

            if not resume:
                raise ValueError("No resume found")

            # Create application record
            application = Application(
                job_id=job_id,
                user_id=user_profile_id,
                platform="linkedin",
                status="processing",
                resume_path=resume.file_path,
            )
            db.add(application)
            db.commit()
            db.refresh(application)

            # Perform automation
            result = await self._perform_easy_apply(
                job=job,
                profile=profile,
                resume_path=Path(resume.file_path),
                application=application,
            )

            # Update application status
            if result["success"]:
                application.status = "submitted"
                application.submitted_at = datetime.utcnow()
            else:
                application.status = "failed"
                application.error_message = result.get("error", "Unknown error")

            db.commit()

            return result

        except Exception as e:
            if 'application' in locals():
                application.status = "failed"
                application.error_message = str(e)
                db.commit()

            return {"success": False, "error": str(e)}
        finally:
            db.close()

    async def _perform_easy_apply(
        self,
        job: Job,
        profile: UserProfile,
        resume_path: Path,
        application: Application,
    ) -> dict:
        """
        Perform the Easy Apply automation.

        Args:
            job: Job model instance
            profile: UserProfile instance
            resume_path: Path to resume file
            application: Application instance

        Returns:
            Result dictionary with success status
        """
        page = await self.browser.new_page()

        try:
            # Navigate to job page
            await page.goto(job.url, wait_until="networkidle")

            # Click Easy Apply button
            easy_apply_button = await page.query_selector(
                'button[aria-label*="Easy Apply"]'
            )

            if not easy_apply_button:
                raise ValueError("Easy Apply button not found - job may not support it")

            await easy_apply_button.click()
            await asyncio.sleep(2)  # Wait for modal to open

            # Process multi-step form
            step = 1
            max_steps = 10  # Prevent infinite loops

            while step <= max_steps:
                # Check if we're done
                review_button = await page.query_selector('button[aria-label="Review"]')
                submit_button = await page.query_selector(
                    'button[aria-label="Submit application"]'
                )

                if review_button:
                    # On review page, click review then submit
                    await review_button.click()
                    await asyncio.sleep(1)
                    continue

                if submit_button:
                    # Final submit
                    await submit_button.click()
                    await asyncio.sleep(2)

                    # Check for confirmation
                    confirmation = await page.query_selector('text="Application sent"')
                    if confirmation:
                        return {
                            "success": True,
                            "message": "Application submitted successfully",
                        }

                # Fill current step
                await self._fill_form_step(page, profile, resume_path)

                # Click Next button
                next_button = await page.query_selector('button[aria-label="Continue"]')
                if not next_button:
                    next_button = await page.query_selector('button:has-text("Next")')

                if next_button:
                    await next_button.click()
                    await asyncio.sleep(2)
                    step += 1
                else:
                    # No next button, might be on last step
                    break

            raise ValueError("Could not complete application - form flow unclear")

        except Exception as e:
            # Take screenshot for debugging
            screenshot_path = await self.browser.screenshot(
                page, f"linkedin_error_{application.id}"
            )
            application.screenshot_path = str(screenshot_path)

            return {"success": False, "error": str(e)}
        finally:
            await page.close()

    async def _fill_form_step(
        self, page: Page, profile: UserProfile, resume_path: Path
    ) -> None:
        """
        Fill fields in the current form step.

        Args:
            page: Playwright page
            profile: UserProfile instance
            resume_path: Path to resume file
        """
        # Common field patterns
        field_mappings = {
            "phone": profile.phone,
            "email": profile.email,
            "firstName": profile.name.split()[0] if profile.name else "",
            "lastName": " ".join(profile.name.split()[1:]) if profile.name else "",
        }

        # Try to fill all visible inputs
        inputs = await page.query_selector_all("input[type='text'], input[type='email']")

        for input_elem in inputs:
            try:
                # Get field name/id
                name = await input_elem.get_attribute("name") or ""
                input_id = await input_elem.get_attribute("id") or ""

                # Try to match with profile data
                for key, value in field_mappings.items():
                    if key.lower() in name.lower() or key.lower() in input_id.lower():
                        if value:
                            await input_elem.fill(str(value))
                        break

            except Exception as e:
                print(f"Could not fill input: {e}")
                continue

        # Handle file upload (resume)
        file_inputs = await page.query_selector_all("input[type='file']")
        for file_input in file_inputs:
            try:
                if resume_path.exists():
                    await file_input.set_input_files(str(resume_path))
            except Exception as e:
                print(f"Could not upload resume: {e}")

        # Handle dropdowns
        selects = await page.query_selector_all("select")
        for select in selects:
            try:
                # Try to select a reasonable default
                options = await select.query_selector_all("option")
                if len(options) > 1:
                    # Skip first (often "Select...")
                    await select.select_option(index=1)
            except Exception as e:
                print(f"Could not fill select: {e}")

    async def check_application_status(self, job_url: str) -> dict:
        """
        Check if already applied to a job.

        Args:
            job_url: LinkedIn job URL

        Returns:
            Status dictionary
        """
        page = await self.browser.new_page()

        try:
            await page.goto(job_url)
            await asyncio.sleep(2)

            # Check for "Applied" indicator
            applied_elem = await page.query_selector('text="Applied"')

            return {
                "already_applied": applied_elem is not None,
                "can_apply": applied_elem is None,
            }

        finally:
            await page.close()
