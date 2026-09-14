import os
import time
from datetime import datetime, timezone
from urllib.parse import quote
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
WEATHER_TIMEOUT = (4, 10)
GROQ_TIMEOUT = (4, 20)

def log(stage, message, started=None):
    item = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "stage": stage, "message": message}
    if started is not None:
        item["elapsed_ms"] = round((time.monotonic() - started) * 1000)
    print(f"[DEBUG] stage={stage} message={message}", flush=True)
    return item

def error(message, logs, status):
    logs.append(log("error", message))
    return jsonify({"ok": False, "error": message, "debug": logs}), status

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "weather-advisor", "version": "1.0"})

@app.post("/api/weather")
def weather():
    logs = [log("weather", "Request started / 開始查詢")]
    started = time.monotonic()
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error("Send a JSON object / 請傳入 JSON 物件", logs, 400)
    city = payload.get("city", "")
    question = payload.get("question", "請依目前天氣提供穿著與外出建議。")
    temperature = payload.get("temperature", 0.3)
    if not isinstance(city, str) or len(city.strip()) > 80:
        return error("Invalid city / 城市輸入不正確", logs, 400)
    if not isinstance(question, str) or not question.strip() or len(question) > 500:
        return error("Invalid question / 問題輸入不正確", logs, 400)
    if type(temperature) not in (int, float) or not 0.1 <= temperature <= 1.0:
        return error("Temperature must be 0.1–1.0 / Temperature 必須介於 0.1–1.0", logs, 400)
    location = city.strip()
    location_mode = "city"
    if not location:
        forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if forwarded and forwarded not in ("127.0.0.1", "::1"):
            location = forwarded
            location_mode = "client_ip"
        else:
            location = "Taipei"
            location_mode = "fallback"
    try:
        url = f"https://wttr.in/{quote(location, safe='')}?format=j1"
        response = requests.get(url, headers={"Accept": "application/json", "User-Agent": "FirebaseFlaskAPILabs/1.0"}, timeout=WEATHER_TIMEOUT)
        response.raise_for_status()
        raw = response.json()
        current = raw["current_condition"][0]
        area = raw.get("nearest_area", [{}])[0]
        place = area.get("areaName", [{"value": location}])[0].get("value", location)
        weather_data = {
            "location": place,
            "temperature_c": current.get("temp_C"),
            "feels_like_c": current.get("FeelsLikeC"),
            "humidity_percent": current.get("humidity"),
            "wind_kmph": current.get("windspeedKmph"),
            "description": current.get("weatherDesc", [{"value": ""}])[0].get("value", ""),
            "location_mode": location_mode,
            "source_url": "https://wttr.in/",
        }
        logs.append(log("weather", "Weather API succeeded / 天氣 API 成功", started))
    except requests.Timeout:
        return error("Weather service timeout / 天氣服務逾時", logs, 504)
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return error("Weather service returned unusable data / 天氣服務資料無法使用", logs, 502)
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        return error("GROQ_API_KEY is not configured / 尚未設定 GROQ_API_KEY", logs, 503)
    context = "\n".join(f"{k}: {v}" for k, v in weather_data.items())
    body = {
        "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        "messages": [
            {"role": "system", "content": "Only use the supplied weather data. Answer in Traditional Chinese plain text. Do not use Markdown tables, hash headings, bold markers, or code fences. State uncertainty and never invent a forecast. / 只能依提供的天氣資料，以繁體中文純文字回答；不得虛構預報。"},
            {"role": "user", "content": f"Weather data / 天氣資料:\n{context}\n\nQuestion / 問題: {question}"},
        ],
        "temperature": temperature,
        "max_tokens": 700,
    }
    if body["model"].startswith("openai/gpt-oss-"):
        body["reasoning_effort"] = "low"
    try:
        ai_started = time.monotonic()
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=body, timeout=GROQ_TIMEOUT)
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"]
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("empty answer")
        logs.append(log("ai", "Groq succeeded / Groq 回覆成功", ai_started))
        return jsonify({"ok": True, "data": {"weather": weather_data, "answer": answer.strip(), "model": body["model"], "temperature": temperature}, "debug": logs})
    except requests.Timeout:
        return error("Groq timeout; weather data remains available / Groq 逾時", logs, 504)
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return error("Groq returned an unusable response / Groq 回覆無法使用", logs, 502)
