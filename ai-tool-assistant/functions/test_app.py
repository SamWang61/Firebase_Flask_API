import json
import app as target

def test_health():
    response=target.app.test_client().get("/api/health")
    assert response.status_code==200
    assert response.get_json()["service"]=="ai-tool-assistant"

def test_tool_validation():
    assert target.validate("fakestore",{"product_id":3})["product_id"]==3
    assert target.validate("usgs",{"hours":24,"min_magnitude":5})["hours"]==24

def test_route_clarification(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY","test-only")
    monkeypatch.setattr(target,"chat",lambda *args,**kwargs:{"content":"請提供 GitHub 帳號。"})
    response=target.app.test_client().post("/api/agent/route",json={"question":"分析他的 GitHub","temperature":0.3})
    assert response.status_code==200
    assert response.get_json()["data"]["mode"]=="reply"

def test_route_tool(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY","test-only")
    call={"id":"c1","function":{"name":"github","arguments":json.dumps({"username":"octocat"})}}
    monkeypatch.setattr(target,"chat",lambda *args,**kwargs:{"tool_calls":[call]})
    response=target.app.test_client().post("/api/agent/route",json={"question":"分析 octocat","temperature":0.3})
    assert response.status_code==200
    assert response.get_json()["data"]["calls"][0]["name"]=="github"

def test_plain_output():
    fence=chr(96)*3
    answer=target.plain("# 標題\n**內容**\n| A | B |\n|---|---|\n"+fence+"\ncode\n"+fence)
    assert "#" not in answer and "**" not in answer and "|" not in answer and fence not in answer
