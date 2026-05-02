import sqlite3
from typing import List, Dict, Optional

DB_PATH = "risk_data.db"

def init_db():
    """Veritabanı tablolarını oluşturur (eğer yoksa) ve örnek verileri ekler."""
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
    """Tüm ülkelerin listesini sözlük listesi olarak döndürür."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT name, conflict_intensity, political_stability, economic_risk FROM countries ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_country(name: str) -> Optional[Dict]:
    """Bir ülkenin verisini döndürür, yoksa None."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT name, conflict_intensity, political_stability, economic_risk FROM countries WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_country(name: str, conflict: float, political: float, economic: float) -> bool:
    """Yeni ülke ekler. Aynı isim varsa False döner."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO countries (name, conflict_intensity, political_stability, economic_risk) VALUES (?,?,?,?)",
            (name, conflict, political, economic)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def update_country(name: str, conflict: float, political: float, economic: float) -> bool:
    """Ülkenin risk değerlerini günceller. Ülke yoksa False döner."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE countries SET conflict_intensity=?, political_stability=?, economic_risk=?, updated_at=CURRENT_TIMESTAMP WHERE name=?",
        (conflict, political, economic, name)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def delete_country(name: str) -> bool:
    """Ülkeyi siler. Başarılıysa True döner."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM countries WHERE name=?", (name,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

# İlk çalıştırmada tabloyu hazırla
init_db()
