from sqlalchemy import Column, Integer, String, text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from db_engine import Base


class WRHClient(Base):
    __tablename__ = 'wrh_client'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    token = Column(String, nullable=False, unique=True)
    measurements = relationship("Measurement")


class Module(Base):
    __tablename__ = 'module'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('wrh_client.id'), primary_key=True, nullable=False)
    type = Column(String, nullable=False)
    name = Column(String, nullable=False)


class Measurement(Base):
    __tablename__ = 'measurement'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('wrh_client.id'), nullable=False, index=True)
    module_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(TIMESTAMP, nullable=False)
    data = Column(JSONB, nullable=False, server_default=text("'{}'"))
