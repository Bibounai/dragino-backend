import os
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import SensorReading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dragino LoRaWAN Backend")

BACKEND_TOKEN = os.environ.get("BACKEND_TOKEN", "")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/uplink")
async def receive_uplink(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    if BACKEND_TOKEN and auth != f"Bearer {BACKEND_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    body = await request.json()
    logger.info("Uplink received: %s", body)

    device_info = body.get("deviceInfo", {})
    device_eui = device_info.get("devEui", "unknown")
    device_name = device_info.get("deviceName", None)
    obj = body.get("object", {})
    rx_info = body.get("rxInfo", [{}])
    rssi = rx_info[0].get("rssi") if rx_info else None
    snr = rx_info[0].get("snr") if rx_info else None
    f_cnt = body.get("fCnt")

    reading = SensorReading(
        device_eui=device_eui,
        device_name=device_name,
        received_at=datetime.utcnow(),
        payload=obj,
        humidity=obj.get("humidity") or obj.get("Hum_SHT"),
        temperature=obj.get("temperature") or obj.get("TempC_SHT"),
        ph=obj.get("ph") or obj.get("PH"),
        conductivity=obj.get("conductivity") or obj.get("EC"),
        rssi=rssi,
        snr=snr,
        f_cnt=f_cnt,
    )
    db.add(reading)
    db.commit()
    logger.info("Saved reading for device %s", device_eui)
    return {"status": "ok"}


@app.get("/api/data")
def get_data(
    device_eui: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(SensorReading).order_by(SensorReading.received_at.desc())
    if device_eui:
        query = query.filter(SensorReading.device_eui == device_eui)
    readings = query.limit(limit).all()
    return [
        {
            "id": r.id,
            "device_eui": r.device_eui,
            "device_name": r.device_name,
            "received_at": r.received_at.isoformat(),
            "humidity": r.humidity,
            "temperature": r.temperature,
            "ph": r.ph,
            "conductivity": r.conductivity,
            "rssi": r.rssi,
            "snr": r.snr,
            "f_cnt": r.f_cnt,
            "payload": r.payload,
        }
        for r in readings
    ]
