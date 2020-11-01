import config
from connect import *

import logging

import telebot

from telebot import types

CS = {'I': 1, 'II': 2, 'III': 3, 'IV': 4}
info = {}
faculty = []

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
    """Обработчик  команд"""
    logging.info(f"Отправлена команда => {message.text}")
    if message.text == "/start":
        logging.info(f"Бот был запущен полтзователем {message.chat.id}")
        bot.send_message(message.chat.id, 'Щоб розпочати роботу бота привітайтесь з ним :=)')
        bot.register_next_step_handler(message, say_hello)
    elif message.text == '/help':
        bot.send_message(message.chat.id,
                         'Даний бот був розрозроблений з ціллю полегшити пошук енного розкладу в енний день енного місяця для користувачів сайту ВНТУ - iq.vntu.edu.ua ')

        bot.send_message(message.chat.id,
                         'Для того, щоб розпочати пошук розкладу по вашим критерiям: \n'
                         '=> Вам потрiбно  привітатись з ботом'
                         'на українській, англійській або російській мовах \n=> після чого вводити коректну інформація на вимоги бота.\n'
                         '!!! Якщо інформація не буде схожа на правду вам запропонується повторити спробу. '
                         '!!! Розклад по вашим критеріям не буде знайдений, якщо: \n'
                         '=> На частині бекенду будуть проводитись технічні роботи, \n'
                         '=> Сайт який надає розклад буде тимчасово недоступний,\n'
                         '=> Ваша інформація була схожа на правдиву - '
                         'вам вдалося обдурити валідатор бота =-)')


@bot.message_handler(func=lambda message: True, content_types=["text"])
def event_handler(message):
    """Главный обработчик событий"""
    logging.info(f"сообщение которое пришло => {message.text}")

    if word_search(message.text):
        say_hello(message)
    elif message.text.upper() == 'ТАК':
        markup = types.ReplyKeyboardMarkup()
        month = [str(i) for i in range(1, 13)]
        markup.row(*month[:3])
        markup.row(*month[3:6])
        markup.row(*month[6:9])
        markup.row(*month[9:])

        bot.send_message(message.chat.id, "Виберіть місяць в яку вас цікавить розклад", reply_markup=markup)
        bot.register_next_step_handler(message, get_month)
    else:
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, f"Захочете знайти розкад, просто привітайтесь зі мною", reply_markup=markup)


def say_hello(message):
    """Данная функция является первой в цепочке обработке событий не считая /start"""
    if word_search(message.text):
        logging.info("С ботом поздоровались")
        global info
        info.clear()
        bot.send_message(message.chat.id,
                         "Доброго часу доби, вас вітає бот для пошуку розкладу.")
        markup = types.ReplyKeyboardMarkup()
        markup.row('I', 'II')
        markup.row('III', 'IV')
        bot.send_message(message.chat.id, "Виберіть або введіть курс групи, яка вас цікавить", reply_markup=markup)
        bot.register_next_step_handler(message, get_course)


def get_course(message):
    if not message.text in [str(i) for i in range(1, 5)] and CS.get(message.text, 'ERROR') is "ERROR":
        bot.send_message(message.chat.id, "Не коректнi данi. Повторiть спробу!")
        bot.send_message(message.chat.id, "Виберіть або введіть курс групи, яка вас цікавить")
        bot.register_next_step_handler(message, get_course)
    else:
        course = CS.get(message.text, message.text)

        save_data('course', course)
        markup = types.ReplyKeyboardMarkup()

        answer = get_timetable(params=info)['message']

        at = answer.find('[') + 1
        to = answer.find(']')
        global faculty
        faculty = answer[at:to].split(', ')
        [markup.row(el) for el in faculty]

        bot.send_message(message.chat.id, f"Ітак ви на {course} курсі. Виберіть назву вашого факультету",
                         reply_markup=markup)

        bot.register_next_step_handler(message, get_fac)


def get_fac(message):
    if not message.text in faculty:
        bot.send_message(message.chat.id, "Не коректнi данi. Повторiть спробу!")
        bot.send_message(message.chat.id, f"Виберіть назву вашого факультету")
        bot.register_next_step_handler(message, get_fac)
    else:
        fac = message.text
        save_data('fac', fac)
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, f"Напишіть назву вашої групи", reply_markup=markup)
        bot.register_next_step_handler(message, get_group)


