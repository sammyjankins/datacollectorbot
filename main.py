import sched
import time
from datetime import datetime, timedelta
from threading import Timer, Lock, Thread, TIMEOUT_MAX

from dateparser import parse
from flask import Flask, request, jsonify, redirect

import bot_actions
import constants
import data_processing
import db_operator
import private_constants
from data_processing import parse_time
from send_IPU import send_data
from tunnel import launch_tunnel

# from flask_sslify import SSLify


# sslify = SSLify(app)

app = Flask(__name__)

lock = Lock()
timers = {}


def when_timer_stop(flag, user_id, in_progress=False):
    user = db_operator.get_user(user_id)
    db_operator.set_state(user_id, user['last_state'])
    print(f'state is {db_operator.get_current_state(user_id)}')
    text = ''
    options = {
        'later_hour': 'через час',
        'later_day': 'завтра',
    }
    try:
        if flag:
            text = "Введите ранее запрошенные показания:"
        else:
            try:
                if str(datetime.today())[:10] == user['last_sending_date'][:10]:
                    data_v = db_operator.get_last_data(user_id)
                    us_vars = db_operator.get_user_data(user_id, 'vars').values()
                    if all(x in data_v.keys() for x in us_vars):
                        db_operator.set_user_last_date(user_id, str(datetime.today() + timedelta(days=1)))
                        db_operator.set_user_next_date(user_id)
                        bot_actions.send_message(user_id,
                                                 'Данные за сегодняшнее число уже были отправлены\n'
                                                 '<b>Следующая дата отправки</b>: '
                                                 f'{db_operator.get_user_data(user_id, "next_date")}',
                                                 parse_mode='HTML')
                        user_set_timer(None, user_id)
                        return
                    elif not in_progress:
                        lens = db_operator.check_collect_progress(user_id)
                        text = f"Введите {user['vars'][f'{lens[1] + 22}']}"
            except Exception:
                if not in_progress:
                    lens = db_operator.check_collect_progress(user_id)
                    text = f"Введите {user['vars'][f'{lens[1] + 22}']}"
    except KeyError:
        try:
            print(user['last_sending_date'])
        except KeyError:
            db_operator.set_user_last_date(user_id, str(datetime.today()))
        text = "Подтвердите отправку"
        options = {
            'send': 'Отправить'
        }
    if text:
        bot_actions.bot_send_keyboard(text, user_id, options)


def user_wait(message, user_id):
    user_id = str(user_id)
    if timers[user_id]['in_progress'] or 'отмен' in message.lower():
        timers[user_id]['timer'].cancel()
        if 'отмен' in message.lower():
            bot_actions.send_message(user_id,
                                     'Отправка данных отменена')
            db_operator.set_state(user_id, constants.States.S_START.value)
            db_operator.swap_collect(user_id)
            return
        elif message.isdigit():
            when_timer_stop(False, user_id, in_progress=True)
            db_operator.set_state(user_id, db_operator.get_user_data(user_id, 'last_state'))
            actions[db_operator.get_user_data(user_id, 'last_state')](message, user_id)
        else:
            when_timer_stop(True, user_id)
    else:
        user = db_operator.get_user(user_id)
        bot_actions.send_message(user_id,
                                 'Следующая отправка данных:\n'
                                 f'{user["next_date"].split(".")[0][:-3]}')


def new_user_init(user_id):
    if db_operator.get_user(user_id):
        bot_actions.send_message(user_id,
                                 'Я нашел ваши данные!\n'
                                 'Если хотите проверить и изменить свои данные, используйте команду /update\n'
                                 'Если хотите удалить свои данные - /delete')
    else:
        if db_operator.init_user(user_id=user_id):
            bot_actions.send_message(user_id, 'Начнем с формирования шаблона!\n<b>Если '
                                              'вдруг что-то пойдет не так - воспользуйтесь командой</b> /delete!\n'
                                              'Введите текст письма. Следуйте примеру, выделяя места появления данных'
                                              ' и текущей даты фигурными скобками (если отметить место для текущей даты'
                                              ', при отправке письма она будет появляться в выбранном месте '
                                              'автоматически). Пример:\n\n'
                                              '<i>Добрый день!\n'
                                              'Показания ИПУ по адресу ул. Пушкина, д. 1, кв. 2 на {дата}:\n\n'
                                              'Электроэнергия: {показания счетчика электроэнергии}\n'
                                              'Холодное водоснабжение: {показания счетчика холодной воды}\n'
                                              'Горячее водоснабжение: {показания счетчика горячей воды}\n\n'
                                              'С уважением, Петров А. А.</i>',
                                     parse_mode='HTML')
            db_operator.set_state(user_id, constants.States.S_SET_TEMPLATE.value)


