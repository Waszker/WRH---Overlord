import json
import socket

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_engine import Base
from db_engine.constants import DB_CONFIG_FILE
from db_engine.wrh_client import WRHClient, Measurement
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
        # TODO: Check if this is optimal way of obtaining client objects? Are those cached within session?
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
            self.session.commit()

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
            await_connection(self.socket, self._new_connection, predicate=predicate, close_connection=False)

    @in_thread
    def _new_connection(self, connection, address):
        data = json.loads(connection.recv(4096).decode('utf-8').replace('\0', ''))
        log('New connection from {} who sent: {}'.format(address, data))
        wrh_client = self.wrh_clients.get(data['token'])
        if wrh_client:
            measurement = Measurement(client_id=wrh_client.id,
                                      module_type=data['module_type'],
                                      module_id=data['module_id'],
                                      timestamp=datetime.strptime(data['date'], '%Y-%m-%d %H:%M:%S'),
                                      # e.g. 2017-01-01 12:00:00
                                      data=data['measurement'])
            self.session.add(measurement)
            self.session.commit()
        connection.close()  # TODO: Await more data instead of closing?

    def _add_new_client(self):
        log('\n*** Adding new WRH client ***')
        client_name = wrh_input(message='Input name of new client: ')
        client = WRHClient(name=client_name, token='Token')
        self.session.add(client)

    def _modify_client(self):
        # TODO: Finish this function
        pass

    def _delete_client(self):
        # TODO: Finish this function
        pass
