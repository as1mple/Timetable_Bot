import config
from connect import get_response

import logging

import telebot

from telebot import types

DAYS = {'Пн': 0, 'Вт': 1, 'Ср': 2, 'Чт': 3, 'Пт': 4, 'Сб': 5, 'Нд': 6}
CS = {'I': 1, 'II': 2, 'III': 3, 'IV': 4}
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
def event_handler(message):
    logging.info(f"сообщение которое пришло => {message.text}")

    if word_search(message.text):
        say_hello(message)
    elif message.text == 'ТАК':
        markup = types.ReplyKeyboardMarkup()
        markup.row('Ця неділя', 'Наступна неділя')
        bot.send_message(message.chat.id,
                         "Вас цікавить розклад на цій неді чи на наступній (діапазон буде розширений у наступних релізах",
                         reply_markup=markup)
        bot.register_next_step_handler(message, get_day)
    else:
        bot.send_message(message.chat.id, f"Не зрозумів. Перевірте правильність введення")


def say_hello(message):
    """Данная функция является первой в цепочке обработке событий не считая /start"""
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
    course = CS[message.text]
    save_data('course', course)
    markup = types.ReplyKeyboardMarkup()

    answer = get_response(params=info)['message']

    at = answer.find('[') + 1
    to = answer.find(']')
    [markup.row(el) for el in answer[at:to].split(',')]

    bot.send_message(message.chat.id, f"Ітак ви на {course} курсі. Вкажіть назву вашого факультету",
                     reply_markup=markup)

    bot.register_next_step_handler(message, get_fac)


def get_fac(message):
    fac = message.text
    save_data('fac', fac)
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, f"Напишіть назву вашої групи", reply_markup=markup)
    bot.register_next_step_handler(message, get_week)


def get_week(message):
    group = message.text
    save_data('group', group)
    markup = types.ReplyKeyboardMarkup()
    markup.row('Ця неділя', 'Наступна неділя')
    bot.send_message(message.chat.id,
                     "Вас цікавить розклад на цій неді чи на наступній (діапазон буде розширений у наступних релізах",
                     reply_markup=markup)
    bot.register_next_step_handler(message, get_day)


def get_day(message):
    week = 0 if message.text == 'Ця неділя' else 1
    save_data('week', week)
    markup = types.ReplyKeyboardMarkup()
    markup.row(*list(DAYS.keys())[:3])
    markup.row(*list(DAYS.keys())[3:6])
    markup.row(list(DAYS.keys())[-1])
    bot.send_message(message.chat.id, 'Виберіть день в який вас цікавить розклад', reply_markup=markup)
    bot.register_next_step_handler(message, get_date)


# def get_group(message):
#     group = message.text
#     save_data('group', group)
#     markup = types.ReplyKeyboardMarkup()
#     month = [str(i) for i in range(1, 13)]
#     markup.row(*month[:3])
#     markup.row(*month[3:6])
#     markup.row(*month[6:9])
#     markup.row(*month[9:])
#
#     bot.send_message(message.chat.id, "Виберіть місяць в яку вас цікавить розклад", reply_markup=markup)
#     bot.register_next_step_handler(message, get_month)
#
#
# def get_month(message):
#     date = message.text
#     save_data('date', date)
#     markup = types.ReplyKeyboardMarkup()
#     dates_range = [str(i) for i in range(1, 32)]
#     markup.row(*dates_range[:7])
#     markup.row(*dates_range[7:14])
#     markup.row(*dates_range[14:21])
#     markup.row(*dates_range[21: 28])
#     markup.row(*dates_range[28:32])
#     bot.send_message(message.chat.id, "Виберіть число в яке вас цікавить розклад", reply_markup=markup)
#     bot.register_next_step_handler(message, get_date)


def get_date(message):
    # date = f"{message.text}.{info.get('date', '')}"
    day = DAYS[message.text]
    save_data('day', day)
    bot.send_message(message.chat.id, 'Ось розклад по вашому запиту')
    show(message)


def show(message):
    """Вывод информации по введенным пользователем критериям"""
    response = get_response(params=info)

    [bot.send_message(message.chat.id,
                      f"{el['lessonNumber']} УРОК -{el['auditoryNumber']}{el['lessonType']} -> {el['disciplineName']} <- {el['lecturer']}")
     for el in response['curricularWeekList'][0].get('curricularDayList', 'ERROR')[4].get('lessonList', 'ERROR')]
    markup = types.ReplyKeyboardMarkup()
    markup.row('ТАК', 'НІ')
    bot.send_message(message.chat.id, "Бажаєте переглянути даний розклад на іншій неділі ?", reply_markup=markup)


def save_data(key: str, value: str):
    """Сохранение введенной пользователем информации"""
    info.update({key: value})
    logging.info(f"Информация успешно добавлена => {info}")


def word_search(text: str) -> bool:
    """Функция котороя ищет слова приветсвия"""
    key_word = ['hello', 'привет', 'hi', 'ку', 'вітаю', 'привіт']
    array = list(map(lambda el: el.lower(), text.split()))
    result = True in list(map(lambda el: el in array, key_word))
    return result


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
