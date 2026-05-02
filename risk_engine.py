from sqlalchemy.orm import Session
from database import Country
from typing import Dict

def calculate_risk_score(conflict: float, political: float, economic: float) -> float:
    score = (conflict * 0.4) + ((10 - political) * 0.3) + (economic * 0.3)
    return round(score, 2)

def get_risk_level(score: float) -> str:
    if score < 3: return "LOW"
    if score < 6: return "MEDIUM"
    if score < 8: return "HIGH"
    return "EXTREME"

def get_risk_color(level: str) -> str:
    return {"LOW":"#00cc66","MEDIUM":"#ffaa00","HIGH":"#ff4444","EXTREME":"#8b0000"}.get(level, "gray")

def get_full_risk_profile(db: Session, country_name: str) -> Dict:
    country = db.query(Country).filter(Country.name == country_name).first()
    if not country:
        raise ValueError("Ülke bulunamadı")
    score = calculate_risk_score(country.conflict_intensity, country.political_stability, country.economic_risk)
    level = get_risk_level(score)
    return {
        "country": country.name,
        "conflict_intensity": country.conflict_intensity,
        "political_stability": country.political_stability,
        "economic_risk": country.economic_risk,
        "risk_score": score,
        "risk_level": level,
        "risk_color": get_risk_color(level)
    }
