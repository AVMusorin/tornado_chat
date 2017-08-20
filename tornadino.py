import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.template
from tornado import gen
import telegramBots
from bot_settings import CHAT_ID, LIVING_TIME
import os
import datetime
import json


class WSHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        super(WSHandler, self).__init__(application, request, **kwargs)
        self.conn, self.cur = telegramBots.connect_postgres()
        _token = telegramBots.used_remote_ip(self.conn, self.cur, request.remote_ip)
        self.user_id = None
        self.name = ""
        # Если открыт сокет с таким же ip 
        if _token:
            bot = telegramBots.get_bot(self.conn, self.cur, _token)
            self.bot_token = bot[1]
            self.customer_asked = bot[4]
            self.user_id = bot[6]
        else:
            self.get_bot(self.conn, self.cur, request.remote_ip)


    def get_bot(self, conn, cur, ip):
        while True:
            bot = telegramBots.get_bot(conn, cur)
            if bot:
                self.bot_token = bot[1]
                self.customer_asked = bot[4]
                # занять бота
                telegramBots._make_bot_busy(self.conn, self.cur, self.bot_token)  
                telegramBots.add_remote_ip(self.conn, self.cur, self.bot_token, ip)
                break


    def check_origin(self, origin):
        return True


    def previous_dialog(self, user_id):
        messages = telegramBots.get_messages(self.conn, self.cur, user_id)
        if telegramBots.check_living_time(self.conn, self.cur, self.user_id, LIVING_TIME, messages=messages):
            while messages:
                message = messages.pop()
                # Если сообщение от менеджера
                if message[1]:
                    self.write_message(message[0])
                else:
                    self.write_message('CLIENT:' + message[0])


    def bot_callback(self):
        ans_telegram = telegramBots.get_updates(self.bot_token, self.conn, self.cur)
        if ans_telegram:
            self.write_message(ans_telegram)
            telegramBots.add_message_from_manager(self.conn, self.cur, ans_telegram, self.user_id)
    

    def open(self):
        print ('connection opened...')
        # будем опрашивать сервер telegram каждые 3сек
        self.telegram_loop = tornado.ioloop.PeriodicCallback(self.bot_callback, 3000) # callback каждые 3сек
        self.telegram_loop.start()
        if self.user_id:
            self.previous_dialog(self.user_id)
    

    def on_message(self, message):
        if '@' in message and '|' in message:
            self.name = message.split('|')[0]
            self.email = message.split('|')[1]
            if self.user_id is None:
                _id = telegramBots.get_user(self.conn, self.cur, self.name, self.email)
                if _id:
                    self.user_id = _id
                    self.previous_dialog(self.user_id)
                else:
                    telegramBots.add_user(self.conn, self.cur, self.name, self.email)
                    self.user_id = telegramBots.get_user(self.conn, self.cur, self.name, self.email)
                telegramBots.add_user_to_bot(self.conn, self.cur, self.bot_token, self.name, self.email)
        else:
            if not self.customer_asked:
                self.customer_asked = True
                # обновить значение в бд, что клиент задал вопрос
                telegramBots._update_customer_asked(self.conn, self.cur, self.bot_token, True)
            telegramBots.send_message(self.bot_token, CHAT_ID, self.name + ': ' + message)
            if self.user_id:
                telegramBots.add_message_from_client(self.conn, self.cur, message, self.user_id)

    def on_close(self):
        print ('connection closed...')
        telegramBots.send_message(self.bot_token, CHAT_ID, "Пользователь закрыл чат")
        self.telegram_loop.stop()
        telegramBots._make_bot_free(self.conn, self.cur, self.bot_token)
        telegramBots._update_customer_asked(self.conn, self.cur, self.bot_token, False)
        telegramBots.delete_remote_ip(self.conn, self.cur, self.bot_token)
        telegramBots.delete_user_from_bot(self.conn, self.cur, self.bot_token)


settings = {
    # "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "cookie_secret": "5lRGlDANTs+fH8NKl2VYcf0zzRnUx0otij8rgH+8Rj0=",
    "xsrf_cookies": False,
}

application = tornado.web.Application([
  (r'/ws', WSHandler),
], **settings)

if __name__ == "__main__":
    application.listen(8080)
    tornado.ioloop.IOLoop.current().start()



