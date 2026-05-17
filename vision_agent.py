# ============================================================
# Smart Household Finance Agent — Claude Vision Integration
# ============================================================

import base64
import json
import re
from io import BytesIO
from typing import Optional

import os
import anthropic
from PIL import Image

from config import EXPENSE_CATEGORIES


# ── Vision Agent ──────────────────────────────────────────

class VisionAgent:
    """
    Uses Claude's vision capability to analyse receipt / bill images
    and extract structured expense data.
    """

    # System prompt that instructs Claude how to parse receipts
    SYSTEM_PROMPT = """You are a smart household finance assistant specialised in reading receipts,
invoices, and bills. When given an image of a financial document, extract all relevant expense
information and return it as valid JSON only — no explanations, no markdown fences, just raw JSON.

Return a JSON object with the following schema:
{
  "store_name": "string | null",
  "date": "YYYY-MM-DD | null",
  "total_amount": float | null,
  "currency": "string (e.g. USD, MYR) | null",
  "category": "string (one of: Utilities, Food & Groceries, Transportation, Entertainment, Healthcare, Education, Shopping, Dining Out, Other)",
  "items": [
    { "name": "string", "quantity": float | null, "unit_price": float | null, "total": float | null }
  ],
  "payment_method": "string | null",
  "notes": "string | null"
}

Be as accurate as possible. If a field cannot be determined, use null.
"""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set. Please check your .env file.")
        self._client = anthropic.Anthropic(api_key=api_key)

    # ── Internal Helpers ──────────────────────────────────

    @staticmethod
    def _image_to_base64(image: Image.Image, fmt: str = "JPEG") -> tuple[str, str]:
        """Convert a PIL Image to a base64-encoded string with its media type."""
        buffer = BytesIO()
        # Ensure RGB mode for JPEG compatibility
        if fmt == "JPEG" and image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(buffer, format=fmt)
        b64 = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
        media_type = f"image/{fmt.lower()}"
        return b64, media_type

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Strip any accidental markdown fences and parse JSON."""
        # Remove ```json ... ``` wrappers if present
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
        return json.loads(cleaned)

    # ── Public API ────────────────────────────────────────

    def analyse_receipt(
        self,
        image: Image.Image,
        extra_context: Optional[str] = None,
    ) -> dict:
        """
        Send a receipt image to Claude for analysis.

        Args:
            image: A PIL Image of the receipt / bill.
            extra_context: Optional free-text hint (e.g. "This is a restaurant bill from Kuala Lumpur").

        Returns:
            A dict with parsed expense fields.

        Raises:
            ValueError: If Claude's response cannot be parsed as JSON.
            anthropic.APIError: On API-level failures.
        """
        b64, media_type = self._image_to_base64(image)

        user_content: list = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": b64,
                },
            },
            {
                "type": "text",
                "text": extra_context or "Please analyse this receipt and extract all expense information.",
            },
        ]

        model_name = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")
        response = self._client.messages.create(
            model=model_name,
            max_tokens=1024,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )

        raw_text = response.content[0].text

        try:
            return self._extract_json(raw_text)
        except (json.JSONDecodeError, IndexError) as exc:
            raise ValueError(
                f"Claude returned non-JSON output. Raw response:\n{raw_text}"
            ) from exc

    def summarise_expenses(self, expenses: list[dict]) -> str:
        """
        Ask Claude to generate a natural-language spending summary.

        Args:
            expenses: A list of expense dicts from the database.

        Returns:
            A human-friendly summary string.
        """
        expense_json = json.dumps(expenses, indent=2, default=str)

        model_name = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")
        response = self._client.messages.create(
            model=model_name,
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Here are my recent household expenses:\n\n"
                        f"{expense_json}\n\n"
                        "Please give me a concise, friendly summary of my spending patterns, "
                        "highlight the biggest categories, and suggest one or two practical tips "
                        "to reduce costs."
                    ),
                }
            ],
        )

        return response.content[0].text


# ── Module-level singleton ─────────────────────────────────
vision_agent = VisionAgent()
