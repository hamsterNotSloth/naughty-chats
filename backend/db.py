import os
from typing import Optional

try:
    from azure.cosmos import CosmosClient
except Exception:
    CosmosClient = None

COSMOS_URL = os.getenv("COSMOS_URL")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DB = os.getenv("COSMOS_DB", "naughtychats-db")
COSMOS_USERS_CONTAINER = os.getenv("COSMOS_USERS_CONTAINER", "users")


def get_cosmos_client() -> Optional[CosmosClient]:
    if not CosmosClient:
        return None
    if not COSMOS_URL or not COSMOS_KEY:
        return None
    return CosmosClient(COSMOS_URL, credential=COSMOS_KEY)


def get_users_container():
    client = get_cosmos_client()
    if not client:
        return None
    try:
        db = client.get_database_client(COSMOS_DB)
        container = db.get_container_client(COSMOS_USERS_CONTAINER)
        return container
    except Exception:
        return None
