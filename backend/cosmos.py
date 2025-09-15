import os
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional

from azure.cosmos import CosmosClient, PartitionKey, exceptions

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "nchatsdb")
USERS_CONTAINER = os.getenv("COSMOS_USERS_CONTAINER", "users")
CHARACTERS_CONTAINER = os.getenv("COSMOS_CHARACTERS_CONTAINER", "characters")
AUTO_PROVISION = os.getenv("COSMOS_AUTO_PROVISION", "false").lower() == "true"

class CosmosUnavailable(RuntimeError):
    pass

@lru_cache(maxsize=1)
def get_client() -> CosmosClient:
    if not COSMOS_ENDPOINT or not COSMOS_KEY:
        raise CosmosUnavailable("COSMOS_ENDPOINT or COSMOS_KEY not set")
    return CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)

def get_database():
    client = get_client()
    try:
        return client.get_database_client(COSMOS_DATABASE)
    except exceptions.CosmosResourceNotFoundError:
        if AUTO_PROVISION:
            return client.create_database_if_not_exists(COSMOS_DATABASE)
        raise CosmosUnavailable(f"Database {COSMOS_DATABASE} not found and AUTO_PROVISION disabled")

def get_container_users():
    db = get_database()
    try:
        return db.get_container_client(USERS_CONTAINER)
    except exceptions.CosmosResourceNotFoundError:
        if AUTO_PROVISION:
            return db.create_container_if_not_exists(id=USERS_CONTAINER, partition_key=PartitionKey(path="/id"), offer_throughput=400)
        raise CosmosUnavailable(f"Users container {USERS_CONTAINER} missing")

def get_container_characters():
    db = get_database()
    try:
        return db.get_container_client(CHARACTERS_CONTAINER)
    except exceptions.CosmosResourceNotFoundError:
        if AUTO_PROVISION:
            return db.create_container_if_not_exists(id=CHARACTERS_CONTAINER, partition_key=PartitionKey(path="/id"), offer_throughput=400)
        raise CosmosUnavailable(f"Characters container {CHARACTERS_CONTAINER} missing")

# Repository-like helpers

def create_user(*, username: str, email: str, hashed_password: str) -> Dict[str, Any]:
    c = get_container_users()
    doc = {
        'id': username,  # use username as id for point reads
        'username': username,
        'email': email,
        'hashed_password': hashed_password,
        'gem_balance': 100,
        'is_active': True,
        'created_at': int(time.time())
    }
    try:
        c.create_item(body=doc)
    except exceptions.CosmosHttpResponseError as e:
        if e.status_code == 409:
            raise ValueError("User already exists")
        raise
    return doc

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    c = get_container_users()
    try:
        return c.read_item(item=username, partition_key=username)
    except exceptions.CosmosResourceNotFoundError:
        return None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    c = get_container_users()
    query = "SELECT * FROM c WHERE c.email = @email"
    items = list(c.query_items(query=query, parameters=[{"name": "@email", "value": email}], enable_cross_partition_query=True))
    return items[0] if items else None

def list_characters(sort: str = "popular", limit: int = 12) -> List[Dict[str, Any]]:
    c = get_container_characters()
    order_field = 'rating_avg' if sort == 'popular' else ('last_active' if sort == 'new' else 'id')
    query = f"SELECT * FROM c ORDER BY c.{order_field} DESC" if order_field != 'id' else "SELECT * FROM c ORDER BY c.id"
    items = []
    for item in c.query_items(query=query, enable_cross_partition_query=True):
        items.append(item)
        if len(items) >= limit:
            break
    return items

def count_characters() -> int:
    c = get_container_characters()
    query = "SELECT VALUE COUNT(1) FROM c"
    result = list(c.query_items(query=query, enable_cross_partition_query=True))
    return result[0] if result else 0

class NoCharacterData(RuntimeError):
    """Raised when expected character data is not present in Cosmos DB."""
    pass

def health_check() -> bool:
    # basic read of users container properties
    try:
        get_container_users().read()
        return True
    except Exception:
        return False
