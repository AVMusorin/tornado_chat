import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.template
import telegramBots
from bot_settings import TELEGRAM_BOTS, CHAT_ID
import os
import datetime
import json


class WSHandler(tornado.websocket.WebSocketHandler):

    def __init__(self, application, request, **kwargs):
        super(WSHandler, self).__init__(application, request, **kwargs)
        for bot in TELEGRAM_BOTS:
            if bot['ready']:
                self.token = bot['token']
                bot['ready'] = False
        # TODO: если нет ни одного свободного бота,то
        # ждать какое то время и опять обой всех ботов


    def check_origin(self, origin):
        return True


    def bot_callback(self):
        ans_telegram = telegramBots.get_updates(self.token)
        if ans_telegram:
            self.write_message(ans_telegram)
    

    def open(self):
        print ('connection opened...')
        self.telegram_loop = tornado.ioloop.PeriodicCallback(self.bot_callback, 3000) # callback каждые 3сек
        self.telegram_loop.start()
    

    def on_message(self, message):
        self.bot.send_message(CHAT_ID, message)

    def on_close(self):
        print ('connection closed...')
        self.bot.send_message(CHAT_ID, 'Пользователь закрыл чат')
        self.telegram_loop.stop()


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