def delete_data(user_id):
    db_operator.delete_user_data(user_id)
    bot_actions.send_message(user_id, 'Ваши данные удалены.')
    try:
        if timers[str(user_id)]:
            timers[str(user_id)]['timer'].cancel()
    except KeyError:
        print(timers)


def update_data(user_id):
    try:
        user = db_operator.get_user(user_id)
        msg = f"<b>Ваши данные</b>:\n" \
              f"<b>Текст письма</b>:\n{user['mail_text']}\n" \
              f"<b>Тема письма</b>:\n{user['mail_theme']}\n" \
              f"<b>Получатель</b>: {user['mail_to']}\n" \
              f"<b>Временная разница с сервером</b>: {user['tz_delta']} ч\n" \
              f"<b>Период отправки данных</b>: {constants.choose_period[(user['send_period'])][0]}\n"
        keys = [key for key in constants.choose_period[data_processing.in_array(list(constants.choose_period.keys()),
                                                                                [user['send_period']])][1:]]
        send_period_info = [f'<b>{value[key][1]}</b>{user[key]}\n' for value in constants.corQuests for key in keys if
                            key in value.keys()]
        msg = f'{msg}{"".join(send_period_info)}'
        bot_actions.send_message(user_id, msg, parse_mode='HTML')
        options = {
            'update_template': 'Текст письма',
            'update_mail_theme': 'Тема письма',
            'update_mail_to': 'Получатель',
            'update_send_period': 'Период отправки данных',
            'update_timezone': 'Часовой пояс',
        }
        db_operator.set_user_data(user_id, 'updating', 'true')
        bot_actions.bot_send_keyboard('Укажите, какие данных вы хотели бы отредактировать: ', user_id, options)
    except TypeError:
        bot_actions.send_message(user_id,
                                 'У меня нет ваших данных.\n'
                                 'Чтобы узнать обо мне, воспользуйтесь командой /info\n'
                                 'Чтобы начать создание шаблона - /start')


def user_asks_info(user_id):
    bot_actions.send_message(user_id,
                             'Я бот, который будет отправлять ваши численные данные по электронной '
                             'почте и поможет вам автоматизировать сам процесс сбора и отправки данных.\n'
                             'Для этого нам изначально необходимо вместе сформировать <b>шаблон письма</b> '
                             '(в который я буду подставлять данные), определиться с <b>периодом отправки</b> '
                             'этого письма и <b>электронными адресами</b> получателей.\n'
                             'Например у вас есть необходимость отправлять данные счетчиков холодной и '
                             'горячей воды на электронную почту вашей коммунальной службы. Чтобы вы не '
                             'забывали это делать, я буду это делать за вас - раз в месяц я буду спрашивать'
                             ' у вас показания и самостоятельно отправлять их на нужный адрес :)\n'
                             'Чтобы начать создание шаблона - воспользуйтесь командой /start\n'
                             'Текст письма должен будет пройти модерацию '
                             '(никаких нигерийских писем и тому подобного!)\n'
                             'P.S.: можете меня использовать для отправки текста без данных.',
                             parse_mode='HTML')


