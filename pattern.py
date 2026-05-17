import sqlite3
import requests
from datetime import datetime

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "gemma3:1b"

def get_history():
    conn = sqlite3.connect("aquamaame.db")
    c = conn.cursor()
    c.execute("""
        SELECT timestamp, temperature, ph, dissolved_oxygen, alert 
        FROM readings 
        ORDER BY id DESC 
        LIMIT 50
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def analyze_patterns():
    rows = get_history()
    if len(rows) < 5:
        return "Not enough data yet. Keep monitoring your pond to build up history."
    
    history_text = ""
    for row in rows:
        history_text += f"Time: {row[0]}, Temp: {row[1]}C, pH: {row[2]}, DO: {row[3]} mg/L\n"
    
    prompt = (
        "You are AquaMaame, an expert AI fish farm advisor for Nigerian catfish farmers.\n"
        "Here are the recent pond readings:\n"
        f"{history_text}\n"
        "Analyze these readings and identify any patterns you notice.\n"
        "Look for: recurring drops in oxygen, temperature trends, pH instability.\n"
        "Give 2-3 specific actionable insights the farmer can use.\n"
        "Be specific about times and values you noticed.\n"
        "Keep response under 5 sentences."
    )
    
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })
    
    return response.json()["response"]

if __name__ == "__main__":
    print("Analyzing pond patterns...")
    result = analyze_patterns()
    print(result)