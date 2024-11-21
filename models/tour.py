from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, Table, LargeBinary, ARRAY
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Tour(Base):
    __tablename__ = "tours"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    part = Column(String, nullable=False)
    theme = Column(String)

    # Foreign keys to other entities
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=True)
    crew_id = Column(Integer, ForeignKey("crews.id"), nullable=True)

    # Relationships
    template = relationship("Template", back_populates="tours")
    sport = relationship("Sport", back_populates="tours")
    crew = relationship("Crew", back_populates="tours")
