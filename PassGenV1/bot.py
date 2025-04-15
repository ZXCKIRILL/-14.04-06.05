from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Токен от BotFather
TOKEN = "8046941301:AAEIO15waeVrrQo_eP4S1DsZ_i0eTvTX4uo"

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Я бот для генерации паролей. Используй /generate.")

# Обработчик команды /generate
async def generate_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Здесь будет логика генерации пароля
    await update.message.reply_text("Пароль: 8s7D$kLm!")

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Регистрация обработчиков команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate_password))
    
    # Запуск бота
    app.run_polling()