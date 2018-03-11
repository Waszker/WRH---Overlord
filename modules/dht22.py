from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, Float

from db_engine import Base


class DHT22(Base):
    WRHID = 'DHT22Module'
    __tablename__ = 'measurement'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('wrh_client.id'), nullable=False, index=True)
    module_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(TIMESTAMP, nullable=False)
    temperature = Column(Float)
    humidity = Column(Float)

    @classmethod
    def get_object(cls, measurement_object):
        obj = measurement_object
        vals = [measurement_object.data['temperature'], measurement_object.data['humidity']]
        for i, v in enumerate(vals):
            try:
                vals[i] = float(v)
            except ValueError:
                vals[i] = None
        return cls(id=obj.id, client_id=obj.client_id, module_id=obj.module_id, timestamp=obj.timestamp,
                   temperature=vals[0], humidity=vals[1])
