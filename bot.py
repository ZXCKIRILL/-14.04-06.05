import logging
import asyncio
import string
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ErrorEvent

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Токен бота (ЗАМЕНИТЕ НА СВОЙ!)
TOKEN = "YOUR_BOT_TOKEN"

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
    
    password = []
    # Гарантируем хотя бы один символ из каждого выбранного набора
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

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Приветственное сообщение"""
    try:
        await message.answer(
            "🔐 Добро пожаловать в генератор паролей!\n\n"
            "Используйте команду /genpass <длина> чтобы создать пароль с настройками\n"
            "Используйте /generate [длина] для быстрой генерации сложного пароля\n"
            "/help - справка по использованию"
        )
    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}", exc_info=True)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Справка по командам"""
    try:
        await message.answer(
            "🛠 Помощь по командам:\n\n"
            "/genpass <длина> - создать пароль с настройками (6-50 символов)\n"
            "/generate [длина] - быстрая генерация сложного пароля (по умолчанию 12 символов)\n"
            "/help - показать эту справку\n\n"
            "Примеры:\n/genpass 12\n/generate 15"
        )
    except Exception as e:
        logger.error(f"Ошибка в cmd_help: {e}", exc_info=True)

@dp.message(Command("generate"))
async def cmd_generate(message: types.Message):
    """Генерация сложного пароля с настройками по умолчанию"""
    try:
        args = message.text.split()
        length = 12  # Длина по умолчанию
        
        # Парсим аргументы
        if len(args) >= 2:
            if not args[1].isdigit():
                await message.answer("❌ Некорректная длина. Укажите число от 6 до 50.")
                return
            
            length = int(args[1])
            if not (6 <= length <= 50):
                await message.answer("❌ Длина должна быть от 6 до 50.")
                return
        
        # Настройки для максимальной сложности
        letters = LETTERS_EN_LOWER + LETTERS_EN_UPPER  # Английские буквы обоих регистров
        use_digits = True
        use_symbols = True
        
        # Генерируем пароль
        password = generate_password(
            length=length,
            use_digits=use_digits,
            use_symbols=use_symbols,
            letters=letters
        )
        
        await message.answer(
            f"🔒 Сгенерированный пароль ({length} символов):\n<code>{password}</code>",
            parse_mode="HTML"
        )
    
    except Exception as e:
        logger.error(f"Ошибка в cmd_generate: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при генерации. Проверьте формат команды.")

@dp.message(Command("genpass"))
async def cmd_genpass(message: types.Message, state: FSMContext):
    """Обработчик команды генерации пароля с настройками"""
    try:
        args = message.text.split()
        if len(args) < 2:
            raise ValueError("Не указана длина пароля")
        
        if not args[1].isdigit():
            raise ValueError("Некорректный формат длины")
        
        length = int(args[1])
        if not (6 <= length <= 50):
            raise ValueError("Длина должна быть от 6 до 50")
        
        await state.update_data(length=length)
        await message.answer(
            "🌐 Выберите язык:\n"
            "1 - Английский\n"
            "2 - Русский"
        )
        await state.set_state(PasswordState.language)
    
    except Exception as e:
        logger.error(f"Ошибка в cmd_genpass: {e}", exc_info=True)
        await message.answer(
            "❌ Ошибка ввода. Используйте формат:\n"
            "/genpass <длина>\n\n"
            "Пример: /genpass 12 (длина от 6 до 50)"
        )
        await state.clear()

@dp.message(PasswordState.language)
async def process_language(message: types.Message, state: FSMContext):
    """Обработка выбора языка"""
    try:
        user_input = message.text.strip()
        if user_input not in ('1', '2'):
            raise ValueError("Некорректный выбор языка")
        
        if user_input == '1':
            letters = LETTERS_EN_LOWER + LETTERS_EN_UPPER
            lang = 'en'
        else:
            letters = LETTERS_RU_LOWER + LETTERS_RU_UPPER
            lang = 'ru'
        
        await state.update_data(language=lang, letters=letters)
        await message.answer(
            "🔤 Выберите регистр:\n"
            "1 - Только нижний\n"
            "2 - Только верхний\n"
            "3 - Оба регистра"
        )
        await state.set_state(PasswordState.case)
    
    except Exception as e:
        logger.error(f"Ошибка в process_language: {e}", exc_info=True)
        await message.answer(
            "❌ Ошибка выбора языка. Отправьте:\n"
            "1 - Английский\n"
            "2 - Русский"
        )

@dp.message(PasswordState.case)
async def process_case(message: types.Message, state: FSMContext):
    """Обработка выбора регистра"""
    try:
        user_input = message.text.strip()
        if user_input not in ('1', '2', '3'):
            raise ValueError("Некорректный выбор регистра")
        
        data = await state.get_data()
        base_letters = data['letters']
        
        if user_input == '1':
            letters = base_letters.lower()
        elif user_input == '2':
            letters = base_letters.upper()
        else:
            letters = base_letters  # Оба регистра уже включены
        
        await state.update_data(letters=letters)
        await message.answer(
            "⚙️ Выберите параметры (через пробел):\n"
            "1 - Цифры (0-9)\n"
            "2 - Спецсимволы (!@# и др.)\n\n"
            "Пример: 1 2 - использовать оба варианта"
        )
        await state.set_state(PasswordState.parameters)
    
    except Exception as e:
        logger.error(f"Ошибка в process_case: {e}", exc_info=True)
        await message.answer(
            "❌ Ошибка выбора регистра. Отправьте:\n"
            "1 - Нижний регистр\n"
            "2 - Верхний регистр\n"
            "3 - Оба регистра"
        )

@dp.message(PasswordState.parameters)
async def process_parameters(message: types.Message, state: FSMContext):
    """Обработка параметров пароля"""
    try:
        data = await state.get_data()
        length = data['length']
        letters = data['letters']
        
        user_input = message.text.strip()
        if not user_input:
            raise ValueError("Пустой ввод параметров")
        
        options = set(user_input.split())
        if not options.issubset({'1', '2'}):
            raise ValueError("Недопустимые параметры")
        
        use_digits = '1' in options
        use_symbols = '2' in options
        
        password = generate_password(
            length=length,
            use_digits=use_digits,
            use_symbols=use_symbols,
            letters=letters
        )
        
        response = (
            f"🔒 Ваш пароль:\n<code>{password}</code>\n\n"
            f"📏 Длина: {length}\n"
            f"🔢 Цифры: {'Да' if use_digits else 'Нет'}\n"
            f"⚡ Символы: {'Да' if use_symbols else 'Нет'}\n"
            f"🌐 Язык: {'Английский' if data.get('language') == 'en' else 'Русский'}"
        )
        
        await message.answer(response, parse_mode="HTML")
        await state.clear()
    
    except Exception as e:
        logger.error(f"Ошибка в process_parameters: {e}", exc_info=True)
        await message.answer(
            "❌ Ошибка выбора параметров. Отправьте цифры через пробел:\n"
            "1 - Цифры\n2 - Символы\n\nПример: 1 2"
        )
        await state.set_state(PasswordState.parameters)

@dp.errors()
async def global_error_handler(event: ErrorEvent):
    """Глобальный обработчик ошибок"""
    logger.critical("Глобальная ошибка: %s", event.exception, exc_info=True)
    await event.update.message.answer("⚠️ Произошла системная ошибка. Попробуйте позже.")

async def main():
    """Запуск бота"""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())