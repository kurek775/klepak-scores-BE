from pydantic import BaseModel


class AssignEvaluatorRequest(BaseModel):
    user_id: int


class EvaluatorRead(BaseModel):
    id: int
    email: str
    full_name: str

    model_config = {"from_attributes": True}


class MyGroupRead(BaseModel):
    id: int
    name: str
    identifier: str
    event_id: int
    event_name: str
    participant_count: int
