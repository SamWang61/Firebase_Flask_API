"""Offline transport and installer regression tests / 離線傳輸與安裝回歸測試。"""
import json
import math
import sys
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from groq import APITimeoutError, APIStatusError
from langchain_core.messages import AIMessage
from langchain_groq import ChatGroq as RealChatGroq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import langchain_adapter_v3 as adapter
from app import validate


def query(name, args):
    return {"name": name, "arguments_json": json.dumps(args, ensure_ascii=False)}


def message(queries):
    return AIMessage(content="", tool_calls=[{"id": "plan1", "name": "submit_api_plan", "args": {"calls": queries}}])


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "offline-test-placeholder")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.delenv("GROQ_MODEL", raising=False)


@pytest.mark.parametrize("count", [1, 2, 4])
def test_real_langchain_transport(count):
    queries = [query("github", {"username":"octocat"}), query("wikipedia", {"topic":"開源軟體"}), query("fakestore", {"product_id":3}), query("usgs", {"hours":24,"min_magnitude":5})][:count]
    requests = []
    def handler(req):
        body = json.loads(req.content)
        requests.append(body)
        if "tools" in body:
            assert body["tools"][0]["function"]["name"] == "submit_api_plan"
            assert "anyOf" not in json.dumps(body["tools"])
            reply = {"role":"assistant", "content":None, "tool_calls":[{"id":"plan1","type":"function","function":{"name":"submit_api_plan","arguments":json.dumps({"calls":queries})}}]}
        else:
            assert all(m["role"] != "tool" for m in body["messages"])
            reply = {"role":"assistant", "content":"根據已驗證資料完成摘要。"}
        return httpx.Response(200, json={"id":"offline", "object":"chat.completion", "created":1, "model":body["model"], "choices":[{"index":0,"message":reply,"finish_reason":"tool_calls" if "tools" in body else "stop"}],"usage":{"prompt_tokens":10,"completion_tokens":10,"total_tokens":20}})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        def factory(**kwargs):
            assert kwargs["max_retries"] == 0
            assert kwargs["timeout"].read == 20
            return RealChatGroq(**kwargs, http_client=client)
        with patch.object(adapter, "ChatGroq", factory):
            result = adapter.chat([{"role":"user","content":"查詢測試"}], .3, True, validate)
            assert len(result["tool_calls"]) == count
            assert [c["function"]["name"] for c in result["tool_calls"]] == [q["name"] for q in queries]
            final = adapter.chat([{"role":"system","content":"只整理已驗證資料"}, {"role":"user","content":"來源資料"}], .3, False, validate)
            assert final["content"] == "根據已驗證資料完成摘要。"
    assert len(requests) == 2


def test_followup_remains_plain_reply():
    result = adapter.normalize(AIMessage(content="請提供 GitHub 帳號。"), True, validate)
    assert result["tool_calls"] == []


@pytest.mark.parametrize("queries", [
    [], [query("unknown", {})], [query("fakestore", {"product_id":True})],
    [query("github", {"username":"octocat", "extra":1})],
    [query("github", {"username":"octocat"})] * 2,
    [query("github", {"username":str(i)}) for i in range(5)],
    [{"name":"github","arguments_json":"{bad"}],
    [{"name":"github","arguments_json":'{"username":"a","username":"b"}'}],
    [{"name":"usgs","arguments_json":'{"hours":24,"min_magnitude":NaN}'}],
])
def test_invalid_plans_rejected(queries):
    with pytest.raises(ValueError):
        adapter.normalize(message(queries), True, validate)


def test_final_stage_cannot_call_tools():
    with pytest.raises(ValueError):
        adapter.normalize(message([query("github", {"username":"octocat"})]), False, validate)


@pytest.mark.parametrize("failure", ["timeout", "http400"])
def test_transport_errors_not_retried(failure, capsys):
    attempts = []
    def handler(req):
        attempts.append(1)
        if failure == "timeout":
            raise httpx.ReadTimeout("offline timeout", request=req)
        return httpx.Response(400, json={"error":{"message":"Tool choice is none, but model called a tool", "code":"tool_use_failed"}})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with patch.object(adapter, "ChatGroq", lambda **kw: RealChatGroq(**kw, http_client=client)):
            with pytest.raises(APITimeoutError if failure == "timeout" else APIStatusError):
                adapter.chat([{"role":"user","content":"test"}], .3, True, validate)
    assert len(attempts) == 1
    log = capsys.readouterr().out
    assert "elapsed_ms=" in log and "cause=" in log
    assert "offline-test-placeholder" not in log
