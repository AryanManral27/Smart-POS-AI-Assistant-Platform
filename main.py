from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from pos_assistant.config import DATA_DIR
from pos_assistant.datasets import load_inventory, load_products, load_sales
from pos_assistant.services.business_insights import generate_business_insights
from pos_assistant.services.product_listing import assist_product_listing

app = FastAPI(
    title="Smart POS AI Assistant",
    description="AI-assisted product listing and business insights over mock POS data.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")


class ProductAssistRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Product name")
    details: str | None = Field(None, description="Optional extra details for the LLM")


class HealthResponse(BaseModel):
    status: str
    data_dir: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", data_dir=str(DATA_DIR.resolve()))


@app.post("/api/v1/products/ai-assist")
def product_ai_assist(body: ProductAssistRequest) -> dict:
    try:
        return assist_product_listing(body.name, body.details)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/api/v1/insights")
def insights() -> dict:
    products = load_products()
    inventory = load_inventory()
    sales = load_sales()
    return generate_business_insights(sales, products, inventory)


@app.get("/")
def root() -> dict:
    return {
        "service": "Smart POS AI Assistant",
        "ui": "/app",
        "docs": "/docs",
        "endpoints": {
            "product_assist": "POST /api/v1/products/ai-assist",
            "insights": "GET /api/v1/insights",
        },
    }


@app.get("/app")
def ui() -> FileResponse:
    # Avoid stale dashboard JS/HTML after edits (common cause of "old error message" reports)
    return FileResponse(
        "static/index.html",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
    )
