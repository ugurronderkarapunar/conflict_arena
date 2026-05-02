from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from risk_engine import get_full_risk_profile
from recommendation_engine import get_advice_for_api
from database import get_all_countries, add_country, update_country, delete_country

app = FastAPI(title="Country Risk Intelligence API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CountryData(BaseModel):
    name: str
    conflict_intensity: float
    political_stability: float
    economic_risk: float

@app.get("/risk")
async def get_risk(country: str):
    """Belirtilen ülke için risk skoru, seviyesi ve önerileri döndürür."""
    try:
        profile = get_full_risk_profile(country)
        advice = get_advice_for_api(profile)
        return {
            "country": profile["country"],
            "score": profile["risk_score"],
            "level": profile["risk_level"],
            "conflict_intensity": profile["conflict_intensity"],
            "political_stability": profile["political_stability"],
            "economic_risk": profile["economic_risk"],
            "advice": advice
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/countries")
async def list_countries():
    """Mevcut ülkelerin listesini döndürür."""
    countries = get_all_countries()
    return {"countries": [c["name"] for c in countries]}

@app.post("/add_country")
async def add_new_country(data: CountryData):
    """Yeni bir ülke ekler."""
    success = add_country(data.name, data.conflict_intensity, data.political_stability, data.economic_risk)
    if not success:
        raise HTTPException(status_code=400, detail="Ülke zaten mevcut veya geçersiz veri.")
    return {"message": f"{data.name} başarıyla eklendi."}

@app.put("/update_risk")
async def update_risk(data: CountryData):
    """Mevcut bir ülkenin risk verilerini günceller."""
    success = update_country(data.name, data.conflict_intensity, data.political_stability, data.economic_risk)
    if not success:
        raise HTTPException(status_code=404, detail="Ülke bulunamadı.")
    return {"message": f"{data.name} güncellendi."}

@app.delete("/delete_country/{country_name}")
async def remove_country(country_name: str):
    """Bir ülkeyi siler."""
    success = delete_country(country_name)
    if not success:
        raise HTTPException(status_code=404, detail="Ülke bulunamadı.")
    return {"message": f"{country_name} silindi."}

@app.get("/health")
async def health():
    return {"status": "ok"}
