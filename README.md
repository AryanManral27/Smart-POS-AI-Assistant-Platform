# Smart POS AI Assistant Platform

Python service that simulates AI features for a Smart POS: **AI-assisted product listing** (descriptions, category, GST, HSN, keywords) and **AI-assisted business insights** (top sellers, trends, performance, recommendations). Metrics are computed from included **mock datasets** and run fully without any API key by default (rule-based mode). If you add `OPENROUTER_API_KEY`, it enables OpenRouter-generated narratives.

## Features

### Module 1 — AI-assisted product listing

- **Input:** product `name`, optional `details`
- **Output:** `description`, `category`, `gst_rate_percent`, `hsn_code`, `keywords`, plus a compliance `disclaimer`

### Module 2 — AI-assisted business insights

Grounded on `data/sales_transactions.json`, `data/products.json`, and `data/inventory.json`:

- Top-selling products (by units and revenue)
- Sales trends (daily revenue, units, transaction count)
- Per-product performance with stock status vs reorder point
- AI-generated **Insights** and **Recommendations** 

## Requirements

- Python 3.10+ installed.
- Optional: [OpenRouter API key](https://openrouter.ai/keys) for LLM features

## Setup

```powershell
cd "c:\Users\HP\Desktop\POS platform"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

You can run the project without `.env` and without any API key.
If you want live OpenRouter output, create `.env` from `.env.example` and set `OPENROUTER_API_KEY`.

## Run

```powershell
cd "c:\Users\HP\Desktop\POS platform"; Start-Process "http://127.0.0.1:8001/app"; .\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

- Interactive API docs: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- Simple web app UI: [http://127.0.0.1:8001/app](http://127.0.0.1:8001/app)

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Server OK + data folder path |
| POST | `/api/v1/products/ai-assist` | Body: `{"name": "...", "details": "optional"}` |
| GET | `/api/v1/insights` | Full JSON: summary, trends, products, inventory alerts, insights text |

### Example: product assist

```powershell
curl -X POST http://127.0.0.1:8001/api/v1/products/ai-assist ^
  -H "Content-Type: application/json" ^
  -d "{\"name\": \"Cold Brew Coffee 300ml\", \"details\": \"unsweetened, shelf stable\"}"
```

### Example: insights

```powershell
curl http://127.0.0.1:8001/api/v1/insights
```

## Data layout (mock data)

| File | Purpose |
|------|---------|
| `data/products.json` | Catalog: id, name, category, HSN, GST %, price, tags |
| `data/inventory.json` | Stock by `product_id`, SKU, quantity, reorder point |
| `data/sales_transactions.json` | Receipts with timestamps, channel, line items |

Each **Refresh Insights** reloads from these files.

## Notes

- **GST and HSN** from the assistant are **informational**; always verify with a qualified professional before compliance use.
- The default model is `openai/gpt-4o-mini` (override with `OPENROUTER_MODEL` in `.env`).
- `OPENROUTER_BASE_URL` is preconfigured for OpenRouter's OpenAI-compatible endpoint.

## Request Flow Diagram

```
User opens web page (http://127.0.0.1:8001/app)
                    ↓
Clicks "Product Listing" or "Insights"
                    ↓
Browser sends API request
                    ↓
main.py receives the request
                    ↓
Routes request to service layer
                    ↓
Services load data and call analytics
                    ↓
Optional call to LLM (chat_json / chat_text)
                    ↓
If AI fails → Use fallback logic
                    ↓
Backend returns JSON response
                    ↓
Frontend updates dashboard
(KPI cards, tables, charts, insight text)
                    ↓
User sees results
```

## Project structure

```
.
├── main.py                 
├── requirements.txt
├── .env.example
├── README.md
├── data/
│   ├── products.json
│   ├── inventory.json
│   └── sales_transactions.json
└── pos_assistant/
    ├── config.py
    ├── datasets.py
    ├── analytics.py
    ├── llm.py
    └── services/
        ├── product_listing.py
        └── business_insights.py
```