import telebot
import os
from dotenv import load_dotenv
from telebot import types
from telebot.types import InputMediaPhoto
import warnings
import numpy as np
from src.graph.graph import parse, validate, dichotomy_max, dichotomy_min, graph as build_graph, simple_graph, parameter_graph
import src.graph.graph as graph_module
from logger import logger
import json
from messages.bot_syntax_info import SYNTAX_INFO
from src.bot.actions import menu, menu_graph, menu_interval, menu_exit, parameter_menu, is_cancelled

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

if not TOKEN:
    raise ValueError("BOT_TOKEN not set")

bot = telebot.TeleBot(TOKEN)


# Директория для картинок
pictures_dir = os.path.dirname(os.path.abspath(__file__))

#===ДАННЫЕ ПОЛЬЗОВАТЕЛЯ=================================================================================================

'''
Единый словарь для всех данных пользователя, структура:
{
    "[chat_id]": {
        "default_a": [DEFAULT_A],       <= сохраняется в json (постоянное)
        "default_b": [DEFAULT_B],        <= сохраняется в json (постоянное)
        "func": "[func]",       <= только в памяти (сессионное)
        "func_raw": "[func_raw]",   <= только в памяти (сессионное)
        "a": [a],               <= только в памяти (сессионное)
        "b": [b]                 <= только в памяти (сессионное)
    }
}
'''

SETTINGS_FILE = os.path.join(BASE_DIR, "user_settings.json")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

# сохранение данных в .json файл
def save_settings_file():
    # сохраняем только постоянные настройки, без сессионных данных, перезаписываем словарь
    to_save = {
        # из данных пользователя берем только def_a и def_b, остальное сессионные данные
        uid: {k: v for k, v in data.items() if k in ('default_a', 'default_b')}
        # перебор всех пользователей, поиск по айди
        for uid, data in user_settings.items()
    }
    with open(SETTINGS_FILE, "w") as f:
        # записываем новый словарь в файл за место старого
        json.dump(to_save, f, indent=4)

# Загружаем настройки при запуске
user_settings = load_settings()

# Стартовые значения диапазонов для построения графиков
DEFAULT_A = -20
DEFAULT_B = 20

# Максимальная длина отрезка
MAX_INTERVAL = 1e4

#===ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ=============================================================================================

def get_default_range(chat_id):
    chat_id = str(chat_id)
    settings = user_settings.get(chat_id, {})
    a = settings.get('default_a', DEFAULT_A)
    b = settings.get('default_b', DEFAULT_B)
    return a, b

def get_user(chat_id):
    # возвращает данные пользователя, создает запись если нет
    chat_id = str(chat_id)
    if chat_id not in user_settings:
        user_settings[chat_id] = {}
    return user_settings[chat_id]

#===СТАРТ, ВЫКИДЫВАЕТ ПАРУ ФОТО=========================================================================================
def send_picture_start(message):
    try:
        photo_path = os.path.join(pictures_dir, "src", "pictures", "DICHOTOMY.png")
        with open(photo_path, "rb") as photo:
            bot.send_photo(message.chat.id, photo,
                           caption=f"👋 Приветствую вас, {message.from_user.first_name}, в <b>GraphBOT!</b>\n\n"
                                   f"Рекомендуем ознакомиться с синтаксисом ввода функции в пункте "
                                   f"ℹ️ Информация", parse_mode='HTML')
    except Exception as e:
        logger.error(f'Fatal error, command Start: {e}')

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
            caption=SYNTAX_INFO,
            parse_mode="HTML"
        )
        bot.send_media_group(message.chat.id, media)
    except Exception as e:
        logger.error(f'Fatal error, command Information: {e}')

#===ВЫХОД НА ГЛАВНУЮ====================================================================================================
@bot.message_handler(func=lambda m: m.text == "🚪 На главную")
def main_tab(message):
    send_picture_start(message)
    bot.send_message(message.chat.id, "🔎 С чего начнем?", reply_markup=menu())
    # Везде, где бот удаляет сообщение, это он подчищает за пользователем, удаляя ненужные данные из переписки
    bot.delete_message(message.chat.id, message.message_id)

#===ПОМОЩЬ==============================================================================================================

@bot.message_handler(commands=['help'])
def help(message):
    search(message)

#===СТАРТ, ВЫКИДЫВАЕТ ПАРУ ФОТО=========================================================================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    send_picture_start(message)
    bot.send_message(message.chat.id, "🔎 С чего начнем?", reply_markup=menu())
    bot.delete_message(message.chat.id, message.message_id)
    # logger.info(f'Запуск бота | id: {message.from_user.id} | '
    #             f'username: @{message.from_user.username} | '
    #             f'имя: {message.from_user.first_name} {message.from_user.last_name} |')

