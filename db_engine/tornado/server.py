import asyncio
import os
from datetime import datetime, timedelta

import tornado
from tornado.web import RequestHandler
from tornado_sqlalchemy import as_future

from db_engine import WRH_MODULES
from db_engine.models import Module
from db_engine.overlord_decorators import with_session
from utils.io import log


class BaseWrhForm(RequestHandler):
    MODULES_CACHE_TIME = timedelta(minutes=10)
    last_modules_update = modules = installed_module_types = None
    module_class_by_wrhid = {c.WRHID: c for c in WRH_MODULES}

    def initialize(self, sessionmaker):
        self.sessionmaker = sessionmaker

    async def prepare(self):
        # TODO: Check that incoming connections are are only from within VPN!
        if not self.last_modules_update or abs(datetime.now() - self.last_modules_update) > self.MODULES_CACHE_TIME:
            log('Invalidating cached modules list and syncing new one')
            BaseWrhForm.last_modules_update = datetime.now()
            BaseWrhForm.modules = await self._get_modules()
            BaseWrhForm.installed_module_types = list({m.type for m in self.modules})

    @with_session
    async def _get_modules(self, session):
        return await asyncio.wrap_future(as_future(session.query(Module).all))


class MainForm(BaseWrhForm):
    def get(self):
        requested_module_type = self.get_argument('class', '')
        kwargs = {
            'classes': self.installed_module_types,
            'requested_modules': [m for m in self.modules if m.type == requested_module_type],
            'requested_class': self.module_class_by_wrhid.get(requested_module_type, None)
        }
        self.render("html/index.html", **kwargs)


class ModuleRequestForm(BaseWrhForm):
    @with_session
    async def post(self, session):
        response = ''
        module_class = self.get_argument('class', '')
        request_message = self.get_argument('message', '')
        mclass = self.module_class_by_wrhid.get(module_class, None)
        if mclass:
            response = await mclass.parse_request(session, request_message)
        self.finish(response)


class TornadoServer:
    """
    Class responsible for maintaining Tornado server.
    """

    def __init__(self, listening_port, sessionmaker):
        self.port = listening_port
        self.sessionmaker = sessionmaker
        self.application = self._create_tornado_app()
        self.server = None

    def start(self):
        if not self.server:
            asyncio.set_event_loop(asyncio.new_event_loop())
            log(f'Starting Tornado server on port {self.port}')
            self.server = self.application.listen(self.port)
            tornado.ioloop.IOLoop.instance().start()

    def stop(self):
        if self.server:
            log('Stopping running Tornado server')
            self.server.stop()
            self.server = None
            tornado.ioloop.IOLoop.instance().stop()

    def _create_tornado_app(self):
        return tornado.web.Application([
            (r"/", MainForm, {'sessionmaker': self.sessionmaker}),
            (r"/request", ModuleRequestForm, {'sessionmaker': self.sessionmaker}),
        ],
            debug=True,
            static_path=os.path.join(os.path.dirname("db_engine/tornado"), "tornado")
        )