def user_asks_help(user_id):
    user = db_operator.get_user(user_id)
    if user:
        try:
            bot_actions.send_message(user_id,
                                     "<b>Ваши данные</b>:\n"
                                     f"<b>Текст письма</b>:\n {user['mail_text']}\n"
                                     f"<b>Получатель</b>: {user['mail_to']}\n"
                                     f"<b>Следующая дата отправки</b>: {user['next_date'].split('.')[0][:-3]}\n"
                                     "Комадны:\n"
                                     "/help - ее вы уже использовали и видите результат\n"
                                     "/update - изменить некоторые данные\n"
                                     "/delete - удалить свои данные\n"
                                     "/last - последние отправленные данные\n"
                                     "/info - чтобы узнать обо мне"
                                     "Чтобы сохранить шаблон, но отменить оправку данных, просто напишите 'отмена'",
                                     parse_mode='HTML')
        except Exception as e:
            print(f'Error while running "user_asks_help" 3 with args: {e.args}')
            return None
    else:
        bot_actions.send_message(user_id,
                                 'Чтобы создать шаблон письма для отправи данных - воспользуйтесь командой /start\n'
                                 'Чтобы узнать обо мне - /info')


def user_asks_last(user_id):
    if db_operator.get_last_data(user_id):
        last_date = db_operator.get_user_data(user_id, 'last_sending_date')
        data_dict = db_operator.get_last_data(user_id)
        data = [f'<b>{key}</b>: {value}\n' for key, value in data_dict.items()]
        msg = f'<b>Дата отправки</b>: {last_date.split(".")[0][:-3]}\n{"".join(data)}'
        bot_actions.send_message(user_id, msg, parse_mode='HTML')
    else:
        bot_actions.send_message(user_id, 'В базе отсутствуют записи об отправляемых вами числовых данных.')


def collect_values(message, user_id):
    user = db_operator.get_user(user_id)
    try:
        user['last_sending_date']
    except KeyError:
        db_operator.set_user_last_date(user_id, str(datetime.today()))
    lens = db_operator.check_collect_progress(user_id)
    if lens[1] < lens[0] and db_operator.get_current_state(user_id) == constants.States.S_ENTER_DATA.value:
        if data_processing.msg_check(message, 'digit'):
            if db_operator.update_data_value(user_id, user['vars'][f'{lens[1] + 22}'], message):
                lens = db_operator.check_collect_progress(user_id)
                if lens[0] >= lens[1] + 1:
                    text = f"Введите {user['vars'][f'{lens[1] + 22}']}"
                    options = {
                        'later_hour': 'через час',
                        'later_day': 'завтра',
                    }
                    bot_actions.bot_send_keyboard(text, user_id, options)
        else:
            bot_actions.send_message(user_id, text="Нужно ввести цифры, попробуй ещё раз.")
    if lens[1] == lens[0]:
        send_data(user_id)
        db_operator.set_user_next_date(user_id)
        bot_actions.send_message(user_id, f'Ваши данные успешно отправлены на адрес {user["mail_to"]}.\n'
                                          f'Следующая дата отправки - '
                                          f'{db_operator.get_user_data(user_id, "next_date").split(".")[0][:-3]}')
        db_operator.set_state(user_id, constants.States.S_USER_WAIT.value)
        time.sleep(1)


def callback_later_hour(user_id):
    callback_wait(user_id, 'hour')


def callback_later_day(user_id):
    callback_wait(user_id, 'day')


def callback_wait(user_id, option):
    user_id = str(user_id)
    user = db_operator.get_user(user_id)
    if option == 'day':
        time_obj = parse(parse_time(user['at_time']))
        seconds_delta = datetime.today() + timedelta(days=1)
        seconds_delta = seconds_delta.replace(hour=time_obj.hour, minute=time_obj.minute, second=0) - datetime.today()
        bot_actions.send_message(user_id, text=f"Переспрошу завтра в {time_obj.hour}:{time_obj.minute}")
    else:
        seconds_delta = timedelta(hours=1)
        bot_actions.send_message(user_id, text="Переспрошу через час")
    timer = Timer(seconds_delta.total_seconds(), when_timer_stop, args=(True, user_id))
    timers.update({user_id: {'timer': timer,
                             'in_progress': True}})
    db_operator.set_user_last_state(user_id, constants.States.S_ENTER_DATA.value)
    db_operator.set_state(user_id, constants.States.S_USER_WAIT.value)
    timers[user_id]['timer'].start()
    print(timers[user_id]['timer'])


