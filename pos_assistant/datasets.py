from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pos_assistant.config import DATA_DIR


@dataclass(frozen=True)
class ProductRecord:
    id: str
    name: str
    category: str
    hsn_code: str
    gst_rate_percent: float
    unit_price: float
    tags: list[str]


@dataclass(frozen=True)
class InventoryRecord:
    product_id: str
    sku: str
    quantity_on_hand: int
    reorder_point: int


@dataclass(frozen=True)
class SaleLine:
    product_id: str
    qty: int
    unit_price: float


@dataclass(frozen=True)
class SaleTransaction:
    id: str
    timestamp: str
    channel: str
    lines: list[SaleLine]


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_products(base: Path | None = None) -> list[ProductRecord]:
    root = base or DATA_DIR
    raw = _load_json(root / "products.json")
    return [
        ProductRecord(
            id=r["id"],
            name=r["name"],
            category=r["category"],
            hsn_code=r["hsn_code"],
            gst_rate_percent=float(r["gst_rate_percent"]),
            unit_price=float(r["unit_price"]),
            tags=list(r.get("tags", [])),
        )
        for r in raw
    ]


def load_inventory(base: Path | None = None) -> list[InventoryRecord]:
    root = base or DATA_DIR
    raw = _load_json(root / "inventory.json")
    return [
        InventoryRecord(
            product_id=r["product_id"],
            sku=r["sku"],
            quantity_on_hand=int(r["quantity_on_hand"]),
            reorder_point=int(r["reorder_point"]),
        )
        for r in raw
    ]


def load_sales(base: Path | None = None) -> list[SaleTransaction]:
    root = base or DATA_DIR
    raw = _load_json(root / "sales_transactions.json")
    out: list[SaleTransaction] = []
    for t in raw:
        lines = [
            SaleLine(
                product_id=ln["product_id"],
                qty=int(ln["qty"]),
                unit_price=float(ln["unit_price"]),
            )
            for ln in t["lines"]
        ]
        out.append(
            SaleTransaction(
                id=t["id"],
                timestamp=t["timestamp"],
                channel=t["channel"],
                lines=lines,
            )
        )
    return out


def product_index(products: list[ProductRecord]) -> dict[str, ProductRecord]:
    return {p.id: p for p in products}
