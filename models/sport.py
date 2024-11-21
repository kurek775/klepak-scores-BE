from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, Table, LargeBinary, ARRAY
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Sport(Base):
    __tablename__ = "sports"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    metric = Column(String, nullable=False)

    # Relationships
    results = relationship("Result", back_populates="sport")
    tours = relationship("Tour", back_populates="sport")