def get_group(message):
    group = message.text
    save_data('group', group)

    markup = types.ReplyKeyboardMarkup()
    month = [str(i) for i in range(1, 13)]
    markup.row(*month[:3])
    markup.row(*month[3:6])
    markup.row(*month[6:9])
    markup.row(*month[9:])

    bot.send_message(message.chat.id, "Виберіть місяць в яку вас цікавить розклад", reply_markup=markup)
    bot.register_next_step_handler(message, get_month)


def get_month(message):
    if not validation_number(message) or not message.text in [str(i) for i in range(1, 13)]:
        bot.send_message(message.chat.id, "Не коректнi данi. Повторiть спробу!")
        bot.send_message(message.chat.id, "Виберіть місяць в яку вас цікавить розклад")
        bot.register_next_step_handler(message, get_month)
    else:
        date = core_date(message.text)
        save_data('date', date)
        markup = types.ReplyKeyboardMarkup()
        dates_range = [str(i) for i in range(1, 32)]
        markup.row(*dates_range[:7])
        markup.row(*dates_range[7:14])
        markup.row(*dates_range[14:21])
        markup.row(*dates_range[21: 28])
        markup.row(*dates_range[28:32])
        bot.send_message(message.chat.id, "Виберіть або введіть число в яке вас цікавить розклад", reply_markup=markup)
        bot.register_next_step_handler(message, get_date)


def get_date(message):
    if not validation_number(message) or not message.text in [str(i) for i in range(1, 32)]:
        bot.send_message(message.chat.id, "Не коректнi данi. Повторiть спробу!")
        bot.send_message(message.chat.id, "Виберіть або введіть число в яке вас цікавить розклад")
        bot.register_next_step_handler(message, get_date)
    else:
        day = core_date(message.text)
        save_data('day', day)
        bot.send_message(message.chat.id, 'Зачекайте, зараз пошукаю')
        show(message)


def show(message):
    """Вывод информации по введенным пользователем критериям"""
    try:
        response = get_timetable(params=info)
        bot.send_message(message.chat.id, 'Ось результати по вашому запиту')
        if len(response.get('lessonList', 'ERROR')) == 0:
            bot.send_message(message.chat.id, "У цей день відсутні уроки (ваші дані коректні)")
        [bot.send_message(message.chat.id,
                          f"{el['lessonNumber']} УРОК -{el['auditoryNumber']} - {el['lessonType']} - {subgroup(el['subGroup'])} -> {el['disciplineName']} <- {el['lecturer']}")
         for el in response.get('lessonList', 'ERROR')];
        logging.info(f"Информация по данным параметрам была найдена")
        markup = types.ReplyKeyboardMarkup()
        markup.row('ТАК', 'НІ')
        bot.send_message(message.chat.id, "Бажаєте переглянути даний розклад на іншу дату", reply_markup=markup)
    except Exception as e:
        logging.warning(f"Информация была не валидна \n {e}")
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "Ваші дані не валідні, повторіть спробу, для цього привітайтесь з ботом",
                         reply_markup=markup)


def save_data(key: str, value: str):
    """Сохранение введенной пользователем информации"""
    info.update({key: value})
    logging.info(f"Информация успешно добавлена => {info}")


def word_search(text: str) -> bool:
    """Функция котороя ищет слова приветсвия"""
    key_word = ['hello', 'привет', 'hi', 'ку', 'вітаю', 'привіт', 'доброго', ]
    array = list(map(lambda el: el.lower(), text.split()))
    result = True in list(map(lambda el: el in array, key_word))
    return result


def core_date(text: str) -> str:
    """Добавлние в число первой цифры 0, в случае если оно не двуцифровое, для валидного представлнеия даты"""
    if len(text) == 1: return f"0{text}"
    return text


def validation_number(message):
    """Проверка является ли введенная информация целым числом или нет"""
    try:
        int(message.text)
        return True
    except Exception:
        print(-1)
        return False


def subgroup(text):
    """Перевод подгруппы в текст"""
    if text == 0:
        return "усі підгрупи"
    else:
        return f"{text} підгрупа"


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
