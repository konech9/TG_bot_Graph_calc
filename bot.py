import telebot
import os
from dotenv import load_dotenv
from telebot import types
from telebot.types import InputMediaPhoto
import re


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Директория для картинок
pictures_dir = os.path.dirname(os.path.abspath(__file__))

# Cоздаем поля для меню (выбор функций в боте)
def menu():
    actions = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actions.row(types.KeyboardButton("Найти Макс/Мин"), types.KeyboardButton("📊 Построить график"))
    actions.row(types.KeyboardButton("ℹ️ Информация"))
    actions.row(types.KeyboardButton("🚪 На главную"))
    return actions

# Приветственное сообщение с иллюстраицей
def send_picture_start(message):
    photo_path = os.path.join(pictures_dir, "src", "pictures", "DICHOTOMY.png")
    with open(photo_path, "rb") as photo:
        bot.send_photo(message.chat.id, photo, caption = f"👋 Приветствую вас, {message.from_user.first_name}, в GraphBOT!"
                                                         f" Вы можете ознакомиться с функционалом и принципом работы"
                                                         f" или сразу приступить к изучению графиков.")

# Функция отправляет ВСЕ картинки из папки examples для функции INFO, с группировкой (сука сложно реализуется)
def send_picture_examples(message):
    examples_dir = os.path.join(pictures_dir, "src", "pictures", "examples")
    files = [f for f in os.listdir(examples_dir) if f.endswith((".png", ".jpg", ".jpeg"))]
    media = [InputMediaPhoto(open(os.path.join(examples_dir, f), "rb")) for f in files]
    media[0].caption = (f"✍️ GraphBOT умеет строить графики, а также находить"
                        f"минимум и максимум функции на выбранном интервале!"
                        f"Примеры работы бота выше. ")
    bot.send_media_group(message.chat.id, media)

# Выход на главную
@bot.message_handler(func=lambda m: m.text == "🚪 На главную")
def main_tab(message):
    send_picture_start(message)
    bot.send_message(message.chat.id, "🔎 С чего начнем?", reply_markup=menu())
    bot.delete_message(message.chat.id, message.message_id)

# Приветствующее сообщение + вывод действий на экран
@bot.message_handler(commands=['start'])
def send_welcome(message):
    send_picture_start(message)
    bot.send_message(message.chat.id, "🔎 С чего начнем?", reply_markup=menu())
    bot.delete_message(message.chat.id, message.message_id)

# Информация о боте, с фото-примерами
@bot.message_handler(func=lambda m: m.text == "ℹ️ Информация")
def search(message):
    send_picture_examples(message)
    bot.delete_message(message.chat.id, message.message_id)

# Проверка того, как бот принимает инфу
@bot.message_handler(func=lambda m: m.text == "📊 Построить график")
def ask_func(message):
    bot.send_message(message.chat.id, "Введите функцию f(x) = ")
    bot.register_next_step_handler(message, ask_a)
def ask_a(message):
    func = message.text
    bot.send_message(message.chat.id, "Введите начало отрезка a = ")
    bot.register_next_step_handler(message, ask_b, func)
def ask_b(message, func):
    a = message.text
    bot.send_message(message.chat.id, "Введите конец отрезка b = ")
    bot.register_next_step_handler(message, calculate, func, a)
def calculate(message, func, a):
    b = message.text
    print(func, a, b)
    bot.send_message(message.chat.id, f"Считаю для f(x) = {func} на [{a}; {b}]...")

if __name__ == "__main__":
    bot.polling()
