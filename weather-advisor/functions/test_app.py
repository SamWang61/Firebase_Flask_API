import app as target

def test_health():
    r = target.app.test_client().get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["service"] == "weather-advisor"

def test_validation():
    c = target.app.test_client()
    assert c.post("/api/weather", data="x", content_type="text/plain").status_code == 400
    assert c.post("/api/weather", json={"city": "x" * 81, "question": "q"}).status_code == 400
    assert c.post("/api/weather", json={"city": "Taipei", "question": "q", "temperature": 2}).status_code == 400

def test_success(monkeypatch):
    class Reply:
        def raise_for_status(self): pass
        def json(self):
            return {"current_condition":[{"temp_C":"25","FeelsLikeC":"26","humidity":"70","windspeedKmph":"8","weatherDesc":[{"value":"Cloudy"}]}],"nearest_area":[{"areaName":[{"value":"Taipei"}]}]}
    class AI:
        def raise_for_status(self): pass
        def json(self): return {"choices":[{"message":{"content":"帶一件薄外套。"}}]}
    monkeypatch.setenv("GROQ_API_KEY", "test-only")
    monkeypatch.setattr(target.requests, "get", lambda *a, **k: Reply())
    monkeypatch.setattr(target.requests, "post", lambda *a, **k: AI())
    r = target.app.test_client().post("/api/weather", json={"city":"Taipei","question":"怎麼穿？","temperature":0.3})
    assert r.status_code == 200
    assert r.get_json()["data"]["weather"]["location"] == "Taipei"
