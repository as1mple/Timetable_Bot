from scraping_timetable import main_scraping
import config

import logging

import pandas as pd
import telebot
from telebot import types

info = {}

# Запускает т.н. Long Polling, а параметр none_stop=True говорит,
# что бот должен стараться не прекращать работу при возникновении каких-либо ошибок.
logging.getLogger('requests').setLevel(logging.CRITICAL)
# Configure our logger
logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s',
                    level=logging.INFO,
                    datefmt='%d.%m.%Y %H:%M:%S')
bot = telebot.TeleBot(config.TOKEN)
logging.info("Bot в режиме ожидания")


@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    logging.info(f"Отправлена команда => {message.text}")
    if message.text == "/start":
        logging.info(f"Бот был запущен полтзователем {message.chat.id}")
        bot.send_message(message.chat.id, 'Щоб розпочати роботу бота привітайтесь з ним :=)')
        bot.register_next_step_handler(message, say_hello)
    elif message.text == '/help':
        bot.send_message(message.chat.id, 'Тут має щось бути...')


@bot.message_handler(func=lambda message: True, content_types=["text"])
def event_handler(message):  # Название функции не играет никакой роли, в принципе
    logging.info(f"сообщение которое пришло => {message.text}")

    if word_search(message.text):
        say_hello(message)
    elif message.text == 'ТАК':
        markup = types.ReplyKeyboardMarkup()
        markup.row(*[str(i) for i in range(13)])

        bot.send_message(message.chat.id, "Виберіть місяць в яку вас цікавить розклад", reply_markup=markup)
        bot.register_next_step_handler(message, get_month)
    else:
        bot.send_message(message.chat.id, f"Не зрозумів. Перевірте правильність введення")


def say_hello(message):
    if word_search(message.text):
        logging.info("С ботом поздоровались")
        bot.send_message(message.chat.id,
                         "Доброго часу доби, вас вітає бот для пошуку розкладу.")
        markup = types.ReplyKeyboardMarkup()
        markup.row('I', 'II')
        markup.row('III', 'IV')
        bot.send_message(message.chat.id, "Виберіть курс групи, яка вас цікавить", reply_markup=markup)
        bot.register_next_step_handler(message, get_course)


def get_course(message):
    # if message.text[:1] == 'I':
    course = message.text
    save_data('course', course)
    bot.send_message(message.chat.id, f"Ітак ви на {course} курсі. Напишіть назву вашого факультету")
    bot.register_next_step_handler(message, get_fac)


def get_fac(message):
    fac = message.text
    save_data('fac', fac)
    bot.send_message(message.chat.id, f"Напишіть назву вашої групи")
    bot.register_next_step_handler(message, get_group)


def get_group(message):
    group = message.text
    save_data('group', group)
    #   bot.send_message(message.chat.id, f"Напишіть дату на яку вас цікавить розклад")
    markup = types.ReplyKeyboardMarkup()
    markup.row(*[str(i) for i in range(13)])

    bot.send_message(message.chat.id, "Виберіть місяць в яку вас цікавить розклад", reply_markup=markup)
    bot.register_next_step_handler(message, get_month)


def get_month(message):
    date = message.text
    save_data('date', date)
    markup = types.ReplyKeyboardMarkup()
    markup.row(*[str(i) for i in range(7)])
    markup.row(*[str(i) for i in range(7, 14)])
    markup.row(*[str(i) for i in range(14, 21)])
    markup.row(*[str(i) for i in range(21, 28)])
    markup.row(*[str(i) for i in range(28, 32)])
    bot.send_message(message.chat.id, "Виберіть число в яке вас цікавить розклад", reply_markup=markup)
    bot.register_next_step_handler(message, get_date)


def get_date(message):
    date = f"{message.text}.{info.get('date', '')}"
    save_data('date', date)
    bot.send_message(message.chat.id, 'Ось розклад по вашому запиту')
    show(message)


def show(message):
    print(info.get("date", ""))
    data = pd.read_csv('РОЗКЛАД.csv')
    information = list(data.query(f'Date == {info.get("date", "")}').values[0])
    [bot.send_message(message.chat.id, f"{i - 2} Урок = > {information[i]}") for i in range(3, len(information))]

    markup = types.ReplyKeyboardMarkup()
    markup.row('ТАК', 'НІ')
    bot.send_message(message.chat.id, "Бажаєте переглянути даний розклад в іншу дату ?", reply_markup=markup)


def save_data(key, value):
    info.update({key: value})
    print(info)
    logging.info(f"Информация успешно добавлена => {key}")


def word_search(text: str) -> bool:
    key_word = ['hello', 'привет', 'hi', 'ку', 'вітаю', 'привіт']
    array = list(map(lambda el: el.lower(), text.split()))
    result = True in list(map(lambda el: el in array, key_word))
    return result


if __name__ == '__main__':
    main_scraping()
    bot.polling(none_stop=True, interval=0)
