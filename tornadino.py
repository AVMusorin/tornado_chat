import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.template
from tornado import gen
import telegramBots
from bot_settings import CHAT_ID
import os
import datetime
import json


class WSHandler(tornado.websocket.WebSocketHandler):

    def __init__(self, application, request, **kwargs):
        super(WSHandler, self).__init__(application, request, **kwargs)
        self.conn, self.cur = telegramBots.connect_postgres()
        # bot(tuple) with id(int), token(str), ready(boolean), last_message(str), customer_asked(boolean)
        self.get_bot(self.conn, self.cur)

    @gen.coroutine
    def get_bot(self, conn, cur):
        while True:
            bot = telegramBots.get_free_bot(conn, cur)
            if bot:
                self.bot_token = bot[1]
                self.customer_asked = bot[4]
                # занять бота
                telegramBots._make_bot_busy(self.conn, self.cur, self.bot_token)  
                break
            else:
                print('Ждать')
                yield gen.sleep(5)


    def check_origin(self, origin):
        return True


    def bot_callback(self):
        ans_telegram = telegramBots.get_updates(self.bot_token, self.conn, self.cur)
        if ans_telegram:
            print(ans_telegram)
            self.write_message(ans_telegram)
    

    def open(self):
        print ('connection opened...')
        self.telegram_loop = tornado.ioloop.PeriodicCallback(self.bot_callback, 3000) # callback каждые 3сек
        self.telegram_loop.start()
    

    def on_message(self, message):
        if not self.customer_asked:
            self.customer_asked = True
            # обновить значение в бд, что клиент задал вопрос
            telegramBots._update_customer_asked(self.conn, self.cur, self.bot_token, True)
        telegramBots.send_message(self.bot_token, CHAT_ID, message)

    def on_close(self):
        print ('connection closed...')
        telegramBots.send_message(self.bot_token, CHAT_ID, "Пользователь закрыл чат")
        self.telegram_loop.stop()
        telegramBots._make_bot_free(self.conn, self.cur, self.bot_token)
        telegramBots._update_customer_asked(self.conn, self.cur, self.bot_token, False)


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



