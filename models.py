# models.py  (patched)
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    LargeBinary,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    UniqueConstraint,
    CheckConstraint,
    and_,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    foreign,
)  # <-- add foreign


class Base(DeclarativeBase):
    pass


class Template(Base):
    __tablename__ = "templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    bg_image: Mapped[Optional[bytes]] = mapped_column("bgImage", LargeBinary)
    font: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    text_position: Mapped[Optional[str]] = mapped_column("textPosition", String)

    tours: Mapped[List["Tour"]] = relationship(
        back_populates="template", lazy="selectin"
    )


# models.py (Tour)
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

    crews: Mapped[List["Crew"]] = relationship(
        back_populates="tour", lazy="selectin", cascade="all, delete-orphan"
    )
    users: Mapped[List["User"]] = relationship(
        back_populates="tour", foreign_keys="[User.tour_id]", lazy="selectin"
    )

    # IMPORTANT: this must exist and be named exactly "sports"
    sports: Mapped[List["TourSport"]] = relationship(
        back_populates="tour", lazy="selectin", cascade="all, delete-orphan"
    )

    # view-only convenience (no direct FK in DB)
    results: Mapped[List["Result"]] = relationship(
        primaryjoin=lambda: Tour.id == foreign(Result.tour_id),
        viewonly=True,
        lazy="selectin",
    )


class Crew(Base):
    __tablename__ = "crews"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[Optional[int]] = mapped_column(Integer)
    tour_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tours.id", ondelete="SET NULL", onupdate="CASCADE")
    )

    tour: Mapped[Optional[Tour]] = relationship(
        back_populates="crews", lazy="joined", foreign_keys=[tour_id]
    )

    users: Mapped[List["User"]] = relationship(
        back_populates="crew",
        primaryjoin=lambda: and_(User.crew_id == Crew.id, User.tour_id == Crew.tour_id),
        foreign_keys="[User.crew_id, User.tour_id]",
        lazy="selectin",
    )

    persons: Mapped[List["Person"]] = relationship(
        back_populates="crew", lazy="selectin", cascade="all, delete-orphan"
    )


# models.py (User)
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    sub: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String)
    picture_url: Mapped[Optional[str]] = mapped_column(Text)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    tour_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tours.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True
    )
    # 🔧 was "ForeKey" before — must be ForeignKey
    crew_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("crews.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["tour_id", "crew_id"],
            ["crews.tour_id", "crews.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="fk_users_crew_in_tour",
        ),
        CheckConstraint(
            "crew_id IS NULL OR tour_id IS NOT NULL",
            name="chk_users_crew_requires_tour",
        ),
    )

    tour: Mapped[Optional["Tour"]] = relationship(
        back_populates="users", foreign_keys=[tour_id], lazy="joined"
    )
    crew: Mapped[Optional["Crew"]] = relationship(
        back_populates="users",
        primaryjoin=lambda: and_(User.crew_id == Crew.id, User.tour_id == Crew.tour_id),
        foreign_keys=[crew_id, tour_id],
        lazy="joined",
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
        back_populates="person", lazy="selectin", cascade="all, delete-orphan"
    )


# models.py (Sport)
class Sport(Base):
    __tablename__ = "sports"
    __table_args__ = (UniqueConstraint("name", name="uq_sports_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    metric: Mapped[Optional[str]] = mapped_column(String)

    # must be named "tour_links" to match TourSport.sport.back_populates="tour_links"
    tour_links: Mapped[List["TourSport"]] = relationship(
        back_populates="sport", lazy="selectin", cascade="all, delete-orphan"
    )

    results: Mapped[List["Result"]] = relationship(
        primaryjoin=lambda: Sport.id == foreign(Result.sport_id),
        viewonly=True,
        lazy="selectin",
    )


# models.py (TourSport)
class TourSport(Base):
    __tablename__ = "tour_sports"

    tour_id: Mapped[int] = mapped_column(
        ForeignKey("tours.id", ondelete="CASCADE"), primary_key=True
    )
    sport_id: Mapped[int] = mapped_column(
        ForeignKey("sports.id", ondelete="RESTRICT"), primary_key=True
    )
    position: Mapped[Optional[int]] = mapped_column(Integer)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)

    # must match the name above on Tour
    tour: Mapped["Tour"] = relationship(back_populates="sports", lazy="joined")
    # and this must match Sport.tour_links (below)
    sport: Mapped["Sport"] = relationship(back_populates="tour_links", lazy="joined")

    results: Mapped[List["Result"]] = relationship(
        back_populates="tour_sport", lazy="selectin", cascade="all, delete-orphan"
    )


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
    # NOTE: these two are part of the composite FK to tour_sports, not direct FKs to tours/sports
    tour_id: Mapped[int] = mapped_column(Integer, nullable=False)
    sport_id: Mapped[int] = mapped_column(Integer, nullable=False)

    person_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[Optional[float]] = mapped_column(Float)

    person: Mapped["Person"] = relationship(back_populates="results", lazy="joined")

    # real FK target via the composite FK above
    tour_sport: Mapped["TourSport"] = relationship(
        back_populates="results",
        primaryjoin=lambda: and_(
            Result.tour_id == TourSport.tour_id, Result.sport_id == TourSport.sport_id
        ),
        lazy="joined",
    )

    # View-only conveniences (no direct FK in DB → annotate foreign())
    tour: Mapped["Tour"] = relationship(
        primaryjoin=lambda: foreign(Result.tour_id) == Tour.id,
        viewonly=True,
        lazy="joined",
    )
    sport: Mapped["Sport"] = relationship(
        primaryjoin=lambda: foreign(Result.sport_id) == Sport.id,
        viewonly=True,
        lazy="joined",
    )
