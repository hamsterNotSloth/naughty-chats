"""Manual seeding script for initial character documents.

Run this once after Cosmos DB containers are provisioned and BEFORE users
expect character browsing to work. This script is intentionally separate so
that the application does not silently fall back or auto-populate data in
production.

Usage:
  python -m seed_characters

Environment variables required (same as app):
  COSMOS_ENDPOINT, COSMOS_KEY, optionally COSMOS_DATABASE / COSMOS_CHARACTERS_CONTAINER
"""
from datetime import datetime
import time
import cosmos
from azure.cosmos import exceptions

SEED_DATA = [
    dict(id="luna", name="Luna the Mystic", avatar_url="https://via.placeholder.com/150", short_description="A mysterious sorceress from the ethereal realm", tags=["fantasy","magical","mysterious"], rating_avg=4.8, rating_count=127, gem_cost_per_message=5, nsfw_flags=False, last_active=int(time.time())),
    dict(id="zara", name="Zara the Adventurer", avatar_url="https://via.placeholder.com/150", short_description="Bold explorer seeking thrilling adventures", tags=["adventure","bold","explorer"], rating_avg=4.6, rating_count=89, gem_cost_per_message=4, nsfw_flags=False, last_active=int(time.time())),
    dict(id="kai", name="Kai the Scholar", avatar_url="https://via.placeholder.com/150", short_description="Wise academic with endless knowledge", tags=["intellectual","wise","academic"], rating_avg=4.9, rating_count=203, gem_cost_per_message=6, nsfw_flags=False, last_active=int(time.time())),
]

def main():
    existing = cosmos.count_characters()
    if existing > 0:
        print(f"Characters already present ({existing}). No action taken.")
        return
    container = cosmos.get_container_characters()
    created = 0
    for row in SEED_DATA:
        try:
            container.create_item(body=row)
            created += 1
        except exceptions.CosmosHttpResponseError as e:
            if e.status_code == 409:
                print(f"Already exists: {row['id']}")
            else:
                raise
    print(f"Seed complete. Inserted {created} character documents.")

if __name__ == "__main__":
    main()
