from telebot import TeleBot
from telebot import apihelper
from bot_settings import TELEGRAM_BOTS


def get_updates(token, offset=None, limit=None, timeout=20):
    ''' Возвращает сообщение из телеграма 
        TODO: При первом конаткте с клиентов в браузере функция выдает 
        свое последнее сообщение
        '''
    json_updates = apihelper.get_updates(token, offset, limit, timeout) #TODO обработать ошибку ApiException
    try:
        answer = json_updates[-1]['message']['text']
    except IndexError:
        answer = ''
    for bot in TELEGRAM_BOTS:
         if bot['token'] == token:
            if bot['customer_asked']:
                if bot['last_message'] != answer:
                    bot['last_message'] = answer
                    return answer
            else:
                # если не было до этого сообщений от пользователя
                bot['last_message'] = answer
                # записать в последнее слово 
                # и отметить customer_asked в True
                bot['customerd_asked'] = True
                











