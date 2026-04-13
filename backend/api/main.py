"""
Pisubí — FastAPI app principal
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import commodities, prices, companies, variables, news, trade, summary, alerts
from backend.api.routes import admin

app = FastAPI(
    title="Pisubí — Monitor de Commodities",
    version="0.1.0",
    description="API REST para seguimiento de litio, oro y soja con foco en Argentina.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(commodities.router, prefix="/commodities", tags=["commodities"])
app.include_router(prices.router,      prefix="/prices",      tags=["prices"])
app.include_router(companies.router,   prefix="/companies",   tags=["companies"])
app.include_router(variables.router,   prefix="/impact-variables", tags=["variables"])
app.include_router(news.router,        prefix="/news",             tags=["news"])
app.include_router(trade.router,       prefix="/trade-flows",       tags=["trade"])
app.include_router(summary.router,     prefix="/summary",           tags=["summary"])
app.include_router(alerts.router,      prefix="/alerts",            tags=["alerts"])
app.include_router(admin.router,       prefix="/admin",             tags=["admin"])


@app.get("/health")
def health():
    return {"status": "ok", "project": "Pisubí"}
