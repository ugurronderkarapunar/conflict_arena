from typing import List, Dict

def generate_recommendations(risk_profile: Dict) -> List[str]:
    """
    Kural tabanlı öneri sistemi.
    Parametreler: risk_level, conflict_intensity, economic_risk, political_stability
    """
    recommendations = []
    
    risk_level = risk_profile["risk_level"]
    conflict = risk_profile["conflict_intensity"]
    economic = risk_profile["economic_risk"]
    political = risk_profile["political_stability"]
    
    if risk_level in ["HIGH", "EXTREME"]:
        recommendations.append("⚠️ Risk: YÜKSEK – Kara yolu taşımacılığı risklidir, alternatif olarak deniz yolu tercih edilmelidir.")
    
    if conflict >= 6:
        recommendations.append("⚔️ Çatışma bölgesine yakın ticaret yapıyorsunuz. Güzergah güvenliğini sürekli izleyin ve sigorta kapsamını artırın.")
    
    if economic >= 6:
        recommendations.append("💰 Ekonomik risk yüksek. Ödeme ve kur riskine karşı forward sözleşmeler veya yerel para biriminde korunma stratejileri uygulayın.")
    
    if political < 4:
        recommendations.append("🏛️ Politik istikrarsızlık mevcut. Ani politika değişikliklerine (vergi, ithalat yasağı) karşı esnek tedarik zinciri kurun.")
    
    if not recommendations:
        recommendations.append("✅ Risk seviyesi düşük. Standart ticaret prosedürleri yeterlidir, ancak periyodik izleme önerilir.")
    
    return recommendations

def get_advice_for_api(risk_profile: Dict) -> List[str]:
    """API için kısa ve öz öneriler üretir (sadece ana başlıklar)."""
    advice = []
    risk_level = risk_profile["risk_level"]
    if risk_level in ["HIGH", "EXTREME"]:
        advice.append("kara yolu riskli")
        advice.append("deniz yolu önerilir")
    if risk_profile["conflict_intensity"] >= 6:
        advice.append("çatışma bölgesine dikkat")
    if risk_profile["economic_risk"] >= 6:
        advice.append("ödeme/kur riskine dikkat")
    if risk_profile["political_stability"] < 4:
        advice.append("politika değişikliği riski")
    return advice if advice else ["risk seviyesi düşük, normal ticaret"]
