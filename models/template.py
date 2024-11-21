from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, Table, LargeBinary, ARRAY
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True)
    bgImage = Column(LargeBinary)
    font = Column(LargeBinary)
    textPosition = Column(String)

    # Relationships
    tours = relationship("Tour", back_populates="template")
