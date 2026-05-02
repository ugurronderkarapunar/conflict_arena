from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict
from datetime import timedelta

from database import SessionLocal, User, Country
from auth import hash_password, verify_password, create_access_token, get_current_user, create_admin_user
from risk_engine import get_full_risk_profile
from recommendation_engine import generate_recommendations
from scheduler import scheduler, update_all_countries

app = FastAPI(title="Country Risk Intelligence API", version="3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----- Auth -----
class LoginRequest(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    password: str
    is_admin: bool = False

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(400, "Email zaten kayıtlı")
    hashed = hash_password(user.password)
    new_user = User(email=user.email, hashed_password=hashed, is_admin=user.is_admin)
    db.add(new_user)
    db.commit()
    return {"msg": "Kullanıcı oluşturuldu"}

@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(401, "Geçersiz email veya şifre")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer", "is_admin": user.is_admin}

@app.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {"email": user.email, "is_admin": user.is_admin}

# ----- Risk -----
@app.get("/risk/{country}")
def get_risk(country: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        profile = get_full_risk_profile(db, country)
        advice = generate_recommendations(profile)
        return {**profile, "advice": advice}
    except ValueError:
        raise HTTPException(404, "Ülke bulunamadı")

@app.get("/countries")
def list_countries(db: Session = Depends(get_db), _=Depends(get_current_user)):
    countries = db.query(Country.name).all()
    return [c[0] for c in countries]

# ----- Admin -----
class CountryUpdate(BaseModel):
    name: str
    conflict_intensity: float
    political_stability: float
    economic_risk: float

@app.post("/admin/country")
def add_country(data: CountryUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin yetkisi gerekli")
    existing = db.query(Country).filter(Country.name == data.name).first()
    if existing:
        raise HTTPException(400, "Ülke zaten var")
    new_c = Country(name=data.name, conflict_intensity=data.conflict_intensity, political_stability=data.political_stability, economic_risk=data.economic_risk)
    db.add(new_c)
    db.commit()
    return {"msg": "Eklendi"}

@app.put("/admin/country")
def update_country(data: CountryUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin yetkisi gerekli")
    country = db.query(Country).filter(Country.name == data.name).first()
    if not country:
        raise HTTPException(404, "Ülke yok")
    country.conflict_intensity = data.conflict_intensity
    country.political_stability = data.political_stability
    country.economic_risk = data.economic_risk
    db.commit()
    return {"msg": "Güncellendi"}

@app.delete("/admin/country/{country}")
def delete_country(country: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin yetkisi gerekli")
    c = db.query(Country).filter(Country.name == country).first()
    if not c:
        raise HTTPException(404, "Ülke yok")
    db.delete(c)
    db.commit()
    return {"msg": "Silindi"}

@app.post("/admin/refresh")
def refresh_all_countries(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(403, "Admin yetkisi gerekli")
    update_all_countries()  # manuel tetikleme
    return {"msg": "Güncelleme başlatıldı"}

@app.on_event("startup")
def startup():
    create_admin_user()
    # İlk veri varsa kontrol et, yoksa örnek ekle
    db = SessionLocal()
    if db.query(Country).count() == 0:
        defaults = [
            ("Iran", 7.2, 3.5, 8.0), ("Israel", 8.5, 4.0, 5.5),
            ("Ukraine", 9.0, 2.5, 7.5), ("China", 2.5, 6.0, 6.5),
            ("Russia", 6.8, 3.0, 7.0), ("Turkey", 5.5, 4.5, 6.0),
            ("Germany", 1.0, 8.0, 2.0)
        ]
        for name, c, p, e in defaults:
            db.add(Country(name=name, conflict_intensity=c, political_stability=p, economic_risk=e))
        db.commit()
    db.close()
    scheduler.start()
