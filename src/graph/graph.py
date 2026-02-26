import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import re
import os
import warnings


# Удобный синтаксис
def parse(expr):
    # степень: ** <=> ^
    expr = expr.replace('^', '**')

    # очевидно X <=> x
    expr = expr.replace('X', 'x')

    # умножение через пробел или без: 2x <=> 2*x
    expr = re.sub(r'(\d)(x)', r'\1*\2', expr)
    expr = re.sub(r'(\d)(sin|cos|tan|exp|log|sqrt|abs)', r'\1*\2', expr)

    # то же самое для скобок
    expr = re.sub(r'(\d)\(', r'\1*(', expr)

    # натуральный логарифм: ln <=> log
    expr = expr.replace('ln(', 'log(')

    return expr


# Словарь
def function(x):
    try:
        dict = {
            'x': x,
            'sin': np.sin,
            'cos': np.cos,
            'tan': np.tan,
            'exp': np.exp,
            'log': np.log,
            'sqrt': np.sqrt,
            'abs': np.abs,
            'pi': np.pi,
            'e': np.e,
            'X': x
        }
        return eval(func, dict)
    except:
        return np.nan


# Проверка функции на работоспособность
def validate(function):
    try:
        dict = {
            'x': 1.0,
            'sin': np.sin,
            'cos': np.cos,
            'tan': np.tan,
            'exp': np.exp,
            'log': np.log,
            'sqrt': np.sqrt,
            'abs': np.abs,
            'pi': np.pi,
            'e': np.e,
            'X': 1.0
        }
        result = eval(parse(function), dict)
        if not isinstance(result, (int, float, np.floating)) or ('x' not in str(parse(function)).lower()):
            return False
        return True
    except:
        return False


'''
Дихтомия, принимает на вход функцию и a, b
a, b - границы отрезка
'''

# ДИХОТОМИЯ МАКСИМУМ

def dichotomy_max(a, b):
    eps = 1e-6  # эпсилон - он же шаг
    r = eps / 2  # отступы от середины отрезка
    global c  # ввел глобальную переменную, чтобы потом ее использовать

    if a > b:
        c = None
        return f'❌ Ошибка: интервал задан некорректно.'

    if a == b:
        c = None
        return f'❌ Ошибка: интервал задан двумя совподающими точками.'

    if np.isnan(function(a)) and np.isnan(function(b)):
        c = None
        return f'❌ Ошибка: функция не определена на отрезке ({a}; {b})'

    while abs(b - a) > eps:  # оценка отрезков, пока их длина не станет меньше шага
        c = (a + b) / 2

        # сравним значения функций по разные концы отрезка:

        if function(c - r) > function(c + r):
            b = c
        else:
            a = c
    # вывод данных
    if np.isnan(function(c)):
        c = None
        return f'❌ Ошибка: функция не определена на отрезке ({a}; {b})'

    # print('> Найден максимум функции: ')
    # округление сделано до 4 цифр после запятой для большего удобства
    return f'f(x_max) = {round(function(c), 4)}, x_max = {round(c, 4)}'

# ДИХОТОМИЯ МИНИМУМ

def dichotomy_min(a, b):
    eps = 1e-6  # эпсилон - он же шаг
    r = eps / 2  # отступы от середины отрезка
    global c  # ввел глобальную переменную, чтобы потом ее использовать

    if a > b:
        c = None
        return f'❌ Ошибка: интервал задан некорректно.'

    if a == b:
        c = None
        return f'❌ Ошибка: интервал задан двумя совподающими точками.'

    if np.isnan(function(a)) and np.isnan(function(b)):
        c = None
        return f'❌ Ошибка: функция не определена на отрезке ({a}; {b})'

    while abs(b - a) > eps:  # оценка отрезков, пока их длина не станет меньше шага
        c = (a + b) / 2

        # сравним значения функций по разные концы отрезка:

        if function(c - r) < function(c + r):
            b = c
        else:
            a = c
    # вывод данных
    if np.isnan(function(c)):
        c = None
        return f'Ошибка: функция не определена на отрезке ({a}; {b})'

    # print('> Найден максимум функции: ')
    # округление сделано до 4 цифр после запятой для большего удобства
    return f'f(x_min) = {round(function(c), 4)}, x_min = {round(c, 4)}'



'''
Отображение графика на оси:

    * красным - основной график;
    * синим - полученный максимум на отрезке путем дихтомии;

Расстояние между действительным максимумом красного
и пересечением синих пунктиров - есть погрешность
'''

# i - то, с чем будет сохраняться файл, с каким префиксом, нужно по айди пользователя или по его тегу

def graph(i, func, a, b, save_dir='./imgs'):
    if c == None:
        print(f'> График не был построен.')
    else:
        x = np.linspace(a, b, 1000)
        y = function(x)

        plt.axhline(y=function(c), color='blue', linestyle='--')
        plt.axvline(x=c, color='blue', linestyle='--')
        plt.plot(x, y, label='f(x)', color='red', linestyle='solid')
        plt.title('График f(x)')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.grid(True)

        # в случае если папки не будет, эта штука создаст папку сама с назв. imgs
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, f'{i}.png')
        plt.savefig(path)
        plt.close()
        return path

def simple_graph(i, func, save_dir='./imgs'):

    x = np.linspace(-20, 20, 1000)
    y = function(x)

    plt.plot(x, y, label='f(x)', color='red', linestyle='solid')
    plt.title('График f(x)')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.grid(True)

    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, f'{i}.png')
    plt.savefig(path)
    plt.close()
    return path

# i = 123
#
# func = parse(input('> Введите функцию f(x) = '))
# if not validate(func):
#     print('Синтаксическая ошибка!')
# else:
#     a = float(input('   Введите начало отрезка: '))
#     b = float(input('   Введите конец отрезка: '))
#     print(dichotomy(a, b))
#     graph(i, func, a, b)
