from sqlalchemy import create_engine


class WRHClient:
    """
    Class representing connected WRH device, authenticated in the system.
    Each device has its own id, secret token and other parameters stored in appropriate table.
    """

    def __init__(self, db_configuration):
        self.db = create_engine('{dialect}://{username}:{password}@{host}:{port}/{database}'.format(**db_configuration))

    def save_measurement_to_db(self, measurement_data):
        # TODO: Parse measurement
        pass
