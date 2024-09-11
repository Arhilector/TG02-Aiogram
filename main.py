import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ChatAction
from aiogram.filters import CommandStart, Command
from config import TOKEN
import random
import logging
from gtts import gTTS
import os
from googletrans import Translator

# Инициализация бота, диспетчера и переводчика
bot = Bot(token=TOKEN)
dp = Dispatcher()
translator = Translator()

# Функция для создания инлайн-клавиатуры
def get_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Фото", callback_data="photo")
    builder.button(text="Видео", callback_data="video")
    builder.button(text="Тренировка", callback_data="training")
    builder.button(text="Презентация", callback_data="presentation")
    builder.button(text="Голосовое", callback_data="voice")
    builder.button(text="Перевод", callback_data="translate")
    builder.adjust(2)  # Размещаем кнопки в два столбца
    return builder.as_markup()

@dp.message(CommandStart())
async def start_command(message: Message):
    avatar = FSInputFile("robot-android-kid_111928-6.jpg")  # Замените на реальный путь к аватару бота
    await message.answer_photo(
        photo=avatar,
        caption=f'Привет, {message.from_user.full_name}! Я медиа-бот. Выберите действие:',
        reply_markup=get_keyboard()
    )

@dp.message(Command('help'))
async def help_command(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/start - Начать взаимодействие\n"
        "/help - Показать список команд\n"
        "Используйте кнопки меню для выбора действий",
        reply_markup=get_keyboard()
    )

@dp.callback_query(F.data == "photo")
async def process_photo_callback(callback: types.CallbackQuery):
    await callback.answer()
    await photo(callback.message)

@dp.callback_query(F.data == "video")
async def process_video_callback(callback: types.CallbackQuery):
    await callback.answer()
    await send_video(callback.message)

@dp.callback_query(F.data == "training")
async def process_training_callback(callback: types.CallbackQuery):
    await callback.answer()
    await training(callback.message)

@dp.callback_query(F.data == "presentation")
async def process_presentation_callback(callback: types.CallbackQuery):
    await callback.answer()
    await doc(callback.message)

@dp.callback_query(F.data == "voice")
async def process_voice_callback(callback: types.CallbackQuery):
    await callback.answer()
    await request_voice(callback.message)

@dp.callback_query(F.data == "translate")
async def process_translate_callback(callback: types.CallbackQuery):
    await callback.answer()
    await translate_mode(callback.message)

async def photo(message: Message):
    try:
        photo_list = [
            "https://i.ytimg.com/vi/q5PHggJKrGs/maxresdefault.jpg",
            "https://img.freepik.com/free-vector/hand-drawn-birthday-background_23-2149483336.jpg",
            "https://via.placeholder.com/150"
        ]
        rand_photo = random.choice(photo_list)
        await message.answer_photo(photo=rand_photo, caption='Лови картинку')
        logging.info(f"Отправлено фото: {rand_photo}")
    except Exception as e:
        logging.error(f"Ошибка при отправке фото: {e}", exc_info=True)
        await message.answer("Извините, произошла ошибка при отправке фото.")

async def training(message: Message):
    training_list = [
        "Тренировка 1:\n1. Скручивания: 3 подхода по 15 повторений\n2. Велосипед: 3 подхода по 20 повторений (каждая сторона)\n3. Планка: 3 подхода по 30 секунд",
        "Тренировка 2:\n1. Подъемы ног: 3 подхода по 15 повторений\n2. Русский твист: 3 подхода по 20 повторений (каждая сторона)\n3. Планка с поднятой ногой: 3 подхода по 20 секунд (каждая нога)",
        "Тренировка 3:\n1. Скручивания с поднятыми ногами: 3 подхода по 15 повторений\n2. Горизонтальные ножницы: 3 подхода по 20 повторений\n3. Боковая планка: 3 подхода по 20 секунд (каждая сторона)"
    ]
    rand_tr = random.choice(training_list)
    await message.answer(f"Это ваша мини-тренировка на сегодня:\n\n{rand_tr}")
    tts_text = rand_tr.replace('\n', ' ')
    tts = gTTS(text=tts_text, lang='ru')
    tts.save("training.ogg")
    audio = FSInputFile('training.ogg')
    await bot.send_voice(message.chat.id, audio)
    os.remove("training.ogg")

async def send_video(message: Message):
    try:
        await message.answer("Загружаю видео, пожалуйста, подождите...")
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_VIDEO)
        video = FSInputFile('video.mp4')
        await message.answer_video(video=video, caption="Вот ваше видео!")
    except Exception as e:
        print(f"Ошибка при отправке видео: {e}")
        await message.answer("Извините, произошла ошибка при отправке видео.")

async def doc(message: Message):
    try:
        file_path = os.path.join(os.getcwd(), "файл.docx")
        if not os.path.exists(file_path):
            await message.answer("Извините, файл не найден.")
            return
        doc = FSInputFile(file_path)
        await message.answer_document(document=doc, caption="Вот ваша презентация!")
    except Exception as e:
        print(f"Ошибка при отправке документа: {e}")
        await message.answer("Извините, произошла ошибка при отправке документа.")


async def request_voice(message: Message):
    await message.answer("Продиктуйте аудио, и я его сохраню.")


@dp.message(F.voice)
async def handle_voice(message: Message):
    try:
        # Создаем директорию img, если она не существует
        if not os.path.exists('img'):
            os.makedirs('img')

        file_id = message.voice.file_id
        file = await bot.get_file(file_id)

        # Генерируем уникальное имя файла
        file_name = f"{message.from_user.id}_{file.file_id}.ogg"
        file_path = os.path.join('img', file_name)

        # Скачиваем файл
        await bot.download_file(file.file_path, file_path)

        # Проверяем, что файл действительно сохранен
        if os.path.exists(file_path):
            await message.answer(f"Ваша аудиозапись сохранена как {file_name}")
        else:
            raise FileNotFoundError("Файл не был сохранен")

    except Exception as e:
        print(f"Ошибка при сохранении голосового сообщения: {e}")
        await message.answer("Извините, произошла ошибка при сохранении голосового сообщения.")

async def translate_mode(message: Message):
    await message.answer("Отправьте текст, который нужно перевести на английский.")

@dp.message(F.text)
async def translate_text(message: Message):
    try:
        translated = translator.translate(message.text, dest='en')
        await message.answer(f"Перевод: {translated.text}")
    except Exception as e:
        print(f"Ошибка при переводе: {e}")
        await message.answer("Извините, произошла ошибка при переводе.")

@dp.message(F.photo)
async def handle_photo(message: Message):
    try:
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        file_path = f'img/{file.file_id}.jpg'
        await bot.download_file(file.file_path, file_path)
        await message.answer(f"Фото сохранено как {file_path}")
    except Exception as e:
        print(f"Ошибка при сохранении фото: {e}")
        await message.answer("Извините, произошла ошибка при сохранении фото.")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())