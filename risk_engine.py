from database import get_country, get_all_countries
from typing import Dict, List

def get_full_risk_profile(country: str) -> Dict:
    """
    Bir ülke için risk profilini hesaplar.
    Formül: (conflict * 0.4) + ((10 - political) * 0.3) + (economic * 0.3)
    """
    country_data = get_country(country)
    if not country_data:
        raise ValueError(f"Ülke '{country}' bulunamadı.")
    
    conflict = country_data["conflict_intensity"]
    political = country_data["political_stability"]
    economic = country_data["economic_risk"]
    
    risk_score = (conflict * 0.4) + ((10 - political) * 0.3) + (economic * 0.3)
    risk_score = round(risk_score, 2)
    
    if risk_score < 3:
        risk_level = "LOW"
        risk_color = "green"
    elif risk_score < 6:
        risk_level = "MEDIUM"
        risk_color = "orange"
    elif risk_score < 8:
        risk_level = "HIGH"
        risk_color = "red"
    else:
        risk_level = "EXTREME"
        risk_color = "darkred"
    
    return {
        "country": country,
        "conflict_intensity": conflict,
        "political_stability": political,
        "economic_risk": economic,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_color": risk_color
    }

def get_all_risk_profiles() -> List[Dict]:
    """Tüm ülkelerin risk profilini döndürür."""
    countries = get_all_countries()
    profiles = []
    for c in countries:
        try:
            profiles.append(get_full_risk_profile(c["name"]))
        except ValueError:
            continue
    return profiles
