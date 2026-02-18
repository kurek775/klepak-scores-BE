import csv
import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.core.dependencies import get_current_active_user
from app.database import get_session
from app.models.activity import Activity, EvaluationType
from app.models.age_category import AgeCategory
from app.models.event import Event
from app.models.group import Group
from app.models.participant import Participant
from app.models.record import Record
from app.models.user import User, UserRole
from app.schemas.leaderboard import (
    ActivityLeaderboard,
    CategoryRanking,
    LeaderboardResponse,
    ParticipantRank,
)

router = APIRouter(tags=["analytics"])


def _assign_age_category(age: int | None, categories: list[AgeCategory], has_categories: bool) -> str:
    if not has_categories:
        return "All"
    if age is None:
        return "Unassigned"
    for cat in categories:
        if cat.min_age <= age <= cat.max_age:
            return cat.name
    return "Unassigned"


def _sort_key_for_record(value_raw: str, evaluation_type: EvaluationType):
    """Return a sortable key. Lower value = better rank for NUMERIC_LOW; higher = better for others."""
    try:
        numeric = float(value_raw)
        if evaluation_type == EvaluationType.NUMERIC_LOW:
            return (0, numeric)
        else:
            return (0, -numeric)
    except (ValueError, TypeError):
        return (1, 0)  # unparseable goes last


@router.get("/events/{event_id}/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    event_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    age_categories = session.exec(
        select(AgeCategory).where(AgeCategory.event_id == event_id)
    ).all()
    has_age_categories = len(age_categories) > 0

    # Build ordering map: age_cat_name -> min_age for sorting
    cat_order: dict[str, int] = {cat.name: cat.min_age for cat in age_categories}

    activities = session.exec(
        select(Activity).where(Activity.event_id == event_id)
    ).all()

    # Build participant lookup: participant_id -> (participant, group_name)
    groups = session.exec(select(Group).where(Group.event_id == event_id)).all()
    participant_map: dict[int, tuple[Participant, str]] = {}
    for group in groups:
        participants = session.exec(
            select(Participant).where(Participant.group_id == group.id)
        ).all()
        for p in participants:
            participant_map[p.id] = (p, group.name)

    activity_leaderboards: list[ActivityLeaderboard] = []

    for activity in activities:
        # Fetch all records for this activity
        records = session.exec(
            select(Record).where(Record.activity_id == activity.id)
        ).all()

        # Group records into (gender, age_cat_name) buckets
        buckets: dict[tuple[str, str], list[tuple[Participant, str, str]]] = {}
        for record in records:
            if record.participant_id not in participant_map:
                continue
            participant, _group_name = participant_map[record.participant_id]
            gender = participant.gender or "?"
            age_cat_name = _assign_age_category(participant.age, list(age_categories), has_age_categories)
            key = (gender, age_cat_name)
            if key not in buckets:
                buckets[key] = []
            buckets[key].append((participant, record.value_raw, _group_name))

        # Sort each bucket and build CategoryRanking
        category_rankings: list[CategoryRanking] = []
        for (gender, age_cat_name), entries in buckets.items():
            sorted_entries = sorted(
                entries,
                key=lambda e: _sort_key_for_record(e[1], activity.evaluation_type),
            )
            participant_ranks: list[ParticipantRank] = []
            rank = 1
            for i, (participant, value_raw, _gn) in enumerate(sorted_entries):
                # Ties: same sort key → same rank
                if i > 0:
                    prev_key = _sort_key_for_record(sorted_entries[i - 1][1], activity.evaluation_type)
                    curr_key = _sort_key_for_record(value_raw, activity.evaluation_type)
                    if curr_key != prev_key:
                        rank = i + 1
                participant_ranks.append(
                    ParticipantRank(
                        rank=rank,
                        participant_id=participant.id,
                        display_name=participant.display_name,
                        gender=participant.gender,
                        age=participant.age,
                        value=value_raw,
                    )
                )
            category_rankings.append(
                CategoryRanking(
                    gender=gender,
                    age_category_name=age_cat_name,
                    participants=participant_ranks,
                )
            )

        # Sort categories: by (gender, age_cat min_age)
        category_rankings.sort(
            key=lambda c: (c.gender, cat_order.get(c.age_category_name, 9999))
        )

        activity_leaderboards.append(
            ActivityLeaderboard(
                activity_id=activity.id,
                activity_name=activity.name,
                evaluation_type=activity.evaluation_type.value,
                categories=category_rankings,
            )
        )

    return LeaderboardResponse(
        event_id=event.id,
        event_name=event.name,
        has_age_categories=has_age_categories,
        activities=activity_leaderboards,
    )


@router.get("/events/{event_id}/export-csv")
def export_csv(
    event_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    activities = session.exec(
        select(Activity).where(Activity.event_id == event_id)
    ).all()

    groups = session.exec(
        select(Group).where(Group.event_id == event_id)
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(
        ["group_name", "participant_name", "gender", "age"] + [a.name for a in activities]
    )

    for group in groups:
        participants = session.exec(
            select(Participant).where(Participant.group_id == group.id)
        ).all()

        for participant in participants:
            row_values: list[str] = [
                group.name,
                participant.display_name,
                participant.gender or "",
                str(participant.age) if participant.age is not None else "",
            ]
            for activity in activities:
                record = session.exec(
                    select(Record).where(
                        Record.participant_id == participant.id,
                        Record.activity_id == activity.id,
                    )
                ).first()
                row_values.append(record.value_raw if record else "")
            writer.writerow(row_values)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=event_{event_id}_export.csv"},
    )
