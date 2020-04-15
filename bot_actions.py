import requests
from telebot import types
from private_constants import URL


def send_message(chat_id, text='default text', reply_markup=None, parse_mode=None):
    answer = {'chat_id': chat_id, 'text': text}
    if reply_markup:
        answer.update({'reply_markup': reply_markup})
    if parse_mode:
        answer.update({'parse_mode': parse_mode})
    r = requests.post(URL + 'sendMessage', json=answer)
    return r.json()


def bot_send_keyboard(msg_text, user_id, callbacks):
    markup = types.InlineKeyboardMarkup()
    for key, value in callbacks.items():
        markup.add(types.InlineKeyboardButton(text=value,
                                              callback_data=key))
    send_message(chat_id=user_id, text=msg_text,
                 reply_markup=markup.to_json())
