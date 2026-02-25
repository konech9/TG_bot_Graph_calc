import telebot
import os
from dotenv import load_dotenv
from telebot import types
from telebot.types import InputMediaPhoto
import re
import warnings
import numpy as np
from src.graph.graph import parse, validate, dichotomy, graph as build_graph
import src.graph.graph as graph_module

# пути сохранения картинок для юзеров
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPHS_DIR = os.path.join(BASE_DIR, "src", "pictures", "users")

# чтобы не было лишних "<string>:1: RuntimeWarning: invalid value encountered in sqrt"
np.seterr(all='ignore')
warnings.filterwarnings('ignore')

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

'''
Макс/Мин в деле! Основные функции подтягиваются из graph.py, правда есть пара
костылей с переменной c например, которая нужна для проверок
'''

@bot.message_handler(func=lambda m: m.text == "📊 Построить график")
def ask_function(message):
    bot.send_message(message.chat.id, "[ƒ] Введите функцию f(x) = ")
    bot.register_next_step_handler(message, ask_a)

def ask_a(message):
    func_raw = message.text
    if not validate(func_raw):
        bot.send_message(message.chat.id, "❌ Синтаксическая ошибка! Попробуйте еще раз")
        bot.register_next_step_handler(message, ask_a)
        return

    func = parse(func_raw)
    bot.send_message(message.chat.id, "[ƒ] Введите начало отрезка a = ")
    bot.register_next_step_handler(message, ask_b, func)

def ask_b(message, func):
    try:
        a = float(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Вводите число! Попробуйте еще раз")
        bot.register_next_step_handler(message, ask_b, func)
        return

    bot.send_message(message.chat.id, "[ƒ] Введите конец отрезка b = ")
    bot.register_next_step_handler(message, calculate, func, a)

def calculate(message, func, a):
    try:
        b = float(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Вводите число! Попробуйте еще раз")
        bot.register_next_step_handler(message, calculate, func, a)
        return

    graph_module.func = func

    result_text = dichotomy(a, b)
    c = graph_module.c

    PATH = build_graph(message.from_user.id, func, a, b, GRAPHS_DIR)

    if PATH:
        with open(PATH, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption = f'📊 {result_text}')
    else:
        bot.send_message(message.chat.id, result_text)

if __name__ == "__main__":
    bot.polling()
