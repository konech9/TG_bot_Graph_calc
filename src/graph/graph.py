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

'''
Немного слов про re (памятка для редактирования):

re.search(pattern, string) <- сканирует строку и возвращает первое совпадение;
re.match(pattern, string) <- проверяет совпадение только в начале строки;
re.findall(pattern, string) <- возвращает список всех непересекающихся совпадений;
re.finditer(pattern, string) <- возвращает итератор по совпадениям (эффективно для больших данных);
re.sub(pattern, repl, string) <- заменяет совпадения шаблона на новую строку repl;
re.split(pattern, string) <- разбивает строку по разделителю-шаблону;
re.compile(pattern) <- компилирует шаблон в объект, что полезно для многократного использования;
'''


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
        result = eval(parsed.lower(), get_dict(1.0, parsed) | {'a':1.0})
        if not isinstance(result, (int, float, np.floating)):
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

    #===Здесь бьем область на 1000 сегментов и на каждом из них считаем минимум/максимум================================

    segments = 1000
    step = (b - a) / segments

    for i in range(segments+1):
        xi = a + (b - a) * i / segments
        val = function(xi)
        if not (np.isnan(val) or np.isinf(val)):
            has_defined = True
            break

    if not has_defined:
        c = None
        return f'❌ Ошибка: функция не определена на отрезке [{a}; {b}]'

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

    #===Здесь бьем область на 1000 сегментов и на каждом из них считаем минимум/максимум================================

    segments = 1000
    step = (b - a) / segments

    best_c = None
    best_val = float('inf')

    # --- проверка на существование значений функции ---
    has_defined = False

    for i in range(segments+1):
        xi = a + (b - a) * i / segments
        val = function(xi)
        if not (np.isnan(val) or np.isinf(val)):
            has_defined = True
            break

    if not has_defined:
        c = None
        return f'❌ Ошибка: функция не определена на отрезке [{a}; {b}]'

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

# --- адаптивный подбор x для точности графика ---
def adaptive_x(a, b, line = 1000):
    x = np.linspace(a, b, line)
    y = compute_y(x)

    new_x = [x[0]]

    for i in range(1, len(x) - 1):
        dy1 = abs(y[i] - y[i-1])
        dy2 = abs(y[i+1] - y[i])

        # если резкий скачок — добавляем больше точек
        if dy1 > 1 or dy2 > 1:
            extra = np.linspace(x[i-1], x[i+1], 5)
            new_x.extend(extra)
        else:
            new_x.append(x[i])

    new_x.append(x[-1])
    return np.unique(new_x)

# i - то, с чем будет сохраняться файл, с каким префиксом, нужно по айди пользователя или по его тегу
def graph(i, func, a, b, save_dir='./imgs'):
    if c is None:
        return None

    x = adaptive_x(a, b, 1500)
    y = compute_y(x)
    y = apply_iqr_clip(y)

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
    ax.set_xlim(a, b)

    # в случае если папки не будет, эта штука создаст папку сама с назв. imgs
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, f'{i}.png')
    plt.savefig(path)
    plt.close()
    return path

# Регулировка масштаба (IQR)
def apply_iqr_clip(y):
    # обрезаем выбросы по IQR — данные не теряем, просто масштаб становится адекватным
    finite_y = y[np.isfinite(y)]
    if len(finite_y) == 0:
        return y
    q1, q3 = np.percentile(finite_y, 25), np.percentile(finite_y, 75)
    iqr = q3 - q1
    if iqr > 0:
        y = np.clip(y, q1 - 3 * iqr, q3 + 3 * iqr)
    return y

# простой график, построение без макс/мин
def simple_graph(i, func, a, b, save_dir='./imgs'):

    x = adaptive_x(a, b, 1000)
    y = compute_y(x)
    y = apply_iqr_clip(y)

    # создание фигуры и оси
    fig, ax = plt.subplots()
    build_axes(ax)

    ax.plot(x, y, label='f(x)', color='red', linestyle='solid')
    ax.set_title('График f(x)')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_xlim(a, b)

    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, f'{i}.png')
    plt.savefig(path)
    plt.close()
    return path

'''
График с параметром, принимает несколько функций
'''

def parameter_graph(color_mode, i, functions, x_a, x_b, save_dir='./imgs'):

    global func

    x = adaptive_x(x_a, x_b, 1000)

    # фигура + оси
    fig, ax = plt.subplots()
    # построение осей через ноль
    build_axes(ax)

    # 10 цветов для построения
    palette = plt.cm.tab10.colors
    # счетчик цветов, каждый раз обновляется после построения функции для смены цвета
    color_index = 0
    if color_mode == 'by_parameter':
        # для каждого значения параметра свой цвет
        all_params = []
        for fn_data in functions:
            for a_val in fn_data['params']:
                if a_val not in all_params:
                    all_params.append(a_val)
        colors = {a_val: palette[i % len(palette)] for i, a_val in enumerate(all_params)}
    else:
        color_index = 0


    for fn_data in functions: # для каждой функции из списка: строка=функция, список значений параметра
        fn = fn_data['func']
        params = fn_data['params']
        func = fn

        for a_val in params: # рассматриваем каждое значение для параметра a
            y = []

            for xi in x: # для каждого x
                try:
                    d = get_dict(xi, fn) # словарь для обработки функции
                    # проверка на условие существования значения параметра и вычисления значений функции
                    if a_val is not None:
                        d['a'] = a_val
                    result = eval(fn, d)
                    y.append(float(np.real(result))) # np.real отсекает невещественную часть
                except:
                    y.append(np.nan)

            y = np.array(y, dtype=float)
            y = apply_iqr_clip(y)

            # подписи для графиков (каждого параметра)
            if a_val is not None:
                label = f'f(x, {a_val})'
            else:
                label = 'f'

            if color_mode == 'by_parameter':
                color = colors[a_val]
            else:
                color = palette[color_index % len(palette)]

            ax.plot(x, y, label=label, color=color)
            color_index += 1

    # легенда + ограничение оси x переданным отрезком
    ax.set_xlim(x_a, x_b)
    ax.legend(fontsize = 8)
    ax.set_xlabel('x')
    ax.set_ylabel('y')

    # сохранение файла
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, f'{i}_parameter.png')
    plt.savefig(path)
    plt.close()
    return path
