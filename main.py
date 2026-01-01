import asyncio
import os
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.requests import async_main, add_user, set_admin, is_admin
from handlers.user import user_router
from handlers.admin import admin_router

load_dotenv()

# Простая проверка токена
TOKEN = os.getenv('bot_token')
if not TOKEN:
    sys.exit("Error: bot_token not found in .env")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Подключаем роутеры
dp.include_router(admin_router)  # Админ роутер первым, чтобы перехватывать команды
dp.include_router(user_router)


@dp.message(CommandStart())
async def start(message: Message):
    await add_user(message)
    
    # ! ВАЖНО: Раскомментируйте строчку ниже один раз, вставьте свой ID, запустите бота, 
    # нажмите /start, чтобы стать админом. Потом закомментируйте обратно.
    # await set_admin(message.from_user.id) 

    builder = InlineKeyboardBuilder()
    
    builder.button(text="🌐 Открыть сайт", url="https://loltrains.ru")
    builder.button(text="💡 Есть идея?", callback_data="idea")
    builder.button(text="📝 Нашли баг?", callback_data="bug")
    builder.button(text="⭐ Отзыв", callback_data="review")
    builder.button(text="⛔ Жалоба", callback_data="report")
    builder.button(text="📰 Наш канал", url="https://t.me/snowlover4ever_ch")
    
    # Проверяем, является ли пользователь админом
    if await is_admin(message.from_user.id):
        builder.button(text="🔐 Админ панель", callback_data="open_admin_panel")
    
    builder.adjust(1, 2, 2, 1, 1)  # Добавил ещё 1 для кнопки админки
    
    await message.answer(
        "📖 Менюшка:",
        reply_markup=builder.as_markup()
    )


async def main():
    await async_main()  # Инит БД
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    print("Bot started!")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")