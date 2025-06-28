import asyncio
import logging
from telethon import TelegramClient
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Логирование
logging.basicConfig(level=logging.INFO)

# Данные Telegram API
API_ID = 27063381
API_HASH = 'cfc4bd37dadce32e75db8760ad9b0421'
SESSION_NAME = 'user'

# Токен Telegram-бота
BOT_TOKEN = '8199472815:AAHx25LNiYcHAJq0dv-yQKHmgOCK0RVA2Fg'

# Инициализация Telethon клиента и бота
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Глобальные переменные
chat_ids = []
interval = 60
sending_messages = False
message_to_send = ""
admin_id = None  # Твой Telegram ID для ограничения управления

# Клавиатура
def get_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("➕ Добавить чат", callback_data="add_chat")],
        [InlineKeyboardButton("🕒 Установить интервал", callback_data="set_interval")],
        [InlineKeyboardButton("✉️ Задать сообщение", callback_data="set_message")],
        [InlineKeyboardButton("▶️ Начать рассылку", callback_data="start")],
        [InlineKeyboardButton("⏹ Остановить рассылку", callback_data="stop")]
    ])

# Команда старт
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    global admin_id
    admin_id = message.from_user.id  # сохраняем админа
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=get_keyboard())

# Обработка нажатий кнопок
@dp.callback_query_handler(lambda c: True)
async def handle_callbacks(callback: types.CallbackQuery):
    if callback.from_user.id != admin_id:
        await callback.answer("Нет доступа.", show_alert=True)
        return

    data = callback.data
    if data == "add_chat":
        await callback.message.answer("Введите username (@username) или ID чата:")
        state["expecting"] = "add_chat"
    elif data == "set_interval":
        await callback.message.answer("Введите интервал в секундах:")
        state["expecting"] = "set_interval"
    elif data == "set_message":
        await callback.message.answer("Введите текст сообщения:")
        state["expecting"] = "set_message"
    elif data == "start":
        if not chat_ids or not message_to_send:
            await callback.message.answer("Сначала добавьте чат и сообщение.")
        else:
            await callback.message.answer("Рассылка запущена.")
            asyncio.create_task(start_sending())
    elif data == "stop":
        global sending_messages
        sending_messages = False
        await callback.message.answer("Рассылка остановлена.")

# Ожидаем ввод пользователя после кнопки
state = {"expecting": None}

@dp.message_handler()
async def handle_user_input(message: types.Message):
    global interval, message_to_send
    if message.from_user.id != admin_id:
        return

    current = state["expecting"]
    if current == "add_chat":
        try:
            entity = await client.get_entity(message.text.strip())
            chat_ids.append(entity.id)
            await message.answer("Чат успешно добавлен.")
        except Exception as e:
            await message.answer(f"Ошибка добавления: {e}")
    elif current == "set_interval":
        try:
            interval = int(message.text.strip())
            await message.answer(f"Интервал установлен: {interval} секунд.")
        except:
            await message.answer("Введите число.")
    elif current == "set_message":
        message_to_send = message.text.strip()
        await message.answer("Сообщение сохранено.")
    state["expecting"] = None

# Фоновая рассылка
async def start_sending():
    global sending_messages
    sending_messages = True
    while sending_messages:
        for chat_id in chat_ids:
            try:
                await client.send_message(chat_id, message_to_send)
            except Exception as e:
                logging.warning(f"Ошибка отправки в чат {chat_id}: {e}")
        await asyncio.sleep(interval)

# Основной запуск
async def main():
    await client.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
