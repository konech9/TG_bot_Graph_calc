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
from logger import logger
import json

#===УСЛОВНЫЙ SETUP======================================================================================================

# Пути сохранения картинок для юзеров
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPHS_DIR = os.path.join(BASE_DIR, "src", "pictures", "users")

# Создание необходимых папок
os.makedirs(GRAPHS_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "src", "pictures", "examples"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

# Чтобы не было лишних "<string>:1: RuntimeWarning: invalid value encountered in sqrt"
np.seterr(all='ignore')
warnings.filterwarnings('ignore')

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Директория для картинок
pictures_dir = os.path.dirname(os.path.abspath(__file__))

#===ДАННЫЕ ПОЛЬЗОВАТЕЛЯ=================================================================================================

# Словарик для работы с данными, вводимыми пользователем, туда записывается a, b и функция, в случае чего перезаписываются
user_data = {}

# Настройки пользователя, структура: {chat_id: {'default_a': -20, 'default_b': 10}}
SETTINGS_FILE = os.path.join(BASE_DIR, "user_settings.json")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_settings_file():
    with open(SETTINGS_FILE, "w") as f:
        json.dump(user_settings, f, indent=4)

# Загружаем настройки при запуске
user_settings = load_settings()

# Стартовые значения диапазонов для построения графиков
DEFAULT_A = -20
DEFAULT_B = 20

# Максимальная длина отрезка
MAX_INTERVAL = 1e4

#===ОСНОВНЫЕ ФУНКЦИИ + МЕНЮ С КНОПКАМИ==================================================================================

#1===ОТМЕНА ДЕЙСТВИЯ====================================================================================================
CANCEL_BUTTONS = [
    "🚪 На главную", "📊 Построить график", "ℹ️ Информация",
    "↕️ Найти Макс/Мин", "⚙️ Настройки",
    ]

def is_cancelled(message):
    return message.text in CANCEL_BUTTONS

#2===ОСНОВНОЕ МЕНЮ, НАСТРОЙКА ПУНКТОВ===================================================================================
def menu():
    actions = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actions.row(types.KeyboardButton("↕️ Найти Макс/Мин"), types.KeyboardButton("📊 Построить график"))
    actions.row(types.KeyboardButton("ℹ️ Информация"), types.KeyboardButton("⚙️ Настройки"))
    actions.row(types.KeyboardButton("🚪 На главную"))
    return actions

#3===ДОП МЕНЮ ДЛЯ ДИХОТОМИИ=============================================================================================
def menu_graph():
    actions = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actions.row(types.KeyboardButton("⬆️ Максимум"), types.KeyboardButton("⬇️ Минимум"))
    actions.row(types.KeyboardButton("🚪 На главную"))
    return actions

def menu_interval():
    actions = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actions.row(types.KeyboardButton("📐 Ввести отрезок"), types.KeyboardButton("✍️ Использовать текущий"))
    actions.row(types.KeyboardButton("🚪 На главную"))
    return actions

#4===СТАРТ, ВЫКИДЫВАЕТ ПАРУ ФОТО========================================================================================
def send_picture_start(message):
    try:
        photo_path = os.path.join(pictures_dir, "src", "pictures", "DICHOTOMY.png")
        with open(photo_path, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption = f"👋 Приветствую вас, {message.from_user.first_name}, в <b>GraphBOT!</b>\n\n"
                                                            f"Рекомендуем ознакомиться с синтаксисом ввода функции в пункте "
                                                            f"ℹ️ Информация", parse_mode = 'HTML')
    except Exception as e:
        logger.error('Fatal error, command Start: ', e)

#5===ПРОМЕЖУТОЧНОЕ МЕНЮ=================================================================================================

def menu_exit():
    actions = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actions.row(types.KeyboardButton("🚪 На главную"))
    return  actions


#===ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ=============================================================================================

def get_default_range(chat_id):
    chat_id = str(chat_id)
    settings = user_settings.get(chat_id, {})
    a = settings.get('default_a', DEFAULT_A)
    b = settings.get('default_b', DEFAULT_B)
    return a, b

#===ПУНКТ МЕНЮ "ИНФОРМАЦИЯ"=============================================================================================

'''
Тут внимательно! отправка настроена так, что отправляет вообще все картинки из папки (конкретным форматом, указанным
в функции), поэтому изображения можно сменить, или добавить больше.
сначала бросает все файлы в список examples_dir, а потом проверяет, что из этого картинка (по формату),
затем кидает нужные файлы в еще один список и делает подпись для первого изображения.
'''

def send_picture_examples(message):
    try:
        examples_dir = os.path.join(pictures_dir, "src", "pictures", "examples")
        files = [f for f in os.listdir(examples_dir) if f.endswith((".png", ".jpg", ".jpeg"))]
        media = [InputMediaPhoto(open(os.path.join(examples_dir, f), "rb")) for f in files]
        media[0] = InputMediaPhoto(
            open(os.path.join(examples_dir, files[0]), "rb"),
            caption="🤖 <b>GraphBOT</b> умеет <i>строить графики</i>, а также <i>находить "
                    "минимум и максимум функции</i> на выбранном интервале!\n\n"
                    "✍️ Примеры работы бота выше.\n\n"
                    "<b>📖 Синтаксис:</b>\n\n"
                    "<b>Переменная:</b>\n"
                    "<code>x</code> или <code>X</code>\n\n"
                    "<b>Операторы:</b>\n"
                    "<code>+</code> - сложение\n"
                    "<code>-</code> - вычитание\n"
                    "<code>*</code> или <i>напр:</i> <code>2x</code>  - умножение\n"
                    "<code>/</code> - деление\n"
                    "<code>^</code> или <code>**</code> - степень\n\n"
                    "<b>Функции:</b>\n"
                    "<code>sin(x)</code> - синус\n"
                    "<code>cos(x)</code> - косинус\n"
                    "<code>tan(x)</code> - тангенс\n"
                    "<code>exp(x)</code> - экспонента\n"
                    "<code>logN(x)</code> - логарифм по основанию N\n"
                    "<code>ln(x)</code> - натуральный логарифм\n"
                    "<code>sqrt(x)</code> - квадратный корень\n"
                    "<code>abs(x)</code> или <code>|x|</code> - модуль\n\n"
                    "<b>Константы:</b>\n"
                    "<code>pi</code>  число <i>π ≈ 3.14159</i>\n"
                    "<code>e</code>   число <i>e ≈ 2.71828</i>\n\n"
                    "<b>Примеры:</b>\n"
                    "<code>sin(x) + cos(x)</code>\n"
                    "<code>x^2 + 2x + 1</code>\n"
                    "<code>sqrt(x) + ln(x)</code>\n"
                    "<code>2sin(x)</code>\n\n"
                    "🤓 <b>Создатель бота (📲 Обратная связь):</b> <b><i><a href='https://t.me/Cnstrct13'>>onemoretime</a></i></b> \n"
                    "<b><i><a href='https://t.me/pritonoflizzaopium'>-TGC</a></i></b>",
            parse_mode="HTML"
        )
        bot.send_media_group(message.chat.id, media)
    except Exception as e:
        logger.error('Fatal error, command Information: ', e)

#===ВЫХОД НА ГЛАВНУЮ====================================================================================================
@bot.message_handler(func=lambda m: m.text == "🚪 На главную")
def main_tab(message):
    send_picture_start(message)
    bot.send_message(message.chat.id, "🔎 С чего начнем?", reply_markup=menu())
    # Везде, где бот удаляет сообщение, это он подчищает за пользователем, удаляя ненужные данные из переписки
    bot.delete_message(message.chat.id, message.message_id)

#===СТАРТ, ВЫКИДЫВАЕТ ПАРУ ФОТО=========================================================================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    send_picture_start(message)
    bot.send_message(message.chat.id, "🔎 С чего начнем?", reply_markup=menu())
    bot.delete_message(message.chat.id, message.message_id)
    logger.info(f'Запуск бота | id: {message.from_user.id} | '
                f'username: @{message.from_user.username} | '
                f'имя: {message.from_user.first_name} {message.from_user.last_name} |')

#===ПУНКТ МЕНЮ "ИНФОРМАЦИЯ"=============================================================================================
@bot.message_handler(func=lambda m: m.text == "ℹ️ Информация")
def search(message):
    send_picture_examples(message)
    bot.delete_message(message.chat.id, message.message_id)

#===НАСТРОЙКИ===========================================================================================================

@bot.message_handler(func = lambda m: m.text == "⚙️ Настройки")
def settings(message):
    a, b = get_default_range(message.chat.id)
    bot.send_message(message.chat.id,
                     f'⚙️ <b>Настройки</b> \n \n'
                     f'<i>Текущий диапазон для построения графика: </i>\n'
                     f'<code>a = {a}, b = {b}</code> \n \n'
                     f'При вводе нового диапазона в формате: <code>a b</code> текущий заменится; \n'
                     f'<i>Например:</i> <code>-20 20</code> \n',
                     parse_mode = 'HTML', reply_markup=menu_exit())
    bot.register_next_step_handler(message, save_settings)

def save_settings(message):
    if is_cancelled(message):
        main_tab(message)
        return
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError
        a, b = float(parts[0]), float(parts[1])
        if b <= a:
            raise ValueError
        if b - a > MAX_INTERVAL:
            bot.send_message(message.chat.id,
                             f"❌ <b>Слишком большой диапазон!</b> Максимум: {MAX_INTERVAL}\nПопробуйте еще раз",
                             parse_mode='HTML')
            bot.register_next_step_handler(message, save_settings)
            return

        # Сохранение в json файл информации о пользователе
        chat_id = str(message.chat.id)

        user_settings[chat_id] = {
            'default_a': a,
            'default_b': b
        }

        save_settings_file()

        bot.send_message(message.chat.id,
                         f"✅ <b>Диапазон обновлён:</b> <code>[{a}; {b}]</code>",
                         parse_mode='HTML',
                         reply_markup=menu())
        return  # ← явный выход, чтобы не проваливаться в except

    except ValueError:
        bot.send_message(message.chat.id,
                         "❌ <b>Неверный формат!</b> Введите два числа через пробел \n <i>Например:</i> <code>-20 20</code>",
                         parse_mode='HTML')
        bot.register_next_step_handler(message, save_settings)


#===САМЫЙ ЖИРНЫЙ БЛОК ДЛЯ ДИХОТОМИИ=====================================================================================

@bot.message_handler(func=lambda m: m.text == "↕️ Найти Макс/Мин")
def ask_function(message):
    bot.send_message(message.chat.id, "<i><b>[ƒ]</b></i> Введите функцию <i>f(x) = </i>", parse_mode='HTML', reply_markup = menu_exit())
    bot.register_next_step_handler(message, ask_a)

def ask_a(message):
    if is_cancelled(message):
        main_tab(message)
        return
    func_raw = message.text
    if not validate(func_raw):
        bot.send_message(message.chat.id, "❌ <b>Синтаксическая ошибка!</b> Попробуйте еще раз", parse_mode='HTML')
        logger.error(f'Ошибка при построении | id: {message.from_user.id} | '
                     f'username: @{message.from_user.username} | '
                     f'f(x) = {func_raw} ')
        bot.register_next_step_handler(message, ask_a)
        bot.delete_message(message.chat.id, message.message_id)
        return

    func = parse(func_raw)
    user_data[message.chat.id] = {'func': func, 'func_raw': func_raw}

    # сохраняет функцию и спрашивает отрезок
    a, b = get_default_range(message.chat.id)
    bot.send_message(message.chat.id,
                     f"📐 Выберите отрезок:\n"
                     f"Текущий: <code>[{a}; {b}]</code>",
                     parse_mode='HTML',
                     reply_markup=menu_interval())
    bot.register_next_step_handler(message, handle_interval_choice_dichotomy)

# Обработка выбора отрезка
def handle_interval_choice_dichotomy(message):
    data = user_data.get(message.chat.id, {})
    func = data.get('func')

    if message.text == "✍️ Использовать текущий":
        a, b = get_default_range(message.chat.id)
        user_data[message.chat.id].update({'a': a, 'b': b})
        graph_module.func = func
        bot.send_message(message.chat.id, "✍️ Что ищем?", reply_markup=menu_graph())

    elif message.text == "📐 Ввести отрезок":
        # [ИЗМЕНЕНО] просим оба числа в одну строку
        bot.send_message(message.chat.id,
                         "<i><b>[ƒ]</b></i> Введите отрезок в формате <code>a b</code>\n"
                         "<i>Например:</i> <code>-20 20</code>",
                         parse_mode='HTML', reply_markup=menu_exit())
        bot.register_next_step_handler(message, calculate, func)

    elif is_cancelled(message):
        main_tab(message)

    else:
        bot.send_message(message.chat.id, "❌ Используйте кнопки меню")
        bot.register_next_step_handler(message, handle_interval_choice_dichotomy)

def calculate(message, func):
    if is_cancelled(message):
        main_tab(message)
        return
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError
        a, b = float(parts[0]), float(parts[1])
    except ValueError:
        bot.send_message(message.chat.id,
                         "❌ <b>Неверный формат!</b> Введите два числа через пробел\n"
                         "<i>Например:</i> <code>-20 20</code>",
                         parse_mode='HTML')
        bot.register_next_step_handler(message, calculate, func)
        return

    if b - a > MAX_INTERVAL:
        bot.send_message(message.chat.id,
                         f"❌ <b>Слишком большой отрезок!</b> Максимальная длина: {MAX_INTERVAL}",
                         parse_mode='HTML')
        bot.register_next_step_handler(message, calculate, func)
        return

    user_data[message.chat.id] = {'func': func, 'a': a, 'b': b}
    graph_module.func = func
    bot.send_message(message.chat.id, "✍️ Что ищем?", reply_markup=menu_graph())

# Для кнопки МАКСИМУМ
@bot.message_handler(func=lambda m: m.text == "⬆️ Максимум")
def handle_max(message):
    data = user_data.get(message.chat.id)
    # Проверка на всякий, а вдруг пользователь решит ввести сообщение до ввода данных
    if not data:
        bot.send_message(message.chat.id, "❌ <b>Ошибка!</b> Введите функцию и отрезок", parse_mode = 'HTML')
        bot.delete_message(message.chat.id, message.message_id)
        return

    graph_module.func = data['func']
    result_text = dichotomy_max(data['a'], data['b'])
    # Смотрит сохраненный файл, если графика нет, то и изображения тоже, значит и смотреть нечего, тогда просто выводим рез. Дихотомии
    PATH = build_graph(message.from_user.id, data['func'], data['a'], data['b'], GRAPHS_DIR)

    # Лог для построения графика
    logger.info(f'График (максимум) | id: {message.from_user.id} | username: @{message.from_user.username} | '
                f'f(x) = {data['func']} | отрезок: [{data['a']}]; [{data['b']}] | результат: {result_text}')

    if PATH:
        with open(PATH, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=f'📊 <b><code>{result_text}</code></b>', parse_mode = 'HTML')
    else:
        bot.send_message(message.chat.id, result_text)

    # Выходим на базовый функционал меню
    bot.send_message(message.chat.id, "🔎 Чем займемся теперь?", reply_markup=menu())

# Все то же самое для МИНИМУМА
@bot.message_handler(func=lambda m: m.text == "⬇️ Минимум")
def handle_min(message):
    data = user_data.get(message.chat.id)
    if not data:
        bot.send_message(message.chat.id, "❌ <b>Ошибка!</b> Введите функцию и отрезок", parse_mode = 'HTML')
        bot.delete_message(message.chat.id, message.message_id)
        return

    graph_module.func = data['func']
    result_text = dichotomy_min(data['a'], data['b'])
    PATH = build_graph(message.from_user.id, data['func'], data['a'], data['b'], GRAPHS_DIR)

    # Лог для построения графика
    logger.info(f'График (минимум) | id: {message.from_user.id} | username: @{message.from_user.username} | '
                f'f(x) = {data['func']} | отрезок: [{data['a']}]; [{data['b']}] | результат: {result_text}')

    if PATH:
        with open(PATH, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=f'📊 <b><code>{result_text}</code></b>', parse_mode = 'HTML')
    else:
        bot.send_message(message.chat.id, result_text)

    # Выходим на базовый функционал меню
    bot.send_message(message.chat.id, "🔎 Чем займемся теперь?", reply_markup=menu())

#===ПОСТРОЕНИЕ ГРАФИКА==================================================================================================
@bot.message_handler(func=lambda m: m.text == "📊 Построить график")
def ask_simple_function(message):
    bot.send_message(message.chat.id, "<i><b>[ƒ]</b></i> Введите функцию <i>f(x) = </i>", parse_mode='HTML', reply_markup=menu_exit())
    bot.register_next_step_handler(message, get_simple_function)

def get_simple_function(message):
    if is_cancelled(message):
        main_tab(message)
        return

    func_raw = message.text
    if not validate(func_raw):
        bot.send_message(message.chat.id, "❌ <b>Синтаксическая ошибка!</b> Попробуйте еще раз", parse_mode='HTML')
        logger.error(f'Ошибка при построении | id: {message.from_user.id} | '
                     f'username: @{message.from_user.username} | '
                     f'f(x) = {func_raw}')
        bot.register_next_step_handler(message, get_simple_function)
        bot.delete_message(message.chat.id, message.message_id)
        return

    func = parse(func_raw)

    # сохраняем функцию и предлагаем выбрать диапазон
    user_data[message.chat.id] = {'func': func, 'func_raw': func_raw}
    a, b = get_default_range(message.chat.id)
    bot.send_message(message.chat.id,
                     f"📐 Выберите диапазон:\n"
                     f"Текущий: <code>[{a}; {b}]</code>",
                     parse_mode='HTML',
                     reply_markup=menu_interval())

@bot.message_handler(func=lambda m: m.text == "✍️ Использовать текущий")
def use_default_interval(message):
    data = user_data.get(message.chat.id)
    if not data or 'func' not in data:
        bot.send_message(message.chat.id, "❌ <b>Ошибка!</b> Сначала введите функцию", parse_mode='HTML')
        return

    a, b = get_default_range(message.chat.id)
    build_simple_graph(message, data['func'], data['func_raw'], a, b)

@bot.message_handler(func=lambda m: m.text == "📐 Ввести отрезок")
def ask_simple_a(message):
    data = user_data.get(message.chat.id)
    if not data or 'func' not in data:
        bot.send_message(message.chat.id, "❌ <b>Ошибка!</b> Сначала введите функцию", parse_mode='HTML')
        return

    bot.send_message(message.chat.id,
                     "<i><b>[ƒ]</b></i> Введите отрезок в формате <code>a b</code>\n"
                     "<i>Например:</i> <code>-20 20</code>",
                     parse_mode='HTML', reply_markup=menu_exit())
    bot.register_next_step_handler(message, get_simple_b)

def get_simple_b(message):
    if is_cancelled(message):
        main_tab(message)
        return
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError
        a, b = float(parts[0]), float(parts[1])
    except ValueError:
        bot.send_message(message.chat.id,
                         "❌ <b>Неверный формат!</b> Введите два числа через пробел\n"
                         "<i>Например:</i> <code>-20 20</code>",
                         parse_mode='HTML')
        bot.register_next_step_handler(message, get_simple_b)
        return

    if b - a > MAX_INTERVAL:
        bot.send_message(message.chat.id,
                         f"❌ <b>Слишком большой отрезок!</b> Максимальная длина: {MAX_INTERVAL}",
                         parse_mode='HTML')
        bot.register_next_step_handler(message, get_simple_b)
        return

    data = user_data.get(message.chat.id, {})
    build_simple_graph(message, data.get('func'), data.get('func_raw'), a, b)

def build_simple_graph(message, func, func_raw, a, b):
    graph_module.func = func
    PATH = simple_graph(message.from_user.id, func, a, b, GRAPHS_DIR)

    logger.info(f'График | id: {message.from_user.id} | username: @{message.from_user.username} | '
                f'f(x) = {func} | отрезок: [{a}; {b}]')

    if PATH:
        with open(PATH, "rb") as photo:
            bot.send_photo(message.chat.id, photo,
                           caption=f'<b>f(x) = <code>{func_raw}</code></b>\n<i>Отрезок: [{a}; {b}]</i>',
                           parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, '❌ График не был построен')

    bot.send_message(message.chat.id, "🔎 Чем займемся теперь?", reply_markup=menu())

#=======================================================================================================================

if __name__ == "__main__":
    bot.polling()
