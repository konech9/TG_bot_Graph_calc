from dotenv import load_dotenv
import os
import warnings
import numpy as np

# настройки numpy/warnings
np.seterr(all='ignore')
warnings.filterwarnings('ignore')

# получение файла .env
load_dotenv()

# загрузка токена
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN not set")

#===пути================================================================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPHS_DIR = os.path.join(BASE_DIR, "src", "pictures", "users")
SETTINGS_FILE = os.path.join(BASE_DIR, "user_settings.json")

# создание необходимых папок
os.makedirs(GRAPHS_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "src", "pictures", "examples"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

#===константы===========================================================================================================

# Стартовые значения диапазонов для построения графиков
DEFAULT_A = -20
DEFAULT_B = 20

# Максимальная длина отрезка
MAX_INTERVAL = 1e5
