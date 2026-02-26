import telebot
import os
from dotenv import load_dotenv
from telebot import types
from telebot.types import InputMediaPhoto
import re
import warnings
import numpy as np
from src.graph.graph import parse, validate, dichotomy_max, dichotomy_min, graph as build_graph, simple_graph
import src.graph.graph as graph_module

#===УСЛОВНЫЙ SETUP======================================================================================================

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

#===ОСНОВНЫЕ ФУНКЦИИ + МЕНЮ С КНОПКАМИ==================================================================================

#===ОТМЕНА ДЕЙСТВИЯ=====================================================================================================
CANCEL_BUTTONS = ["🚪 На главную", "📊 Построить график", "ℹ️ Информация", "↕️ Найти Макс/Мин"]
def is_cancelled(message):
    return message.text in CANCEL_BUTTONS

#===ОСНОВНОЕ МЕНЮ, НАСТРОЙКА ПУНКТОВ====================================================================================
def menu():
    actions = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actions.row(types.KeyboardButton("↕️ Найти Макс/Мин"), types.KeyboardButton("📊 Построить график"))
    actions.row(types.KeyboardButton("ℹ️ Информация"))
    actions.row(types.KeyboardButton("🚪 На главную"))
    return actions

#===ДОП МЕНЮ ДЛЯ ДИХОТОМИИ==============================================================================================
def menu_graph():
    actions = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actions.row(types.KeyboardButton("⬆️ Максимум"), types.KeyboardButton("⬇️ Минимум"))
    actions.row(types.KeyboardButton("🚪 На главную"))
    return actions

#===СТАРТ, ВЫКИДЫВАЕТ ПАРУ ФОТО=========================================================================================
def send_picture_start(message):
    photo_path = os.path.join(pictures_dir, "src", "pictures", "DICHOTOMY.png")
    with open(photo_path, "rb") as photo:
        bot.send_photo(message.chat.id, photo, caption = f"👋 Приветствую вас, {message.from_user.first_name}, в GraphBOT!"
                                                         f" Вы можете ознакомиться с функционалом и принципом работы"
                                                         f" или сразу приступить к изучению графиков.")

#===ПУНКТ МЕНЮ "ИНФОРМАЦИЯ"=============================================================================================

'''
Тут внимательно! отправка настроена так, что отправляет вообще все картинки из папки (конкретным форматом, указанным
в функции), поэтому изображения можно сменить, или добавить больше.
'''

def send_picture_examples(message):
    examples_dir = os.path.join(pictures_dir, "src", "pictures", "examples")
    files = [f for f in os.listdir(examples_dir) if f.endswith((".png", ".jpg", ".jpeg"))]
    media = [InputMediaPhoto(open(os.path.join(examples_dir, f), "rb")) for f in files]
    media[0].caption = (f"🤖 GraphBOT умеет строить графики, а также находить"
                        f"минимум и максимум функции на выбранном интервале! \n"
                        f"✍️ Примеры работы бота выше.\n\n"
                        f"Создатель бота: >onemoretime")

    bot.send_media_group(message.chat.id, media)

#===ВЫХОД НА ГЛАВНУЮ====================================================================================================
@bot.message_handler(func=lambda m: m.text == "🚪 На главную")
def main_tab(message):
    send_picture_start(message)
    bot.send_message(message.chat.id, "🔎 С чего начнем?", reply_markup=menu())
    bot.delete_message(message.chat.id, message.message_id)

#===СТАРТ, ВЫКИДЫВАЕТ ПАРУ ФОТО=========================================================================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    send_picture_start(message)
    bot.send_message(message.chat.id, "🔎 С чего начнем?", reply_markup=menu())
    bot.delete_message(message.chat.id, message.message_id)

#===ПУНКТ МЕНЮ "ИНФОРМАЦИЯ"=============================================================================================
@bot.message_handler(func=lambda m: m.text == "ℹ️ Информация")
def search(message):
    send_picture_examples(message)
    bot.delete_message(message.chat.id, message.message_id)

#===САМЫЙ ЖИРНЫЙ БЛОК ДЛЯ ДИХОТОМИИ=====================================================================================

'''
Макс/Мин в деле! Основные функции подтягиваются из graph.py, правда есть пара
костылей с переменной c например, которая нужна для проверок
'''

@bot.message_handler(func=lambda m: m.text == "↕️ Найти Макс/Мин")

def ask_function(message):
    bot.send_message(message.chat.id, "[ƒ] Введите функцию f(x) = ")
    bot.register_next_step_handler(message, ask_a)

