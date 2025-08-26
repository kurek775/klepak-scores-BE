from fastapi import  Depends, HTTPException,  Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from utils.auth import get_user_from_cookie
from db import get_db 

async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    claims = get_user_from_cookie(request)  
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid session")
    res = await db.execute(select(User.is_admin).where(User.sub == sub))
    row = res.first()
    if not row or not bool(row[0]):
        raise HTTPException(status_code=403, detail="Admin only")
    return True
