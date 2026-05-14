from __future__ import annotations

import json
from typing import Any

from pos_assistant.analytics import build_insights_context
from pos_assistant.datasets import InventoryRecord, ProductRecord, SaleTransaction
from pos_assistant.llm import chat_text, get_client


def _friendly_llm_error(exc: Exception) -> str:
    msg = str(exc).lower()
    if "403" in msg and ("credits" in msg or "license" in msg or "permission" in msg):
        return "OpenRouter request blocked by provider permissions/billing. Using fallback recommendations."
    return "OpenRouter request failed. Using fallback recommendations."


def _fallback_recommendations(ctx: dict[str, Any]) -> str:
    low = ctx["inventory_alerts"]["low_stock"]
    top = ctx["top_selling_products"][:3]
    lines = [
        "Recommendations (rule-based):",
        f"- Revenue across sample window: {ctx['summary']['total_revenue']} with {ctx['summary']['transaction_count']} transactions.",
    ]
    if top:
        names = ", ".join(f"{x['name']} ({x['units_sold']} units)" for x in top)
        lines.append(f"- Prioritize availability and margin review on top movers: {names}.")
    if low:
        skus = ", ".join(f"{x['name']} (QoH {x['quantity_on_hand']})" for x in low[:5])
        lines.append(f"- Restock or transfer inventory for low-stock items: {skus}.")
    lines.append("- Compare online vs store mix using channel data when you expand the dataset.")
    return "\n".join(lines)


def generate_business_insights(
    sales: list[SaleTransaction],
    products: list[ProductRecord],
    inventory: list[InventoryRecord],
) -> dict[str, Any]:
    ctx = build_insights_context(sales, products, inventory)
    narrative: dict[str, Any] = {
        "insights": "",
        "recommendations": "",
        "llm_used": False,
        "llm_error": "",
    }

    if get_client() is None:
        narrative["insights"] = (
            "LLM not configured. Structured metrics below are computed from mock POS data."
        )
        narrative["recommendations"] = _fallback_recommendations(ctx)
        return {**ctx, **narrative}

    payload = json.dumps(
        {
            "summary": ctx["summary"],
            "top_selling_products": ctx["top_selling_products"][:8],
            "sales_trends": ctx["sales_trends"],
            "inventory_alerts": ctx["inventory_alerts"],
        },
        indent=2,
    )

    system = """You are a retail analyst for a Smart POS. Given JSON metrics from a store:
Write two markdown sections:
1) ### Insights — bullet list: top sellers, trend direction, categories/stock risks (only what data supports).
2) ### Recommendations — bullet list: concrete next actions (inventory, pricing experiments, bundling, staffing by peak days).
Be concise, actionable, and avoid inventing numbers not present in the input."""

    user = f"POS analytics JSON:\n{payload}\n\nProduce the two sections exactly as described."

    try:
        text = chat_text(system, user)
        narrative["llm_used"] = True
        parts = text.split("### Recommendations")
        if len(parts) >= 2:
            narrative["insights"] = parts[0].strip()
            narrative["recommendations"] = ("### Recommendations" + parts[1]).strip()
        else:
            narrative["insights"] = text
            narrative["recommendations"] = text
    except Exception as exc:
        narrative["insights"] = "LLM unavailable; see structured blocks and fallback recommendations."
        narrative["recommendations"] = _fallback_recommendations(ctx)
        narrative["llm_error"] = _friendly_llm_error(exc)

    return {**ctx, **narrative}
