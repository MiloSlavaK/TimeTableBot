import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher import filters
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv
from database import bd

load_dotenv()

TOKEN = os.getenv("TOKEN")

API_TOKEN = TOKEN


# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния для машины состояний
class Form(StatesGroup):
    waiting_for_day = State()
    waiting_for_time = State()
    waiting_for_event_description = State()

# Хранение расписания пользователей
data_base = bd

async def notify_user(chat_id, event):
    try:
        await bot.send_message(chat_id, f"Напоминание: {event} через 10 минут!")
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")

async def schedule_notifications():
    while True:
        now = datetime.now().strftime("%H:%M")
        for chat_id, events in data_base.items():
            for day, description, event_time in events:
                if event_time.strftime("%H:%M") == now:
                    await notify_user(chat_id, description)
        await asyncio.sleep(60)  # Проверка каждую минуту

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Добро пожаловать в бот расписания! Выберите неделю:", reply_markup=main_menu())

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Верхняя неделя", "Нижняя неделя", "Просмотреть задачи")
    return markup

@dp.message_handler(filters.Text(equals=["Верхняя неделя", "Нижняя неделя"]))
async def choose_week(message: types.Message):
    week_type = message.text
    await message.answer(f"Вы выбрали {week_type}. Выберите день:", reply_markup=day_menu())
    await Form.waiting_for_day.set()

def day_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    markup.add(*days)
    return markup

@dp.message_handler(state=Form.waiting_for_day)
async def choose_day(message: types.Message, state: FSMContext):
    day = message.text
    await message.answer(f"Вы выбрали {day}. Укажите время в формате ЧЧ:ММ:")
    await Form.waiting_for_time.set()
    await state.update_data(day=day)

@dp.message_handler(state=Form.waiting_for_time)
async def set_time(message: types.Message, state: FSMContext):
    time_str = message.text
    try:
        event_time = datetime.strptime(time_str, "%H:%M").replace(year=datetime.now().year,
                                                                  month=datetime.now().month,
                                                                  day=datetime.now().day)
        await message.answer("Введите описание события:")
        await Form.waiting_for_event_description.set()
        await state.update_data(event_time=event_time)
    except ValueError:
        await message.answer("Неверный формат времени. Попробуйте снова:")

@dp.message_handler(state=Form.waiting_for_event_description)
async def save_event(message: types.Message, state: FSMContext):
    event_description = message.text
    data = await state.get_data()
    day = data.get('day')
    event_time = data.get('event_time')

    chat_id = message.chat.id

    # Сохраняем событие
    if chat_id not in data_base:
        data_base[chat_id] = []

    data_base[chat_id].append((day, event_description, event_time))

    # Запланируем уведомление за 10 минут до события
    notify_time = event_time - timedelta(minutes=10)

    # Запускаем задачу для уведомления
    asyncio.create_task(schedule_event_notification(chat_id, notify_time, event_description))

    await message.answer(f"Событие '{event_description}' на {day} в {event_time.strftime('%H:%M')} сохранено!")
    await state.finish()


async def schedule_event_notification(chat_id, notify_time, event_description):
    while True:
        if datetime.now() >= notify_time:
            await notify_user(chat_id, event_description)
            break
        await asyncio.sleep(30)  # Проверка каждые 30 секунд

@dp.message_handler(filters.Text(equals="Просмотреть задачи"))
async def view_tasks(message: types.Message):
    chat_id = message.chat.id
    if chat_id in data_base and data_base[chat_id]:
        tasks_list = "\n".join([f"{day}: {description} в {event_time.strftime('%H:%M')}"
                                for day, description, event_time in data_base[chat_id]])
        await message.answer(f"Ваши сохраненные задачи:\n{tasks_list}")
    else:
        await message.answer("У вас нет сохраненных задач.")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(schedule_notifications())  # Запуск фоновой задачи для уведомлений
    executor.start_polling(dp, skip_updates=True)
