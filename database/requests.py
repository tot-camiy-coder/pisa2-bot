import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload
from database.models import Base, User, Feedback, Report
from aiogram.types import Message

if not os.path.exists('data'):
    os.makedirs('data')

engine = create_async_engine(url='sqlite+aiosqlite:///data/storage.db')
async_session = async_sessionmaker(engine)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- Пользователи ---
async def add_user(message: Message):
    tg_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        
        if not user:
            session.add(User(telegram_id=tg_id, username=username, full_name=full_name))
            await session.commit()
        else:
            if user.username != username or user.full_name != full_name:
                user.username = username
                user.full_name = full_name
                await session.commit()

async def set_admin(tg_id: int):
    """Временная функция чтобы выдать админку вручную или через код"""
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if user:
            user.admin = True
            await session.commit()

async def is_admin(tg_id: int) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        return user.admin if user else False

async def get_users_paginated(page: int = 1, limit: int = 10, only_banned: bool = False):
    offset = (page - 1) * limit
    async with async_session() as session:
        stmt = select(User)
        if only_banned:
            stmt = stmt.where(User.banned == True)
        
        # Получаем общее кол-во для подсчета страниц
        count_stmt = select(func.count()).select_from(User)
        if only_banned:
            count_stmt = count_stmt.where(User.banned == True)
        total = await session.scalar(count_stmt)

        result = await session.scalars(stmt.offset(offset).limit(limit).order_by(desc(User.registered_at)))
        return result.all(), total

# --- Блокировка ---
async def toggle_ban_status(tg_id: int, status: bool):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if user:
            user.banned = status
            await session.commit()
            return True
        return False

async def is_blocked(tg_id: int) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        return user.banned if user else False

# --- Фидбек и Репорты ---
async def save_feedback(tg_id: int, category: str, content_type: str, text: str = None, file_id: str = None):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if user:
            session.add(Feedback(
                user_id=user.id,
                category=category,
                content_type=content_type,
                text=text,
                file_id=file_id
            ))
            await session.commit()

async def save_report(tg_id: int, content_type: str, text: str = None, file_id: str = None):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if user:
            session.add(Report(
                user_id=user.id,
                content_type=content_type,
                text=text,
                file_id=file_id
            ))
            await session.commit()

async def get_items_paginated(item_type: str, page: int = 1, limit: int = 10):
    """Универсальная функция для получения фидбека или репортов"""
    offset = (page - 1) * limit
    Model = Feedback if item_type == 'feedback' else Report
    
    async with async_session() as session:
        # Получаем данные вместе с пользователем (joinedload)
        stmt = select(Model).options(joinedload(Model.user)).order_by(desc(Model.created_at)).offset(offset).limit(limit)
        result = await session.scalars(stmt)
        
        # Считаем общее кол-во
        total = await session.scalar(select(func.count()).select_from(Model))
        
        return result.all(), total

async def get_item_by_id(item_type: str, item_id: int):
    Model = Feedback if item_type == 'feedback' else Report
    async with async_session() as session:
        stmt = select(Model).options(joinedload(Model.user)).where(Model.id == item_id)
        return await session.scalar(stmt)
    
async def get_user_by_telegram_id(telegram_id: int):
    """Получает пользователя по telegram_id"""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()