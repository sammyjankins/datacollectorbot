import ast
from pprint import pprint
from sys import _getframe

from vedis import Vedis

import bot_actions
import constants
import data_processing
import private_constants
from timezone import get_user_tz_delta


def get_current_state(user_id):
    with Vedis(private_constants.db_state_file) as db:
        try:
            return db[user_id].decode()
        except (KeyError, OSError):
            return constants.States.S_START.value


def set_state(user_id, value):
    with Vedis(private_constants.db_state_file) as db:
        try:
            print(f'Changing state of user {user_id} from [{get_current_state(user_id)}] to [{value}]')
            db[user_id] = value
            return True
        except Exception as e:
            func_name = _getframe().f_code.co_name
            print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
            return False


def get_data(user_id):
    with Vedis(private_constants.db_file) as db:
        try:
            data = ast.literal_eval(db[user_id].decode('utf-8'))
            return data
        except (KeyError, OSError):
            return {'DATA': {}}


def get_last_data(user_id):
    data = get_data(user_id)
    try:
        return data['DATA'][get_user_data(user_id, 'last_sending_date')]
    except (KeyError, OSError):
        return {}


def get_user(user_id, return_obj=True):
    with Vedis(private_constants.db_users) as db:
        try:
            user = ast.literal_eval(db[user_id].decode('utf-8'))
            if return_obj:
                return user
            else:
                pprint(user)
                bot_actions.send_message(user_id,
                                         "<b>Ваши данные</b>:\n"
                                         f"<b>Текст письма</b>:\n{user['mail_text']}\n"
                                         f"<b>Получатель</b>: {user['mail_to']}\n"
                                         f"<b>Следующая дата отправки</b>: {user['next_date'].split('.')[0][:-3]}",
                                         parse_mode='HTML')
        except Exception as e:
            func_name = _getframe().f_code.co_name
            print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
            return False


def get_user_data(user_id, key):
    try:
        user = get_user(user_id)
        return user[key]
    except Exception as e:
        func_name = _getframe().f_code.co_name
        print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
        return False


def set_user_data(user_id, key, value):
    with Vedis(private_constants.db_users) as db:
        try:
            user = get_user(user_id)
            user.update({key: value})
            db[user_id] = user
        except Exception as e:
            func_name = _getframe().f_code.co_name
            print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
            return False


def remove_user_data(user_id, key):
    with Vedis(private_constants.db_users) as db:
        try:
            user = get_user(user_id)
            out = user.pop(key)
            db[user_id] = user
            return out
        except Exception as e:
            func_name = _getframe().f_code.co_name
            print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
            return False


def set_moder_status(user_id, message, status='requires_confirmation'):
    try:
        set_user_data(user_id, 'moderation', status)
        if status == 'deny':
            bot_actions.send_message(user_id,
                                     'Отправленный вами текст не прошел модерацию. В случае, если вас интересует '
                                     'функционал, предоставляемый мной, просьба отправить корректный текст, '
                                     'написанный в соответствии с показанным примером. Если имеете претензии '
                                     'к модерации, просьба связаться с создателем бота.')
        if status == 'confirm':
            bot_actions.send_message(user_id,
                                     'Текст успешно прошел модерацию!')
            if get_user_data(user_id, 'updating') == 'updating_process':
                set_user_data(user_id, 'updating', 'updated')
            set_user_template(message, user_id)
    except Exception as e:
        func_name = _getframe().f_code.co_name
        print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
        return False


def update_data_value(user_id, key, value):
    with Vedis(private_constants.db_file) as db:
        try:
            last_data = get_user_data(user_id, 'last_sending_date')
            new_data = get_data(user_id)
            if last_data in new_data['DATA'].keys():
                new_data['DATA'][last_data].update({key: value})
            else:
                new_data['DATA'].update({last_data: {key: value}})
            db[user_id] = new_data
            return True
        except Exception as e:
            func_name = _getframe().f_code.co_name
            print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
            return False


