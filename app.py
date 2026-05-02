import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from typing import Dict, List, Optional

# ------------------- VERİTABANI -------------------
DB_PATH = "risk_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            conflict_intensity REAL NOT NULL,
            political_stability REAL NOT NULL,
            economic_risk REAL NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM countries")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ("Iran", 7.2, 3.5, 8.0),
            ("Israel", 8.5, 4.0, 5.5),
            ("Ukraine", 9.0, 2.5, 7.5),
            ("China", 2.5, 6.0, 6.5),
            ("Russia", 6.8, 3.0, 7.0),
            ("Turkey", 5.5, 4.5, 6.0),
            ("Germany", 1.0, 8.0, 2.0),
        ]
        cursor.executemany("INSERT INTO countries (name, conflict_intensity, political_stability, economic_risk) VALUES (?,?,?,?)", sample_data)
    conn.commit()
    conn.close()

def get_all_countries() -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT name, conflict_intensity, political_stability, economic_risk FROM countries ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_country(name: str) -> Optional[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT name, conflict_intensity, political_stability, economic_risk FROM countries WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_country(name: str, conflict: float, political: float, economic: float) -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO countries (name, conflict_intensity, political_stability, economic_risk) VALUES (?,?,?,?)",
                       (name, conflict, political, economic))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def update_country(name: str, conflict: float, political: float, economic: float) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE countries SET conflict_intensity=?, political_stability=?, economic_risk=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
                   (conflict, political, economic, name))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def delete_country(name: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM countries WHERE name=?", (name,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

# ------------------- RİSK HESAPLAMA -------------------
def calculate_risk_score(conflict: float, political: float, economic: float) -> float:
    score = (conflict * 0.4) + ((10 - political) * 0.3) + (economic * 0.3)
    return round(score, 2)

def get_risk_level(score: float) -> str:
    if score < 3:
        return "LOW"
    elif score < 6:
        return "MEDIUM"
    elif score < 8:
        return "HIGH"
    else:
        return "EXTREME"

def get_risk_color(level: str) -> str:
    colors = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red", "EXTREME": "darkred"}
    return colors.get(level, "gray")

def get_full_risk_profile(country: str) -> Dict:
    data = get_country(country)
    if not data:
        raise ValueError(f"Ülke {country} bulunamadı")
    conflict = data["conflict_intensity"]
    political = data["political_stability"]
    economic = data["economic_risk"]
    score = calculate_risk_score(conflict, political, economic)
    level = get_risk_level(score)
    return {
        "country": country,
        "conflict_intensity": conflict,
        "political_stability": political,
        "economic_risk": economic,
        "risk_score": score,
        "risk_level": level,
        "risk_color": get_risk_color(level)
    }

def get_all_risk_profiles() -> List[Dict]:
    countries = get_all_countries()
    profiles = []
    for c in countries:
        try:
            profiles.append(get_full_risk_profile(c["name"]))
        except:
            continue
    return profiles

# ------------------- ÖNERİ MOTORU -------------------
def generate_recommendations(risk_profile: Dict) -> List[str]:
    recs = []
    level = risk_profile["risk_level"]
    conflict = risk_profile["conflict_intensity"]
    economic = risk_profile["economic_risk"]
    political = risk_profile["political_stability"]
    
    if level in ["HIGH", "EXTREME"]:
        recs.append("⚠️ Risk: YÜKSEK – Kara yolu taşımacılığı risklidir, alternatif olarak deniz yolu tercih edilmelidir.")
    if conflict >= 6:
        recs.append("⚔️ Çatışma bölgesine yakın ticaret yapıyorsunuz. Güzergah güvenliğini sürekli izleyin ve sigorta kapsamını artırın.")
    if economic >= 6:
        recs.append("💰 Ekonomik risk yüksek. Ödeme ve kur riskine karşı forward sözleşmeler veya yerel para biriminde korunma stratejileri uygulayın.")
    if political < 4:
        recs.append("🏛️ Politik istikrarsızlık mevcut. Ani politika değişikliklerine (vergi, ithalat yasağı) karşı esnek tedarik zinciri kurun.")
    if not recs:
        recs.append("✅ Risk seviyesi düşük. Standart ticaret prosedürleri yeterlidir.")
    return recs

# ------------------- STREAMLIT UI -------------------
st.set_page_config(page_title="Risk Intelligence Dashboard", layout="wide")
st.title("📊 Country Risk Intelligence Dashboard (Standalone)")
st.markdown("Dinamik veri yönetimi – SQLite tabanlı, FastAPI gerektirmez.")

init_db()

# Sidebar: Yönetim Modu
st.sidebar.header("🔧 Yönetim")
admin = st.sidebar.checkbox("Yönetim Modu (Ekle/Güncelle/Sil)")

if admin:
    st.sidebar.subheader("➕ Yeni Ülke Ekle")
    new_name = st.sidebar.text_input("Ülke adı")
    c1 = st.sidebar.slider("Çatışma (0-10)", 0.0, 10.0, 5.0)
    c2 = st.sidebar.slider("Politik İstikrar (0-10)", 0.0, 10.0, 5.0)
    c3 = st.sidebar.slider("Ekonomik Risk (0-10)", 0.0, 10.0, 5.0)
    if st.sidebar.button("Ekle"):
        if new_name and add_country(new_name, c1, c2, c3):
            st.sidebar.success(f"{new_name} eklendi!")
            st.rerun()
        else:
            st.sidebar.error("Ülke zaten var veya geçersiz isim")
    
    st.sidebar.subheader("✏️ Güncelle")
    countries_list = [c["name"] for c in get_all_countries()]
    upd_country = st.sidebar.selectbox("Seç", countries_list)
    current = get_full_risk_profile(upd_country)
    u1 = st.sidebar.slider("Yeni Çatışma", 0.0, 10.0, current["conflict_intensity"])
    u2 = st.sidebar.slider("Yeni Politik İstikrar", 0.0, 10.0, current["political_stability"])
    u3 = st.sidebar.slider("Yeni Ekonomik Risk", 0.0, 10.0, current["economic_risk"])
    if st.sidebar.button("Güncelle"):
        if update_country(upd_country, u1, u2, u3):
            st.sidebar.success("Güncellendi")
            st.rerun()
        else:
            st.sidebar.error("Hata")
    
    st.sidebar.subheader("🗑️ Sil")
    del_country = st.sidebar.selectbox("Silinecek ülke", ["Seçiniz"] + countries_list)
    if del_country != "Seçiniz" and st.sidebar.button("Sil"):
        if delete_country(del_country):
            st.sidebar.success(f"{del_country} silindi")
            st.rerun()
        else:
            st.sidebar.error("Silinemedi")

# Normal kullanıcı arayüzü
countries = [c["name"] for c in get_all_countries()]
if not countries:
    st.warning("Henüz ülke verisi yok. Lütfen yönetim modu ile ülke ekleyin.")
    st.stop()

selected = st.sidebar.selectbox("🌍 Ülke Seçin", countries)
profile = get_full_risk_profile(selected)

col1, col2, col3 = st.columns(3)
col1.metric("Risk Skoru (0-10)", profile["risk_score"])
col2.markdown(f"**Risk Seviyesi**<br><span style='color:{profile['risk_color']}; font-size:2rem;'>{profile['risk_level']}</span>", unsafe_allow_html=True)
col3.metric("Çatışma Yoğunluğu", f"{profile['conflict_intensity']}/10")

st.subheader("📉 Risk Bileşenleri")
df = pd.DataFrame({
    "Faktör": ["Çatışma", "Politik İstikrarsızlık", "Ekonomik Risk"],
    "Değer": [profile["conflict_intensity"], 10-profile["political_stability"], profile["economic_risk"]]
})
fig = px.bar(df, x="Faktör", y="Değer", color="Değer", color_continuous_scale="Reds", text="Değer")
st.plotly_chart(fig, use_container_width=True)

st.subheader("💡 Ticaret ve Lojistik Önerileri")
for rec in generate_recommendations(profile):
    st.info(rec)

with st.expander("🔍 Detaylı Veriler"):
    st.write(f"**Politik İstikrar (0-10):** {profile['political_stability']}")
    st.write(f"**Ekonomik Risk (0-10):** {profile['economic_risk']}")

# Dünya haritası
st.subheader("🗺️ Dünya Risk Haritası")
all_profiles = get_all_risk_profiles()
if all_profiles:
    map_df = pd.DataFrame(all_profiles)
    fig_map = px.choropleth(map_df, locations="country", locationmode="country names",
                            color="risk_score", color_continuous_scale="RdYlGn_r",
                            range_color=(0,10), title="Risk Skoru")
    st.plotly_chart(fig_map, use_container_width=True)
