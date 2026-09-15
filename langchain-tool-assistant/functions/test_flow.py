"""Signed stage integration tests / 簽章階段整合測試。"""
import json
import pytest
from groq import APITimeoutError, APIStatusError
import httpx
import app as target

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY','offline-test-placeholder')
    monkeypatch.setenv('LANGSMITH_TRACING','false')
    return target.app.test_client()

def plan(client,monkeypatch):
    calls=[{'id':'q1','function':{'name':'github','arguments':'{"username":"octocat"}'}},
           {'id':'q2','function':{'name':'wikipedia','arguments':'{"topic":"開源軟體"}'}}]
    monkeypatch.setattr(target,'chat',lambda *a: {'tool_calls':calls})
    r=client.post('/api/agent/route',json={'question':'分析octocat並查開源軟體','temperature':.3})
    assert r.status_code==200
    return r.json['data']

def execute(client,monkeypatch,p,fail=False):
    def fetch(args):
        if fail: raise target.requests.Timeout()
        return {'value':'public'},'Only provided source facts.'
    monkeypatch.setitem(target.FETCHERS,'github',fetch)
    monkeypatch.setitem(target.FETCHERS,'wikipedia',fetch)
    return [client.post('/api/agent/execute',json={'plan':p['plan'],'call_id':c['id']}).json['data']['receipt'] for c in p['calls']]

@pytest.mark.parametrize('failure',[False,True])
def test_two_results_summary(client,monkeypatch,failure):
    p=plan(client,monkeypatch);receipts=execute(client,monkeypatch,p,failure)
    def summary(messages,temp,with_tools=False):
        assert not with_tools and temp==.3
        assert [m['role'] for m in messages]==['system','user']
        data=json.loads(messages[1]['content'])
        assert len(data['verified_results'])==2
        assert all(x['result']['ok'] is (not failure) for x in data['verified_results'])
        return {'content':'資料不足。' if failure else '依據兩項資料摘要。'}
    monkeypatch.setattr(target,'chat',summary)
    r=client.post('/api/agent/finish',json={'plan':p['plan'],'receipts':receipts})
    assert r.status_code==200
    assert '已驗證 2 項結果' in str(r.json)

@pytest.mark.parametrize('mode',['missing','duplicate','tampered','different_plan'])
def test_bad_receipts_rejected(client,monkeypatch,mode):
    p=plan(client,monkeypatch);rs=execute(client,monkeypatch,p)
    if mode=='missing': rs=rs[:1]
    if mode=='duplicate': rs=[rs[0],rs[0]]
    if mode=='tampered': rs[0]='invalid'
    if mode=='different_plan':
        d=target.load_token(rs[0],'receipt');d['plan_hash']='wrong';rs[0]=target.signer().dumps(d)
    monkeypatch.setattr(target,'chat',lambda *a: pytest.fail('must not call model'))
    assert client.post('/api/agent/finish',json={'plan':p['plan'],'receipts':rs}).status_code==400

@pytest.mark.parametrize('temp',[True,0,1.1,'0.3',None])
def test_invalid_temperature(client,temp):
    assert client.post('/api/agent/route',json={'question':'octocat','temperature':temp}).status_code==400

@pytest.mark.parametrize('kind',['timeout','400'])
def test_sdk_error_http_mapping(client,monkeypatch,kind):
    def chat(*a):
        req=httpx.Request('POST','https://example.invalid')
        if kind=='timeout': raise APITimeoutError(request=req)
        raise APIStatusError('private provider payload',response=httpx.Response(400,request=req),body=None)
    monkeypatch.setattr(target,'chat',chat)
    r=client.post('/api/agent/route',json={'question':'octocat'})
    assert r.status_code==(504 if kind=='timeout' else 502)
    assert 'private provider payload' not in r.text

def test_clarification_history(client,monkeypatch):
    def chat(messages,*a):
        assert messages[-2]['content']=='請提供帳號。'
        return {'content':'收到 octocat。'}
    monkeypatch.setattr(target,'chat',chat)
    r=client.post('/api/agent/route',json={'question':'octocat','history':[{'role':'assistant','content':'請提供帳號。'}]})
    assert r.status_code==200 and r.json['data']['mode']=='reply'
