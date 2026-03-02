import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import re
import os

# создает нормальную функцию логарифма, а не это дерьмо в numpy, которое не понимает основания
def make_logn(base):
    return lambda x: np.log(x) / np.log(base)

# объединенный словарь + фиксы для логарифма
def get_dict(x, expression=''):
    bases = re.findall(r'log(\d+\.?\d*)', expression)
    # доп функции для логарифма с учетом неизвестных для программы оснований
    extra = {f'log{i}': make_logn(float(i)) for i in bases}
    return {
        'x': x, 'X': x,
        'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
        'exp': np.exp, 'log': np.log, 'sqrt': np.sqrt,
        'abs': np.abs, 'pi': np.pi, 'e': np.e,
        **extra
    }

# Удобный синтаксис
def parse(expr):
    # исправление заглавных букв
    for fn in ['sin', 'cos', 'tan', 'exp', 'sqrt', 'abs', 'ln', 'log']:
        expr = re.sub(fn, fn, expr, flags=re.IGNORECASE)
    # исправление степени
    expr = expr.replace('^', '**')
    # исправление аргумента
    expr = expr.replace('X', 'x')
    # исправление запятой на точку
    expr = expr.replace(',', '.')
    # исправление для модуля
    expr = re.sub(r'\|([^|]+)\|', r'abs(\1)', expr)
    # исправление для натурального логарифма (в numpy log без основания то же, что и ln)
    expr = expr.replace('ln(', 'log(')

    # заменяем logn(x) на LOGN_n_(x)
    expr = re.sub(r'log(\d+\.?\d*)\(', r'LOGN_\1_(', expr)
    # фикс для работы умножения на число перед логарифмом
    expr = re.sub(r'(\d\.?\d*)(LOGN_)', r'\1*\2', expr)
    # умножение
    expr = re.sub(r'(\d)(x)', r'\1*\2', expr)
    expr = re.sub(r'(\d\.?\d*)(sin|cos|tan|exp|log|sqrt|abs)', r'\1*\2', expr)
    expr = re.sub(r'(\d)\(', r'\1*(', expr)

    # возвращаем logn(x) (чтобы не было конфликтов с умножениями)
    expr = re.sub(r'LOGN_(\d+\.?\d*)_\(', r'log\1(', expr)

    return expr

# Словарь
def function(x):
    try:
        return eval(func, get_dict(x, func))
    except:
        return np.nan

# Проверка функции на работоспособность
def validate(expression):
    try:
        parsed = parse(expression)
        result = eval(parsed.lower(), get_dict(1.0, parsed))
        if not isinstance(result, (int, float, np.floating)) or ('x' not in str(parsed).lower()):
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
    global c
    eps = 1e-6
    r = eps / 2

    if a > b:
        c = None
        return f'❌ Ошибка: интервал задан некорректно.\na должно быть меньше b'
    if a == b:
        c = None
        return f'❌ Ошибка: интервал задан двумя совпадающими точками.'
    if np.isnan(function(a)) and np.isnan(function(b)):
        c = None
        return f'❌ Ошибка: функция не определена на отрезке ({a}; {b})'

    #===Здесь бьем область на 1000 сегментов и на каждом из них считаем минимум/максимум================================

    segments = 1000
    step = (b - a) / segments

    best_c = None
    best_val = float('-inf')

    for i in range(segments):
        seg_a = a + i * step
        seg_b = seg_a + step

        if np.isnan(function(seg_a)) and np.isnan(function(seg_b)):
            continue

        local_a, local_b = seg_a, seg_b
        while abs(local_b - local_a) > eps:
            mid = (local_a + local_b) / 2
            if function(mid - r) > function(mid + r):
                local_b = mid
            else:
                local_a = mid

        local_c = (local_a + local_b) / 2
        local_val = function(local_c)

        # пропускаем nan, inf и значения на краях подотрезка (асимптоты)
        if np.isnan(local_val) or np.isinf(local_val):
            continue
        if abs(local_c - seg_a) < eps or abs(local_c - seg_b) < eps:
            continue

        if local_val > best_val:
            best_val = local_val
            best_c = local_c

    c = best_c
    if c is None:
        return f'❌ Ошибка: не удалось найти максимум на отрезке ({a}; {b})'

    return f'f(x_max) = {round(function(c), 4)}, x_max = {round(c, 4)}'

