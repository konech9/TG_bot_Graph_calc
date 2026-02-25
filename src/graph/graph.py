import numpy as np
from matplotlib import  as plt
import re

def parse(expr):
    # степень: ** <=> ^
    expr = expr.replace('^', '**')

    # умножение через пробел или без: 2x <=> 2*x
    expr = re.sub(r'(\d)(x)', r'\1*\2', expr)
    expr = re.sub(r'(\d)(sin|cos|tan|exp|log|sqrt|abs)', r'\1*\2', expr)

    # то же самое для скобок
    expr = re.sub(r'(\d)\(', r'\1*(', expr)

    # натуральный логарифм: ln <=> log
    expr = expr.replace('ln(', 'log(')

    return expr


# Словарь
def f(x):
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