def ask_a(message):
    # Выкидывает на главную, если пользователь захочет выйти
    if is_cancelled(message):
        main_tab(message)
        return
    func_raw = message.text
    if not validate(func_raw):
        bot.send_message(message.chat.id, "❌ Синтаксическая ошибка! Попробуйте еще раз")
        bot.register_next_step_handler(message, ask_a)
        bot.delete_message(message.chat.id, message.message_id)
        return

    func = parse(func_raw)
    bot.send_message(message.chat.id, "[ƒ] Введите начало отрезка a = ")
    bot.register_next_step_handler(message, ask_b, func)

def ask_b(message, func):
    # Выкидывает на главную, если пользователь захочет выйти
    if is_cancelled(message):
        main_tab(message)
        return
    try:
        a = float(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Вводите число! Попробуйте еще раз")
        bot.register_next_step_handler(message, ask_b, func)
        bot.delete_message(message.chat.id, message.message_id)
        return

    bot.send_message(message.chat.id, "[ƒ] Введите конец отрезка b = ")
    bot.register_next_step_handler(message, calculate, func, a)

# Словарик для работы с данными, вводимыми пользователем
user_data = {}

def calculate(message, func, a):
    # Выкидывает на главную, если пользователь захочет выйти
    if is_cancelled(message):
        main_tab(message)
        return
    try:
        b = float(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "❌ <b>Вводите число! Попробуйте еще раз</b>", parse_mode = 'HTML')
        bot.register_next_step_handler(message, calculate, func, a)
        bot.delete_message(message.chat.id, message.message_id)
        return

    # сохранение данных после всех проверок!
    user_data[message.chat.id] = {'func': func, 'a': a, 'b': b}
    graph_module.func = func
    # Показываем новую клавиатуру с действиями и по ней работаем.
    bot.send_message(message.chat.id, "✍️ Что ищем?", reply_markup = menu_graph())

# Для кнопки МАКСИМУМ
@bot.message_handler(func=lambda m: m.text == "⬆️ Максимум")
def handle_max(message):
    data = user_data.get(message.chat.id)
    # Проверка на всякий, а вдруг пользователь решит ввести сообщение до ввода данных
    if not data:
        bot.send_message(message.chat.id, "❌ <b>Ошибка! Введите функцию и отрезок</b>", parse_mode = 'HTML')
        bot.delete_message(message.chat.id, message.message_id)
        return

    graph_module.func = data['func']
    result_text = dichotomy_max(data['a'], data['b'])
    c = graph_module.c
    PATH = build_graph(message.from_user.id, data['func'], data['a'], data['b'], GRAPHS_DIR)

    if PATH:
        with open(PATH, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=f'📊 <b><code>{result_text}</code></b>', parse_mode = 'HTML')
    else:
        bot.send_message(message.chat.id, result_text)

    # Выходим на базовый функционал меню
    bot.send_message(message.chat.id, "🔎 Чем займемся теперь?", reply_markup=menu())

# Все то же самое для МИНИМУМ
@bot.message_handler(func=lambda m: m.text == "⬇️ Минимум")
def handle_min(message):
    data = user_data.get(message.chat.id)
    if not data:
        bot.send_message(message.chat.id, "❌ <b>Ошибка! Введите функцию и отрезок</b>", parse_mode = 'HTML')
        bot.delete_message(message.chat.id, message.message_id)
        return

    graph_module.func = data['func']
    result_text = dichotomy_min(data['a'], data['b'])
    c = graph_module.c
    PATH = build_graph(message.from_user.id, data['func'], data['a'], data['b'], GRAPHS_DIR)

    if PATH:
        with open(PATH, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=f'📊 <b><code>{result_text}</code></b>', parse_mode = 'HTML')
    else:
        bot.send_message(message.chat.id, result_text)

    # Выходим на базовый функционал меню
    bot.send_message(message.chat.id, "🔎 Чем займемся теперь?", reply_markup=menu())

#===ПОСТРОЕНИЕ ГРАФИКА==================================================================================================
@bot.message_handler(func=lambda m: m.text == "📊 Построить график")
def ask_simple_function(messege):
    bot.send_message(messege.chat.id, "[ƒ] Введите функцию f(x) = ")
    bot.register_next_step_handler(messege, get_simple_function)

def get_simple_function(message):
    if is_cancelled(message):
        main_tab(message)
        return

    func_raw = message.text
    if not validate(func_raw):
        bot.send_message(message.chat.id, "❌ Синтаксическая ошибка! Попробуйте еще раз")
        bot.register_next_step_handler(message, get_simple_function)
        bot.delete_message(message.chat.id, message.message_id)
        return

    func = parse(func_raw)
    graph_module.func = func
    PATH = simple_graph(message.from_user.id, func, GRAPHS_DIR)
    if PATH:
        with open(PATH, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption = f'<b>f(x) = <code>{func_raw}</code></b>', parse_mode="HTML")

    bot.send_message(message.chat.id, "🔎 Чем займемся теперь?", reply_markup=menu())
#=======================================================================================================================

if __name__ == "__main__":
    bot.polling()
