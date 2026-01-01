from aiogram import Router, F
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
    
    builder.button(text="💡 Идея", callback_data="idea")
    builder.button(text="🐛 Баг", callback_data="bug")
    builder.button(text="⭐ Отзыв", callback_data="review")
    builder.button(text="⛔ Жалоба", callback_data="report")
    
    # Добавляем кнопку админки только для админов
    if await is_admin(user_id):
        builder.button(text="🔐 Админ панель", callback_data="open_admin_panel")
    
    builder.adjust(2, 2, 1)  # 2 кнопки в ряд, потом 2, потом 1 (админка)
    return builder


# --- Callbacks меню ---
@user_router.callback_query(F.data.in_({"idea", "bug", "review"}))
async def start_feedback(callback: CallbackQuery, state: FSMContext):
    if await is_blocked(callback.from_user.id):
        return await callback.answer("⛔ Вы заблокированы.", show_alert=True)
        
    await state.update_data(category=callback.data)
    await state.set_state(UserStates.send_feedback)
    
    texts = {
        "idea": "💡 Опишите вашу идею. Вы можете прикрепить фото/видео.",
        "bug": "📝 Опишите найденный баг. Скриншоты приветствуются.",
        "review": "⭐ Напишите ваш отзыв."
    }
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Отмена", callback_data="cancel_action")
    
    await callback.message.answer(texts[callback.data], reply_markup=builder.as_markup())
    await callback.answer()


@user_router.callback_query(F.data == "report")
async def start_report(callback: CallbackQuery, state: FSMContext):
    if await is_blocked(callback.from_user.id):
        return await callback.answer("⛔ Вы заблокированы.", show_alert=True)

    await state.set_state(UserStates.send_report)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Отмена", callback_data="cancel_action")
    
    await callback.message.answer("⛔ Опишите жалобу или перешлите сообщение нарушителя:", reply_markup=builder.as_markup())
    await callback.answer()


@user_router.callback_query(F.data == "open_admin_panel")
async def open_admin_panel(callback: CallbackQuery):
    """Открывает админ-панель: удаляет сообщение и вызывает /admin"""
    if not await is_admin(callback.from_user.id):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)
    
    # Удаляем сообщение с кнопкой
    await callback.message.delete()
    
    # Отправляем команду /admin как текст, которую подхватит твой handler
    await callback.message.answer("/admin")
    await callback.answer()


@user_router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("❌ Действие отменено.")


# --- Обработка контента (Фидбек) ---
@user_router.message(UserStates.send_feedback)
async def process_feedback(message: Message, state: FSMContext):
    data = await state.get_data()
    category = data.get("category")
    
    c_type, text, file_id = get_content_data(message)
    
    await save_feedback(message.from_user.id, category, c_type, text, file_id)
    
    await message.answer("✅ Сообщение принято! Спасибо.")
    await state.clear()


# --- Обработка контента (Жалоба) ---
@user_router.message(UserStates.send_report)
async def process_report(message: Message, state: FSMContext):
    c_type, text, file_id = get_content_data(message)
    
    await save_report(message.from_user.id, c_type, text, file_id)
    
    await message.answer("✅ Жалоба отправлена администрации.")
    await state.clear()