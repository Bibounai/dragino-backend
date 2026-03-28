from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, JSON
from database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    device_eui = Column(String, index=True, nullable=False)
    device_name = Column(String, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    payload = Column(JSON, nullable=True)

    humidity = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    ph = Column(Float, nullable=True)
    conductivity = Column(Float, nullable=True)

    rssi = Column(Float, nullable=True)
    snr = Column(Float, nullable=True)
    f_cnt = Column(Integer, nullable=True)
