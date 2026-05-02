import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from risk_engine import get_full_risk_profile, get_all_risk_profiles
from recommendation_engine import generate_recommendations

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Country Risk Intelligence", page_icon="📊", layout="wide")

st.title("📊 Country Risk Intelligence Dashboard")
st.markdown("Dinamik risk verileri – Ülke ekleyin, güncelleyin, silin. Tüm değişiklikler anında veritabanına yansır.")

# Sidebar: Veri Yönetimi
st.sidebar.header("🔧 Veri Yönetimi")
admin_mode = st.sidebar.checkbox("Yönetim Modunu Aç (Ekle/Güncelle/Sil)")

if admin_mode:
    st.sidebar.subheader("➕ Yeni Ülke Ekle")
    new_name = st.sidebar.text_input("Ülke adı")
    new_conflict = st.sidebar.slider("Çatışma Yoğunluğu (0-10)", 0.0, 10.0, 5.0, 0.1)
    new_political = st.sidebar.slider("Politik İstikrar (0-10)", 0.0, 10.0, 5.0, 0.1)
    new_economic = st.sidebar.slider("Ekonomik Risk (0-10)", 0.0, 10.0, 5.0, 0.1)
    if st.sidebar.button("Ekle"):
        if new_name.strip():
            response = requests.post(f"{API_URL}/add_country", json={
                "name": new_name.strip(),
                "conflict_intensity": new_conflict,
                "political_stability": new_political,
                "economic_risk": new_economic
            })
            if response.status_code == 200:
                st.sidebar.success(f"{new_name} eklendi!")
                st.rerun()
            else:
                st.sidebar.error(response.json().get("detail", "Hata oluştu"))
        else:
            st.sidebar.warning("Ülke adı boş olamaz.")
    
    # Mevcut ülkeleri al
    try:
        resp = requests.get(f"{API_URL}/countries")
        countries_list = resp.json().get("countries", []) if resp.status_code == 200 else []
    except:
        countries_list = []
    
    if countries_list:
        st.sidebar.subheader("✏️ Ülke Güncelle")
        upd_country = st.sidebar.selectbox("Güncellenecek ülke", countries_list)
        current = get_full_risk_profile(upd_country)
        upd_conflict = st.sidebar.slider("Yeni Çatışma", 0.0, 10.0, current["conflict_intensity"], 0.1)
        upd_political = st.sidebar.slider("Yeni Politik İstikrar", 0.0, 10.0, current["political_stability"], 0.1)
        upd_economic = st.sidebar.slider("Yeni Ekonomik Risk", 0.0, 10.0, current["economic_risk"], 0.1)
        if st.sidebar.button("Güncelle"):
            resp = requests.put(f"{API_URL}/update_risk", json={
                "name": upd_country,
                "conflict_intensity": upd_conflict,
                "political_stability": upd_political,
                "economic_risk": upd_economic
            })
            if resp.status_code == 200:
                st.sidebar.success("Güncellendi!")
                st.rerun()
            else:
                st.sidebar.error("Güncelleme başarısız")
        
        st.sidebar.subheader("🗑️ Ülke Sil")
        del_country = st.sidebar.selectbox("Silinecek ülke", ["Seçiniz"] + countries_list)
        if del_country != "Seçiniz" and st.sidebar.button("Sil"):
            resp = requests.delete(f"{API_URL}/delete_country/{del_country}")
            if resp.status_code == 200:
                st.sidebar.success(f"{del_country} silindi")
                st.rerun()
            else:
                st.sidebar.error("Silme başarısız")

# Normal kullanıcı arayüzü
st.sidebar.markdown("---")
st.sidebar.header("🌍 Ülke Seçimi")

try:
    resp = requests.get(f"{API_URL}/countries", timeout=3)
    if resp.status_code == 200:
        countries = resp.json()["countries"]
    else:
        countries = []
        st.error("API'den ülke listesi alınamadı.")
except Exception as e:
    countries = []
    st.error(f"API bağlantı hatası: {e}")

if countries:
    selected = st.sidebar.selectbox("Bir ülke seçin", countries)
    risk_profile = get_full_risk_profile(selected)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Risk Skoru (0-10)", f"{risk_profile['risk_score']}")
    col2.markdown(f"**Risk Seviyesi**<br><span style='color:{risk_profile['risk_color']}; font-size:2rem; font-weight:bold;'>{risk_profile['risk_level']}</span>", unsafe_allow_html=True)
    col3.metric("Çatışma Yoğunluğu", f"{risk_profile['conflict_intensity']}/10")
    
    st.subheader("📉 Risk Bileşenleri")
    breakdown = pd.DataFrame({
        "Faktör": ["Çatışma Yoğunluğu", "Politik İstikrarsızlık", "Ekonomik Risk"],
        "Değer (0-10)": [
            risk_profile["conflict_intensity"],
            10 - risk_profile["political_stability"],
            risk_profile["economic_risk"]
        ]
    })
    fig = px.bar(breakdown, x="Faktör", y="Değer (0-10)", color="Değer (0-10)",
                 color_continuous_scale="Reds", text="Değer (0-10)")
    fig.update_traces(textposition="outside")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("💡 Ticaret ve Lojistik Önerileri")
    recommendations = generate_recommendations(risk_profile)
    for rec in recommendations:
        st.info(rec)
    
    with st.expander("🔍 Detaylı Risk Verileri"):
        st.write(f"**Çatışma Yoğunluğu:** {risk_profile['conflict_intensity']}/10")
        st.write(f"**Politik İstikrar:** {risk_profile['political_stability']}/10")
        st.write(f"**Ekonomik Risk:** {risk_profile['economic_risk']}/10")
        st.write(f"**Risk Skoru:** {risk_profile['risk_score']}")
        st.write(f"**Risk Seviyesi:** {risk_profile['risk_level']}")
else:
    st.warning("Henüz hiç ülke yok. Lütfen yönetim modu ile ülke ekleyin veya API'nin çalıştığından emin olun.")

# Dünya haritası (tüm ülkeler)
st.subheader("🗺️ Dünya Risk Haritası")
all_profiles = get_all_risk_profiles()
if all_profiles:
    map_df = pd.DataFrame(all_profiles)
    fig_map = px.choropleth(map_df, locations="country", locationmode="country names",
                            color="risk_score", color_continuous_scale="RdYlGn_r",
                            range_color=(0,10), title="Ülke Bazında Risk Skoru (0=düşük, 10=yüksek)")
    fig_map.update_layout(height=500)
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("Harita için yeterli ülke verisi yok.")

st.markdown("---")
st.caption("Veriler SQLite veritabanında saklanır. Yönetim modu ile verileri güncelleyebilir veya yeni ülke ekleyebilirsiniz.")