# ДИХОТОМИЯ МИНИМУМ
def dichotomy_min(a, b):
    global c
    eps = 1e-6
    r = eps / 2

    if a > b:
        c = None
        return f'❌ Ошибка: интервал задан некорректно.\na должно быть меньше b'
    if a == b:
        c = None
        return f'❌ Ошибка: интервал задан двумя совпадающими точками.'
    if np.isnan(function(a)) and np.isnan(function(b)):
        c = None
        return f'❌ Ошибка: функция не определена на отрезке ({a}; {b})'

    #===Здесь бьем область на 1000 сегментов и на каждом из них считаем минимум/максимум================================

    segments = 1000
    step = (b - a) / segments

    best_c = None
    best_val = float('inf')

    for i in range(segments):
        seg_a = a + i * step
        seg_b = seg_a + step

        if np.isnan(function(seg_a)) and np.isnan(function(seg_b)):
            continue

        local_a, local_b = seg_a, seg_b
        while abs(local_b - local_a) > eps:
            mid = (local_a + local_b) / 2
            if function(mid - r) < function(mid + r):
                local_b = mid
            else:
                local_a = mid

        local_c = (local_a + local_b) / 2
        local_val = function(local_c)

        # пропускаем nan, inf и значения на краях подотрезка (асимптоты)
        if np.isnan(local_val) or np.isinf(local_val):
            continue
        if abs(local_c - seg_a) < eps or abs(local_c - seg_b) < eps:
            continue

        if local_val < best_val:
            best_val = local_val
            best_c = local_c

    c = best_c
    if c is None:
        return f'❌ Ошибка: не удалось найти минимум на отрезке ({a}; {b})'

    return f'f(x_min) = {round(function(c), 4)}, x_min = {round(c, 4)}'

'''
Отображение графика на оси:

    * красным - основной график;
    * синим - полученный максимум на отрезке путем дихтомии;

Расстояние между действительным максимумом красного
и пересечением синих пунктиров - есть погрешность
'''

# построение основных осей координат (x, y)
def build_axes(ax):
    # удаление стандартных рамок
    for spine in ax.spines.values():
        spine.set_visible(False)

    # создание новых осей, проходящих через т(0;0)
    ax.axhline(y=0, color='black', linewidth=1)
    ax.axvline(x=0, color='black', linewidth=1)

    # немного меньше непрозрачность у сетки
    ax.grid(True, alpha=0.3)

# просчет y
def compute_y(x_arr):
    # поменял принцип получения y, теперь он проверяет, вещественное ли это число, иначе вкидывает пустоту
    y = []
    for xi in x_arr:
        try:
            y.append(float(np.real(function(xi))))
        except:
            y.append(np.nan)
    # конвертация в массив нампая, где все элементы - дробные числа
    return np.array(y, dtype=float)

# i - то, с чем будет сохраняться файл, с каким префиксом, нужно по айди пользователя или по его тегу
def graph(i, func, a, b, save_dir='./imgs'):
    if c is None:
        return None

    x = np.linspace(a, b, 1000)
    y = compute_y(x)

    # создание фигуры и оси
    fig, ax = plt.subplots()
    build_axes(ax)

    # максимум/минимум
    ax.axhline(y=function(c), color='blue', linestyle='--')
    ax.axvline(x=c, color='blue', linestyle='--')
    ax.plot(x, y, label='f(x)', color='red', linestyle='solid')
    ax.set_title('График f(x)')
    ax.set_xlabel('x')
    ax.set_ylabel('y')

    # в случае если папки не будет, эта штука создаст папку сама с назв. imgs
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, f'{i}.png')
    plt.savefig(path)
    plt.close()
    return path

# простой график, построение без макс/мин
def simple_graph(i, func, save_dir='./imgs'):
    x = np.linspace(-20, 20, 1000)
    y = compute_y(x)

    # создание фигуры и оси
    fig, ax = plt.subplots()
    build_axes(ax)

    ax.plot(x, y, label='f(x)', color='red', linestyle='solid')
    ax.set_title('График f(x)')
    ax.set_xlabel('x')
    ax.set_ylabel('y')

    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, f'{i}.png')
    plt.savefig(path)
    plt.close()
    return path