#===ПУНКТ МЕНЮ "ИНФОРМАЦИЯ"=============================================================================================
@bot.message_handler(func=lambda m: m.text == "ℹ️ Информация")
def search(message):
    send_picture_examples(message)
    bot.delete_message(message.chat.id, message.message_id)

#===НАСТРОЙКИ===========================================================================================================

@bot.message_handler(func=lambda m: m.text == "⚙️ Настройки")
def settings(message):
    a, b = get_default_range(message.chat.id)
    bot.send_message(message.chat.id,
                     f'⚙️ <b>Настройки</b> \n \n'
                     f'<i>Текущий диапазон для построения графика: </i>\n'
                     f'<code>a = {a}, b = {b}</code> \n \n'
                     f'При вводе нового диапазона в формате: <code>a b</code> текущий заменится; \n'
                     f'<i>Например:</i> <code>-20 20</code> \n',
                     parse_mode='HTML', reply_markup=menu_exit())
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

        # сохраняем в единый словарь и пишем в json
        get_user(message.chat.id).update({'default_a': a, 'default_b': b})
        save_settings_file()

        bot.send_message(message.chat.id,
                         f"✅ <b>Диапазон обновлён:</b> <code>[{a}; {b}]</code>",
                         parse_mode='HTML',
                         reply_markup=menu())
        return

    except ValueError:
        bot.send_message(message.chat.id,
                         "❌ <b>Неверный формат!</b> Введите два числа через пробел \n <i>Например:</i> <code>-20 20</code>",
                         parse_mode='HTML')
        bot.register_next_step_handler(message, save_settings)

#===САМЫЙ ЖИРНЫЙ БЛОК ДЛЯ ДИХОТОМИИ=====================================================================================

'''
Дихотомия, все функции берутся из graph.py, затем используются в боте для просчетов
'''

@bot.message_handler(func=lambda m: m.text == "↕️ Найти Макс/Мин")
def ask_function(message):
    bot.send_message(message.chat.id, "<i><b>[ƒ]</b></i> Введите функцию <i>f(x) = </i>", parse_mode='HTML', reply_markup=menu_exit())
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
                     f'f(x) = {func_raw}')
        bot.register_next_step_handler(message, ask_a)
        bot.delete_message(message.chat.id, message.message_id)
        return

    func = parse(func_raw)

    # сохраняем функцию в единый словарь
    get_user(message.chat.id).update({'func': func, 'func_raw': func_raw})

    a, b = get_default_range(message.chat.id)
    bot.send_message(message.chat.id,
                     f"📐 Выберите отрезок:\n"
                     f"Текущий: <code>[{a}; {b}]</code>",
                     parse_mode='HTML',
                     reply_markup=menu_interval())
    bot.register_next_step_handler(message, handle_interval_choice_dichotomy)

# Обработка выбора отрезка для дихотомии
def handle_interval_choice_dichotomy(message):
    data = user_settings.get(str(message.chat.id), {})
    func = data.get('func')

    if message.text == "✍️ Использовать текущий":
        a, b = get_default_range(message.chat.id)
        get_user(message.chat.id).update({'a': a, 'b': b})
        graph_module.func = func
        bot.send_message(message.chat.id, "✍️ Что ищем?", reply_markup=menu_graph())

    elif message.text == "📐 Ввести отрезок":
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

    get_user(message.chat.id).update({'func': func, 'a': a, 'b': b})
    graph_module.func = func
    bot.send_message(message.chat.id, "✍️ Что ищем?", reply_markup=menu_graph())

# Для кнопки МАКСИМУМ
@bot.message_handler(func=lambda m: m.text == "⬆️ Максимум")
def handle_max(message):
    data = user_settings.get(str(message.chat.id))
    # Проверка на всякий, а вдруг пользователь решит ввести сообщение до ввода данных
    if not data or 'func' not in data:
        bot.send_message(message.chat.id, "❌ <b>Ошибка!</b> Введите функцию и отрезок", parse_mode='HTML')
        bot.delete_message(message.chat.id, message.message_id)
        return

    graph_module.func = data['func']
    result_text = dichotomy_max(data['a'], data['b'])
    # Смотрит сохраненный файл, если графика нет, то и изображения тоже, значит и смотреть нечего, тогда просто выводим рез. Дихотомии
    PATH = build_graph(message.from_user.id, data['func'], data['a'], data['b'], GRAPHS_DIR)

    # Лог для построения графика
    logger.info(f'График (максимум) | id: {message.from_user.id} | username: @{message.from_user.username} | '
                f'f(x) = {data["func"]} | отрезок: [{data["a"]}]; [{data["b"]}] | результат: {result_text}')

    if PATH:
        with open(PATH, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=f'📊 <b><code>{result_text}</code></b>', parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, result_text)

    # Выходим на базовый функционал меню
    bot.send_message(message.chat.id, "🔎 Чем займемся теперь?", reply_markup=menu())

