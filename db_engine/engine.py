import hashlib
import json
import signal
import socket
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_engine import Base, WRH_MODULES
from db_engine.constants import DB_CONFIG_FILE
from db_engine.models import WRHClient, Measurement, Module
from db_engine.overlord_decorators import with_session
from db_engine.tornado.server import TornadoServer
from utils.decorators import with_open, in_thread, log_exceptions
from utils.io import log, Color, wrh_input, non_empty_positive_numeric_input
from utils.sockets import wait_bind_socket, await_connection

npinput = non_empty_positive_numeric_input


class DBEngine:
    def __init__(self, port, tornado_port):
        self.socket = None
        self.port = port
        self._should_end = False
        log('Following additional db models have been found: \n*{}'.format(
            '\n*'.join(str(m.__name__) for m in WRH_MODULES)), Color.BLUE)
        self.wrh_modules = {m.WRHID: m for m in WRH_MODULES}
        self._read_db_configuration()
        self.tornado_server = TornadoServer(tornado_port, self.sessionmaker)

    @property
    def wrh_clients(self):
        # TODO: Check if this is optimal way of obtaining client objects? Are those cached within session?
        session = self.sessionmaker()
        try:
            clients = session.query(WRHClient).all()
        finally:
            session.close()
        return {c.token: c for c in clients}

    def start_work(self):
        if not self.wrh_clients:
            log('No point in running while there are no clients configured!', Color.WARNING)
        else:
            self._should_end = False
            signal.signal(signal.SIGINT, self._sigint_handler)
            self._start_tornado()
            self._await_connections()
            log('Stopping work')
            signal.signal(signal.SIGINT, signal.SIG_DFL)

    def run_interactive(self):
        log('*** Existing clients ***')
        [log(f'{client.id} --- {client.name}', Color.BLUE) for client in self.wrh_clients.values()]
        choices = {1: ('Add new WRH client', self._add_new_client),
                   2: ('Edit existing WRH client', self._modify_client),
                   3: ('Delete existing WRH client', self._delete_client),
                   4: ('Start work', self.start_work), 5: ('Exit', lambda: None)}
        choice = -1
        while choice != 5:
            [log(f'{k}) {v[0]}') for k, v in choices.items()]
            choice = wrh_input(message='> ', input_type=int, sanitizer=lambda x: 1 <= x <= len(choices),
                               allowed_exceptions=(ValueError,))
            choices[choice][1]()  # run selected procedure
            if choice in (1, 2, 3):
                log('Sucess!\n\n', Color.GREEN)

    @with_open(DB_CONFIG_FILE, 'r', ())
    def _read_db_configuration(self, _file_=None):
        try:
            log('Connecting to database')
            db_configuration = json.loads(_file_.read())
            self.db_engine = create_engine('{dialect}://{username}:{password}@{host}:{port}/{database}'.format(
                **db_configuration))
            Base.metadata.create_all(self.db_engine)
            self.sessionmaker = sessionmaker(bind=self.db_engine)
        except (IOError, KeyError) as e:
            log(f'Error when trying to read db configuration: {e}', Color.FAIL)
            raise

    def _await_connections(self):
        predicate = lambda: self._should_end is False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bind_result = wait_bind_socket(self.socket, '', self.port, sleep=10, retries=5, predicate=predicate,
                                       error_message=f'Unable to bind to port {self.port}')
        if bind_result:
            log(f'Listening for incoming connections on port {self.port}')
            self.socket.listen(5)
            await_connection(self.socket, self._new_connection, predicate=predicate, close_connection=False)

    @in_thread
    def _start_tornado(self):
        self.tornado_server.start()

    @in_thread
    def _new_connection(self, connection, address):
        try:
            data = json.loads(connection.recv(4096).decode('utf-8').replace('\0', ''))
            log(f'New connection from {address} who sent: {data}')
            wrh_client = self.wrh_clients.get(data['token'])
            if wrh_client:
                self._update_module_info(wrh_client.id, data['module_id'], data['module_type'], data['module_name'])
                self._upload_new_measurement(wrh_client, data)
        finally:
            connection.close()

    @log_exceptions()
    @with_session
    def _upload_new_measurement(self, session, wrh_client, data):
        measurement = Measurement(client_id=wrh_client.id,
                                  module_id=data['module_id'],
                                  timestamp=datetime.strptime(data['date'], '%Y-%m-%d %H:%M:%S'),
                                  # e.g. 2017-01-01 12:00:00
                                  data=data['measurement'])
        dedicated_model = self.wrh_modules.get(data['module_type'])
        session.add(dedicated_model.get_object(measurement) if dedicated_model else measurement)

    @with_session
    def _update_module_info(self, session, client_id, module_id, module_type, module_name):
        module = session.query(Module).filter(Module.id == module_id, Module.client_id == client_id).first()
        if not module:
            module = Module(id=module_id, client_id=client_id, type=module_type, name=module_name)
            session.add(module)
        elif module.name != module_name:
            module.name = module_name

    @with_session
    def _add_new_client(self, session):
        log('\n*** Adding new WRH client ***')
        client_name = wrh_input(message='Input name of new client: ')
        client = WRHClient(name=client_name, token=self._generate_client_token(client_name))
        session.add(client)

    @with_session
    def _modify_client(self, session):
        log('\n*** Existing clients ***')
        [log(f'{client.id} --- {client.name}', Color.BLUE) for client in self.wrh_clients.values()]
        client_id = npinput(message='Id of client to edit: ')
        to_edit = session.query(WRHClient).filter(WRHClient.id == client_id).first()
        if to_edit:
            to_edit.name = wrh_input(message='Input new name of the client: ')

    @with_session
    def _delete_client(self, session):
        log('\n*** Existing clients ***')
        [log(f'{client.id} --- {client.name}', Color.BLUE) for client in self.wrh_clients.values()]
        client_id = npinput(message='Id of client to remove: ')
        to_remove = session.query(WRHClient).filter(WRHClient.id == client_id).first()
        if to_remove:
            session.delete(to_remove)

    def _sigint_handler(self, *_):
        self.tornado_server.stop()
        self._should_end = True
        if self.socket:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()

    @staticmethod
    def _generate_client_token(client_name):
        return hashlib.sha256(
            '{}{}'.format(client_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')).encode('utf-8')
        ).hexdigest()
