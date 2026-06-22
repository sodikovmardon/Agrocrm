from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, schema: CreateSchemaType, **extra_fields: Any) -> ModelType:
        data = schema.model_dump(exclude_unset=True)
        data.update(extra_fields)
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get(self, id: UUID) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        descending: bool = False,
    ) -> List[ModelType]:
        stmt = select(self.model)
        if filters:
            for key, value in filters.items():
                column = getattr(self.model, key, None)
                if column is not None:
                    if isinstance(value, (list, tuple)):
                        stmt = stmt.where(column.in_(value))
                    else:
                        stmt = stmt.where(column == value)
        if order_by:
            column = getattr(self.model, order_by, None)
            if column is not None:
                if descending:
                    stmt = stmt.order_by(column.desc())
                else:
                    stmt = stmt.order_by(column.asc())
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        stmt = select(func.count(self.model.id))
        if filters:
            for key, value in filters.items():
                column = getattr(self.model, key, None)
                if column is not None:
                    stmt = stmt.where(column == value)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def update(
        self,
        id: UUID,
        schema: UpdateSchemaType,
    ) -> Optional[ModelType]:
        data = schema.model_dump(exclude_unset=True)
        if not data:
            return await self.get(id)
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**data)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def update_by_dict(
        self,
        id: UUID,
        data: Dict[str, Any],
    ) -> Optional[ModelType]:
        if not data:
            return await self.get(id)
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**data)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def delete(self, id: UUID) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def exists(self, id: UUID) -> bool:
        stmt = select(func.count(self.model.id)).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0
