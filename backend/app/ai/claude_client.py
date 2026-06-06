"""Claude Code CLI integration for AI capabilities."""
import json
import subprocess
from typing import Any, Dict, Optional

from backend.app.config import settings


class ClaudeCodeClient:
    """Client for interacting with Claude Code CLI."""

    def __init__(self, claude_path: Optional[str] = None):
        """
        Initialize Claude Code client.

        Args:
            claude_path: Path to Claude CLI executable
        """
        self.claude_path = claude_path or settings.claude_cli_path

    def prompt(
        self,
        prompt: str,
        output_format: str = "text",
        timeout: int = 60,
    ) -> str:
        """
        Send a prompt to Claude Code CLI and get response.

        Args:
            prompt: Prompt text
            output_format: Response format (text or json)
            timeout: Timeout in seconds

        Returns:
            Response text

        Raises:
            RuntimeError: If Claude Code CLI fails
        """
        try:
            # Build command
            cmd = [self.claude_path]

            # Add prompt
            cmd.extend(["--prompt", prompt])

            # Add format flag if JSON
            if output_format == "json":
                cmd.append("--output-json")

            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Claude Code CLI failed: {result.stderr}"
                )

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Claude Code CLI timed out after {timeout}s")
        except FileNotFoundError:
            raise RuntimeError(
                f"Claude Code CLI not found at {self.claude_path}. "
                "Make sure Claude Code is installed and configured."
            )
        except Exception as e:
            raise RuntimeError(f"Claude Code CLI error: {e}")

    def prompt_json(self, prompt: str, timeout: int = 60) -> Dict[str, Any]:
        """
        Send prompt and parse JSON response.

        Args:
            prompt: Prompt text
            timeout: Timeout in seconds

        Returns:
            Parsed JSON response
        """
        response = self.prompt(prompt, output_format="json", timeout=timeout)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            # Sometimes Claude returns JSON wrapped in markdown
            import re

            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            # Try to find any JSON object
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))

            raise ValueError(f"Could not parse JSON from response: {response}")
