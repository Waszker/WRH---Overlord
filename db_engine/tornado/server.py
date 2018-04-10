import os
import signal

import tornado

from utils.io import log, Color


class BaseHandler(tornado.web.RequestHandler):
    pass


class MainForm(BaseHandler):
    pass

application = tornado.web.Application([
    (r"/", MainForm),
],
    debug=True,
    static_path=os.path.join(os.path.dirname("db_engine/tornado"), "tornado")
)


def sigint_handler(*_):
    tornado.ioloop.IOLoop.instance().stop()


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGINT, sigint_handler)
        application.listen(8888)
        log('Tornado: Started.')
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        log(e, Color.EXCEPTION)
