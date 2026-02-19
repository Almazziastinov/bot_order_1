from sqlalchemy import BigInteger, String, ForeignKey, DateTime, Boolean  # Добавлен ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship  # Добавлен relationship
from typing import List, Optional
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

class ButtonLink(Base):
    __tablename__ = 'button_links'

    id: Mapped[int] = mapped_column(primary_key=True)
    button_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # Например: 'support', 'contest'
    button_text: Mapped[str] = mapped_column(String(100), nullable=False)  # Текст кнопки
    url: Mapped[str] = mapped_column(String(500), nullable=False)  # URL ссылки
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # Описание для админа
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # Активна ли кнопка
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # ID админа, который последний раз менял
