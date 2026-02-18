from pydantic import BaseModel


class ParticipantRank(BaseModel):
    rank: int
    participant_id: int
    display_name: str
    gender: str | None
    age: int | None
    value: str


class CategoryRanking(BaseModel):
    gender: str
    age_category_name: str
    participants: list[ParticipantRank]


class ActivityLeaderboard(BaseModel):
    activity_id: int
    activity_name: str
    evaluation_type: str
    categories: list[CategoryRanking]


class LeaderboardResponse(BaseModel):
    event_id: int
    event_name: str
    has_age_categories: bool
    activities: list[ActivityLeaderboard]
