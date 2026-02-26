import csv
import io
import logging
from collections import defaultdict
from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.core.redis_client import redis_client
from app.core.dependencies import get_current_active_user
from app.core.permissions import require_admin
from app.database import get_session
from app.models.activity import Activity, EvaluationType
from app.models.age_category import AgeCategory
from app.models.event import Event
from app.models.group import Group
from app.models.participant import Participant
from app.models.record import Record
from app.models.user import User
from app.schemas.leaderboard import (
    ActivityLeaderboard,
    CategoryRanking,
    LeaderboardResponse,
    ParticipantRank,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analytics"])


# ── Shared leaderboard helpers ──────────────────────────────────────────────

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


@dataclass
class RankedEntry:
    rank: int
    participant: Participant
    group_name: str
    value_raw: str
    gender: str
    age_category_name: str


def _load_event_data(
    session: Session, event_id: int
) -> tuple[
    list[Activity],
    list[AgeCategory],
    bool,
    dict[int, tuple[Participant, str]],
    dict[int, list[Record]],
]:
    """Load activities, age categories, participant map, and records for an event."""
    age_categories = session.exec(
        select(AgeCategory).where(AgeCategory.event_id == event_id)
    ).all()
    has_age_categories = len(age_categories) > 0

    activities = session.exec(
        select(Activity).where(Activity.event_id == event_id)
    ).all()

    groups = session.exec(select(Group).where(Group.event_id == event_id)).all()
    group_name_map = {g.id: g.name for g in groups}
    participants = session.exec(
        select(Participant).join(Group, Participant.group_id == Group.id)
        .where(Group.event_id == event_id)
    ).all()
    participant_map: dict[int, tuple[Participant, str]] = {
        p.id: (p, group_name_map[p.group_id]) for p in participants
    }

    all_records = session.exec(
        select(Record).join(Activity, Record.activity_id == Activity.id)
        .where(Activity.event_id == event_id)
    ).all()
    records_by_activity: dict[int, list[Record]] = defaultdict(list)
    for r in all_records:
        records_by_activity[r.activity_id].append(r)

    return activities, list(age_categories), has_age_categories, participant_map, records_by_activity


def _bucket_and_rank(
    records: list[Record],
    activity: Activity,
    age_categories: list[AgeCategory],
    has_age_categories: bool,
    participant_map: dict[int, tuple[Participant, str]],
) -> dict[tuple[str, str], list[RankedEntry]]:
    """Group records into (gender, age_cat) buckets, sort, and assign ranks."""
    buckets: dict[tuple[str, str], list[tuple[Participant, str, str]]] = {}
    for record in records:
        if record.participant_id not in participant_map:
            continue
        participant, group_name = participant_map[record.participant_id]
        gender = participant.gender or "?"
        age_cat_name = _assign_age_category(participant.age, age_categories, has_age_categories)
        key = (gender, age_cat_name)
        buckets.setdefault(key, []).append((participant, record.value_raw, group_name))

    ranked: dict[tuple[str, str], list[RankedEntry]] = {}
    for (gender, age_cat_name), entries in buckets.items():
        sorted_entries = sorted(
            entries,
            key=lambda e: _sort_key_for_record(e[1], activity.evaluation_type),
        )
        rank = 1
        ranked_list: list[RankedEntry] = []
        for i, (participant, value_raw, group_name) in enumerate(sorted_entries):
            if i > 0:
                prev_key = _sort_key_for_record(sorted_entries[i - 1][1], activity.evaluation_type)
                curr_key = _sort_key_for_record(value_raw, activity.evaluation_type)
                if curr_key != prev_key:
                    rank = i + 1
            ranked_list.append(RankedEntry(
                rank=rank,
                participant=participant,
                group_name=group_name,
                value_raw=value_raw,
                gender=gender,
                age_category_name=age_cat_name,
            ))
        ranked[(gender, age_cat_name)] = ranked_list

    return ranked


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/events/{event_id}/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    event_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_active_user),
):
    try:
        cached = redis_client.get(f"leaderboard:{event_id}")
        if cached:
            return LeaderboardResponse.model_validate_json(cached)
    except Exception:
        logger.warning("Failed to read leaderboard cache for event %s", event_id)

    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    activities, age_categories, has_age_categories, participant_map, records_by_activity = (
        _load_event_data(session, event_id)
    )
    cat_order: dict[str, int] = {cat.name: cat.min_age for cat in age_categories}

    activity_leaderboards: list[ActivityLeaderboard] = []

    for activity in activities:
        ranked_buckets = _bucket_and_rank(
            records_by_activity[activity.id],
            activity,
            age_categories,
            has_age_categories,
            participant_map,
        )

        category_rankings: list[CategoryRanking] = []
        for (gender, age_cat_name), ranked_entries in ranked_buckets.items():
            category_rankings.append(
                CategoryRanking(
                    gender=gender,
                    age_category_name=age_cat_name,
                    participants=[
                        ParticipantRank(
                            rank=e.rank,
                            participant_id=e.participant.id,
                            display_name=e.participant.display_name,
                            gender=e.participant.gender,
                            age=e.participant.age,
                            value=e.value_raw,
                            group_name=e.group_name,
                        )
                        for e in ranked_entries
                    ],
                )
            )

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

    result = LeaderboardResponse(
        event_id=event.id,
        event_name=event.name,
        has_age_categories=has_age_categories,
        activities=activity_leaderboards,
    )
    try:
        redis_client.setex(f"leaderboard:{event_id}", 300, result.model_dump_json())
    except Exception:
        logger.warning("Failed to write leaderboard cache for event %s", event_id)
    return result


@router.get("/events/{event_id}/export-csv")
def export_csv(
    event_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_active_user),
):
    require_admin(user)

    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    activities, age_categories, has_age_categories, participant_map, records_by_activity = (
        _load_event_data(session, event_id)
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["rank", "podium", "activity", "gender", "age_category", "participant_name", "group_name", "age", "score"])

    for activity in activities:
        ranked_buckets = _bucket_and_rank(
            records_by_activity[activity.id],
            activity,
            age_categories,
            has_age_categories,
            participant_map,
        )

        for (_gender, _age_cat), ranked_entries in sorted(ranked_buckets.items()):
            for e in ranked_entries:
                podium = {1: "Gold", 2: "Silver", 3: "Bronze"}.get(e.rank, "")
                writer.writerow([
                    e.rank,
                    podium,
                    activity.name,
                    e.gender,
                    e.age_category_name,
                    e.participant.display_name,
                    e.group_name,
                    e.participant.age if e.participant.age is not None else "",
                    e.value_raw,
                ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=event_{event_id}_results.csv"},
    )
