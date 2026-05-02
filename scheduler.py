from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from database import SessionLocal, Country
from data_fetcher import get_latest_risk_data
import logging

logging.basicConfig(level=logging.INFO)

def update_all_countries():
    """Tüm ülkelerin risk verilerini günceller (arka planda çalışır)."""
    db: Session = SessionLocal()
    countries = db.query(Country).all()
    for c in countries:
        # Ülke kodu basit bir mapping (gerçek uygulamada tabloda kod tutulur)
        code_map = {"Turkey": "TR", "Germany": "DE", "Iran": "IR", "Israel": "IL", "Ukraine": "UA", "China": "CN", "Russia": "RU"}
        code = code_map.get(c.name, "US")
        new_data = get_latest_risk_data(c.name, code)
        c.conflict_intensity = new_data["conflict_intensity"]
        c.political_stability = new_data["political_stability"]
        c.economic_risk = new_data["economic_risk"]
    db.commit()
    db.close()
    logging.info("Tüm ülkelerin risk verileri güncellendi.")

scheduler = BackgroundScheduler()
scheduler.add_job(update_all_countries, 'interval', hours=6, next_run_time=None)  # 6 saatte bir
scheduler.start()