# Все то же самое для МИНИМУМА
@bot.message_handler(func=lambda m: m.text == "⬇️ Минимум")
def handle_min(message):
    data = user_settings.get(str(message.chat.id))
    if not data or 'func' not in data:
        bot.send_message(message.chat.id, "❌ <b>Ошибка!</b> Введите функцию и отрезок", parse_mode='HTML')
        bot.delete_message(message.chat.id, message.message_id)
        return

    graph_module.func = data['func']
    result_text = dichotomy_min(data['a'], data['b'])
    PATH = build_graph(message.from_user.id, data['func'], data['a'], data['b'], GRAPHS_DIR)

    # Лог для построения графика
    logger.info(f'График (минимум) | id: {message.from_user.id} | username: @{message.from_user.username} | '
                f'f(x) = {data["func"]} | отрезок: [{data["a"]}]; [{data["b"]}] | результат: {result_text}')

    if PATH:
        with open(PATH, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=f'📊 <b><code>{result_text}</code></b>', parse_mode='HTML')
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
    get_user(message.chat.id).update({'func': func, 'func_raw': func_raw})
    a, b = get_default_range(message.chat.id)
    bot.send_message(message.chat.id,
                     f"📐 Выберите диапазон:\n"
                     f"Текущий: <code>[{a}; {b}]</code>",
                     parse_mode='HTML',
                     reply_markup=menu_interval())

@bot.message_handler(func=lambda m: m.text == "✍️ Использовать текущий")
def use_default_interval(message):
    data = user_settings.get(str(message.chat.id))
    if not data or 'func' not in data:
        bot.send_message(message.chat.id, "❌ <b>Ошибка!</b> Сначала введите функцию", parse_mode='HTML')
        return

    a, b = get_default_range(message.chat.id)
    build_simple_graph(message, data['func'], data['func_raw'], a, b)

@bot.message_handler(func=lambda m: m.text == "📐 Ввести отрезок")
def ask_simple_a(message):
    data = user_settings.get(str(message.chat.id))
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

    data = user_settings.get(str(message.chat.id), {})
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
        logger.error(f'Ошибка при построении | id: {message.from_user.id} | '
                     f'username: @{message.from_user.username} | '
                     f'f(x) = {func_raw}')

    bot.send_message(message.chat.id, "🔎 Чем займемся теперь?", reply_markup=menu())

#===ГРАФИК С ПАРАМЕТРОМ=================================================================================================

@bot.message_handler(func=lambda m: m.text == "📈 График с параметром (WIP)")
def ask_parameter_function(message):
    get_user(message.chat.id)['parameter_functions'] = []  # сброс списка функций

    bot.send_message(message.chat.id, "<b><i>[ƒ]</i></b> Введите функцию <i>f(x, a)</i>", parse_mode='HTML', reply_markup=menu_exit())
    bot.register_next_step_handler(message, get_parameter_function)

def get_parameter_function(message):
    if is_cancelled(message):
        main_tab(message)
        return

    func_raw = message.text
    if not validate(func_raw):
        bot.send_message(message.chat.id, "❌ <b>Синтаксическая ошибка!</b> Попробуйте еще раз", parse_mode='HTML')
        bot.register_next_step_handler(message, get_parameter_function)
        return

    func = parse(func_raw)
    get_user(message.chat.id).update({'current_parameter_func': func, 'current_parameter_func_raw': func_raw})

    functions = user_settings.get(str(message.chat.id), {}).get('parameter_functions', [])
    if not functions:
        # первая функция — спрашиваем отрезок
        a, b = get_default_range(message.chat.id)
        bot.send_message(message.chat.id,
                         f"📐 Выберите диапазон:\n"
                         f"Текущий: <code>[{a}; {b}]</code>",
                         parse_mode='HTML', reply_markup=menu_interval())
        bot.register_next_step_handler(message, get_parameter_interval)
    else:
        # отрезок уже задан — сразу к параметрам
        ask_parameter_values_msg(message, func_raw)

def get_parameter_interval(message):
    if message.text == "✍️ Использовать текущий":
        a, b = get_default_range(message.chat.id)
        get_user(message.chat.id).update({'parameter_a': a, 'parameter_b': b})
        func_raw = user_settings.get(str(message.chat.id), {}).get('current_parameter_func_raw', '')
        ask_parameter_values_msg(message, func_raw)

    elif message.text == "📐 Ввести отрезок":
        bot.send_message(message.chat.id,
                         "<i><b>[ƒ]</b></i> Введите отрезок в формате <code>a b</code>\n"
                         "<i>Например:</i> <code>-20 20</code>",
                         parse_mode='HTML', reply_markup=menu_exit())
        bot.register_next_step_handler(message, get_parameter_interval_manual)

    elif is_cancelled(message):
        main_tab(message)

    else:
        bot.send_message(message.chat.id, "❌ Используйте кнопки меню")
        bot.register_next_step_handler(message, get_parameter_interval)

