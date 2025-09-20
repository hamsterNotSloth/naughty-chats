import os
import pytest
from uuid import uuid4

from ..ledger import LedgerService

try:
    from azure.cosmos import CosmosClient
except Exception:
    CosmosClient = None

COSMOS_URL = os.getenv("COSMOS_URL")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DB = os.getenv("COSMOS_DB", "naughtychats-db")
COSMOS_LEDGER_CONTAINER = os.getenv("COSMOS_CONTAINER", "ledger")


@pytest.fixture(scope="module")
def cosmos_container():
    if not COSMOS_URL or not COSMOS_KEY or CosmosClient is None:
        pytest.skip("Cosmos DB not configured for integration tests")
    client = CosmosClient(COSMOS_URL, COSMOS_KEY)
    db = client.get_database_client(COSMOS_DB)
    container = db.get_container_client(COSMOS_LEDGER_CONTAINER)
    return container


def make_balance_doc(user_id: str, balance: int):
    return {"id": f"balance:{user_id}", "docType": "balance", "user_id": user_id, "balance": int(balance)}


def test_hold_and_finalize_and_cancel(cosmos_container):
    user_id = f"testuser:{uuid4().hex}"
    # ensure balance doc
    bal_doc = make_balance_doc(user_id, 100)
    try:
        cosmos_container.create_item(bal_doc)
    except Exception:
        # if exists, replace
        try:
            cosmos_container.upsert_item(bal_doc)
        except Exception:
            pass

    ledger = LedgerService(cosmos_container)

    # place hold 30
    res = ledger.reserve_hold(user_id, 30)
    assert res["balance_after"] == 70

    hold_id = res["hold_id"]

    # finalize with same cost
    out = ledger.finalize_hold(user_id, hold_id, 30)
    assert out["balance_after"] == 70

    # place another hold and cancel
    res2 = ledger.reserve_hold(user_id, 20)
    assert res2["balance_after"] == 50
    hid2 = res2["hold_id"]
    cancel_out = ledger.cancel_hold(user_id, hid2)
    assert cancel_out["balance_after"] == 70
