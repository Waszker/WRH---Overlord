import json
import socket

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_engine import Base
from db_engine.constants import DB_CONFIG_FILE
from db_engine.wrh_client import WRHClient
from utils.decorators import with_open, in_thread
from utils.io import log, Color, wrh_input
from utils.sockets import wait_bind_socket, await_connection


class DBEngine:
    def __init__(self, port, tornado_port):
        self.socket = None
        self.port = port
        self.tornado_port = tornado_port
        self._should_end = False
        self._read_db_configuration()

    @property
    def wrh_clients(self):
        clients = self.session.query(WRHClient).all()
        return {c.token: c for c in clients}

    def start_work(self):
        if not self.wrh_clients:
            log('No point in running while there are no clients configured!', Color.WARNING)
        else:
            # TODO: Start tornado server
            self._await_connections()
            # TODO: Stop everything

    def run_interactive(self):
        log('*** Existing clients ***')
        [log('{client.id} --- {client.name}'.format(client=client), Color.BLUE) for client in self.wrh_clients.values()]
        choices = {1: ('Add new WRH client', self._add_new_client),
                   2: ('Edit existing WRH client', self._modify_client),
                   3: ('Delete existing WRH client', self._delete_client),
                   4: ('Start work', self.start_work), 5: ('Exit', lambda: None)}
        choice = -1
        while choice != 5:
            [log('{}) {}'.format(k, v[0])) for k, v in choices.items()]
            choice = wrh_input(message='> ', input_type=int, sanitizer=lambda x: 1 <= x <= len(choices),
                               allowed_exceptions=(ValueError,))
            choices[choice][1]()  # run selected procedure

    @with_open(DB_CONFIG_FILE, 'r', ())
    def _read_db_configuration(self, _file_=None):
        try:
            db_configuration = json.loads(_file_.read())
            self.db_engine = create_engine('{dialect}://{username}:{password}@{host}:{port}/{database}'.format(
                **db_configuration))
            Base.metadata.create_all(self.db_engine)
            self.session = sessionmaker(bind=self.db_engine)()
        except (IOError, KeyError) as e:
            log('Error when trying to read db configuration: {}'.format(e), Color.FAIL)
            raise

    def _await_connections(self):
        predicate = lambda: self._should_end is False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bind_result = wait_bind_socket(self.socket, '', self.port, 10, predicate=predicate,
                                       error_message='Unable to bind to port {}'.format(self.port))
        if bind_result:
            self.socket.listen(5)
            await_connection(self.socket, self._new_connection, predicate=predicate)

    @in_thread
    def _new_connection(self, connection, address):
        data = connection.recv(4096)
        log('New connection from {} who sent: {}'.format(address, connection))
        client_token, measurement_data = data.split('|')
        wrh_client = self.wrh_clients.get(client_token)
        if wrh_client:
            wrh_client.save_measurement_to_db(measurement_data)
        connection.sendall('OK')

    def _add_new_client(self):
        log('\n*** Adding new WRH client ***')
        client_name = wrh_input(message='Input name of new client: ')
        client = WRHClient(name=client_name, token='Token')
        self.session.add(client)
        self.session.commit()

    def _modify_client(self):
        pass

    def _delete_client(self):
        pass