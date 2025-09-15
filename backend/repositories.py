from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from . import models

# User repositories
async def get_user_by_username(session: AsyncSession, username: str) -> Optional[models.User]:
    result = await session.execute(select(models.User).where(models.User.username == username))
    return result.scalar_one_or_none()

async def get_user_by_email(session: AsyncSession, email: str) -> Optional[models.User]:
    result = await session.execute(select(models.User).where(models.User.email == email))
    return result.scalar_one_or_none()

async def create_user(session: AsyncSession, *, email: str, username: str, hashed_password: str) -> models.User:
    user = models.User(email=email, username=username, hashed_password=hashed_password)
    session.add(user)
    await session.flush()  # assign id
    return user

# Character repositories
async def list_characters(session: AsyncSession, sort: str = "popular", limit: int = 12) -> List[models.Character]:
    stmt = select(models.Character)
    if sort == "popular":
        stmt = stmt.order_by(models.Character.rating_avg.desc())
    elif sort == "new":
        stmt = stmt.order_by(models.Character.last_active.desc())
    else:
        stmt = stmt.order_by(models.Character.id.asc())
    stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

async def count_characters(session: AsyncSession) -> int:
    from sqlalchemy import func
    stmt = select(func.count(models.Character.id))
    result = await session.execute(stmt)
    return result.scalar_one()

async def seed_characters(session: AsyncSession):
    if await count_characters(session) > 0:
        return
    # Basic seed data (mirroring previous in-memory examples)
    seed_data = [
        dict(name="Luna the Mystic", avatar_url="https://via.placeholder.com/150", short_description="A mysterious sorceress from the ethereal realm", tags=["fantasy","magical","mysterious"], rating_avg=4.8, rating_count=127, gem_cost_per_message=5, nsfw_flags=False),
        dict(name="Zara the Adventurer", avatar_url="https://via.placeholder.com/150", short_description="Bold explorer seeking thrilling adventures", tags=["adventure","bold","explorer"], rating_avg=4.6, rating_count=89, gem_cost_per_message=4, nsfw_flags=False),
        dict(name="Kai the Scholar", avatar_url="https://via.placeholder.com/150", short_description="Wise academic with endless knowledge", tags=["intellectual","wise","academic"], rating_avg=4.9, rating_count=203, gem_cost_per_message=6, nsfw_flags=False),
    ]
    for row in seed_data:
        session.add(models.Character(**row))
    await session.flush()
