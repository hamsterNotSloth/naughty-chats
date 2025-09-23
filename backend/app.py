import os
from fastapi import FastAPI, HTTPException, Depends, WebSocket
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

try:
    from azure.cosmos import CosmosClient
except Exception:
    CosmosClient = None

from .ledger import LedgerService, InsufficientFunds, BatchFailedError
from . import ledger as ledger_module
from .api import auth_routes
from .api import characters as characters_router
from .api import chat as chat_router
from .api import gems as gems_router
from .api import generate as generate_router
from .api import affiliates as affiliates_router
from .api import users as users_router

app = FastAPI(title="naughty-chats-backend")

# configure CORS (allow dev frontend origins)
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://naughty-frontend-dev-ysurana.eastus.azurecontainer.io")
_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(auth_routes.router)
app.include_router(characters_router.router)
app.include_router(chat_router.router)
app.include_router(gems_router.router)
app.include_router(generate_router.router)
app.include_router(affiliates_router.router)
app.include_router(users_router.router)

@app.get("/")
def root():
    return {"ok": True, "service": "naughty-chats backend skeleton"}


@app.websocket('/ws')
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    await ws.send_text('hello from ws (auth handshake not implemented)')
    await ws.close()

COSMOS_URL = os.getenv("COSMOS_URL")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DB = os.getenv("COSMOS_DB", "appdb")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER", "ledger")

client = None
container = None
ledger_service = None

if COSMOS_URL and COSMOS_KEY and CosmosClient is not None:
    client = CosmosClient(COSMOS_URL, COSMOS_KEY)
    db = client.get_database_client(COSMOS_DB)
    container = db.get_container_client(COSMOS_CONTAINER)
    ledger_service = LedgerService(container)
else:
    # Lazy: ledger_service remains None and endpoints will return 500 with helpful message
    pass


class HoldRequest(BaseModel):
    user_id: str
    amount: int
    idempotency_key: str | None = None


class FinalizeRequest(BaseModel):
    user_id: str
    hold_id: str
    actual_cost: int
    idempotency_key: str | None = None


class CancelRequest(BaseModel):
    user_id: str
    hold_id: str
    idempotency_key: str | None = None


@app.get("/api/v1/gems/balance")
def balance(user_id: str):
    if not ledger_service:
        raise HTTPException(status_code=500, detail="Cosmos not configured")
    try:
        bal = ledger_service.get_balance(user_id)
        return {"user_id": user_id, "balance": bal}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/gems/ledger")
def ledger_list(user_id: str, limit: int = 50):
    if not ledger_service:
        raise HTTPException(status_code=500, detail="Cosmos not configured")
    items = ledger_service.list_ledger_events(user_id, limit=limit)
    return {"items": items}


@app.post("/api/v1/gems/hold")
def place_hold(req: HoldRequest):
    if not ledger_service:
        raise HTTPException(status_code=500, detail="Cosmos not configured")
    try:
        out = ledger_service.reserve_hold(req.user_id, req.amount, req.idempotency_key)
        return out
    except InsufficientFunds:
        raise HTTPException(status_code=402, detail="Insufficient gems")
    except BatchFailedError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/gems/finalize")
def finalize(req: FinalizeRequest):
    if not ledger_service:
        raise HTTPException(status_code=500, detail="Cosmos not configured")
    try:
        out = ledger_service.finalize_hold(req.user_id, req.hold_id, req.actual_cost, req.idempotency_key)
        return out
    except BatchFailedError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/gems/cancel")
def cancel(req: CancelRequest):
    if not ledger_service:
        raise HTTPException(status_code=500, detail="Cosmos not configured")
    try:
        out = ledger_service.cancel_hold(req.user_id, req.hold_id, req.idempotency_key)
        return out
    except BatchFailedError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
