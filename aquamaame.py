import requests
import json
import random
import time
import sqlite3
from datetime import datetime

# ── Ollama config ──────────────────────────────────────────
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "gemma3:1b"

# ── Database setup ─────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("aquamaame.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            temperature REAL,
            ph REAL,
            dissolved_oxygen REAL,
            alert TEXT
        )
    """)
    conn.commit()
    conn.close()

# ── Simulate sensor data ───────────────────────────────────
def get_sensor_data():
    hour = datetime.now().hour
    # Simulate nighttime danger (between 1am - 4am)
    if 1 <= hour <= 4:
        temperature = round(random.uniform(17.0, 20.0), 2)
        ph = round(random.uniform(5.5, 6.2), 2)
        dissolved_oxygen = round(random.uniform(1.8, 3.0), 2)
    else:
        temperature = round(random.uniform(26.0, 30.0), 2)
        ph = round(random.uniform(6.8, 7.8), 2)
        dissolved_oxygen = round(random.uniform(5.5, 7.5), 2)
    return temperature, ph, dissolved_oxygen

# ── Ask Gemma ──────────────────────────────────────────────
def ask_gemma(temperature, ph, dissolved_oxygen):
    prompt = f"""You are AquaMaame, an expert AI fish farm advisor for Nigerian catfish farmers.

Current pond readings:
- Water Temperature: {temperature}°C
- pH Level: {ph}
- Dissolved Oxygen: {dissolved_oxygen} mg/L

Safe ranges for Nigerian catfish:
- Temperature: 25-30°C
- pH: 6.5-8.0
- Dissolved Oxygen: above 5 mg/L

Analyze these readings. If danger is detected, start your response with ALERT.
Give a short clear response in 3-4 sentences maximum.
Tell the farmer what is wrong and exactly what to do right now."""

    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })
    
    result = response.json()
    return result["response"]

# ── Save to database ───────────────────────────────────────
def save_reading(temperature, ph, dissolved_oxygen, gemma_response):
    conn = sqlite3.connect("aquamaame.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO readings (timestamp, temperature, ph, dissolved_oxygen, alert)
        VALUES (?, ?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          temperature, ph, dissolved_oxygen, gemma_response))
    conn.commit()
    conn.close()

# ── Main loop ──────────────────────────────────────────────
def monitor():
    init_db()
    print("🐟 AquaMaame is watching your pond...")
    print("=" * 50)
    
    temperature, ph, dissolved_oxygen = get_sensor_data()
    
    print(f"📊 Reading at {datetime.now().strftime('%H:%M:%S')}")
    print(f"   🌡  Temperature: {temperature}°C")
    print(f"   ⚗️  pH: {ph}")
    print(f"   💧 Dissolved Oxygen: {dissolved_oxygen} mg/L")
    print("\n🤖 AquaMaame is thinking...")
    
    gemma_response = ask_gemma(temperature, ph, dissolved_oxygen)
    save_reading(temperature, ph, dissolved_oxygen, gemma_response)
    
    print(f"\n💬 AquaMaame says:\n{gemma_response}")
    print("=" * 50)

if __name__ == "__main__":
    while True:
        monitor()