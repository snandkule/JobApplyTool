"""Browser automation manager using Playwright."""
import asyncio
from pathlib import Path
from typing import Optional

from backend.app.config import settings

try:
    from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = BrowserContext = Page = Playwright = None


class BrowserManager:
    """Manages browser instances and sessions for automation."""

    def __init__(self):
        """Initialize the browser manager."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is not installed. Install it with: "
                "pip install playwright && playwright install chromium"
            )

        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._session_dir = settings.data_dir / "browser_sessions"
        self._session_dir.mkdir(exist_ok=True)

    async def start(self, headless: bool = None) -> Browser:
        """
        Start the browser.

        Args:
            headless: Run in headless mode (default from settings)

        Returns:
            Browser instance
        """
        if headless is None:
            headless = settings.browser_headless

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',  # Hide automation
                '--disable-dev-shm-usage',  # Overcome limited resource problems
                '--no-sandbox',  # Required for some environments
            ]
        )
        return self.browser

    async def create_context(
        self,
        platform: str = "default",
        viewport: dict = None,
        user_agent: str = None,
    ) -> BrowserContext:
        """
        Create a new browser context with optional session persistence.

        Args:
            platform: Platform name for session storage (linkedin, indeed, etc.)
            viewport: Custom viewport size
            user_agent: Custom user agent string

        Returns:
            BrowserContext instance
        """
        if not self.browser:
            await self.start()

        # Session storage path for this platform
        session_path = self._session_dir / platform

        # Default viewport
        if viewport is None:
            viewport = {"width": 1920, "height": 1080}

        # Create context with session persistence
        context_options = {
            "viewport": viewport,
            "user_agent": user_agent,
            "locale": "en-US",
            "timezone_id": "America/New_York",
        }

        # Use persistent context for session storage
        if session_path.exists():
            self.context = await self.browser.new_context(
                storage_state=str(session_path),
                **context_options
            )
        else:
            self.context = await self.browser.new_context(**context_options)

        return self.context

    async def save_session(self, platform: str) -> None:
        """
        Save the current session state for a platform.

        Args:
            platform: Platform name (linkedin, indeed, etc.)
        """
        if not self.context:
            raise ValueError("No context available to save")

        session_path = self._session_dir / platform
        await self.context.storage_state(path=str(session_path))

    async def new_page(self) -> Page:
        """
        Create a new page in the current context.

        Returns:
            Page instance
        """
        if not self.context:
            await self.create_context()

        page = await self.context.new_page()

        # Set default timeout
        page.set_default_timeout(settings.browser_timeout)

        return page

    async def screenshot(self, page: Page, name: str) -> Path:
        """
        Take a screenshot for debugging.

        Args:
            page: Page to screenshot
            name: Screenshot filename

        Returns:
            Path to screenshot file
        """
        screenshot_path = settings.screenshots_dir / f"{name}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        return screenshot_path

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class FormFiller:
    """Utility class for filling forms intelligently."""

    @staticmethod
    async def fill_text_field(page: Page, selector: str, value: str, timeout: int = 5000):
        """
        Fill a text field with proper waiting.

        Args:
            page: Playwright page
            selector: CSS selector for field
            value: Value to fill
            timeout: Wait timeout in milliseconds
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            await page.fill(selector, value)
        except Exception as e:
            raise ValueError(f"Could not fill field {selector}: {e}")

    @staticmethod
    async def select_dropdown(page: Page, selector: str, value: str, timeout: int = 5000):
        """
        Select a dropdown option.

        Args:
            page: Playwright page
            selector: CSS selector for dropdown
            value: Value or label to select
            timeout: Wait timeout in milliseconds
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            await page.select_option(selector, value)
        except Exception as e:
            raise ValueError(f"Could not select dropdown {selector}: {e}")

    @staticmethod
    async def upload_file(page: Page, selector: str, file_path: Path, timeout: int = 5000):
        """
        Upload a file to a file input.

        Args:
            page: Playwright page
            selector: CSS selector for file input
            file_path: Path to file to upload
            timeout: Wait timeout in milliseconds
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            await page.set_input_files(selector, str(file_path))
        except Exception as e:
            raise ValueError(f"Could not upload file to {selector}: {e}")

    @staticmethod
    async def click_button(page: Page, selector: str, timeout: int = 5000):
        """
        Click a button with proper waiting.

        Args:
            page: Playwright page
            selector: CSS selector for button
            timeout: Wait timeout in milliseconds
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            await page.click(selector)
        except Exception as e:
            raise ValueError(f"Could not click button {selector}: {e}")


def run_async(coro):
    """
    Helper to run async function in sync context.

    Args:
        coro: Coroutine to run

    Returns:
        Result of coroutine
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)
