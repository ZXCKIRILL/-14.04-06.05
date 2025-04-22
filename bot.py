"""
Этот модуль реализует бота для генерации случайных паролей с настройкой параметров.
"""

import logging
import asyncio
import string
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота (ЗАМЕНИТЕ НА СВОЙ!)
TOKEN = "7809682956:AAHf7F0Huo4I4dGlLYV4vMjh5gwoHnUqFOM"

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Символьные наборы
LETTERS_EN_UPPER = string.ascii_uppercase
LETTERS_EN_LOWER = string.ascii_lowercase
LETTERS_RU_UPPER = 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
LETTERS_RU_LOWER = 'абвгдежзийклмнопрстуфхцчшщъыьэюя'
DIGITS = string.digits
SYMBOLS = '!@#$%^&*()_+-=[]{}|;:,.<>?'

class PasswordState(StatesGroup):
    """Класс состояний для генерации пароля"""
    language = State()
    case = State()
    parameters = State()
    length = State()

def generate_password(length: int, use_digits: bool, use_symbols: bool, letters: str) -> str:
    """Генерирует пароль с заданными параметрами"""
    if length < 1:
        return ""
    
    chars = letters
    if use_digits:
        chars += DIGITS
    if use_symbols:
        chars += SYMBOLS
    
    # Гарантируем хотя бы один символ из каждого выбранного набора
    password = []
    password.append(random.choice(letters))
    if use_digits:
        password.append(random.choice(DIGITS))
    if use_symbols:
        password.append(random.choice(SYMBOLS))
    
    # Добираем остальные символы
    remaining = length - len(password)
    if remaining > 0:
        password += [random.choice(chars) for _ in range(remaining)]
    
    # Перемешиваем результат
    random.shuffle(password)
    return ''.join(password)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Приветственное сообщение с инструкциями"""
    await message.answer(
        "🔐 Добро пожаловать в генератор паролей!\n\n"
        "Используйте команду /genpass <длина>, чтобы создать новый пароль.\n"
        "Или /help для получения справки."
    )

# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Справка по использованию бота"""
    await message.answer(
        "🛠 Помощь по использованию бота:\n\n"
        "/genpass <длина> - создать новый пароль заданной длины\n"
        "/help - показать эту справку\n\n"
        "После запуска генерации следуйте инструкциям бота."
    )

# Обработчик команды /genpass
@dp.message(Command("genpass"))
async def cmd_genpass(message: types.Message, state: FSMContext):
    """Начало процесса генерации пароля с указанием длины"""
    args = message.text.split()
    
    if len(args) > 1 and args[1].isdigit():
        length = int(args[1])
        if 6 <= length <= 50:
            await state.update_data(length=length)
            await message.answer(
                "🌐 Выберите язык (отправьте 1 для английского или 2 для русского):"
            )
            await state.set_state(PasswordState.language)
        else:
            await message.answer("⚠️ Длина должна быть от 6 до 50. Попробуйте снова.")
    else:
        await message.answer("❌ Пожалуйста, укажите длину пароля (например, /genpass 12).")

# Обработчик выбора языка
@dp.message(PasswordState.language)
async def process_language(message: types.Message, state: FSMContext):
    """Обработка выбора языка"""
    if message.text == '1':
        await state.update_data(language='en')
        await message.answer(
            "🔤 Выберите регистр (отправьте 1 для нижнего, 2 для верхнего, 3 для обоих):"
        )
        await state.update_data(letters=LETTERS_EN_LOWER + LETTERS_EN_UPPER)
    elif message.text == '2':
        await state.update_data(language='ru')
        await message.answer(
            "🔤 Выберите регистр (отправьте 1 для нижнего, 2 для верхнего, 3 для обоих):"
        )
        await state.update_data(letters=LETTERS_RU_LOWER + LETTERS_RU_UPPER)
    else:
        await message.answer("❌ Неверный выбор. Пожалуйста, отправьте 1 для английского или 2 для русского.")
        return
    
    await state.set_state(PasswordState.case)

# Обработчик выбора регистра
@dp.message(PasswordState.case)
async def process_case(message: types.Message, state: FSMContext):
    """Обработка выбора регистра"""
    data = await state.get_data()
    letters = data['letters']
    
    if message.text == '1':
        # Использовать только нижний регистр
        letters = letters.lower()
    elif message.text == '2':
        # Использовать только верхний регистр
        letters = letters.upper()
    elif message.text == '3':
        # Использовать оба регистра
        letters = data['letters']
    else:
        await message.answer("❌ Неверный выбор. Пожалуйста, отправьте 1, 2 или 3.")
        return

    await state.update_data(letters=letters)
    await message.answer(
        "⚙️ Выберите параметры (отправьте цифры через пробел):\n\n"
        "1. Использовать цифры (0-9)\n"
        "2. Использовать спецсимволы (!@# и др.)\n\n"
        "Пример: 1 2 - использовать оба варианта"
    )
    await state.set_state(PasswordState.parameters)

# Обработчик параметров пароля
@dp.message(PasswordState.parameters)
async def process_parameters(message: types.Message, state: FSMContext):
    """Обработка выбора параметров пароля"""
    data = await state.get_data()
    length = data['length']
    letters = data['letters']
    
    options = message.text.split()
    
    # Проверка на ввод только одной цифры
    if len(options) == 1:
        try:
            option = int(options[0])
            if option == 1:
                use_digits = True
                use_symbols = False
            elif option == 2:
                use_digits = False
                use_symbols = True
            else:
                await message.answer("❌ Неверный выбор. Пожалуйста, отправьте 1 или 2.")
                return
        except ValueError:
            await message.answer("❌ Некорректный ввод. Используйте цифры через пробел, например: 1 2")
            return
    else:
        try:
            options = list(map(int, options))
            use_digits = 1 in options
            use_symbols = 2 in options
            
            if not any([use_digits, use_symbols]):
                await message.answer("⚠️ Выберите хотя бы один дополнительный параметр (1 или 2)")
                return
        except (ValueError, TypeError):
            await message.answer("❌ Некорректный ввод. Используйте цифры через пробел, например: 1 2")
            return

    password = generate_password(
        length=length,
        use_digits=use_digits,
        use_symbols=use_symbols,
        letters=letters
    )
    
    await message.answer(
        f"🔒 Ваш новый пароль:\n\n"
        f"<code>{password}</code>\n\n"
        f"📏 Длина: {length}\n"
        f"🔢 Цифры: {'Да' if use_digits else 'Нет'}\n"
        f"⚡ Спецсимволы: {'Да' if use_symbols else 'Нет'}\n"
        f"🌐 Язык: {'Английский' if data['language'] == 'en' else 'Русский'}",
        parse_mode="HTML"
    )
    await state.clear()

# Запуск бота
async def main():
    """Основная функция запуска бота"""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())