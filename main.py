import asyncio
import os
import sys
import random
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

def get_random_welcome_sticker():
    stickers = ["CAACAgIAAxkBAAEU3JBpSyNlsQ5lBKzKMxdy-fozh-poNQAC9SwAApB_iElQpWlBK-7ghzYE", "CAACAgQAAxkBAAEU3I5pSyNWNe1Lqe_vR0TBST_B0IPlLwACyAoAAuBWgVDzFIAWz9caRzYE",
                "CAACAgQAAxkBAAEU3IxpSyNTmrSOSE_6RoMJgAcTbdZb-gACLA4AAkergVAfseRQjo3VVDYE", "CAACAgIAAxkBAAEU3IppSyNHFI4CZGGe25hNh2nJpXm5JAACLVYAAlx4QEvGY5AYemj_gzYE",
                "CAACAgIAAxkBAAEU3IhpSyNFBrVBljspGVNwno0UDRAbpAACilQAAs9_SUsS79c03q2WYjYE", "CAACAgIAAxkBAAEU3IJpSyMxeevsecjHx6BlPVFmVpKzxgAClDgAAnwXCUmZu5mTOKoNsDYE",
                "CAACAgIAAxkBAAEU3JJpSyQQVqO9CmVTAsfui3a_FzeT3gACIhEAAuegsUvoorIci0ypVjYE", "CAACAgIAAxkBAAEU3JRpSyQj4oBz74v0u8cpieMS7kQinAACBxQAAjq8GUnb-7dSZcigwzYE",
                "CAACAgIAAxkBAAEU3JhpSyQ0phMVJpu0mxthvtJCERWrewACNhQAAjKsAUh2R0xw5X8U1zYE", "CAACAgIAAxkBAAEU3JxpSyRNdrLM6Uicz65D_U_SO3_tdAAC82oAAm7OGEjI0Xnb43CjkDYE",
                "CAACAgIAAxkBAAEU3J5pSyRgSLOJjyg7wYrXEaH7Y64VEgACM2cAAqj7GEgS9kty0z-3FjYE", "CAACAgIAAxkBAAEU3KBpSySFxmsPlZSLCCR4mvSR6WTX_QACuygAAitGsEnkViOfu2Bo5DYE",
                "CAACAgIAAxkBAAEU3KJpSyS2KOLvcLKXgU2juiPRX-T1cQACyG0AAkYUUUtq-y81tn33uDYE", "CAACAgIAAxkBAAEU3KRpSyS9pSm54HS4S9BDqT4w2HcMygACTWgAAuj48Et3--gt0X1TZDYE"]
    return random.choice(stickers)

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
    
    await message.answer_sticker(get_random_welcome_sticker())
    await message.answer(
        "👋 Привет! Добро пожаловать в официального бота @loltrains",
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