from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, Table, LargeBinary, ARRAY
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    crew_id = Column(Integer, ForeignKey("crews.id"), nullable=True)
    category = Column(String)

    # Relationships
    crew = relationship("Crew", back_populates="members")
    results = relationship("Result", back_populates="person")