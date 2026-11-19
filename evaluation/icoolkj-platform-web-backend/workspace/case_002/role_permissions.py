from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.services.roles import replace_role_permissions

router = APIRouter()


class PermissionUpdate(BaseModel):
    organization_id: str
    permission_codes: list[str]


@router.put("/roles/{role_id}/permissions")
async def update_permissions(
    role_id: str,
    body: PermissionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await replace_role_permissions(
        db,
        role_id=role_id,
        organization_id=body.organization_id,
        permission_codes=body.permission_codes,
    )
    return {"role_id": role_id, "permission_codes": body.permission_codes}
