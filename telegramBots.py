from telebot import TeleBot
from telebot import apihelper
from bot_settings import db
import psycopg2


def get_updates(token, conn, cur, offset=None, limit=None, timeout=20):
    ''' Возвращает сообщение из телеграма '''
    json_updates = apihelper.get_updates(token, offset, limit, timeout) #TODO обработать ошибку ApiException
    try:
        answer = json_updates[-1]['message']['text']
    except IndexError:
        answer = ''
    if is_customer_asked(conn, cur, token):
        if not is_last_message(conn, cur, token, answer):
            _update_last_message(conn, cur, token, answer)
            return answer
    else:
        _update_last_message(conn, cur, token, answer)


def send_message(token, chat_id, text):
    '''Отправить сообщение менеджеру в телеграм'''
    apihelper.send_message(token, chat_id, text)


def connect_postgres(**kwargs):
    '''
    TODO: Возможность передать через kwargs аргументы для поключения
    '''
    try:
        conn = psycopg2.connect(dbname=db['db_name'],
                                user=db['user'],
                                password=db['password'])
    except Exception as e:
        print(e, 'Ошибка при подключении к posqgres')
        raise e
    cur = conn.cursor()
    return conn, cur
    

def _update_last_message(conn, cur, token, message, **kwargs):
    query = "UPDATE chat SET last_message = %s WHERE token = %s"
    data = [message, token]
    try:
        cur.execute(query, data)
        conn.commit()
    except Exception as e:
        print(e, 'Ошибка при попытке обновить последнее сообщение на %s' %message)
        raise e


def is_last_message(conn, cur, token, message, **kwargs):
    query = "SELECT last_message FROM chat WHERE token = %s"
    data = [token, ]
    try:
        cur.execute(query, data)
        last_message = cur.fetchone()
        if last_message:
            if last_message[0] == message:
                return True
        return False
    except Exception as e:
        print(e, 'Ошибка при определении последнего сообщения')
        raise e


def _update_customer_asked(conn, cur, token, to_value):
    '''to_value(boolean)'''
    query = "UPDATE chat SET customer_asked = %s WHERE token = %s"
    data = [to_value, token]
    try:
        cur.execute(query, data)
        conn.commit()
    except Exception as e:
        print(e, 'Ошибка при попытке обновить "customer_asked" на %s' %to_value)
        raise e


def is_customer_asked(conn, cur, token):
    query = "SELECT customer_asked FROM chat WHERE token = %s"
    data = [token, ]
    try:
        cur.execute(query, data)
        customer_asked = cur.fetchone()
        return customer_asked[0]
    except Exception as e:
        print(e, "Ошибка при попытке узнать написал ли пользователь сообщение или еще нет")
        raise e


def get_free_bot(conn, cur):
    '''
    Возвращает 
    (id, token, ready, last_message, customer_asked)
    '''
    query = "SELECT * FROM chat WHERE ready = True"
    try:
        cur.execute(query)
        bot = cur.fetchone()
        if bot:
            return bot
        else:
            return None
    except Exception as e:
        print(e, "Ошибка при попытке найти свободного бота")
        raise e


def _make_bot_busy(conn, cur, token):
    query = "UPDATE chat SET ready = False WHERE token = %s"
    data = [token,]
    try:
        cur.execute(query, data)
        conn.commit()
    except Exception as e:
        print(e, 'Ошибка при попытке изменить значение "ready" на False')
        raise e


def _make_bot_free(conn, cur, token):
    query = "UPDATE chat SET ready = True WHERE token = %s"
    data = [token,]
    try:
        cur.execute(query, data)
        conn.commit()
    except Exception as e:
        print(e, 'Ошибка при попытке изменить значение "ready" на True')
        raise e
