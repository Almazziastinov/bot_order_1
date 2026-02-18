from sqlalchemy import BigInteger, String, ForeignKey, DateTime  # Добавлен ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship  # Добавлен relationship
from typing import List  # Добавлен List
from datetime import datetime



class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(BigInteger, unique=True)
    username: Mapped[str] = mapped_column(String(32), nullable=True)
    first_name: Mapped[str] = mapped_column(String(64), nullable=True)
    last_name: Mapped[str] = mapped_column(String(64), nullable=True)

    # Связь с Linktr
    linktrs: Mapped[List["Linktr"]] = relationship(back_populates="user")


class Linktr(Base):
    __tablename__ = 'linktrs'

    id: Mapped[int] = mapped_column(primary_key=True)
    # Добавлен ForeignKey для связи с users.user_id
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.user_id'))
    link: Mapped[str] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Связь с User (исправлено back_populates)
    user: Mapped["User"] = relationship(back_populates="linktrs")
