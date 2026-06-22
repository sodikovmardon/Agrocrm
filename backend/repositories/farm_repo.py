from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farm import Farm, FarmMember
from app.repositories.base import BaseRepository


class FarmRepository(BaseRepository[Farm, Any, Any]):
    def __init__(self, session: AsyncSession):
        super().__init__(Farm, session)

    async def get_farms_by_owner(self, owner_id: UUID) -> List[Farm]:
        stmt = select(Farm).where(Farm.owner_id == owner_id).order_by(Farm.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_farms_by_member(self, user_id: UUID) -> List[Farm]:
        stmt = (
            select(Farm)
            .join(FarmMember, FarmMember.farm_id == Farm.id)
            .where(FarmMember.user_id == user_id)
            .order_by(Farm.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_farm_with_members(self, farm_id: UUID) -> Optional[Farm]:
        from sqlalchemy.orm import joinedload

        stmt = (
            select(Farm)
            .options(joinedload(Farm.members))
            .where(Farm.id == farm_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_member_count(self, farm_id: UUID) -> int:
        stmt = select(func.count(FarmMember.id)).where(FarmMember.farm_id == farm_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add_member(self, farm_id: UUID, user_id: UUID, role: str, permissions: Optional[Dict[str, Any]] = None) -> FarmMember:
        member = FarmMember(
            farm_id=farm_id,
            user_id=user_id,
            role=role,
            permissions=permissions or {},
        )
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def remove_member(self, farm_id: UUID, user_id: UUID) -> bool:
        stmt = select(FarmMember).where(
            and_(
                FarmMember.farm_id == farm_id,
                FarmMember.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        member = result.scalar_one_or_none()
        if member is None:
            return False
        await self.session.delete(member)
        await self.session.flush()
        return True

    async def get_members(self, farm_id: UUID) -> List[FarmMember]:
        stmt = select(FarmMember).where(FarmMember.farm_id == farm_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_member_role(self, farm_id: UUID, user_id: UUID, role: str) -> Optional[FarmMember]:
        from sqlalchemy import update

        stmt = (
            update(FarmMember)
            .where(
                and_(
                    FarmMember.farm_id == farm_id,
                    FarmMember.user_id == user_id,
                )
            )
            .values(role=role)
            .returning(FarmMember)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def get_member_by_user_and_farm(self, farm_id: UUID, user_id: UUID) -> Optional[FarmMember]:
        stmt = select(FarmMember).where(
            and_(
                FarmMember.farm_id == farm_id,
                FarmMember.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
