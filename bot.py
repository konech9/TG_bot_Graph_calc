import telebot
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    print("Обработано сообщение страт")
    bot.send_message(message.chat.id, "Привет!")

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.send_message(message.chat.id, f"Ты написал мне: {message.text}")

if __name__ == "__main__":
    bot.polling()
    print("Бот запущен")

