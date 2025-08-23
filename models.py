from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    LargeBinary,
    Float,
    ForeignKey,
    Table,
    UniqueConstraint,
    ForeignKeyConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# --- Association table: users ↔ crews (leaders) ---
crew_leaders = Table(
    "crew_leaders",
    Base.metadata,
    Column("crew_id", ForeignKey("crews.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    sub: Mapped[int]= mapped_column(Text)
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String)
    picture_url: Mapped[Optional[str]] = mapped_column(Text)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # crews where this user is leader
    leads_crews: Mapped[List["Crew"]] = relationship(
        secondary=crew_leaders,
        back_populates="leaders",
        lazy="selectin",
    )


class Crew(Base):
    __tablename__ = "crews"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[Optional[int]] = mapped_column(Integer)

    # leaders (users) via association
    leaders: Mapped[List[User]] = relationship(
        secondary=crew_leaders,
        back_populates="leads_crews",
        lazy="selectin",
    )

    # persons belonging to this crew
    persons: Mapped[List["Person"]] = relationship(
        back_populates="crew",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String)
    crew_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("crews.id", ondelete="SET NULL")
    )

    crew: Mapped[Optional[Crew]] = relationship(back_populates="persons", lazy="joined")

    results: Mapped[List["Result"]] = relationship(
        back_populates="person",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Sport(Base):
    __tablename__ = "sports"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    metric: Mapped[Optional[str]] = mapped_column(String)

    tour_links: Mapped[List["TourSport"]] = relationship(
        back_populates="sport",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    bg_image: Mapped[Optional[bytes]] = mapped_column("bgImage", LargeBinary)
    font: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    text_position: Mapped[Optional[str]] = mapped_column("textPosition", String)

    tours: Mapped[List["Tour"]] = relationship(
        back_populates="template", lazy="selectin"
    )


class Tour(Base):
    __tablename__ = "tours"

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[Optional[int]] = mapped_column(Integer)
    part: Mapped[Optional[str]] = mapped_column(String)
    theme: Mapped[Optional[str]] = mapped_column(String)
    template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("templates.id", ondelete="SET NULL")
    )

    template: Mapped[Optional[Template]] = relationship(
        back_populates="tours", lazy="joined"
    )

    sports: Mapped[List["TourSport"]] = relationship(
        back_populates="tour",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    results: Mapped[List["Result"]] = relationship(
        back_populates="tour",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class TourSport(Base):
    """
    Association object for the m:n relationship between Tour and Sport.
    PK is composite (tour_id, sport_id).
    """

    __tablename__ = "tour_sports"

    tour_id: Mapped[int] = mapped_column(
        ForeignKey("tours.id", ondelete="CASCADE"), primary_key=True
    )
    sport_id: Mapped[int] = mapped_column(
        ForeignKey("sports.id", ondelete="RESTRICT"), primary_key=True
    )
    position: Mapped[Optional[int]] = mapped_column(Integer)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)

    tour: Mapped[Tour] = relationship(back_populates="sports", lazy="joined")
    sport: Mapped[Sport] = relationship(back_populates="tour_links", lazy="joined")

    results: Mapped[List["Result"]] = relationship(
        back_populates="tour_sport",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


# --- Result model ---
class Result(Base):
    __tablename__ = "results"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tour_id", "sport_id"],
            ["tour_sports.tour_id", "tour_sports.sport_id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "tour_id", "sport_id", "person_id", name="uq_result_tour_sport_person"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # add direct FKs:
    tour_id: Mapped[int] = mapped_column(
        ForeignKey("tours.id", ondelete="CASCADE"), nullable=False
    )
    sport_id: Mapped[int] = mapped_column(
        ForeignKey("sports.id", ondelete="RESTRICT"), nullable=False
    )

    person_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[Optional[float]] = mapped_column(Float)

    tour: Mapped["Tour"] = relationship(back_populates="results", lazy="joined")
    person: Mapped["Person"] = relationship(back_populates="results", lazy="joined")

    # link to the association (still useful)
    tour_sport: Mapped["TourSport"] = relationship(
        back_populates="results",
        primaryjoin="and_(Result.tour_id==TourSport.tour_id, Result.sport_id==TourSport.sport_id)",
        viewonly=True,
        lazy="joined",
    )
