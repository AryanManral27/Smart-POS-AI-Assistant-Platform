from __future__ import annotations

import re
from typing import Any

from pos_assistant.llm import chat_json, get_client


def _fallback_listing(name: str, details: str | None) -> dict[str, Any]:
    blob = f"{name} {details or ''}".lower()
    category = "General Merchandise"
    if any(k in blob for k in ("chai", "coffee", "juice", "drink", "beverage")):
        category = "Beverages"
    elif any(k in blob for k in ("bread", "cake", "bake")):
        category = "Bakery"
    elif any(k in blob for k in ("rice", "dal", "flour", "grocery")):
        category = "Groceries"
    elif any(k in blob for k in ("shirt", "apparel", "cotton", "wear")):
        category = "Apparel"
    elif any(k in blob for k in ("lamp", "usb", "scanner", "electronics", "led")):
        category = "Electronics"
    elif any(k in blob for k in ("honey", "ayurvedic", "wellness", "supplement")):
        category = "Wellness"
    gst = 18.0
    if category in ("Beverages", "Bakery", "Groceries", "Wellness"):
        gst = 5.0
    if "bread" in blob or "rice" in blob or "milk" in blob:
        gst = 0.0
    hsn = "00000000"
    if category == "Beverages":
        hsn = "22029990"
    elif category == "Bakery":
        hsn = "19059090"
    elif category == "Groceries":
        hsn = "10063090"
    elif category == "Apparel":
        hsn = "61091000"
    elif category == "Electronics":
        hsn = "85176200"
    elif category == "Wellness":
        hsn = "04090000"
    desc = (
        f"{name.strip()} is positioned for retail POS cataloging. "
        f"Use this listing as a starting point and verify GST/HSN with your CA for India compliance."
    )
    if details:
        desc = f"{desc} Notes from merchant: {details.strip()}"
    tags = list(
        dict.fromkeys(
            [w for w in re.split(r"[^\w]+", f"{name} {details or ''}".lower()) if len(w) > 2][:8]
        )
    )
    return {
        "description": desc,
        "category": category,
        "gst_rate_percent": gst,
        "hsn_code": hsn,
        "keywords": tags,
        "disclaimer": "Fallback heuristics used (no LLM). Set OPENROUTER_API_KEY for AI-generated output.",
    }


def _friendly_llm_error(exc: Exception) -> str:
    msg = str(exc).lower()
    if "403" in msg and ("credits" in msg or "license" in msg or "permission" in msg):
        return "OpenRouter request blocked by provider permissions/billing. Using fallback output."
    return "OpenRouter request failed. Using fallback output."


def assist_product_listing(name: str, details: str | None = None) -> dict[str, Any]:
    name = name.strip()
    if not name:
        raise ValueError("product name is required")

    if get_client() is None:
        return _fallback_listing(name, details)

    system = """You assist Indian retail/POS users. Output ONLY valid JSON with keys:
description (string, 2-4 sentences, merchant-ready),
category (string, concise retail category),
gst_rate_percent (number, one of 0, 5, 12, 18, 28 when plausible for India GST),
hsn_code (string, 8-digit style code, best-effort),
keywords (array of 5-12 short lowercase tags).
Use conservative, typical classifications; mention uncertainty only inside description if needed."""

    user = f"Product name: {name}\n"
    if details:
        user += f"Extra details: {details}\n"
    user += "Respond with JSON only."

    try:
        data = chat_json(system, user)
    except Exception as exc:
        out = _fallback_listing(name, details)
        out["disclaimer"] = "LLM call failed; heuristic fallback returned."
        out["llm_error"] = _friendly_llm_error(exc)
        return out

    required = ["description", "category", "gst_rate_percent", "hsn_code", "keywords"]
    for k in required:
        if k not in data:
            return _fallback_listing(name, details)
    if not isinstance(data["keywords"], list):
        data["keywords"] = [str(data["keywords"])]
    data["keywords"] = [str(x).strip().lower() for x in data["keywords"] if str(x).strip()]
    data["gst_rate_percent"] = float(data["gst_rate_percent"])
    data["disclaimer"] = "AI-generated; verify GST/HSN with a qualified professional before filing."
    return data
