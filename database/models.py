from typing import Optional
from sqlalchemy import BigInteger, String, DateTime, func, Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    admin: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    banned: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    registered_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="user")
    reports: Mapped[list["Report"]] = relationship(back_populates="user")

class Feedback(Base):
    __tablename__ = 'feedback'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Кто?
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped["User"] = relationship(back_populates="feedbacks")

    # Тип: ⭐отзыв | 📝баг | 💡идея
    category: Mapped[str] = mapped_column(String(50)) 

    # Контент
    content_type: Mapped[str] = mapped_column(String(50)) # текст, фото, стикер, аудио, файл, и тп
    text: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Текст или подпись к чему-то
    file_id: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Telegram ID файла
    
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

class Report(Base):
    __tablename__ = 'report'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Кто?
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped["User"] = relationship(back_populates="reports")

    # Контент
    content_type: Mapped[str] = mapped_column(String(50)) # текст, фото, стикер, аудио, файл, и тп
    text: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Описание
    file_id: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Telegram ID файла

    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())