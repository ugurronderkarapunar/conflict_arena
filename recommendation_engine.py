def generate_recommendations(risk_profile):
    recs = []
    level = risk_profile["risk_level"]
    conflict = risk_profile["conflict_intensity"]
    economic = risk_profile["economic_risk"]
    political = risk_profile["political_stability"]
    
    if level in ["HIGH", "EXTREME"]:
        recs.append("⚠️ Kara yolu taşımacılığı riskli, deniz yolu alternatifi düşünün.")
    if conflict >= 6:
        recs.append("⚔️ Çatışma bölgesine yakın, güvenlik önlemlerini artırın ve sigorta yaptırın.")
    if economic >= 6:
        recs.append("💰 Ödeme ve kur riskine karşı forward sözleşmeleri değerlendirin.")
    if political < 4:
        recs.append("🏛️ Politik istikrarsızlık var, ani politika değişikliklerine hazırlıklı olun.")
    if not recs:
        recs.append("✅ Risk seviyesi düşük, normal ticaret prosedürleri yeterlidir.")
    return recs
