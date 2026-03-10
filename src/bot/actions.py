from telebot import types

#===ОСНОВНЫЕ ФУНКЦИИ + МЕНЮ С КНОПКАМИ==================================================================================

#1===ОТМЕНА ДЕЙСТВИЯ====================================================================================================
CANCEL_BUTTONS = [
    "🚪 На главную", "📊 Построить график", "ℹ️ Информация",
    "↕️ Найти Макс/Мин", "⚙️ Настройки", "/start"
]

def is_cancelled(message):
    return message.text in CANCEL_BUTTONS

#2===ОСНОВНОЕ МЕНЮ, НАСТРОЙКА ПУНКТОВ===================================================================================
def menu():
    actions = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actions.row(types.KeyboardButton("↕️ Найти Макс/Мин"), types.KeyboardButton("📊 Построить график"))
    actions.row(types.KeyboardButton("📈 График с параметром (WIP)"))
    actions.row(types.KeyboardButton("ℹ️ Информация"), types.KeyboardButton("⚙️ Настройки"))
    return actions

#3===ДОП МЕНЮ ДЛЯ ДИХОТОМИИ=============================================================================================
def menu_graph():
    actions = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actions.row(types.KeyboardButton("⬆️ Максимум"), types.KeyboardButton("⬇️ Минимум"))
    actions.row(types.KeyboardButton("🚪 На главную"))
    return actions

#4===МЕНЮ ДЛЯ ВЫБОРА ИНТЕРВАЛА==========================================================================================
def menu_interval():
    actions = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actions.row(types.KeyboardButton("📐 Ввести отрезок"), types.KeyboardButton("✍️ Использовать текущий"))
    actions.row(types.KeyboardButton("🚪 На главную"))
    return actions

#5===ПРОМЕЖУТОЧНОЕ МЕНЮ (только кнопка выхода)==========================================================================
def menu_exit():
    actions = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actions.row(types.KeyboardButton("🚪 На главную"))
    return actions

#6===МЕНЮ ДЛЯ ГРАФИКА С ПАРАМЕТРОМ======================================================================================
def parameter_menu():
    actions = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actions.row(types.KeyboardButton("➕ Добавить функцию"), types.KeyboardButton("📊 Построить"))
    actions.row(types.KeyboardButton("🚪 На главную"))
    return actions
