"""Google Gemini Vision integration for receipt parsing with brand extraction"""
import base64
from pathlib import Path
from google import genai
import os
from dotenv import load_dotenv
import json

load_dotenv()

MODEL_NAME = "models/gemini-2.5-flash"


class VisionAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        self.client = genai.Client(api_key=api_key)

    def extract_bill_data(self, image_path: str):
        """Extract itemized data with brand info from a receipt image."""
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()

            ext = Path(image_path).suffix.lower()
            mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

            from google.genai import types

            prompt = (
                "Analyze this receipt or bill image. "
                "Extract the store name, date, every line item, and the total.\n\n"
                "For each item, separate the BRAND from the PRODUCT DESCRIPTION.\n"
                "Example: 'Coca-Cola 1.5L' -> brand: 'Coca-Cola', name: 'Soda 1.5L'\n"
                "Example: 'Tide Powder 1kg' -> brand: 'Tide', name: 'Detergent Powder 1kg'\n"
                "If no clear brand, set brand to empty string.\n\n"
                "Return ONLY valid JSON:\n"
                "{\n"
                '  "store_name": "store or vendor name",\n'
                '  "date": "YYYY-MM-DD or null",\n'
                '  "total_amount": <number>,\n'
                '  "confidence": "high" or "medium" or "low",\n'
                '  "items": [\n'
                "    {\n"
                '      "name": "product description without brand",\n'
                '      "brand": "brand name or empty string",\n'
                '      "quantity": <number>,\n'
                '      "unit_price": <number>,\n'
                '      "total": <line total>,\n'
                '      "category": "<one of: Utilities, Food & Groceries, '
                "Beverages, Frozen Goods, Toiletries, Household Supplies, "
                "Transportation, Entertainment, Healthcare, Education, "
                'Tuition, Shopping, Dining Out, Other>"\n'
                "    }\n"
                "  ]\n"
                "}\n\n"
                "Rules:\n"
                "- Include EVERY readable item.\n"
                "- Categorize each item individually.\n"
                "- Separate brand from product name.\n"
                "- total_amount = receipt grand total.\n"
                "- Do NOT wrap in markdown code fences."
            )

            response = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    types.Part.from_bytes(data=image_data, mime_type=mime),
                    prompt,
                ],
            )
            raw = response.text

            try:
                cleaned = raw.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1]
                if cleaned.endswith("```"):
                    cleaned = cleaned.rsplit("```", 1)[0]
                cleaned = cleaned.strip()

                start = cleaned.find("{")
                end = cleaned.rfind("}") + 1
                data = json.loads(cleaned[start:end])

                items = data.get("items", [])
                for it in items:
                    it.setdefault("name", "Item")
                    it.setdefault("brand", "")
                    it.setdefault("quantity", 1)
                    it.setdefault("unit_price", 0)
                    it.setdefault("total", it.get("unit_price", 0))
                    it.setdefault("category", "Other")

                return {
                    "success": True,
                    "store_name": data.get("store_name", ""),
                    "date": data.get("date"),
                    "total_amount": float(data.get("total_amount", 0)),
                    "confidence": data.get("confidence", "medium"),
                    "items": items,
                    "raw_response": raw,
                }
            except (json.JSONDecodeError, ValueError):
                return {"success": False, "error": "Could not parse receipt", "raw_response": raw}

        except Exception as e:
            return {"success": False, "error": str(e), "raw_response": ""}