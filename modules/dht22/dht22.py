import asyncio
from datetime import datetime

from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, DECIMAL
from tornado_sqlalchemy import as_future

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
    def get_html(cls, module):
        if not cls.html_repr:
            with open('modules/dht22/repr.html', 'r') as f:
                cls.html_repr = f.read()
        return cls.html_repr.format(id='{}{}'.format(module.id, module.client_id), name=module.name,
                                    request='{0.id},{0.client_id}'.format(module), wrhid=cls.WRHID)

    @classmethod
    async def parse_request(cls, session, request_string):
        dates, temp_data, hum_data = [], [], []
        module_id, client_id = request_string.split(',')  # TODO: Beware of unpacking error!
        # TODO: Add possibility to change from_date and until_date values from user interface
        data = await asyncio.wrap_future(as_future(session.execute(cls._get_monthly_average_query(),
                                                                   {'module_id': module_id, 'client_id': client_id,
                                                                    'from_date': datetime(year=2000, month=1, day=1),
                                                                    'until_date': datetime.now()}).fetchall))
        for temp, hum, date in data:
            temp_data.append(str(temp))
            hum_data.append(str(hum))
            dates.append('"{}"'.format(date))
        formatted = """
                {{
                    "labels":[{month_list}],
                    "datasets":[
                    {{"label":"temperature","data":[{temp_data}],"borderColor":"rgb(175,92,22)"}},
                    {{"label":"humidity","data":[{hum_data}],"borderColor":"rgb(50,50,192)"}}
                    ]
                }}
                """.format(month_list=','.join(dates), temp_data=','.join(temp_data), hum_data=','.join(hum_data))
        return formatted

    @classmethod
    def get_object(cls, measurement_object):
        obj = measurement_object
        temp, hum = measurement_object.data['temperature'], measurement_object.data['humidity']
        if temp is None or hum is None:
            raise ValueError('No point in storing dht22 measurement if both temperature and humidity values are None')
        return cls(id=obj.id, client_id=obj.client_id, module_id=obj.module_id, timestamp=obj.timestamp,
                   temperature=temp, humidity=hum)

    @classmethod
    def _get_monthly_average_query(cls):
        query = """
        SELECT CAST(avg(temperature) AS NUMERIC(4, 2)), CAST(avg(humidity) AS NUMERIC(4, 2)), timestamp::DATE
        FROM {table_name}
        WHERE client_id = :client_id and timestamp >= :from_date and timestamp <= :until_date
        GROUP BY timestamp::DATE ORDER BY timestamp::DATE
        """.format(table_name=cls.__tablename__)
        return query