def delete_user_data(user_id):
    with Vedis(private_constants.db_users) as db:
        try:
            del db[user_id]
            users = ast.literal_eval(db['USERS'].decode('utf-8'))
            users.remove(user_id)
            db['USERS'] = users
        except Exception as e:
            func_name = _getframe().f_code.co_name
            print(f'{e.__class__.__name__} while running "{func_name}" 1 with args: {e.args}')
    with Vedis(private_constants.db_file) as db:
        try:
            del db[user_id]
        except Exception as e:
            func_name = _getframe().f_code.co_name
            print(f'{e.__class__.__name__} while running "{func_name}" 2 with args: {e.args}')
    with Vedis(private_constants.db_state_file) as db:
        try:
            del db[user_id]
        except Exception as e:
            func_name = _getframe().f_code.co_name
            print(f'{e.__class__.__name__} while running "{func_name}" 3 with args: {e.args}')


def init_user(user_id):
    with Vedis(private_constants.db_users) as db:
        try:
            user = dict()
            db[user_id] = user
        except (KeyError, OSError):
            return False
        return True


def get_users():
    with Vedis(private_constants.db_users) as db:
        try:
            users = ast.literal_eval(db['USERS'].decode('utf-8'))
            return users
        except (KeyError, OSError) as e:
            func_name = _getframe().f_code.co_name
            print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
            return None


def set_user_theme(message, user_id):
    try:
        if get_user_data(user_id, 'updating') == 'updating_process':
            if not message:
                bot_actions.send_message(user_id,
                                         'Введите тему письма.\nПример:\n'
                                         '<i>Показания ИПУ по адресу ул. Пушкина, д. 1, кв. 2</i>',
                                         parse_mode='HTML')
                set_state(user_id, constants.States.S_SET_MAILTHEME.value)
                return
        set_user_data(user_id, 'mail_theme', message)
        if get_user_data(user_id, 'updating') == 'updating_process':
            bot_actions.send_message(user_id, 'Данные успешно изменены.')
            set_state(user_id, get_user_data(user_id, 'last_state'))
            set_user_data(user_id, 'updating', 'false')
        else:
            bot_actions.send_message(user_id, 'Введите e-mail получателя.\nМожете ввести несколько адресов через '
                                              'пробел.\nЕсли хотите проверять то, что приходит получателю, можете'
                                              'ввести, в том числе, свой e-mail:')
            set_state(user_id, constants.States.S_SET_MAIL_TO.value)
    except Exception as e:
        func_name = _getframe().f_code.co_name
        print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
        return False


def set_user_mailto(message, user_id):
    try:
        if get_user_data(user_id, 'updating') == 'updating_process':
            if not message and get_current_state(user_id) != constants.States.S_SET_MAIL_TO.value:
                bot_actions.send_message(user_id, 'Введите e-mail получателя.\nМожете ввести несколько адресов через '
                                                  'пробел.\nЕсли хотите проверять то, что приходит получателю, можете'
                                                  'ввести, в том числе, свой e-mail:')
                set_state(user_id, constants.States.S_SET_MAIL_TO.value)
                return
        check = data_processing.msg_check(message, 'mail_to')
        if not isinstance(check, bool):
            if check > 1:
                bot_actions.send_message(user_id,
                                         'Один из отправленных вами адресов содержит ошибки, введите адреса еще'
                                         ' раз и проверьте корректность написанного.')
            else:
                bot_actions.send_message(user_id, 'Отправленный вами адрес содержит ошибки, введите адрес еще раз'
                                                  ' и проверьте корректность написанного.')
            return
        else:
            set_user_data(user_id, 'mail_to', message)
            if get_user_data(user_id, 'updating') == 'updating_process':
                bot_actions.send_message(user_id, 'Данные успешно изменены.')
                set_state(user_id, get_user_data(user_id, 'last_state'))
                set_user_data(user_id, 'updating', 'false')
            else:
                bot_actions.send_message(user_id, 'Мне нужно определить ваш часовой пояс. '
                                                  'Пожалуйста, напишите точное время в городе, где вы находитесь.')
                set_state(user_id, constants.States.S_SET_TIMEZONE.value)
    except Exception as e:
        func_name = _getframe().f_code.co_name
        print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
        return False


