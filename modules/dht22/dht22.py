from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, DECIMAL

from db_engine import Base
from modules.base import ModuleBase


class DHT22(Base, ModuleBase):
    WRHID = 'DHT22Module'
    __abstract__ = False
    __tablename__ = 'measurement_dht22'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('wrh_client.id'), nullable=False, index=True)
    module_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(TIMESTAMP, nullable=False)
    temperature = Column(DECIMAL(precision=4, scale=2, asdecimal=False))
    humidity = Column(DECIMAL(precision=4, scale=2, asdecimal=False))

    @classmethod
    def get_html(cls):
        repr = """<div>
                    </div>"""
        return ''
        pass

    @classmethod
    def get_object(cls, measurement_object):
        obj = measurement_object
        temp, hum = measurement_object.data['temperature'], measurement_object.data['humidity']
        if temp is None or hum is None:
            raise ValueError('No point in storing dht22 measurement if both temperature and humidity values are None')
        return cls(id=obj.id, client_id=obj.client_id, module_id=obj.module_id, timestamp=obj.timestamp,
                   temperature=temp, humidity=hum)
