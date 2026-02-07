from __future__ import annotations

from typing import List, Optional

from sqlalchemy import (
    String,
    ForeignKey,
    Boolean,
    Float,
    Enum as SAEnum,
    func, UniqueConstraint, Date, Enum,
)
from sqlalchemy.dialects.postgresql import JSON, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.model.role import Role


class Base(DeclarativeBase):
    pass





class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, nullable=False
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP, server_default=func.now(), nullable=False
    )
    role: Mapped[Role] = mapped_column(SAEnum(Role), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)




# CROSS

class Cross(Base):
    __tablename__ = "cross"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    datetime_start: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, nullable=False)
    distance: Mapped[float] = mapped_column(Float, nullable=False)
    executed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    runners: Mapped[List[Runner]] = relationship(
        "Runner", secondary="cross_runners", back_populates="crosses"
    )


class Runner(Base):
    __tablename__ = "runners"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    serial_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    running_time: Mapped[float] = mapped_column(Float, nullable=False)

    crosses: Mapped[List[Cross]] = relationship(
        "Cross", secondary="cross_runners", back_populates="runners"
    )


class CrossRunners(Base):
    __tablename__ = "cross_runners"

    cross_id: Mapped[int] = mapped_column(ForeignKey("cross.id"), primary_key=True)
    runner_id: Mapped[int] = mapped_column(ForeignKey("runners.id"), primary_key=True)


class Unit(Base):
    __tablename__ = "units"
    __table_args__ = (
        UniqueConstraint("name", name="uq_units_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    base_location: Mapped[str] = mapped_column(String(150), nullable=False)

    def __repr__(self) -> str:
        return f"Unit(id={self.id}, name='{self.name}', base_location='{self.base_location}')"

    def __str__(self) -> str:
        return f"{self.name} ({self.base_location})"