def set_user_timezone(message, user_id):
    try:
        if get_user_data(user_id, 'updating') == 'updating_process':
            if not message and get_current_state(user_id) != constants.States.S_SET_TIMEZONE.value:
                bot_actions.send_message(user_id, 'Мне нужно определить ваш часовой пояс. '
                                                  'Пожалуйста, напишите точное время в городе, где вы находитесь.')
                set_state(user_id, constants.States.S_SET_TIMEZONE.value)
                return
        if data_processing.check_correction_data(user_id, 'at_time', message):
            timezone = get_user_tz_delta(message)
            set_user_data(user_id, 'tz_delta', timezone)
        else:
            return
        if get_user_data(user_id, 'updating') == 'updating_process':
            bot_actions.send_message(user_id, 'Данные успешно изменены.')
            set_state(user_id, get_user_data(user_id, 'last_state'))
            set_user_data(user_id, 'updating', 'false')
        else:
            bot_actions.bot_send_keyboard('Выберите периодичность сбора данных', user_id,
                                          {key: value[0] for (key, value) in constants.choose_period.items()})
            set_state(user_id, constants.States.S_SET_DATE.value)
    except Exception as e:
        func_name = _getframe().f_code.co_name
        print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
        return False


def set_user_last_date(user_id, date_str):
    try:
        set_user_data(user_id, 'last_sending_date', date_str)
    except Exception as e:
        func_name = _getframe().f_code.co_name
        print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
        return False


def set_user_last_state(user_id, state):
    try:
        set_user_data(user_id, 'last_state', state)
    except Exception as e:
        func_name = _getframe().f_code.co_name
        print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
        return False


def set_user_next_date(user_id):
    try:
        user = get_user(user_id)
        set_user_data(user_id, 'next_date', str(data_processing.count_timedelta(user)))
    except Exception as e:
        func_name = _getframe().f_code.co_name
        print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
        return False


def set_user_date(message, user_id):
    try:
        if get_user_data(user_id, 'updating') == 'updating_process':
            if not message and get_current_state(user_id) != constants.States.S_SET_DATE.value:
                corquest_keys = [list(x.keys())[0] for x in constants.corQuests]
                print([remove_user_data(user_id, item) for item in corquest_keys if get_user_data(user_id, item)])
                bot_actions.bot_send_keyboard('Выберите периодичность сбора данных', user_id,
                                              {key: value[0] for (key, value) in constants.choose_period.items()})
                set_state(user_id, constants.States.S_SET_DATE.value)
                return
        set_user_data(user_id, 'send_period', message)
        user = get_user(user_id)
        for item in constants.corQuests:
            item_key = list(item.keys())[0]
            if all([item_key in constants.choose_period[user['send_period']], item_key not in user.keys()]):
                bot_actions.send_message(user_id,
                                         item[item_key][0])
                break
        set_state(user_id, constants.States.S_CORRECT_DATE.value)
    except Exception as e:
        func_name = _getframe().f_code.co_name
        print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
        return False


def correct_user_date(message, user_id):
    try:
        user = get_user(user_id)
        for item in constants.corQuests:
            item_key = list(item.keys())[0]
            period_details = constants.choose_period[get_user_data(user_id, 'send_period')]
            if all([item_key in period_details, item_key not in user.keys()]):
                if data_processing.check_correction_data(user_id, item_key, message):
                    set_user_data(user_id, item_key, message)
                    user = get_user(user_id)
                    if item_key == period_details[-1]:
                        continue
                    for next_item in constants.corQuests:
                        item_key = list(next_item.keys())[0]
                        if all([item_key in period_details, item_key not in user.keys()]):
                            bot_actions.send_message(user_id, next_item[item_key][0])
                            break
                    return
                else:
                    return

        set_state(user_id, constants.States.S_SET_TIMER.value)
        set_user_data(user_id, 'next_date', str(data_processing.count_timedelta(user)))
        if get_user_data(user_id, 'updating') != 'updating_process':
            set_user_data(user_id, 'collecting', 'true')
            append_user(user_id)
        else:
            bot_actions.send_message(user_id, 'Данные успешно изменены.')
        get_user(user_id, return_obj=False)
        set_user_data(user_id, 'updating', 'false')
        return 'collect'

    except Exception as e:
        func_name = _getframe().f_code.co_name
        print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
        return False


