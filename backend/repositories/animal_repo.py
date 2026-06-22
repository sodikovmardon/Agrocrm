from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.animal import Animal, AnimalGroup
from app.repositories.base import BaseRepository


class AnimalRepository(BaseRepository[Animal, Any, Any]):
    def __init__(self, session: AsyncSession):
        super().__init__(Animal, session)

    async def get_animals_by_farm(self, farm_id: UUID, status: Optional[str] = None) -> List[Animal]:
        stmt = select(Animal).where(Animal.farm_id == farm_id)
        if status:
            stmt = stmt.where(Animal.status == status)
        stmt = stmt.order_by(Animal.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_animals_by_type(self, farm_id: UUID, animal_type: str) -> List[Animal]:
        stmt = (
            select(Animal)
            .where(and_(Animal.farm_id == farm_id, Animal.type == animal_type))
            .order_by(Animal.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_animal_count(self, farm_id: UUID) -> int:
        stmt = select(func.count(Animal.id)).where(
            and_(Animal.farm_id == farm_id, Animal.status == "active")
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_animal_by_tag(self, farm_id: UUID, tag_number: str) -> Optional[Animal]:
        stmt = select(Animal).where(
            and_(Animal.farm_id == farm_id, Animal.tag_number == tag_number)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_animal_status(self, animal_id: UUID, status: str) -> Optional[Animal]:
        from sqlalchemy import update

        stmt = (
            update(Animal)
            .where(Animal.id == animal_id)
            .values(status=status)
            .returning(Animal)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()


class AnimalGroupRepository(BaseRepository[AnimalGroup, Any, Any]):
    def __init__(self, session: AsyncSession):
        super().__init__(AnimalGroup, session)

    async def get_groups_by_farm(self, farm_id: UUID, status: Optional[str] = None) -> List[AnimalGroup]:
        stmt = select(AnimalGroup).where(AnimalGroup.farm_id == farm_id)
        if status:
            stmt = stmt.where(AnimalGroup.status == status)
        stmt = stmt.order_by(AnimalGroup.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_group_count(self, farm_id: UUID) -> int:
        stmt = select(func.count(AnimalGroup.id)).where(
            and_(AnimalGroup.farm_id == farm_id, AnimalGroup.status == "active")
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_groups_by_type(self, farm_id: UUID, group_type: str) -> List[AnimalGroup]:
        stmt = (
            select(AnimalGroup)
            .where(and_(AnimalGroup.farm_id == farm_id, AnimalGroup.type == group_type))
            .order_by(AnimalGroup.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_group_count(self, group_id: UUID, count: int) -> Optional[AnimalGroup]:
        from sqlalchemy import update

        stmt = (
            update(AnimalGroup)
            .where(AnimalGroup.id == group_id)
            .values(current_count=count)
            .returning(AnimalGroup)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()
