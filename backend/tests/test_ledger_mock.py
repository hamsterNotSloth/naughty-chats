import pytest
from unittest.mock import MagicMock
from ..ledger import LedgerService, InsufficientFunds


class DummyResp:
    def __init__(self, successful=True):
        self.is_successful = successful


class DummyBatch:
    def __init__(self):
        self.ops = []

    def create_item(self, item):
        self.ops.append(("create", item))

    def replace_item(self, item, body, if_match=None):
        self.ops.append(("replace", item, body, if_match))

    def execute(self):
        return DummyResp(successful=True)


def make_container(balance=1000):
    container = MagicMock()

    balance_doc = {"id": "balance:user-1", "docType": "balance", "user_id": "user-1", "balance": balance, "_etag": 'etag-1'}
    hold_doc = {"id": "hold:existing", "docType": "hold", "user_id": "user-1", "amount": 200, "status": "placed"}

    def read_item(item, partition_key):
        if item == balance_doc["id"]:
            return dict(balance_doc)
        if item == hold_doc["id"]:
            return dict(hold_doc)
        raise Exception("not found")

    container.read_item.side_effect = read_item
    container.create_transactional_batch.side_effect = lambda partition_key: DummyBatch()
    container.query_items.side_effect = lambda query, parameters, partition_key, enable_cross_partition_query: []
    return container


def test_reserve_hold_success():
    c = make_container(balance=1000)
    svc = LedgerService(c)
    out = svc.reserve_hold("user-1", 100, idempotency_key="k1")
    assert out["balance_after"] == 900
    assert out["hold_id"].startswith("hold:")


def test_reserve_hold_insufficient():
    c = make_container(balance=50)
    svc = LedgerService(c)
    with pytest.raises(InsufficientFunds):
        svc.reserve_hold("user-1", 100, idempotency_key="k2")


def test_finalize_hold_refund_and_debit():
    # finalize where actual_cost < hold -> refund
    c = make_container(balance=800)
    svc = LedgerService(c)
    # monkeypatch read_item to return custom hold with amount 200 for finalize case
    hold = {"id": "hold:h1", "docType": "hold", "user_id": "user-1", "amount": 200, "status": "placed"}

    def read_item(item, partition_key):
        if item == "balance:user-1":
            return {"id": "balance:user-1", "docType": "balance", "user_id": "user-1", "balance": 800, "_etag": 'etag-2'}
        if item == "hold:h1":
            return dict(hold)
        raise Exception("not found")

    c.read_item.side_effect = read_item
    c.create_transactional_batch.side_effect = lambda partition_key: DummyBatch()

    out_refund = svc.finalize_hold("user-1", "hold:h1", actual_cost=100)
    assert out_refund["balance_after"] == 900

    # finalize where actual_cost > hold -> extra debit
    hold2 = {"id": "hold:h2", "docType": "hold", "user_id": "user-1", "amount": 100, "status": "placed"}

    def read_item2(item, partition_key):
        if item == "balance:user-1":
            return {"id": "balance:user-1", "docType": "balance", "user_id": "user-1", "balance": 900, "_etag": 'etag-3'}
        if item == "hold:h2":
            return dict(hold2)
        raise Exception("not found")

    c.read_item.side_effect = read_item2
    out_debit = svc.finalize_hold("user-1", "hold:h2", actual_cost=250)
    # hold was 100, actual 250 -> delta 150 debited from 900 -> 750
    assert out_debit["balance_after"] == 750
