from sqlmodel import Field, SQLModel


class EventEvaluator(SQLModel, table=True):
    __tablename__ = "event_evaluator"
    event_id: int = Field(foreign_key="event.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)
