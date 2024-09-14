import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
from config import TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Создание клавиатуры для основного меню
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="/start")],
        [KeyboardButton(text="/links")],
        [KeyboardButton(text="/dynamic")],
        [KeyboardButton(text="/help")]
    ], resize_keyboard=True)
    return keyboard

# Функция для отправки приветственного сообщения
async def send_welcome_message(message: types.Message):
    welcome_text = """
Привет! Я многофункциональный бот. Вот что я умею:

1. Отвечать на приветствия и прощания
2. Показывать ссылки на полезные ресурсы
3. Демонстрировать динамическое меню

Используйте команду /help, чтобы увидеть список всех доступных команд.
    """
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await send_welcome_message(message)
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Привет")],
        [KeyboardButton(text="Пока")]
    ], resize_keyboard=True)
    await message.answer("Выберите действие:", reply_markup=keyboard)

# Обработчик кнопок "Привет" и "Пока"
@dp.message(F.text.in_(["Привет", "Пока"]))
async def process_simple_buttons(message: types.Message):
    if message.text == "Привет":
        await message.answer(f"Привет, {message.from_user.first_name}!")
    else:
        await message.answer(f"До свидания, {message.from_user.first_name}!")

# Обработчик команды /links
@dp.message(Command("links"))
async def cmd_links(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Новости", url="https://news.google.com/"))
    builder.add(InlineKeyboardButton(text="Музыка", url="https://www.spotify.com/"))
    builder.add(InlineKeyboardButton(text="Видео", url="https://www.youtube.com/"))
    await message.answer("Выберите ссылку:", reply_markup=builder.as_markup())

# Обработчик команды /dynamic
@dp.message(Command("dynamic"))
async def cmd_dynamic(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Показать больше", callback_data="show_more"))
    await message.answer("Нажмите кнопку для показа дополнительных опций:", reply_markup=builder.as_markup())

# Обработчик нажатия на инлайн-кнопки
@dp.callback_query(F.data == "show_more")
async def process_callback_show_more(callback_query: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Опция 1", callback_data="option1"))
    builder.add(InlineKeyboardButton(text="Опция 2", callback_data="option2"))
    await callback_query.message.edit_reply_markup(reply_markup=builder.as_markup())
    await callback_query.answer()

@dp.callback_query(F.data.in_(["option1", "option2"]))
async def process_callback_options(callback_query: types.CallbackQuery):
    option = "Опция 1" if callback_query.data == "option1" else "Опция 2"
    await callback_query.message.answer(f"Вы выбрали: {option}")
    await callback_query.answer()

# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = """
Доступные команды:
/start - Показать приветственное меню
/links - Показать ссылки на ресурсы
/dynamic - Показать динамическое меню
/help - Показать это сообщение помощи
    """
    await message.answer(help_text, reply_markup=get_main_keyboard())

# Обработчик для всех остальных сообщений
@dp.message()
async def echo(message: types.Message):
    await message.answer("Я не понимаю это сообщение. Используйте /help для просмотра доступных команд.", reply_markup=get_main_keyboard())

# Функция для запуска бота
async def main():
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Начать"),
        types.BotCommand(command="links", description="Показать ссылки"),
        types.BotCommand(command="dynamic", description="Динамическое меню"),
        types.BotCommand(command="help", description="Помощь")
    ])
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())