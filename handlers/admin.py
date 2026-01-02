import math
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.requests import (
    is_admin, get_items_paginated, get_item_by_id, 
    get_users_paginated, toggle_ban_status, get_user_by_telegram_id
)
from utils.states import AdminStates

admin_router = Router()

ITEMS_PER_PAGE = 5


# === HELPER ФУНКЦИИ ===
async def cleanup_extra_messages(state: FSMContext, bot: Bot, chat_id: int):
    """Удаляет сохраненные в состоянии сообщения (например, стикеры, аватарки)"""
    data = await state.get_data()
    extra_msg_ids = data.get("extra_msg_ids", [])
    
    for msg_id in extra_msg_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass
    
    # Старый формат для совместимости
    extra_msg_id = data.get("extra_msg_id")
    if extra_msg_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=extra_msg_id)
        except Exception:
            pass
    
    await state.update_data(extra_msg_id=None, extra_msg_ids=[])


async def safe_edit_or_send(callback: CallbackQuery, text: str, reply_markup=None, parse_mode="HTML"):
    """Редактирует текст или удаляет медиа и отправляет новое сообщение"""
    if callback.message.text:
        try:
            await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
    else:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)


async def get_user_profile_info(bot: Bot, telegram_id: int) -> dict:
    """Получает информацию о пользователе из Telegram API"""
    try:
        chat = await bot.get_chat(telegram_id)
        photos = await bot.get_user_profile_photos(telegram_id, limit=1)
        
        return {
            "id": chat.id,
            "first_name": chat.first_name or "",
            "last_name": chat.last_name or "",
            "username": chat.username,
            "bio": chat.bio,
            "photo": photos.photos[0][-1] if photos.photos else None,  # Самое большое фото
            "has_private_forwards": getattr(chat, 'has_private_forwards', False),
        }
    except Exception as e:
        return {"error": str(e)}


# === ГЛАВНОЕ МЕНЮ (ИЗМЕНЕНО) ===
# Теперь ловим Callback, а не команду /admin
@admin_router.callback_query(F.data == "open_admin_panel")
async def admin_panel(callback: CallbackQuery, state: FSMContext, bot: Bot):
    # Проверяем права по ID того, кто нажал кнопку
    if not await is_admin(callback.from_user.id):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)
    
    # Чистим старые сообщения
    await cleanup_extra_messages(state, bot, callback.message.chat.id)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📩 Фидбек", callback_data="menu_feedback_1")
    kb.button(text="⛔ Жалобы", callback_data="menu_report_1")
    kb.button(text="👥 Пользователи", callback_data="menu_users_1")
    kb.button(text="☠ Бан-лист", callback_data="menu_banned_1")
    # Можно добавить кнопку закрытия админки
    kb.button(text="❌ Закрыть", callback_data="close_admin") 
    kb.adjust(2, 2, 1)
    
    # Используем edit_text через safe helper
    await safe_edit_or_send(callback, "👮‍♂️ <b>Панель администратора</b>", reply_markup=kb.as_markup())
    await callback.answer()


