from flask import Flask, render_template, jsonify, request
import requests
import random
import sqlite3
from datetime import datetime
from pattern import analyze_patterns
app = Flask(__name__)

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "gemma3:1b"

@app.route("/api/sensor", methods=["POST"])
def receive_sensor():
    data = request.json
    temperature = data.get("temperature")
    
    conn = sqlite3.connect("aquamaame.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO readings (timestamp, temperature, ph, dissolved_oxygen, alert)
        VALUES (?, ?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          temperature, 7.0, 6.0, "Real sensor reading"))
    conn.commit()
    conn.close()
    
    print(f"Real temperature received: {temperature}°C")
    return jsonify({"status": "ok", "temperature": temperature})

def ask_gemma(prompt):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/reading")
def get_reading():
    temperature, ph, dissolved_oxygen = get_sensor_data()
    prompt = (
        "You are AquaMaame, an expert AI fish farm advisor for Nigerian catfish farmers.\n"
        "Current pond readings:\n"
        f"- Water Temperature: {temperature}C\n"
        f"- pH Level: {ph}\n"
        f"- Dissolved Oxygen: {dissolved_oxygen} mg/L\n"
        "Safe ranges for Nigerian catfish:\n"
        "- Temperature: 25-30C\n"
        "- pH: 6.5-8.0\n"
        "- Dissolved Oxygen: above 5 mg/L\n"
        "If any value is outside safe range start your response with ALERT.\n"
        "Give a short clear response in 3 sentences maximum.\n"
        "Tell the farmer exactly what to do right now."
    )
    gemma_response = ask_gemma(prompt)
    is_alert = "ALERT" in gemma_response.upper()
    return jsonify({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temperature": temperature,
        "ph": ph,
        "dissolved_oxygen": dissolved_oxygen,
        "response": gemma_response,
        "is_alert": is_alert
    })

@app.route("/api/ask", methods=["POST"])
def ask_question():
    data = request.json
    question = data.get("question", "")
    language = data.get("language", "english")
    language_map = {
        "english": "Respond in simple English.",
        "igbo": "You MUST respond ONLY in Igbo language.",
        "yoruba": "You MUST respond ONLY in Yoruba language.",
        "hausa": "You MUST respond ONLY in Hausa language.",
        "pidgin": "You MUST respond ONLY in Nigerian Pidgin English.",
        "french": "You MUST respond ONLY in French language.",
        "swahili": "You MUST respond ONLY in Swahili language."
    }
    lang_instruction = language_map.get(language, "Respond in simple English.")
    prompt = (
        "You are AquaMaame, an expert AI fish farm advisor for Nigerian catfish farmers.\n"
        f"A farmer asks: {question}\n"
        f"{lang_instruction}\n"
        "Give practical advice in 3-4 sentences maximum."
    )
    response = ask_gemma(prompt)
    return jsonify({"response": response})

@app.route("/api/patterns")
def get_patterns():
    result = analyze_patterns()
    return jsonify({"patterns": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)