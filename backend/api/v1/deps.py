"""Shared FastAPI dependencies."""
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.farm_repo import FarmRepository
from app.api.v1.auth import get_current_user_id


async def verify_farm_access(
    farm_id: UUID,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> UUID:
    """Ensure the authenticated user owns or is a member of the farm.

    Prevents IDOR: without this, any logged-in user could read/modify another
    farmer's data just by knowing the farm_id.
    """
    repo = FarmRepository(session)
    farm = await repo.get(farm_id)
    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ferma topilmadi.",
        )

    uid = UUID(user_id)
    if farm.owner_id == uid:
        return farm_id

    member = await repo.get_member_by_user_and_farm(farm_id, uid)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu fermaga ruxsatingiz yo'q.",
        )
    return farm_id
