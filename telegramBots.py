from telebot import TeleBot
from telebot import apihelper
from bot_settings import db
import psycopg2
import datetime


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


def add_remote_ip(conn, cur, token, ip):
    query = "UPDATE chat SET remote_ip = %s WHERE token = %s"
    data = [ip, token]
    try:
        cur.execute(query, data)
        conn.commit()
    except Exception as e:
        print(e, 'Ошибка при попытке добавить ip адрес')
        raise e


def used_remote_ip(conn, cur, ip):
    '''
    Вернет token если, какой то из ботов уже использует этот ip, если нет, то верет False
    '''
    query = "SELECT token FROM chat WHERE remote_ip = %s"
    data = [ip]
    try:
        cur.execute(query, data)
        token = cur.fetchone()
        if token:
            return token[0]
        return False
    except Exception as e:
        print('Ошибка произошла при попытке узнать используется ли данный ip адрес')
        raise e


def delete_remote_ip(conn, cur, token):
    ''' Удалить ip адрес у переданного токена '''
    query = "UPDATE chat SET remote_ip = %s WHERE token = %s"
    data = ['', token]
    try:
        cur.execute(query, data)
        conn.commit()
    except Exception as e:
        print(e, 'Ошибка при попытке удалить ip адрес')
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


def get_bot(conn, cur, token = None):
    '''
    Возвращает 
    (id, token, ready, last_message, customer_asked)
    '''
    if token:
        query = "SELECT * FROM chat where token = %s"
        data = [token,]
        try:
            cur.execute(query, data)
            bot = cur.fetchone()
            return bot
        except Exception as e:
            raise e
    else:
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
        conn.rollback()
        print(e, 'Ошибка при попытке изменить значение "ready" на True')
    except Exception as e:
        raise e



def add_user(conn, cur, name, email):
    query = "INSERT INTO users (user_name, user_email) VALUES (%s, %s)"
    data = [name, email]
    try:
        cur.execute(query, data)
        conn.commit()
    except Exception as e:
        print(e, 'Ошибка при попытке добавить нового пользователя')
        raise e


def get_user(conn, cur, name, email)    :
    ''' Если пользователь сущетсвует то вернет его id, если нет то False '''
    query = "SELECT id FROM users WHERE user_name = %s AND user_email = %s"
    data = [name, email]
    try:
        cur.execute(query, data)
        _id = cur.fetchone()
        if _id:
            return _id[0]
        return False
    except Exception as e:
        print(e, 'Ошибка при попытке взять id пользователя')
        raise e


def add_user_to_bot(conn, cur, token, name, email):
    user_id = get_user(conn, cur, name, email)
    if user_id:
        query = "UPDATE chat SET user_id = %s WHERE token = %s"
        data = [user_id, token]
        try:
            cur.execute(query, data)
            conn.commit()
        except Exception as e:
            print(e, 'Ошибка при попытке добавить пользователя боту')
            raise e


def delete_user_from_bot(conn, cur, token):
    query = "UPDATE chat SET user_id = null WHERE token = %s"
    data = [token,]
    try:
        cur.execute(query, data)
        conn.commit()
    except Exception as e:
        print(e, "Ошибка при удалении пользователя у бота")
        raise e


def add_message_from_manager(conn, cur, message, user_id):
    query = "INSERT INTO messages (message, user_id, manager, create_date) VALUES (%s, %s, True, now())"
    data = [message, user_id]
    try:
        cur.execute(query, data)
        conn.commit()
    except Exception as e:
        print(e, 'Ошибка при попытке добавить сообщение от менеджера')
        raise e   


def add_message_from_client(conn, cur, message, user_id):
    query = "INSERT INTO messages (message, user_id, manager, create_date) VALUES (%s, %s, False, now())"
    data = [message, user_id]
    try:
        cur.execute(query, data)
        conn.commit()
    except Exception as e:
        print(e, 'Ошибка при попытке добавить сообщение от клиента')
        raise e   


def get_messages(conn, cur, user_id):
    query = "SELECT message, manager, create_date FROM messages WHERE user_id = %s ORDER BY create_date DESC"
    data = [user_id]
    try:
        cur.execute(query, data)
        messages = cur.fetchall()
        return messages
    except Exception as e:
        print(e, "Ошибка при попытке достать все сообщения для пользователя %s" %user_id)
        raise e


def check_living_time(conn, cur, user_id, living_time, messages=None):
    ''' Если последнее сообщение было прислано позже чем living_time, то вернется False '''
    if messages is None:
        messages = get_messages(conn, cur, user_id)
    if messages:
        last_message = messages[-1]
        difference = last_message[2] - datetime.datetime.today()
        if difference.days < living_time:
            return True
        delete_messeges(conn, cur, user_id)
        return False


def delete_messeges(conn, cur, user_id):
    query = "DELETE FROM messages WHERE user_id = %s"
    data = [user_id,]
    try:
        cur.execute(query, data)
        conn.commit()
    except Exception as e:
        print(e, "Ошибка при удалении сообщении")
        raise e

if __name__ == '__main__':
    conn, cur = connect_postgres()
    print(get_messages(conn, cur, 2))