from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from sqlmodel import Session

from app.core.dependencies import get_current_active_user
from app.core.limiter import limiter
from app.database import get_session
from app.models.user import User
from app.schemas.activity import BulkRecordCreate, RecordCreate, RecordRead
from app.services import record_service

router = APIRouter(tags=["records"])


@router.post("/records/process-image")
@limiter.limit("20/minute")
async def process_image(
    request: Request,
    file: UploadFile = File(...),
    activity_id: int = Form(...),
    group_id: int = Form(...),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    return await record_service.process_image(session, user, file, activity_id, group_id)


@router.post("/records", response_model=RecordRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
def submit_record(
    request: Request,
    body: RecordCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    return record_service.submit_record(session, user, body)


@router.post("/records/bulk", response_model=list[RecordRead], status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def submit_bulk_records(
    request: Request,
    body: BulkRecordCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    return record_service.submit_bulk_records(session, user, body)


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    record_service.delete_record(session, user, record_id)


@router.get("/activities/{activity_id}/records", response_model=list[RecordRead])
def get_activity_records(
    activity_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    return record_service.get_activity_records(session, user, activity_id)
