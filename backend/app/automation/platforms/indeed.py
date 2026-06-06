"""Indeed Quick Apply automation."""
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


class IndeedApplicator:
    """Automate Indeed Quick Apply process."""

    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize Indeed applicator.

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
        Apply to a job using Quick Apply.

        Args:
            job_id: Database job ID
            user_profile_id: User profile ID
            resume_id: Resume ID (uses default if None)

        Returns:
            Application result dictionary
        """
        db = SessionLocal()

        try:
            # Get job and profile
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")

            profile = db.query(UserProfile).filter(UserProfile.id == user_profile_id).first()
            if not profile:
                raise ValueError(f"Profile {user_profile_id} not found")

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
                platform="indeed",
                status="processing",
                resume_path=resume.file_path,
            )
            db.add(application)
            db.commit()
            db.refresh(application)

            # Perform automation
            result = await self._perform_quick_apply(
                job=job,
                profile=profile,
                resume_path=Path(resume.file_path),
                application=application,
            )

            # Update status
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

    async def _perform_quick_apply(
        self,
        job: Job,
        profile: UserProfile,
        resume_path: Path,
        application: Application,
    ) -> dict:
        """
        Perform Indeed Quick Apply automation.

        Args:
            job: Job instance
            profile: UserProfile instance
            resume_path: Path to resume
            application: Application instance

        Returns:
            Result dictionary
        """
        page = await self.browser.new_page()

        try:
            # Navigate to job
            await page.goto(job.url, wait_until="networkidle")
            await asyncio.sleep(2)

            # Click Apply button
            apply_button = await page.query_selector(
                'button:has-text("Apply now"), button:has-text("Apply")'
            )

            if not apply_button:
                raise ValueError("Apply button not found")

            await apply_button.click()
            await asyncio.sleep(2)

            # Fill application form
            await self._fill_application_form(page, profile, resume_path)

            # Submit application
            submit_button = await page.query_selector(
                'button:has-text("Submit"), button:has-text("Submit application")'
            )

            if submit_button:
                await submit_button.click()
                await asyncio.sleep(3)

                # Check for confirmation
                confirmation = await page.query_selector(
                    'text="Application submitted", text="Your application was sent"'
                )

                if confirmation:
                    return {
                        "success": True,
                        "message": "Application submitted successfully",
                    }

            raise ValueError("Could not confirm submission")

        except Exception as e:
            # Screenshot for debugging
            screenshot_path = await self.browser.screenshot(
                page, f"indeed_error_{application.id}"
            )
            application.screenshot_path = str(screenshot_path)

            return {"success": False, "error": str(e)}
        finally:
            await page.close()

    async def _fill_application_form(
        self, page: Page, profile: UserProfile, resume_path: Path
    ) -> None:
        """
        Fill Indeed application form.

        Args:
            page: Playwright page
            profile: UserProfile instance
            resume_path: Path to resume
        """
        # Upload resume
        resume_input = await page.query_selector('input[type="file"][accept*="pdf"]')
        if resume_input and resume_path.exists():
            await resume_input.set_input_files(str(resume_path))
            await asyncio.sleep(1)

        # Fill contact info
        name_parts = profile.name.split() if profile.name else ["", ""]
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        field_mappings = {
            "firstName": first_name,
            "lastname": last_name,
            "email": profile.email,
            "phone": profile.phone,
        }

        # Fill all text inputs
        for field_name, value in field_mappings.items():
            if not value:
                continue

            try:
                # Try multiple selector patterns
                selectors = [
                    f'input[name="{field_name}"]',
                    f'input[id*="{field_name}"]',
                    f'input[placeholder*="{field_name}"]',
                ]

                for selector in selectors:
                    input_elem = await page.query_selector(selector)
                    if input_elem:
                        await input_elem.fill(str(value))
                        break

            except Exception as e:
                print(f"Could not fill {field_name}: {e}")

        # Handle additional questions (select reasonable defaults)
        selects = await page.query_selector_all("select")
        for select in selects:
            try:
                options = await select.query_selector_all("option")
                if len(options) > 1:
                    await select.select_option(index=1)
            except:
                pass

        # Handle checkboxes (required consents)
        checkboxes = await page.query_selector_all('input[type="checkbox"]')
        for checkbox in checkboxes:
            try:
                label = await checkbox.evaluate(
                    'el => el.parentElement?.innerText || ""'
                )
                if "agree" in label.lower() or "consent" in label.lower():
                    await checkbox.check()
            except:
                pass