def get_parameter_interval_manual(message):
    if is_cancelled(message):
        main_tab(message)
        return
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError
        a, b = float(parts[0]), float(parts[1])
        if b - a > MAX_INTERVAL:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id,
                         "❌ <b>Неверный формат!</b> Введите два числа через пробел\n"
                         "<i>Например:</i> <code>-20 20</code>",
                         parse_mode='HTML')
        bot.register_next_step_handler(message, get_parameter_interval_manual)
        return

    get_user(message.chat.id).update({'parameter_a': a, 'parameter_b': b})
    func_raw = user_settings.get(str(message.chat.id), {}).get('current_parameter_func_raw', '')
    ask_parameter_values_msg(message, func_raw)

def ask_parameter_values_msg(message, func_raw):
    if 'a' in func_raw:
        bot.send_message(message.chat.id,
                         f"<code>f(x) = {func_raw}</code>\n\n"
                         f"Введите значения параметра <code>a</code> через пробел:\n"
                         f"<i>Например:</i> <code>0.5 1 2 3</code>",
                         parse_mode='HTML', reply_markup=menu_exit())
        bot.register_next_step_handler(message, get_parameter_values)
    else:
        data = user_settings.get(str(message.chat.id), {})
        func = data.get('current_parameter_func')
        data['parameter_functions'].append({'func': func, 'func_raw': func_raw, 'params': [None]})
        offer_parameter_add_more(message)

def get_parameter_values(message):
    if is_cancelled(message):
        main_tab(message)
        return
    try:
        params = [float(p) for p in message.text.split()]
        if not params:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id,
                         "❌ <b>Неверный формат!</b> Введите числа через пробел\n"
                         "<i>Например:</i> <code>0.5 1 2 3</code>",
                         parse_mode='HTML')
        bot.register_next_step_handler(message, get_parameter_values)
        return

    data = user_settings.get(str(message.chat.id), {})
    func = data.get('current_parameter_func')
    func_raw = data.get('current_parameter_func_raw')
    data['parameter_functions'].append({'func': func, 'func_raw': func_raw, 'params': params})
    offer_parameter_add_more(message)

def offer_parameter_add_more(message):
    data = user_settings.get(str(message.chat.id), {})
    functions = data.get('parameter_functions', [])

    lines = []
    for fn in functions:
        if fn['params'] == [None]:
            lines.append(f"• <code>{fn['func_raw']}</code>")
        else:
            lines.append(f"<code>{fn['func_raw']}</code> при a = {', '.join(str(p) for p in fn['params'])}")

    text = "✅ <b>Добавлено:</b>\n\n" + "\n".join(lines) + "\n\n<i>Что дальше?</i>"
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=parameter_menu())

@bot.message_handler(func=lambda m: m.text == "➕ Добавить функцию")
def add_more_parameter_function(message):
    bot.send_message(message.chat.id, "Введите следующую функцию:", parse_mode='HTML', reply_markup=menu_exit())
    bot.register_next_step_handler(message, get_parameter_function)

@bot.message_handler(func=lambda m: m.text == "📊 Построить")
def build_parameter_graph_handler(message):
    data = user_settings.get(str(message.chat.id), {})
    functions = data.get('parameter_functions', [])
    a = data.get('parameter_a')
    b = data.get('parameter_b')

    if not functions:
        bot.send_message(message.chat.id, "❌ <b>Ошибка!</b> Сначала добавьте функции", parse_mode='HTML')
        return

    PATH = parameter_graph(message.from_user.id, functions, a, b, GRAPHS_DIR)

    lines = []
    for fn in functions:
        if fn['params'] == [None]:
            lines.append(f"<code>{fn['func_raw']}</code>")
        else:
            lines.append(f"<code>{fn['func_raw']}</code>, a = {', '.join(str(p) for p in fn['params'])}")
    caption = "📊 " + "\n".join(lines)

    logger.info(f'Параметрический график | id: {message.from_user.id} | username: @{message.from_user.username} | '
                f'функции: {[fn["func_raw"] for fn in functions]} | отрезок: [{a}; {b}]')

    if PATH:
        with open(PATH, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=caption, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "❌ График не был построен")

    bot.send_message(message.chat.id, "🔎 Чем займемся теперь?", reply_markup=menu())

#=======================================================================================================================

if __name__ == "__main__":
    bot.polling()