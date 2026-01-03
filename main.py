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
from handlers.user import user_router, get_main_menu_keyboard
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
                "CAACAgIAAxkBAAEU3KJpSyS2KOLvcLKXgU2juiPRX-T1cQACyG0AAkYUUUtq-y81tn33uDYE", "CAACAgIAAxkBAAEU3KRpSyS9pSm54HS4S9BDqT4w2HcMygACTWgAAuj48Et3--gt0X1TZDYE",
                "CAACAgIAAxkBAAEVBXBpWHJxXmUvlT35Z1MaTMl__fA4ZwACxmIAAsVdGUjWMyERI450IjgE", "CAACAgIAAxkBAAEVBXJpWHKLjM7SqWARKnVTHZQHROye5AACRmQAAlAkGEjNoMIU94wyaTgE",
                "CAACAgIAAxkBAAEVBXRpWHKWOvODYD2iTkYUehB0Gu1ENgACLG4AAij8GUiXdU8L1wZYIzgE", "CAACAgIAAxkBAAEVBXZpWHK3p6Ou_7O_Mntx8so2h6fKrgAC_mIAAv23GUjBksOXxQUe6DgE",
                "CAACAgIAAxkBAAEVBXhpWHK6Fn4nTjjA0uBC4eyvyECKqQAChGAAAlzQIEiScgeIRG1L1DgE", "CAACAgIAAxkBAAEVBXppWHK_SFD2RZ-vQA9wrPyuIlhldwACGKUAAtwq2EhoYqTclqsIIjgE",
                "CAACAgIAAxkBAAEVBXxpWHLBdlLRNQU7LQRNk-yXFutkpAAC-IUAAuSHyUg8PtLQYgHv_TgE", "CAACAgIAAxkBAAEVBX5pWHLC3k_mAjJeVrwzVT7zjX16TAACo4EAAv2MyEiZEerDzlPqOzgE",
                "CAACAgIAAxkBAAEVBYBpWHLFB2juIPGUaBQLqRG8jKtTmgAC_40AAtJiyUi6ofd1ansWZDgE", "CAACAgIAAxkBAAEVBYJpWHLpOaQhV5YDDC4Z25WlyCY9YgACi3AAAlHKQEj9xzyZ3VM-ZTgE",
                "CAACAgIAAxkBAAEVBYRpWHLs9CZZMT1I_wRMc-94GnNN_gAC3nsAAgtfQEjFIi3QMNqi_jgE", "CAACAgIAAxkBAAEVBYZpWHL-ah-RNLzABr9qWg8C7hzZAwACAnEAAu2DQEmneB_mCebHtjgE",
                "CAACAgIAAxkBAAEVBYhpWHMQBkJ6tEXgdLRK2J9D4wkHgAACiIIAAtAFuEj9lQjOMU2kMzgE", "CAACAgIAAxkBAAEVBYxpWHOTTPeZqK7z0tb4z9lvWly6hQACcIQAAnvcMEkdaL3W9uhtxzgE",
                "CAACAgIAAxkBAAEVBY5pWHOgH77oG4eKD_wInYRdCZA5-AACjHkAArEl4EuQXQlTx7fZezgE", "CAACAgIAAxkBAAEVBZBpWHOkU26pwlLnQfge1KyKjCV-XQACqkAAAiBkAUnF8lHqmyrbDDgE",
                "CAACAgIAAxkBAAEVBZJpWHOq2j0lVOl8gHrW4ClI3kAOYgACJzgAAlIHAUmcR_JTVc049DgE", "CAACAgIAAxkBAAEVBZRpWHOz0y_n20mYiOi_OPuhukC4DwACkzwAAp8JAUklB6AQwctbxzgE",
                "CAACAgIAAxkBAAEVBZZpWHO94sm91ZWtbhOhpE9qWAgZ0QACITsAAu6vAUlre-8kSRxasTgE", "CAACAgIAAxkBAAEVBZhpWHPEDIWzcnNZfF6rd0Zy9WWvxgACVjoAAqegCUn-pfGXt2hMUjgE",
                "CAACAgIAAxkBAAEVBZppWHPMUhEepsyoEdSreDBD6_TV2wACVRAAAgOT8EsIH-5Vo2ax3TgE", "CAACAgIAAxkBAAEVBZxpWHPnBMKByvUfbQn-YCb7xBY7BQACxHUAAn5QgEnyiZpzbT59qDgE",
                "CAACAgIAAxkBAAEVBZ5pWHPv_pH0Dv1HwKvg4f6ci-Vl7AACilQAAs9_SUsS79c03q2WYjgE", "CAACAgIAAxkBAAEVBaBpWHPwOLCHoX1tiXoyTHl_KXJ4qwACn1oAAnnWSUt8PHuDP4p8XDgE",
                "CAACAgIAAxkBAAEVBaJpWHPzvX9D1G3FrM5pHlgNzA4TlAACzGQAAoqGSEsyiwv4VG080DgE", "CAACAgQAAxkBAAEVBaRpWHP8j4j2jHS01VYOmf-RZlQnmgACBgsAAr1ogFA_Adgz7FCdITgE",
                "CAACAgQAAxkBAAEVBaZpWHQDuLMV8K24vmsEq7wlHJe7eAACJQ4AAu8UgVAmq_On_q0OtjgE", "CAACAgQAAxkBAAEVBahpWHTtPiCsstaSHpW9R2G44pVrsgAC6Q4AAi9zgVD8h8-x0TWv9jgE",
                "CAACAgQAAxkBAAEVBappWHT0knTacERubYPzJQpCKTtnsAACfQ0AArRRIFKwduCPnzlXIjgE", "CAACAgIAAxkBAAEVBaxpWHUDO37owpWgVXXqJC17I992HAAC9SwAApB_iElQpWlBK-7ghzgE",
                "CAACAgIAAxkBAAEVBa5pWHUKet5GLQxO88xgosEUewXj5QACzFIAAodpyUuEBcyHYVExMzgE", "CAACAgIAAxkBAAEVBbBpWHU3YnkhHIMymTXMlFuQSK1vBwACJlkAAiIayEtlDxBUFynt7jgE",
                "CAACAgIAAxkBAAEVBbJpWHU6ybcHTTmmPgW8F2fuCRBrngACXVkAAkaByUsV7JhzUZ96qzgE", "CAACAgIAAxkBAAEVBbRpWHVAQDNlcszxSWgzcB2VWT_L0QACE1kAAsTAyUsjKvVfk9QaLzgE",
                "CAACAgIAAxkBAAEVBbZpWHVN_Q8uuTgAAWGzypAl9Yiw3g0AAopWAAJmichLDUJJouPDN1A4BA", "CAACAgIAAxkBAAEVBbhpWHVxUvJCqvbRBhkc30Z7RrqeVQAC_VgAAsN02ElhbtWYRU_zCzgE",
                "CAACAgIAAxkBAAEVBbppWHV5TZ_D7Em9eBxVIqlPWXeR6gACUyUAApMwYEtUzjQuRkCnZjgE", "CAACAgIAAxkBAAEVBbxpWHV8Gswoi_v8_I-EfKxcJe1YHwACoyYAAqZEYEvnmVJpDHZwGzgE",
                "CAACAgIAAxkBAAEVBb5pWHWEl335fEhlQpS1fVnqUEO6_QACkzwAAuPLyUrYx4gaL0RYDzgE", "CAACAgIAAxkBAAEVBcBpWHWEUhO2RwqWLSklzwWSVCTgPgAChEcAAj4E4EjkDYerlQvIJjgE",
                "CAACAgIAAxkBAAEVBcJpWHWG6P1uFs6uddoqfyQCMLVaGQAC1yMAAroqwEn5hTRDTEnWvjgE", "CAACAgIAAxkBAAEVBcRpWHWKq5vAu60inigrB59te2Sy1QACaxsAAh5daEs-Fz0zds-_9jgE",
                "CAACAgIAAxkBAAEVBcZpWHWVQOxXyOSy5--WnH5BQ9Ze6AACzCAAAj4HYUt7ZTXZWwU0lDgE", "CAACAgIAAxkBAAEVBchpWHWdvw83S-saEjmUAbN8BkEOpAACIiIAApfZIUhQxfUZvjllyjgE",
                "CAACAgIAAxkBAAEVBcppWHXJ3_yCLILyGph3YJuQEC7bjwACCwADfHRwGtuHTtDDjonMOAQ", "CAACAgIAAxkBAAEVBcxpWHXKPQ9wVFeFd75wXPla45eyKAACCgADfHRwGutTO8gctDUfOAQ",
                "CAACAgIAAxkBAAEVBc5pWHXezrVuyWwlP2ZjjddvxtMGZwACdEkAAg4cKUleBT4mUPYV6zgE", "CAACAgIAAxkBAAEVBdBpWHXiatH7MHDLGq8ZZ_Nmz3ewHQACYUUAAr5RKUmaBC6anDWQCDgE",
                "CAACAgIAAxkBAAEVBdJpWHXx3rhi3uCBga7Xit4Tek6DkAAC5zQAAlM1AUhOgP-jCFtzajgE", "CAACAgIAAxkBAAEVBdRpWHXzaziCcIubLCLc3OyXCmwCQQACtyYAAhLOAAFI7bPdqVNfTQc4BA",
                "CAACAgIAAxkBAAEVBdZpWHX8nw2svEfWp-rqdW7zK3owTQAC4SoAAvWvAUidBVC6yfdDzzgE", "CAACAgIAAxkBAAEVBdhpWHX9BbbU8QOx5wFl4_TPeHnZywACFjEAApBLAAFIWhJYq1YsAAHWOAQ",
                "CAACAgIAAxkBAAEVBdppWHYDM_6KG5G-lz46accgBuH0jQACnyUAAgaYAAFIyBSKYos5PHI4BA", "CAACAgIAAxkBAAEVBdxpWHZbO6UxR1mS-wrQfb3bw1axygAC1mQAApiEOUg0CC7fRjf6CTgE",
                "CAACAgIAAxkBAAEVBd5pWHZsHlbvGI0Fl9ArjF42LDfThAACFRUAAq31SUtDOJ2N5jWYAAE4BA", "CAACAgIAAxkBAAEVBeBpWHZyypebZcBHQCfHlmeOFj25ZwACli0AAmCJqEvPCXwAAZUjs084BA",
                "CAACAgIAAxkBAAEVBeJpWHZ2PKJWsBBO0MB9t3jXbimbAgACfBUAAr-jMUkYBotdJLW7VDgE", "CAACAgIAAxkBAAEVBeRpWHZ-Jjxhb7C5HsSXsxWw7k3dAgACwVEAAmaogElrNTvLup9BPzgE",
                "CAACAgIAAxkBAAEVBeZpWHaEEFSiLPrL9QABZXJPSj0-3d8AAsk3AAJG0kFIAQnbMplf_9g4BA", "CAACAgIAAxkBAAEVBehpWHaQxV5xA26FQ5r1par3M44jcAAC8QsAAty-sUsnZBn3z65Z3TgE",
                "CAACAgIAAxkBAAEVBeppWHapWvPQJcjEQgPD7kiyqaZ0YwACMRAAAoKaeUvhKcGIWesLGTgE", "CAACAgIAAxkBAAEVBexpWHb1i7bFnpVcntI0hhY9bu6jOQACqhUAAvmmwUiKwP5nihcQ5jgE",
                "CAACAgIAAxkBAAEVBe5pWHb-HfDvI-KHsrFGKYIkREXcVQACcBcAAtkKKEuibvvJ2SXMJzgE", "CAACAgIAAxkBAAEVBfBpWHb_Ap7Wokve6RlAkLLQMntQxQACaxUAAlS5KEuf9ko0wOhGjzgE",
                "CAACAgIAAxkBAAEVBfJpWHcE6EomBybNN3bY265FD7e3QwACPi0AAmQ9WEmJQedCOW79qDgE", "CAACAgIAAxkBAAEU_rxpVVucgIu50O_vHv5VXbGoHFK-vwACzHwAAmsaqEqkBokrCKdbdTgE",
                "CAACAgIAAxkBAAEVBfZpWHcwKRi08kg_MmyB2gkXoWBYIQACixgAAoEEGEtXM-qXfb71iDgE", "CAACAgQAAxkBAAEVBfhpWHc_sGmEMaAj7-MNO4WWZWAnbQAC3A0AAgE76VGe-MaNqWj0pTgE",
                "CAACAgIAAxkBAAEVBfppWHdMf4Lzzc6_ozZyYrzADjG_GQACKEgAAqF6mUjurV8b65qUnDgE", "CAACAgIAAxkBAAEU_XBpVNRRK-8HH-46E5x2m70YC5ugAQACWwwAAl9cMUpdk39XaJ8KbjgE",
                "CAACAgIAAxkBAAEVBf5pWHdYuJS80lVpIDie9ejCZRh05wACQBUAAsvQKEhYAvM4TJrDvzgE", "CAACAgIAAxkBAAEVBgABaVh47c5XPAdRHGAcXMoasTT0vSYAAg5nAAKLTBlIV2S74tS6y084BA"]
    print(len(stickers))
    return random.choice(stickers)

@dp.message(CommandStart())
async def start(message: Message):
    await add_user(message)
    
    # ! ВАЖНО: Раскомментируйте строчку ниже один раз, вставьте свой ID, запустите бота, 
    # нажмите /start, чтобы стать админом. Потом закомментируйте обратно.
    # await set_admin(message.from_user.id) 

    keyboard = await get_main_menu_keyboard(message.from_user.id)
    
    await message.answer_sticker(get_random_welcome_sticker())
    await message.answer(
        "👋 Привет! Добро пожаловать в официального бота @loltrains",
        reply_markup=keyboard.as_markup()
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