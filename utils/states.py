from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    send_feedback = State() # Для идеи, бага, отзыва
    send_report = State()   # Для жалобы

class AdminStates(StatesGroup):
    replying = State() # Состояние ответа пользователю