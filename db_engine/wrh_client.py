from sqlalchemy import Column, Integer, String

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
