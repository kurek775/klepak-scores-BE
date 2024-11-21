from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, Table, LargeBinary, ARRAY
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()
class Crew(Base):
    __tablename__ = "crews"

    id = Column(Integer, primary_key=True)
    leaders = Column(ARRAY(String), nullable=True)
    number = Column(Integer, nullable=False)
    password = Column(String)

    # Relationships
    members = relationship("Person", back_populates="crew")
    tours = relationship("Tour", back_populates="crew")
