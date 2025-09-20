from typing import Optional, List, Dict, Any
from uuid import uuid4
from datetime import datetime

try:
    from azure.cosmos import CosmosClient, exceptions
except Exception:
    # In test environments the azure.cosmos package may be missing; allow import-time fallback
    CosmosClient = None
    exceptions = None


class InsufficientFunds(Exception):
    pass


class BatchFailedError(Exception):
    pass


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


class LedgerService:
    def __init__(self, container, db_name: Optional[str] = None):
        """
        container: azure.cosmos.ContainerProxy (or a compatible mocked object)
        """
        self.container = container

    def _balance_id(self, user_id: str) -> str:
        return f"balance:{user_id}"

    def _hold_id(self, hold_uuid: Optional[str] = None) -> str:
        return f"hold:{hold_uuid or uuid4().hex}"

    def _evt_id(self) -> str:
        return f"evt:{uuid4().hex}"

    def get_balance_doc(self, user_id: str) -> Dict[str, Any]:
        balance_id = self._balance_id(user_id)
        try:
            return self.container.read_item(item=balance_id, partition_key=user_id)
        except Exception as e:
            # bubble original for visibility in integration tests
            raise

    def get_balance(self, user_id: str) -> int:
        doc = self.get_balance_doc(user_id)
        return int(doc.get("balance", 0))

    def list_ledger_events(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        # simple query by partition
        query = "SELECT * FROM c WHERE c.user_id=@uid AND c.docType='ledger_event' ORDER BY c.created_at DESC"
        params = [{"name": "@uid", "value": user_id}]
        items = list(self.container.query_items(query=query, parameters=params, partition_key=user_id, enable_cross_partition_query=False))
        return items[:limit]

    def reserve_hold(self, user_id: str, amount: int, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """Place a hold: create ledger_event (negative) + hold doc + update balance in a transactional batch.
        Returns hold_id and event id and new balance_after.
        Raises InsufficientFunds if balance < amount.
        """
        balance_id = self._balance_id(user_id)
        # 1) read balance
        balance_doc = self.container.read_item(item=balance_id, partition_key=user_id)
        current_balance = int(balance_doc.get("balance", 0))
        if current_balance < amount:
            raise InsufficientFunds("insufficient balance for hold")
        etag = balance_doc.get("_etag")

        hold_id = self._hold_id()
        evt_id = self._evt_id()
        new_balance = current_balance - amount

        ledger_event = {
            "id": evt_id,
            "docType": "ledger_event",
            "user_id": user_id,
            "change": -int(amount),
            "balance_after": new_balance,
            "event_type": "hold",
            "reference_id": hold_id,
            "idempotency_key": idempotency_key,
            "metadata": {},
            "created_at": now_iso(),
        }

        hold_doc = {
            "id": hold_id,
            "docType": "hold",
            "user_id": user_id,
            "amount": int(amount),
            "status": "placed",
            "created_at": now_iso(),
            "settled_at": None,
            "idempotency_key": idempotency_key,
            "metadata": {},
        }

        updated_balance_doc = dict(balance_doc)
        updated_balance_doc["balance"] = new_balance
        updated_balance_doc["updated_at"] = now_iso()

        # Build transactional batch
        batch = self.container.create_transactional_batch(partition_key=user_id)
        batch.create_item(ledger_event)
        batch.create_item(hold_doc)
        # use if_match header to protect against concurrent updates if SDK supports
        try:
            batch.replace_item(item=balance_id, body=updated_balance_doc, if_match=etag)
        except TypeError:
            # older SDKs might not accept if_match param via replace_item; try without it
            batch.replace_item(item=balance_id, body=updated_balance_doc)

        resp = batch.execute()
        # SDK returns a BatchResponse-like object; adapt accordingly
        # If resp is truthy and has status code list we can check success, otherwise rely on exception
        try:
            if hasattr(resp, 'is_successful') and not resp.is_successful:
                raise BatchFailedError("batch execution failed")
        except AttributeError:
            # best-effort: if execute didn't raise, assume success
            pass

        return {"hold_id": hold_id, "event_id": evt_id, "balance_after": new_balance}

    def finalize_hold(self, user_id: str, hold_id: str, actual_cost: int, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """Settle a hold. Compute actual_cost vs hold.amount and either refund or charge the difference.
        Ensures idempotency if hold already settled.
        """
        balance_id = self._balance_id(user_id)
        hold = self.container.read_item(item=hold_id, partition_key=user_id)
        if hold.get("status") != "placed":
            return {"already_settled": True}

        balance_doc = self.container.read_item(item=balance_id, partition_key=user_id)
        etag = balance_doc.get("_etag")
        hold_amount = int(hold.get("amount", 0))
        delta = int(actual_cost) - hold_amount
        events = []
        new_balance = int(balance_doc.get("balance", 0))

        if delta > 0:
            # additional debit
            ev = {
                "id": self._evt_id(),
                "docType": "ledger_event",
                "user_id": user_id,
                "change": -int(delta),
                "event_type": "debit_settlement",
                "reference_id": hold_id,
                "created_at": now_iso(),
            }
            events.append(ev)
            new_balance -= delta
        elif delta < 0:
            refund_amount = -delta
            ev = {
                "id": self._evt_id(),
                "docType": "ledger_event",
                "user_id": user_id,
                "change": int(refund_amount),
                "event_type": "refund_settlement",
                "reference_id": hold_id,
                "created_at": now_iso(),
            }
            events.append(ev)
            new_balance += refund_amount

        updated_hold = dict(hold)
        updated_hold["status"] = "settled"
        updated_hold["settled_at"] = now_iso()

        updated_balance = dict(balance_doc)
        updated_balance["balance"] = new_balance
        updated_balance["updated_at"] = now_iso()

        batch = self.container.create_transactional_batch(partition_key=user_id)
        for ev in events:
            batch.create_item(ev)
        batch.replace_item(item=hold_id, body=updated_hold)
        try:
            batch.replace_item(item=balance_id, body=updated_balance, if_match=etag)
        except TypeError:
            batch.replace_item(item=balance_id, body=updated_balance)

        resp = batch.execute()
        try:
            if hasattr(resp, 'is_successful') and not resp.is_successful:
                raise BatchFailedError("batch execution failed")
        except AttributeError:
            pass

        return {"balance_after": new_balance, "events": [e.get("id") for e in events]}

    def cancel_hold(self, user_id: str, hold_id: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        balance_id = self._balance_id(user_id)
        hold = self.container.read_item(item=hold_id, partition_key=user_id)
        if hold.get("status") != "placed":
            return {"already_settled_or_cancelled": True}

        balance_doc = self.container.read_item(item=balance_id, partition_key=user_id)
        etag = balance_doc.get("_etag")
        hold_amount = int(hold.get("amount", 0))

        # refund the hold amount
        refund_ev = {
            "id": self._evt_id(),
            "docType": "ledger_event",
            "user_id": user_id,
            "change": int(hold_amount),
            "event_type": "refund_hold_cancel",
            "reference_id": hold_id,
            "created_at": now_iso(),
        }

        updated_hold = dict(hold)
        updated_hold["status"] = "cancelled"
        updated_hold["settled_at"] = now_iso()

        updated_balance = dict(balance_doc)
        updated_balance["balance"] = int(balance_doc.get("balance", 0)) + hold_amount
        updated_balance["updated_at"] = now_iso()

        batch = self.container.create_transactional_batch(partition_key=user_id)
        batch.create_item(refund_ev)
        batch.replace_item(item=hold_id, body=updated_hold)
        try:
            batch.replace_item(item=balance_id, body=updated_balance, if_match=etag)
        except TypeError:
            batch.replace_item(item=balance_id, body=updated_balance)

        resp = batch.execute()
        try:
            if hasattr(resp, 'is_successful') and not resp.is_successful:
                raise BatchFailedError("batch execution failed")
        except AttributeError:
            pass

        return {"refunded": hold_amount, "balance_after": updated_balance["balance"]}