def append_user(user_id):
    with Vedis(private_constants.db_users) as db:
        try:
            users = ast.literal_eval(db['USERS'].decode('utf-8'))
            users.append(user_id)
            db['USERS'] = users
        except Exception as e:
            func_name = _getframe().f_code.co_name
            print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}'
                  f'First user in DB')
            users = [user_id]
            db['USERS'] = users


def set_user_template(message, user_id):
    try:
        if get_user_data(user_id, 'updating') == 'updating_process':
            if not message:
                bot_actions.send_message(user_id,
                                         'Введите текст письма. Следуйте примеру, выделяя места появления данных'
                                         ' и текущей даты фигурными скобками. Пример:\n\n'
                                         '<i>Добрый день!\n'
                                         'Показания ИПУ по адресу ул. Пушкина, д. 1, кв. 2 на {дата}:\n\n'
                                         'Электроэнергия: {показания счетчика электроэнергии}\n'
                                         'Холодное водоснабжение: {показания счетчика холодной воды}\n'
                                         'Горячее водоснабжение: {показания счетчика горячей воды}\n\n'
                                         'С уважением, Петров А. А.</i>',
                                         parse_mode='HTML')
                set_state(user_id, constants.States.S_SET_TEMPLATE.value)
                set_moder_status(user_id, message, 'new')
                return
        print(str(get_user_data(user_id, 'moderation')))
        if not get_user_data(user_id, 'moderation'):
            set_moder_status(user_id, message, 'new')
        if get_user_data(user_id, 'moderation') == 'confirm':
            if get_user_data(user_id, 'updating') != 'updated':
                bot_actions.send_message(user_id,
                                         'Введите тему письма.\nПример:\n'
                                         '<i>Показания ИПУ по адресу ул. Пушкина, д. 1, кв. 2</i>',
                                         parse_mode='HTML')
                set_state(user_id, constants.States.S_SET_MAILTHEME.value)
            else:
                set_user_data(user_id, 'updating', 'false')
                bot_actions.send_message(user_id, 'Данные успешно изменены.')
                set_state(user_id, get_user_data(user_id, 'last_state'))
        elif get_user_data(user_id, 'moderation') == 'requires_confirmation':
            bot_actions.send_message(user_id,
                                     'Ваше сообщение находится на модерации. Оформление шаблона продолжится позже.')
        elif get_user_data(user_id, 'moderation') in ('deny', 'new'):
            if not message.count('{') == message.count('}'):
                bot_actions.send_message(user_id,
                                         'Некорректно выделены переменные. Каждая из них должна '
                                         'быть заключена в две фигурные скобки - '
                                         'на пример {переменная раз} и {переменная два}')
                return
            variables = {str(i + 20): segment.split('}')[0] for (i, segment) in enumerate(message.split('{')) if
                         '}' in segment and 'дата' not in segment}
            set_user_data(user_id, 'mail_text', message)
            set_user_data(user_id, 'vars', variables)
            bot_actions.send_message(user_id,
                                     'Ваше сообщение отправлено на модерацию.'
                                     '\nПосле подтверждения, оформление шаблона продолжится позже.')

            set_moder_status(user_id, message=message)
            print(message)
            bot_actions.bot_send_keyboard(message,
                                          private_constants.moder_id,
                                          {f'confirm {user_id}': 'Одобрить',
                                           f'deny {user_id}': 'Отклонить'})
    except Exception as e:
        func_name = _getframe().f_code.co_name
        print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
        return False


def check_collect_progress(user_id):
    try:
        user = get_user(user_id)
        data = get_last_data(user_id)
        user_var_len = len(user['vars'].keys())
        collected_vars_len = len(data.keys())
        return [user_var_len, collected_vars_len]
    except Exception as e:
        func_name = _getframe().f_code.co_name
        print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
        return None


def swap_collect(user_id):
    try:
        set_user_data(user_id, 'collecting', 'false' if get_user_data(user_id, 'collecting') == 'true' else 'true')
    except Exception as e:
        func_name = _getframe().f_code.co_name
        print(f'{e.__class__.__name__} while running "{func_name}" with args: {e.args}')
        return False
