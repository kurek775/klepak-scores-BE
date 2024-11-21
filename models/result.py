from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, Table, LargeBinary, ARRAY
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True)
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=False)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    score = Column(Float)

    # Relationships
    sport = relationship("Sport", back_populates="results")
    person = relationship("Person", back_populates="results")