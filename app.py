import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
import plotly.express as px
from streamlit.components.v1 import html
import time

API_URL = "http://localhost:8000"
st.set_page_config(page_title="Risk Intelligence", layout="wide", page_icon="🌍")

# Custom CSS (modern)
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    }
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00f2fe, #4facfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    .risk-card {
        background: rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
    }
    .stButton button {
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        border: none;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🌍 Country Risk Intelligence</div>', unsafe_allow_html=True)
st.markdown("---")

# Session state for login
if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.is_admin = False

# Sidebar: Login / Logout
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/globe--v1.png", width=80)
    st.markdown("### 🔐 Giriş")
    if not st.session_state.token:
        email = st.text_input("E-posta")
        password = st.text_input("Şifre", type="password")
        if st.button("Giriş Yap"):
            res = requests.post(f"{API_URL}/login", json={"email": email, "password": password})
            if res.status_code == 200:
                data = res.json()
                st.session_state.token = data["access_token"]
                st.session_state.is_admin = data["is_admin"]
                st.rerun()
            else:
                st.error("Hatalı giriş")
    else:
        st.success("✅ Giriş yapıldı")
        if st.button("Çıkış"):
            st.session_state.token = None
            st.session_state.is_admin = False
            st.rerun()

if not st.session_state.token:
    st.warning("Lütfen giriş yapın.")
    st.stop()

# Headers for API
headers = {"Authorization": f"Bearer {st.session_state.token}"}

# Ülke listesini al
countries_res = requests.get(f"{API_URL}/countries", headers=headers)
if countries_res.status_code != 200:
    st.error("API bağlantı hatası")
    st.stop()
countries = countries_res.json()

# Admin panel
if st.session_state.is_admin:
    with st.expander("🛠️ Admin Panel", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("➕ Yeni Ülke")
            new_name = st.text_input("Ülke adı")
            c1 = st.slider("Çatışma", 0.0, 10.0, 5.0)
            c2 = st.slider("Politik İstikrar", 0.0, 10.0, 5.0)
            c3 = st.slider("Ekonomik Risk", 0.0, 10.0, 5.0)
            if st.button("Ekle"):
                r = requests.post(f"{API_URL}/admin/country", json={"name": new_name, "conflict_intensity": c1, "political_stability": c2, "economic_risk": c3}, headers=headers)
                if r.status_code == 200:
                    st.success("Eklendi")
                    st.rerun()
                else:
                    st.error(r.json().get("detail"))
        with col2:
            st.subheader("🗑️ Sil")
            del_sel = st.selectbox("Ülke seç", countries)
            if st.button("Sil"):
                r = requests.delete(f"{API_URL}/admin/country/{del_sel}", headers=headers)
                st.success("Silindi") if r.status_code == 200 else st.error("Hata")
        if st.button("🔄 Tüm verileri yenile (NewsAPI)"):
            r = requests.post(f"{API_URL}/admin/refresh", headers=headers)
            st.info("Güncelleme başlatıldı, 10 saniye bekleyin...")
            time.sleep(10)
            st.rerun()

# Ülke seçimi
selected = st.selectbox("📌 Ülke Seçin", countries)
# Risk detaylarını al
risk_res = requests.get(f"{API_URL}/risk/{selected}", headers=headers)
if risk_res.status_code != 200:
    st.error("Risk verisi alınamadı")
else:
    data = risk_res.json()
    col1, col2, col3 = st.columns(3)
    col1.metric("📊 Risk Skoru", f"{data['risk_score']} / 10")
    col2.markdown(f"<div class='risk-card'><h3>Risk Seviyesi</h3><span style='color:{data['risk_color']};font-size:2rem;'>{data['risk_level']}</span></div>", unsafe_allow_html=True)
    col3.metric("⚔️ Çatışma Yoğunluğu", data['conflict_intensity'])

    # Breakdown plotly
    df = pd.DataFrame({
        "Faktör": ["Çatışma", "Politik İstikrarsızlık", "Ekonomik Risk"],
        "Değer": [data['conflict_intensity'], 10 - data['political_stability'], data['economic_risk']]
    })
    fig = px.bar(df, x="Faktör", y="Değer", color="Değer", color_continuous_scale="Reds", text="Değer")
    st.plotly_chart(fig, use_container_width=True)

    # Öneriler
    st.subheader("💡 Akıllı Öneriler")
    for rec in data['advice']:
        st.info(rec)

# 3D Interaktif Harita (pydeck)
st.subheader("🗺️ 3D Risk Haritası")
# Tüm ülkelerin risk skorlarını al
all_risks = []
for c in countries:
    r = requests.get(f"{API_URL}/risk/{c}", headers=headers)
    if r.status_code == 200:
        d = r.json()
        all_risks.append({"lat": 0, "lon": 0, "country": c, "risk_score": d['risk_score']})
# Ülkelerin koordinatları (basit)
coords = {
    "Turkey": [38.9637, 35.2433], "Germany": [51.1657, 10.4515], "Iran": [32.4279, 53.6880],
    "Israel": [31.0461, 34.8516], "Ukraine": [48.3794, 31.1656], "China": [35.8617, 104.1954],
    "Russia": [61.5240, 105.3188]
}
for item in all_risks:
    if item['country'] in coords:
        item['lat'], item['lon'] = coords[item['country']]
    else:
        item['lat'], item['lon'] = 20.0, 0.0
df_map = pd.DataFrame(all_risks)
view = pdk.ViewState(latitude=30, longitude=20, zoom=1.5, pitch=40)
layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position='[lon, lat]',
    get_color='[risk_score * 25, 255 - risk_score * 25, 0]',
    get_radius=200000,
    pickable=True,
    auto_highlight=True
)
tooltip = {"html": "<b>{country}</b><br/>Risk Skoru: {risk_score}", "style": {"backgroundColor": "black", "color": "white"}}
r = pdk.Deck(layers=[layer], initial_view_state=view, tooltip=tooltip, map_style="mapbox://styles/mapbox/dark-v10")
st.pydeck_chart(r)

# Yasal uyarı
st.markdown("---")
st.warning("⚠️ **Yasal Uyarı:** Bu dashboard eğitim ve bilgilendirme amaçlıdır. Gerçek ticari kararlar için uzman görüşü alın. Risk skorları tahmini olup kesinlik taşımaz. Kullanım sonucu oluşabilecek zararlardan yazılım sorumlu değildir.")
