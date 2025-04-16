"""
Этот модуль реализует эхо-бота на основе aiogram, который работает с
фото, видео, аудио, текстом, стикерами и гифками, а также преобразует
голосовые сообщения и аудиофайлы в текст.
"""

import os
import tempfile
import logging
import asyncio

import speech_recognition as sr
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ContentType
from pydub import AudioSegment
from pydub.utils import which

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота (ЗАМЕНИТЕ НА СВОЙ!)
TOKEN = "7809682956:AAHf7F0Huo4I4dGlLYV4vMjh5gwoHnUqFOM"

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Проверка наличия ffmpeg
if not which("ffmpeg"):
    raise RuntimeError("FFmpeg не установлен! Скачайте с https://ffmpeg.org/")

async def convert_audio(input_path: str, output_format: str = "wav") -> str:
    """Конвертирует аудиофайл в WAV формат и возвращает путь к файлу."""
    output_path = tempfile.mktemp(suffix=f".{output_format}")
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format=output_format)
    return output_path

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Отправляет приветственное сообщение при команде /start."""
    await message.answer(
        "👋 Я эхо-бот! Отправь мне фото, видео, аудио, голосовое сообщение, "
        "текст, стикер или гифку, и я повторю их. Голосовые и аудио также "
        "преобразую в текст."
    )

# Обработчик голосовых сообщений и аудио
@dp.message(lambda m: m.voice or m.audio)
async def handle_audio(message: types.Message):
    """Обрабатывает голосовые сообщения и аудиофайлы, возвращая эхо и распознанный текст."""
    # Отправляем эхо
    if message.voice:
        await message.answer_voice(message.voice.file_id)
    elif message.audio:
        await message.answer_audio(message.audio.file_id)
    
    download_path = None
    wav_path = None

    try:
        file = message.voice or message.audio
        file_info = await bot.get_file(file.file_id)
        download_path = f"temp_{file.file_id}"
        await bot.download_file(file_info.file_path, download_path)

        wav_path = await convert_audio(download_path)
        
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language='ru-RU')
            await message.answer(f"🎤 Распознанный текст:\n{text}")

    except sr.UnknownValueError:
        await message.answer("🚫 Не удалось распознать аудио. Попробуйте другое сообщение.")
    except (sr.RequestError, OSError) as e:
        logging.error("Ошибка: %s", e)
        await message.answer("🚫 Произошла ошибка при обработке файла.")
    finally:
        for path in [download_path, wav_path]:
            if path and os.path.exists(path):
                os.remove(path)

# Обработчики различных типов контента
@dp.message(lambda m: m.content_type == ContentType.STICKER)
async def handle_sticker(message: types.Message):
    """Возвращает полученный стикер."""
    await message.answer_sticker(message.sticker.file_id)

@dp.message(lambda m: m.content_type == ContentType.TEXT)
async def echo_text(message: types.Message):
    """Возвращает полученный текст."""
    await message.answer(message.text)

@dp.message(lambda m: m.content_type == ContentType.PHOTO)
async def handle_photo(message: types.Message):
    """Возвращает полученное фото."""
    await message.answer_photo(message.photo[-1].file_id)

@dp.message(lambda m: m.content_type == ContentType.VIDEO)
async def handle_video(message: types.Message):
    """Возвращает полученное видео."""
    await message.answer_video(message.video.file_id)

@dp.message(lambda m: m.content_type == ContentType.ANIMATION)
async def handle_animation(message: types.Message):
    """Возвращает полученную анимацию (гифку)."""
    await message.answer_animation(message.animation.file_id)

# Запуск бота
async def main():
    """Основная функция запуска бота."""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())