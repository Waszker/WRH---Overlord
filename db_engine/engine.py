import json
import socket

from db_engine.constants import DB_CONFIG_FILE
from db_engine.wrh_clients import WRHClient
from utils.decorators import with_open, in_thread
from utils.io import log, Color
from utils.sockets import wait_bind_socket, await_connection


class DBEngine:
    def __init__(self, port):
        self.socket = None
        self.port = port
        self._should_end = False
        self.wrh_clients = {}

        self._read_db_configuration()

    def start_work(self, tornado_port):
        if not self.wrh_clients:
            log('No point in running while there are no clients configured!', Color.WARNING)
        else:
            # TODO: Start tornado server
            self._await_connections()
            # TODO: Stop everything

    def run_interactive(self):
        # TODO: Run interactive procedures e.g. add/remove clients, etc.
        pass

    @with_open(DB_CONFIG_FILE, 'r')
    def _read_db_configuration(self, _file_=None):
        try:
            configurations = json.loads(_file_.read())
            self.wrh_clients = {c['token']: WRHClient(c) for c in configurations}
        except (IOError, KeyError) as e:
            log('Error when trying to read db configuration: {}'.format(e), Color.FAIL)

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
