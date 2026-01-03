from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.requests import save_feedback, save_report, add_user, is_blocked, is_admin
from utils.states import UserStates

user_router = Router()


# Вспомогательная функция для парсинга контента
def get_content_data(message: Message):
    text = message.text or message.caption
    file_id = None
    content_type = 'text'

    if message.photo:
        file_id = message.photo[-1].file_id
        content_type = 'photo'
    elif message.video:
        file_id = message.video.file_id
        content_type = 'video'
    elif message.audio:
        file_id = message.audio.file_id
        content_type = 'audio'
    elif message.voice:
        file_id = message.voice.file_id
        content_type = 'voice'
    elif message.document:
        file_id = message.document.file_id
        content_type = 'document'
    elif message.sticker:
        file_id = message.sticker.file_id
        content_type = 'sticker'
    elif message.video_note:
        file_id = message.video_note.file_id
        content_type = 'video_note'
    
    return content_type, text, file_id


# --- Функция для генерации главного меню ---
async def get_main_menu_keyboard(user_id: int) -> InlineKeyboardBuilder:
    """Генерирует клавиатуру главного меню с учётом прав пользователя"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🌐 Открыть сайт", url="https://loltrains.ru")
    builder.button(text="💡 Есть идея?", callback_data="idea")
    builder.button(text="📝 Нашли баг?", callback_data="bug")
    builder.button(text="⭐ Отзыв", callback_data="review")
    builder.button(text="⛔ Жалоба", callback_data="report")
    builder.button(text="📰 Наш канал", url="https://t.me/snowlover4ever_ch")
    
    if await is_admin(user_id):
        builder.button(text="🔐 Админ панель", callback_data="open_admin_panel")
        builder.adjust(1, 2, 2, 1, 1)
    else:
        builder.adjust(1, 2, 2, 1)
    
    return builder


# --- Callbacks меню ---
@user_router.callback_query(F.data.in_({"idea", "bug", "review"}))
async def start_feedback(callback: CallbackQuery, state: FSMContext):
    if await is_blocked(callback.from_user.id):
        return await callback.answer("⛔ Вы заблокированы.", show_alert=True)
    
    texts = {
        "idea": "💡 Опишите вашу идею. Вы можете прикрепить фото/видео.",
        "bug": "📝 Опишите найденный баг. Скриншоты приветствуются.",
        "review": "⭐ Напишите ваш отзыв."
    }
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Отмена", callback_data="cancel_action")
    
    # Редактируем текущее сообщение
    await callback.message.edit_text(texts[callback.data], reply_markup=builder.as_markup())
    
    # Сохраняем категорию и ID сообщения бота
    await state.update_data(
        category=callback.data,
        bot_message_id=callback.message.message_id
    )
    await state.set_state(UserStates.send_feedback)
    await callback.answer()


@user_router.callback_query(F.data == "report")
async def start_report(callback: CallbackQuery, state: FSMContext):
    if await is_blocked(callback.from_user.id):
        return await callback.answer("⛔ Вы заблокированы.", show_alert=True)

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Отмена", callback_data="cancel_action")
    
    # Редактируем текущее сообщение
    await callback.message.edit_text(
        "⛔ Опишите жалобу или перешлите сообщение нарушителя:",
        reply_markup=builder.as_markup()
    )
    
    # Сохраняем ID сообщения бота
    await state.update_data(bot_message_id=callback.message.message_id)
    await state.set_state(UserStates.send_report)
    await callback.answer()


@user_router.callback_query(F.data == "open_admin_panel")
async def open_admin_panel(callback: CallbackQuery):
    """Открывает админ-панель"""
    if not await is_admin(callback.from_user.id):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)
    
    await callback.message.delete()
    await callback.message.answer("/admin")
    await callback.answer()


@user_router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    # Возвращаем главное меню вместо просто текста
    keyboard = await get_main_menu_keyboard(callback.from_user.id)
    await callback.message.edit_text(
        "❌ Действие отменено.\n\n🏠 Главное меню:",
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()


# --- Обработка контента (Фидбек) ---
@user_router.message(UserStates.send_feedback)
async def process_feedback(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    category = data.get("category")
    bot_message_id = data.get("bot_message_id")
    
    c_type, text, file_id = get_content_data(message)
    
    await save_feedback(message.from_user.id, category, c_type, text, file_id)
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except Exception:
        pass
    
    # Редактируем сообщение бота с возвратом в меню
    keyboard = await get_main_menu_keyboard(message.from_user.id)
    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="✅ Сообщение принято! Спасибо.\n\n🏠 Главное меню:",
            reply_markup=keyboard.as_markup()
        )
    except Exception:
        await message.answer(
            "✅ Сообщение принято! Спасибо.\n\n🏠 Главное меню:",
            reply_markup=keyboard.as_markup()
        )
    
    await state.clear()


# --- Обработка контента (Жалоба) ---
@user_router.message(UserStates.send_report)
async def process_report(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    bot_message_id = data.get("bot_message_id")
    
    c_type, text, file_id = get_content_data(message)
    
    await save_report(message.from_user.id, c_type, text, file_id)
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except Exception:
        pass
    
    # Редактируем сообщение бота с возвратом в меню
    keyboard = await get_main_menu_keyboard(message.from_user.id)
    try:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_message_id,
            text="✅ Жалоба отправлена администрации.\n\n🏠 Главное меню:",
            reply_markup=keyboard.as_markup()
        )
    except Exception:
        await message.answer(
            "✅ Жалоба отправлена администрации.\n\n🏠 Главное меню:",
            reply_markup=keyboard.as_markup()
        )
    
    await state.clear()