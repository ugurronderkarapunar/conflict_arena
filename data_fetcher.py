import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")

logging.basicConfig(level=logging.INFO)

# Basit bir 'risk sözlüğü'
CONFLICT_KEYWORDS = ["war", "conflict", "violence", "attack", "bomb", "military", "rebel", "clash", "fighting"]
POLITICAL_KEYWORDS = ["protest", "coup", "unrest", "demonstration", "government crisis", "political instability"]
ECONOMIC_KEYWORDS = ["inflation", "currency crash", "default", "recession", "economic crisis", "sanction"]

def fetch_news_sentiment(country_name: str) -> dict:
    """NewsAPI ile son 7 gündeki haberleri analiz eder, conflict_intensity ve political_stability tahmini yapar."""
    if not NEWS_API_KEY:
        logging.warning("NEWS_API_KEY yok, varsayılan değerler dönecek")
        return {"conflict": 5.0, "political": 5.0}
    url = f"https://newsapi.org/v2/everything?q={country_name}&from={(datetime.now() - timedelta(days=7)).date()}&sortBy=relevancy&apiKey={NEWS_API_KEY}&language=en&pageSize=50"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("status") != "ok":
            return {"conflict": 5.0, "political": 5.0}
        articles = data.get("articles", [])
        if not articles:
            return {"conflict": 5.0, "political": 5.0}
        conflict_score = 0
        political_score = 0
        count = 0
        for art in articles:
            title = art.get("title", "").lower()
            desc = art.get("description", "").lower()
            text = title + " " + desc
            for kw in CONFLICT_KEYWORDS:
                if kw in text:
                    conflict_score += 1
                    break
            for kw in POLITICAL_KEYWORDS:
                if kw in text:
                    political_score += 1
                    break
            count += 1
        # normalize 0-10 arası
        max_score = 30   # 50 haber içinde max 30 anahtar kelime görülür varsayımı
        conflict = min(10, conflict_score / max_score * 10)
        political = min(10, political_score / max_score * 10)
        # political stability = 10 - political_unrest
        political_stability = max(0, 10 - political)
        return {"conflict": round(conflict, 1), "political": round(political_stability, 1)}
    except Exception as e:
        logging.error(f"NewsAPI hatası: {e}")
        return {"conflict": 5.0, "political": 5.0}

def fetch_economic_risk(country_code: str) -> float:
    """ExchangeRate-API ile para birimi volatilitesi / kur riski simülasyonu."""
    if not EXCHANGE_RATE_API_KEY:
        return 5.0
    # Basit: döviz kurundaki % değişim riski - ücretsiz API'de tarihsel yok, sabit döndür
    # Gerçekte yapılacak: USD/TRY, USD/RUB gibi son 30 günlük volatilite.
    # Simülasyon:
    return round(5.0 + (hash(country_code) % 5) - 2, 1)

def get_latest_risk_data(country_name: str, country_code: str) -> dict:
    """Tüm verileri birleştirir."""
    news = fetch_news_sentiment(country_name)
    economic = fetch_economic_risk(country_code)
    return {
        "conflict_intensity": news["conflict"],
        "political_stability": news["political"],
        "economic_risk": economic
    }
