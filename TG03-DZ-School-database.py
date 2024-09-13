import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
import sqlite3
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Определение состояний
class Form(StatesGroup):
    name = State()
    age = State()
    grade = State()
    edit_name = State()
    edit_field = State()
    edit_value = State()


# Создание клавиатуры
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добавить Ученика"), KeyboardButton(text="Изменить данные")]
    ],
    resize_keyboard=True,
    persistent=True
)


# Функция для инициализации базы данных
def init_db():
    try:
        conn = sqlite3.connect('school_data.db')
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS students
                       (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        age INTEGER,
                        grade TEXT)''')
        conn.commit()
        logger.info("База данных успешно инициализирована")
    except sqlite3.Error as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
    finally:
        if conn:
            conn.close()


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет, друг! Я умею создавать базу данных для записи студентов.", reply_markup=keyboard)


# Обработчик кнопки "Добавить Ученика"
@dp.message(lambda message: message.text == "Добавить Ученика")
async def add_student(message: types.Message, state: FSMContext):
    await message.answer("Давай добавим нового ученика. Как его зовут?")
    await state.set_state(Form.name)


@dp.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Отлично! Теперь введи возраст ученика.")
    await state.set_state(Form.age)


@dp.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи возраст числом.")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Хорошо! Теперь введи класс ученика (например, '10A').")
    await state.set_state(Form.grade)


@dp.message(Form.grade)
async def process_grade(message: types.Message, state: FSMContext):
    await state.update_data(grade=message.text)
    user_data = await state.get_data()

    # Сохранение данных в базу
    try:
        conn = sqlite3.connect('school_data.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO students (name, age, grade) VALUES (?, ?, ?)",
                    (user_data['name'], user_data['age'], user_data['grade']))
        conn.commit()
        logger.info(f"Данные успешно сохранены: {user_data}")
        await message.answer(f"Спасибо! Данные ученика сохранены:\n"
                             f"Имя: {user_data['name']}\n"
                             f"Возраст: {user_data['age']}\n"
                             f"Класс: {user_data['grade']}")
    except sqlite3.Error as e:
        logger.error(f"Ошибка при сохранении данных: {e}")
        await message.answer("Извините, произошла ошибка при сохранении данных. Попробуйте еще раз.")
    finally:
        if conn:
            conn.close()

    await state.clear()


# Обработчик кнопки "Изменить данные"
@dp.message(lambda message: message.text == "Изменить данные")
async def edit_data(message: types.Message, state: FSMContext):
    await message.answer("Введите имя ученика, данные которого хотите изменить:")
    await state.set_state(Form.edit_name)


@dp.message(Form.edit_name)
async def process_edit_name(message: types.Message, state: FSMContext):
    name = message.text
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE name = ?", (name,))
    student = cur.fetchone()
    conn.close()

    if student:
        await state.update_data(student_id=student[0], current_name=student[1])
        await message.answer(f"Выберите, что хотите изменить для {name}:\n1. Имя\n2. Возраст\n3. Класс")
        await state.set_state(Form.edit_field)
    else:
        await message.answer("Ученик с таким именем не найден. Попробуйте еще раз.")
        await state.clear()


@dp.message(Form.edit_field)
async def process_edit_field(message: types.Message, state: FSMContext):
    choice = message.text

    if choice == "1":
        await message.answer("Введите новое имя:")
        await state.update_data(edit_field="name")
    elif choice == "2":
        await message.answer("Введите новый возраст:")
        await state.update_data(edit_field="age")
    elif choice == "3":
        await message.answer("Введите новый класс:")
        await state.update_data(edit_field="grade")
    else:
        await message.answer("Неверный выбор. Попробуйте еще раз.")
        return

    await state.set_state(Form.edit_value)


@dp.message(Form.edit_value)
async def save_edited_value(message: types.Message, state: FSMContext):
    new_value = message.text
    user_data = await state.get_data()

    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()

    try:
        cur.execute(f"UPDATE students SET {user_data['edit_field']} = ? WHERE id = ?",
                    (new_value, user_data['student_id']))
        conn.commit()
        await message.answer(f"Данные успешно обновлены!")
    except sqlite3.Error as e:
        logger.error(f"Ошибка при обновлении данных: {e}")
        await message.answer("Произошла ошибка при обновлении данных. Попробуйте еще раз.")
    finally:
        conn.close()

    await state.clear()


# Функция для запуска бота
async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())