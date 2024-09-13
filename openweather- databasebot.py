import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ChatAction
from aiogram.filters import CommandStart, Command
from config import TOKEN, WEATHER_API_KEY
import random
import logging
from gtts import gTTS
import os
from googletrans import Translator
import sqlite3
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery
import aiohttp
from aiohttp import ClientSession, ClientConnectorError, ClientOSError

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Инициализация бота, диспетчера и переводчика
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class Form(StatesGroup):
    name = State()
    age = State()
    city = State()


def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 name TEXT NOT NULL, age INTEGER NOT NULL, 
                 city TEXT NOT NULL)''')
    conn.commit()
    conn.close()


init_db()


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer('Привет!\nКак тебя зовут?')
    await state.set_state(Form.name)


@dp.message(Form.name)
async def name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Form.age)


@dp.message(Form.age)
async def age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Из какого ты города?")
    await state.set_state(Form.city)


@dp.message(Form.city)
async def city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    user_data = await state.get_data()

    logging.info(f"Получены данные пользователя: {user_data}")

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('''
       INSERT INTO users (name, age, city) VALUES (?, ?, ?)''',
                (user_data['name'], user_data['age'], user_data['city']))
    conn.commit()
    conn.close()

    logging.info("Данные пользователя сохранены в базу данных")

    # Запрос к API погоды
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logging.info(f"Попытка {attempt + 1} получения данных о погоде")
            async with ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={user_data['city']}&appid={WEATHER_API_KEY}&units=metric"
                logging.info(f"URL запроса: {url}")
                async with session.get(url) as response:
                    logging.info(f"Статус ответа: {response.status}")
                    if response.status == 200:
                        weather_data = await response.json()
                        logging.info(f"Получены данные о погоде: {weather_data}")
                        main = weather_data['main']
                        weather = weather_data['weather'][0]

                        temperature = main['temp']
                        humidity = main['humidity']
                        description = weather['description']

                        weather_report = (f"Город - {user_data['city']}\n"
                                          f"Температура - {temperature}°C\n"
                                          f"Влажность воздуха - {humidity}%\n"
                                          f"Описание погоды - {description}")

                        await message.answer(weather_report)
                        logging.info("Отправлен отчет о погоде")
                        break
                    else:
                        error_data = await response.text()
                        logging.error(
                            f"Ошибка при получении данных о погоде. Статус: {response.status}, Данные: {error_data}")
                        await message.answer("Не удалось получить данные о погоде. Попробуйте позже.")
                        break
        except Exception as e:
            logging.error(f"Исключение при получении данных о погоде: {str(e)}")
            if attempt == max_retries - 1:
                await message.answer(f"Не удалось получить данные о погоде. Ошибка: {str(e)}")
            else:
                await asyncio.sleep(1)  # Пауза перед повторной попыткой

    await state.clear()
    logging.info("Состояние очищено")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = """
    Доступные команды:
    /start - Начать взаимодействие с ботом
    /help - Показать это сообщение помощи
    """
    await message.answer(help_text)


async def main():
    logging.info("Запуск бота")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())