# Добавил хендлер для закрытия админки (удаляет сообщение)
@admin_router.callback_query(F.data == "close_admin")
async def close_admin(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await cleanup_extra_messages(state, bot, callback.message.chat.id)
    await state.clear()
    await callback.message.delete()
    await callback.answer("Админ-панель закрыта")


@admin_router.callback_query(F.data == "home")
async def go_home(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await cleanup_extra_messages(state, bot, callback.message.chat.id)
    await state.clear()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📩 Фидбек", callback_data="menu_feedback_1")
    kb.button(text="⛔ Жалобы", callback_data="menu_report_1")
    kb.button(text="👥 Пользователи", callback_data="menu_users_1")
    kb.button(text="☠ Бан-лист", callback_data="menu_banned_1")
    kb.button(text="❌ Закрыть", callback_data="close_admin")
    kb.adjust(2, 2, 1)
    
    await safe_edit_or_send(callback, "👮‍♂️ <b>Панель администратора</b>", reply_markup=kb.as_markup())


# === СПИСКИ ФИДБЕКА И ЖАЛОБ ===
@admin_router.callback_query(F.data.startswith("menu_feedback_") | F.data.startswith("menu_report_"))
async def list_items(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await cleanup_extra_messages(state, bot, callback.message.chat.id)

    parts = callback.data.split("_")
    item_type = parts[1]
    page = int(parts[2])
    
    items, total = await get_items_paginated(item_type, page, ITEMS_PER_PAGE)
    total_pages = max(1, math.ceil(total / ITEMS_PER_PAGE))
    
    if not items:
        kb = InlineKeyboardBuilder()
        kb.button(text="🔙 Назад", callback_data="home")
        return await safe_edit_or_send(callback, "📭 Список пуст", reply_markup=kb.as_markup())
    
    title = "📩 Фидбек" if item_type == "feedback" else "⛔ Жалобы"
    text = f"<b>{title}</b>\n\n"
    
    kb = InlineKeyboardBuilder()
    
    for item in items:
        if item_type == "feedback":
            icons = {"idea": "💡", "bug": "📝", "review": "⭐"}
            icon = icons.get(item.category, "❓")
        else:
            icon = "⛔"
        
        user_display = f"@{item.user.username}" if item.user.username else item.user.full_name[:10]
        
        content_preview = ""
        if item.text:
            clean_text = item.text.replace("\n", " ")[:10]
            content_preview = f"{clean_text}.."
        else:
            types_map = {
                "photo": "Фото", "video": "Видео", "voice": "Голос",
                "document": "Файл", "sticker": "Стикер"
            }
            content_preview = f"[{types_map.get(item.content_type, 'Медиа')}]"

        btn_text = f"#{item.id} | {content_preview} | {user_display}"
        
        full_name = item.user.full_name or "Аноним"
        full_preview = (item.text[:50] + "...") if item.text else f"[{item.content_type}]"
        text += f"{icon} <b>#{item.id}</b> {full_name}\n└ {full_preview}\n\n"
        
        kb.button(text=btn_text, callback_data=f"view_{item_type}_{item.id}_{page}")
    
    kb.adjust(1)
    
    nav_row = []
    if page > 1:
        nav_row.append(("⬅️", f"menu_{item_type}_{page-1}"))
    if page < total_pages:
        nav_row.append(("➡️", f"menu_{item_type}_{page+1}"))
    
    if nav_row:
        for text_btn, data in nav_row:
            kb.button(text=text_btn, callback_data=data)
        kb.adjust(1, 1, 1, 1, 1, len(nav_row))
    
    kb.button(text="🔙 Назад", callback_data="home")
    
    await safe_edit_or_send(callback, text, reply_markup=kb.as_markup())


# === ПРОСМОТР ОДНОЙ ЗАПИСИ ===
@admin_router.callback_query(F.data.startswith("view_"))
async def view_item(callback: CallbackQuery, state: FSMContext):
    _, item_type, item_id, back_page = callback.data.split("_")
    item = await get_item_by_id(item_type, int(item_id))
    
    if not item:
        return await callback.answer("❌ Не найдено", show_alert=True)
    
    try:
        await callback.message.delete()
    except Exception:
        pass

    caption = (
        f"🆔 <b>#{item.id}</b>\n"
        f"👤 {item.user.full_name} (@{item.user.username or 'нет'})\n"
        f"📅 {item.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"📝 {item.text or '—'}"
    )
    
    kb = InlineKeyboardBuilder()
    kb.button(text="↩️ Ответить", callback_data=f"reply_{item.user.telegram_id}_{item.id}")
    
    ban_text = "🕊 Разбан" if item.user.banned else "🔨 Бан"
    ban_action = "unban" if item.user.banned else "ban"
    kb.button(text=ban_text, callback_data=f"{ban_action}_{item.user.telegram_id}_view_{item_type}_{item_id}_{back_page}")
    
    # Кнопка профиля пользователя
    kb.button(text="👤 Профиль", callback_data=f"profile_{item.user.telegram_id}_view_{item_type}_{item_id}_{back_page}")
    
    kb.button(text="🔙 К списку", callback_data=f"menu_{item_type}_{back_page}")
    kb.adjust(2, 1, 1)
    
    try:
        if item.content_type == "photo":
            await callback.message.answer_photo(item.file_id, caption=caption, reply_markup=kb.as_markup(), parse_mode="HTML")
        elif item.content_type == "video":
            await callback.message.answer_video(item.file_id, caption=caption, reply_markup=kb.as_markup(), parse_mode="HTML")
        elif item.content_type == "voice":
            await callback.message.answer_voice(item.file_id, caption=caption, reply_markup=kb.as_markup(), parse_mode="HTML")
        elif item.content_type == "document":
            await callback.message.answer_document(item.file_id, caption=caption, reply_markup=kb.as_markup(), parse_mode="HTML")
        elif item.content_type == "sticker":
            st_msg = await callback.message.answer_sticker(item.file_id)
            await state.update_data(extra_msg_ids=[st_msg.message_id])
            await callback.message.answer(caption, reply_markup=kb.as_markup(), parse_mode="HTML")
        else:
            await callback.message.answer(caption, reply_markup=kb.as_markup(), parse_mode="HTML")
            
    except Exception as e:
        await callback.message.answer(f"⚠️ Ошибка контента: {e}\n\n{caption}", reply_markup=kb.as_markup(), parse_mode="HTML")


# === ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ===
@admin_router.callback_query(F.data.startswith("profile_"))
async def view_profile(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await cleanup_extra_messages(state, bot, callback.message.chat.id)
    
    parts = callback.data.split("_")
    telegram_id = int(parts[1])
    back_callback = "_".join(parts[2:])  # Куда вернуться
    
    # Получаем данные из БД
    db_user = await get_user_by_telegram_id(telegram_id)
    
    # Получаем данные из Telegram API
    tg_info = await get_user_profile_info(bot, telegram_id)
    
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    extra_msg_ids = []
    
    # Формируем текст профиля
    if "error" in tg_info:
        text = f"⚠️ <b>Ошибка получения данных Telegram:</b> {tg_info['error']}\n\n"
    else:
        text = ""
    
    # Основная информация
    text += f"👤 <b>Профиль пользователя</b>\n\n"
    
    # ID
    text += f"🆔 <b>Telegram ID:</b> <code>{telegram_id}</code>\n"
    
    # Имя из Telegram API (актуальное)
    if "error" not in tg_info:
        full_name = f"{tg_info.get('first_name', '')} {tg_info.get('last_name', '')}".strip()
        text += f"📛 <b>Имя:</b> {full_name or '—'}\n"
        text += f"👤 <b>Username:</b> @{tg_info.get('username') or '—'}\n"
        
        if tg_info.get('bio'):
            text += f"📝 <b>Bio:</b> {tg_info['bio']}\n"
        
        if tg_info.get('has_private_forwards'):
            text += f"🔒 <b>Приватные пересылки:</b> Да\n"
    
    text += "\n"
    
    # Информация из БД
    if db_user:
        text += f"━━━ <b>Данные в боте</b> ━━━\n"
        text += f"📛 <b>Сохранённое имя:</b> {db_user.full_name or '—'}\n"
        text += f"👤 <b>Сохранённый @:</b> @{db_user.username or '—'}\n"
        text += f"🚫 <b>Статус:</b> {'💀 Забанен' if db_user.banned else '🟢 Активен'}\n"
        if db_user.admin:
            text += f"🎭 <b>Роль: Админ</b>"
        
        if db_user.registered_at:
            text += f"📅 <b>Первый контакт:</b> {db_user.registered_at.strftime('%d.%m.%Y %H:%M')}\n"
    else:
        text += f"⚠️ <i>Пользователь не найден в базе данных</i>\n"
    
    # Кнопки
    kb = InlineKeyboardBuilder()
    
    # Ссылка на профиль в Telegram
    kb.button(text="💬 Открыть в Telegram", url=f"tg://user?id={telegram_id}")
    
    # Написать напрямую
    kb.button(text="✉️ Написать", callback_data=f"dm_{telegram_id}_{back_callback}")
    
    # Бан/разбан
    if db_user:
        if db_user.banned:
            kb.button(text="🕊 Разбанить", callback_data=f"unban_{telegram_id}_profile_{telegram_id}_{back_callback}")
        else:
            kb.button(text="🔨 Забанить", callback_data=f"ban_{telegram_id}_profile_{telegram_id}_{back_callback}")
    
    # Кнопка назад
    kb.button(text="🔙 Назад", callback_data=back_callback)
    
    kb.adjust(1)
    
    # Отправляем аватарку если есть
    if "error" not in tg_info and tg_info.get('photo'):
        try:
            photo_msg = await callback.message.answer_photo(
                tg_info['photo'].file_id,
                caption=text,
                reply_markup=kb.as_markup(),
                parse_mode="HTML"
            )
        except Exception:
            await callback.message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    else:
        await callback.message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    
    await callback.answer()


# === НАПИСАТЬ ПОЛЬЗОВАТЕЛЮ НАПРЯМУЮ ===
@admin_router.callback_query(F.data.startswith("dm_"))
async def start_dm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await cleanup_extra_messages(state, bot, callback.message.chat.id)
    
    parts = callback.data.split("_")
    tg_id = int(parts[1])
    back_callback = "_".join(parts[2:])
    
    await state.update_data(target_id=tg_id, back_callback=back_callback, dm_mode=True)
    await state.set_state(AdminStates.replying)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отмена", callback_data=f"profile_{tg_id}_{back_callback}")
    
    await safe_edit_or_send(
        callback,
        f"✍️ <b>Отправьте сообщение пользователю</b>\n\n"
        f"🆔 ID: <code>{tg_id}</code>\n\n"
        f"<i>Можно отправить текст, фото, стикер — что угодно</i>",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


# === ОТВЕТ ПОЛЬЗОВАТЕЛЮ ===
@admin_router.callback_query(F.data.startswith("reply_"))
async def start_reply(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await cleanup_extra_messages(state, bot, callback.message.chat.id)

    _, tg_id, item_id = callback.data.split("_")
    await state.update_data(target_id=int(tg_id), item_id=item_id, dm_mode=False)
    await state.set_state(AdminStates.replying)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отмена", callback_data="home")
    
    await safe_edit_or_send(callback, 
                            f"✍️ Отправьте ответ для пользователя (запрос #{item_id})\n(текст, фото, стикер — что угодно)", 
                            reply_markup=kb.as_markup())
    await callback.answer()


@admin_router.message(AdminStates.replying)
async def send_reply(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target_id = data["target_id"]
    item_id = data.get("item_id")
    dm_mode = data.get("dm_mode", False)
    
    try:
        await message.copy_to(chat_id=target_id)
        
        if dm_mode:
            await bot.send_message(target_id, "🔔 Сообщение от администратора")
        else:
            await bot.send_message(target_id, f"🔔 Ответ администратора на запрос #{item_id}")
        
        await message.answer("✅ Отправлено!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Домой", callback_data="home")
    await message.answer("Что дальше?", reply_markup=kb.as_markup())


# === СПИСОК ПОЛЬЗОВАТЕЛЕЙ (ОБНОВЛЁННЫЙ) ===
@admin_router.callback_query(F.data.startswith("menu_users_") | F.data.startswith("menu_banned_"))
async def list_users(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await cleanup_extra_messages(state, bot, callback.message.chat.id)
    
    parts = callback.data.split("_")
    mode = parts[1]  # users или banned
    page = int(parts[2])
    
    only_banned = (mode == "banned")
    users, total = await get_users_paginated(page, ITEMS_PER_PAGE, only_banned)
    total_pages = max(1, math.ceil(total / ITEMS_PER_PAGE))
    
    if not users:
        kb = InlineKeyboardBuilder()
        kb.button(text="🔙 Назад", callback_data="home")
        return await safe_edit_or_send(callback, "📭 Список пуст", reply_markup=kb.as_markup())
    
    title = "☠ Бан-лист" if only_banned else "👥 Пользователи"
    text = f"<b>{title}</b> (стр. {page}/{total_pages})\n\n"
    
    kb = InlineKeyboardBuilder()
    
    for user in users:
        status = "☠" if user.banned else "🟢"
        name = user.full_name[:15] if user.full_name else "Без имени"
        username = f"@{user.username}" if user.username else "—"
        
        # Текст в списке: статус + имя + @username
        text += f"{status} <b>{name}</b>\n"
        text += f"   └ {username} | <code>{user.telegram_id}</code>\n\n"
        
        # Кнопка — открывает профиль
        btn_text = f"👤 {name[:12]} ({username[:10] if user.username else 'нет @'})"
        kb.button(text=btn_text, callback_data=f"profile_{user.telegram_id}_menu_{mode}_{page}")
    
    kb.adjust(1)  # Кнопки по одной в ряд для читаемости
    
    # Навигация
    nav_buttons = []
    if page > 1:
        nav_buttons.append(("⬅️", f"menu_{mode}_{page-1}"))
    if page < total_pages:
        nav_buttons.append(("➡️", f"menu_{mode}_{page+1}"))
    
    for text_btn, data in nav_buttons:
        kb.button(text=text_btn, callback_data=data)
    
    if nav_buttons:
        kb.adjust(*([1] * len(users)), len(nav_buttons))
    
    kb.button(text="🔙 Назад", callback_data="home")
    
    await safe_edit_or_send(callback, text, reply_markup=kb.as_markup())


# === БАН/РАЗБАН ===
@admin_router.callback_query(F.data.startswith("ban_") | F.data.startswith("unban_"))
async def toggle_ban(callback: CallbackQuery, state: FSMContext, bot: Bot):
    parts = callback.data.split("_")
    action = parts[0]
    tg_id = int(parts[1])
    back_callback = "_".join(parts[2:])
    
    should_ban = (action == "ban")
    
    if should_ban and await is_admin(tg_id):
        return await callback.answer("❌ Нельзя забанить админа", show_alert=True)
    
    await toggle_ban_status(tg_id, should_ban)
    status = "забанен ☠" if should_ban else "разбанен 🕊"
    await callback.answer(f"Пользователь {status}")
    
    # Устанавливаем callback для возврата
    callback.data = back_callback
    
    # Определяем куда вернуться
    if back_callback.startswith("view_"):
        await view_item(callback, state)
    elif back_callback.startswith("profile_"):
        await view_profile(callback, state, bot)
    elif back_callback.startswith("menu_"):
        if "users" in back_callback or "banned" in back_callback:
            await list_users(callback, state, bot)
        else:
            await list_items(callback, state, bot)


@admin_router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()