from bot import bot


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message, "Привет!")

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.send_message(message.chat.id, f"Ты написал мне: {message.text}")