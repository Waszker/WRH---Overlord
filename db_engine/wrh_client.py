from sqlalchemy import Column, Integer, String, text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from db_engine import Base


class WRHClient(Base):
    """
    Class representing connected WRH device, authenticated in the system.
    Each device has its own id, secret token and other parameters stored in appropriate table.
    """
    __tablename__ = 'wrh_client'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    token = Column(String, nullable=False)
    measurements = relationship("Measurement")


class Measurement(Base):
    __tablename__ = 'measurement'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('wrh_client.id'))
    module_type = Column(Integer, nullable=False)
    module_id = Column(Integer, nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    data = Column(JSONB, nullable=False, server_default=text("'{}'"))