def user_set_timer(message, user_id):
    user_id = str(user_id)
    user = db_operator.get_user(user_id)
    if user and user['collecting'] == 'true':
        db_operator.set_user_last_state(user_id, constants.States.S_ENTER_DATA.value)
        db_operator.set_state(user_id, constants.States.S_USER_WAIT.value)
        seconds = datetime.fromisoformat(user['next_date']) - datetime.today()
        if seconds.total_seconds() > TIMEOUT_MAX:
            timer = Timer(timedelta(days=30).total_seconds(), user_set_timer, args=(None, user_id))
        else:
            timer = Timer(seconds.total_seconds() - timedelta(hours=user['tz_delta']).total_seconds(), when_timer_stop,
                          args=(False, user_id))
        timers.update({user_id: {'timer': timer,
                                 'in_progress': False}})
        timers[user_id]['timer'].start()
        print(timers[user_id]['timer'])


def user_doing_nothing(message, user_id):
    user = db_operator.get_user(user_id)
    if user:
        bot_actions.bot_send_keyboard(
            'Нажмите на кнопку, чтобы возобновить отправку данных.\nЧтобы получить справку, введите /help',
            user_id,
            {
                'renew': 'Возобновить'
            }
        )
    else:
        bot_actions.send_message(user_id, 'Чтобы узнать обо мне, воспользуйтесь командой /info\n'
                                          'Чтобы получить информацию о командах и ваших данных '
                                          '(если вы их вносили) - /help')


def user_resume(user_id):
    db_operator.swap_collect(user_id)
    bot_actions.send_message(user_id, 'Отправка данных возобновлена')
    user_set_timer(None, user_id)


commands = {
    '/start': new_user_init,
    '/delete': delete_data,
    '/update': update_data,
    '/help': user_asks_help,
    '/info': user_asks_info,
    '/last': user_asks_last,
}

actions = {
    '0': user_doing_nothing,
    '1': collect_values,
    '4': user_wait,
    '5': db_operator.set_user_template,
    '6': db_operator.set_user_theme,
    '7': db_operator.set_user_mailto,
    '9': db_operator.correct_user_date,
    '10': user_set_timer,
    '12': db_operator.set_user_timezone,
}

callbacks = {
    'later_hour': callback_later_hour,
    'later_day': callback_later_day,
    'renew': user_resume,
    'send': send_data,
    'update_template': db_operator.set_user_template,
    'update_mail_theme': db_operator.set_user_theme,
    'update_mail_to': db_operator.set_user_mailto,
    'update_send_period': db_operator.set_user_date,
    'update_timezone': db_operator.set_user_timezone,
}


@app.route(f'/{private_constants.token}', methods=['POST', 'GET'])
def index(message=None):
    if request.method == 'POST':
        r = request.get_json()
        try:
            chat_id = r['message']['chat']['id']
            if not message:
                message = r['message']['text']
        except KeyError:
            call_data = r['callback_query']['data']
            chat_id = r['callback_query']['message']['chat']['id']
            if call_data in constants.choose_period.keys():
                db_operator.set_user_date(call_data, chat_id)
            elif call_data in callbacks.keys():
                if 'update' in call_data:
                    db_operator.set_user_data(chat_id, 'updating', 'updating_process')
                    db_operator.set_user_data(chat_id, 'last_state', db_operator.get_current_state(chat_id))
                    callbacks[call_data](message=None, user_id=chat_id)
                else:
                    callbacks[call_data](chat_id)
            else:
                decision, uid = call_data.split()
                db_operator.set_moder_status(uid, message=message, status=decision)
        current_state = db_operator.get_current_state(chat_id)
        if db_operator.get_user_data(chat_id, 'updating') == 'true':
            db_operator.set_user_data(chat_id, 'updating', 'false')
        if message in commands.keys():
            commands[message](chat_id)
        elif current_state in actions and message is not None:
            answer = actions[current_state](message, chat_id)
            if answer == 'collect':
                index()
        return jsonify(r)
    return redirect(private_constants.most_important_link, code=302)


sch = sched.scheduler(time.time, time.sleep)

if __name__ == '__main__':
    launch_tunnel()
    with lock:
        Thread(target=app.run).start()
    users = db_operator.get_users()
    if users is not None:
        for person in users:
            user_set_timer('', str(person))
