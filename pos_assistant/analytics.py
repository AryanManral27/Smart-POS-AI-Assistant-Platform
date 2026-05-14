from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any

from pos_assistant.datasets import (
    InventoryRecord,
    ProductRecord,
    SaleTransaction,
    product_index,
)


def _parse_day(ts: str) -> date:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).date()


def compute_top_selling_products(
    sales: list[SaleTransaction],
    products: list[ProductRecord],
    limit: int = 8,
) -> list[dict[str, Any]]:
    qty_by_product: dict[str, int] = defaultdict(int)
    revenue_by_product: dict[str, float] = defaultdict(float)
    for t in sales:
        for ln in t.lines:
            qty_by_product[ln.product_id] += ln.qty
            revenue_by_product[ln.product_id] += ln.qty * ln.unit_price
    idx = product_index(products)
    ranked = sorted(qty_by_product.items(), key=lambda x: (-x[1], x[0]))
    out: list[dict[str, Any]] = []
    for pid, qty in ranked[:limit]:
        p = idx.get(pid)
        out.append(
            {
                "product_id": pid,
                "name": p.name if p else pid,
                "category": p.category if p else "",
                "units_sold": qty,
                "revenue": round(revenue_by_product[pid], 2),
            }
        )
    return out


def compute_sales_trends(
    sales: list[SaleTransaction],
    products: list[ProductRecord],
) -> list[dict[str, Any]]:
    by_day: dict[date, dict[str, Any]] = {}
    idx = product_index(products)
    for t in sales:
        d = _parse_day(t.timestamp)
        if d not in by_day:
            by_day[d] = {"date": d.isoformat(), "transaction_count": 0, "revenue": 0.0, "units": 0}
        bucket = by_day[d]
        bucket["transaction_count"] += 1
        for ln in t.lines:
            bucket["revenue"] += ln.qty * ln.unit_price
            bucket["units"] += ln.qty
    trend = sorted(by_day.values(), key=lambda x: x["date"])
    for b in trend:
        b["revenue"] = round(float(b["revenue"]), 2)
    return trend


def compute_product_performance(
    sales: list[SaleTransaction],
    products: list[ProductRecord],
    inventory: list[InventoryRecord],
) -> list[dict[str, Any]]:
    inv_by_pid = {i.product_id: i for i in inventory}
    tops = {r["product_id"]: r for r in compute_top_selling_products(sales, products, limit=999)}
    idx = product_index(products)
    rows: list[dict[str, Any]] = []
    for p in products:
        t = tops.get(p.id, {"units_sold": 0, "revenue": 0.0})
        inv = inv_by_pid.get(p.id)
        qoh = inv.quantity_on_hand if inv else 0
        ro = inv.reorder_point if inv else 0
        stock_status = "ok"
        if qoh <= ro:
            stock_status = "at_or_below_reorder"
        elif qoh <= ro * 1.5:
            stock_status = "watch"
        rows.append(
            {
                "product_id": p.id,
                "name": p.name,
                "category": p.category,
                "units_sold": int(t["units_sold"]),
                "revenue": float(t["revenue"]),
                "quantity_on_hand": qoh,
                "reorder_point": ro,
                "stock_status": stock_status,
            }
        )
    rows.sort(key=lambda x: (-x["revenue"], x["name"]))
    return rows


def build_insights_context(
    sales: list[SaleTransaction],
    products: list[ProductRecord],
    inventory: list[InventoryRecord],
) -> dict[str, Any]:
    top = compute_top_selling_products(sales, products)
    trend = compute_sales_trends(sales, products)
    perf = compute_product_performance(sales, products, inventory)
    total_rev = sum(t["revenue"] for t in trend)
    total_units = sum(t["units"] for t in trend)
    low_stock = [p for p in perf if p["stock_status"] == "at_or_below_reorder"]
    return {
        "summary": {
            "transaction_count": len(sales),
            "distinct_products_in_catalog": len(products),
            "total_revenue": round(total_rev, 2),
            "total_units_sold": total_units,
            "days_in_range": len(trend),
        },
        "top_selling_products": top,
        "sales_trends": trend,
        "product_performance": perf,
        "inventory_alerts": {
            "low_stock_count": len(low_stock),
            "low_stock": low_stock[:10],
        },
    }
