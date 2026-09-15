"""Offline deployment guard tests / 離線部署保護測試。"""
import ast
import json
import io
from pathlib import Path
import pytest
import deploy_isolated as d


@pytest.fixture
def stage(tmp_path, monkeypatch):
    token = "123456abcd"
    root = tmp_path / "stage"
    (root / "functions").mkdir(parents=True)
    state = {"project":d.PROJECT, "stage":str(root), "source":"unused", "token":token,
             "site":f"sam-lc-{token}","function":f"api_lc_{token}","codebase":f"lc-{token}",
             "langsmith":False,"preflight_done":False,"created_site":False}
    d.write_json(root / "firebase.json", d.config_for(token,"python312"))
    d.write_json(root / ".firebaserc", {"projects":{"default":d.PROJECT},"targets":{d.PROJECT:{"hosting":{"langchain":[state['site']]}}}})
    (root / "functions/main.py").write_text(d.main_source(state['function'],token,False))
    monkeypatch.setattr(d, "STATE_FILE", tmp_path / "state.json")
    return state


@pytest.mark.parametrize("tamper", ["site","function","codebase","hosting","entry"])
def test_refuses_old_targets(stage, tamper):
    root = Path(stage['stage'])
    if tamper in ("site","function","codebase"):
        stage[tamper] = d.PROJECT if tamper == "site" else "api"
    elif tamper == "hosting":
        rc=json.loads((root/'.firebaserc').read_text())
        rc['targets'][d.PROJECT]['hosting']['langchain']=[d.PROJECT]
        d.write_json(root/'.firebaserc',rc)
    else:
        (root/'functions/main.py').write_text('def api(req): pass')
    with pytest.raises(ValueError):
        d.validate_state(stage)


def test_deploy_calls_only_new_resources(stage, monkeypatch):
    calls=[]
    old=[{"id":"api","region":"asia-east1","codebase":"default","updateTime":"original"}]
    monkeypatch.setattr(d.shutil,"which",lambda _:"firebase.cmd")
    def run(args,cwd=None,capture=False):
        calls.append(args)
        if "functions:list" in args:
            return json.dumps({"status":"success","result":old})
        return "{}"
    monkeypatch.setattr(d,"run",run)
    def get(url):
        if url.endswith('/api/health'):
            return json.dumps({"ok":True,"deployment_id":stage['token'],"function_id":stage['function']}).encode()
        return b"unchanged home"
    monkeypatch.setattr(d,"get_bytes",get)
    monkeypatch.setattr(d,"verify_ai",lambda *args: {"tools":args[2],"answer_nonempty":True})
    d.deploy(stage)
    assert calls[0][1] == "login"
    deployments=[c for c in calls if c[1]=='deploy']
    assert len(deployments)==2
    assert deployments[0][deployments[0].index('--only')+1] == 'functions:'+stage['codebase']
    assert deployments[1][deployments[1].index('--only')+1] == 'hosting:langchain'
    assert all('--project' in c for c in calls[1:])
    assert all('delete' not in str(c) and 'secrets:set' not in str(c) for c in calls)
    assert not any('functions:secrets:get' in c for c in calls)
    report=json.loads((Path(stage['stage'])/'DEPLOY-RESULT.json').read_text())
    assert report['existing_function_metadata_unchanged'] is True
    assert report['old_homepage_bytes_unchanged'] is True


def test_function_collision_stops_before_creation(stage,monkeypatch):
    calls=[]
    monkeypatch.setattr(d.shutil,'which',lambda _:'firebase.cmd')
    def run(args,**kw):
        calls.append(args)
        return json.dumps({'status':'success','result':[{'id':stage['function']}]})
    monkeypatch.setattr(d,'run',run)
    with pytest.raises(ValueError): d.deploy(stage)
    assert not any(c[1] in ('deploy','hosting:sites:create') for c in calls)


def test_failed_site_creation_stops_before_deploy(stage,monkeypatch):
    calls=[]
    monkeypatch.setattr(d.shutil,'which',lambda _:'firebase.cmd')
    monkeypatch.setattr(d,'get_bytes',lambda _:b'home')
    def run(args,**kw):
        calls.append(args)
        if args[1]=='hosting:sites:create': raise RuntimeError('already exists')
        return json.dumps({'status':'success','result':[]})
    monkeypatch.setattr(d,'run',run)
    with pytest.raises(RuntimeError): d.deploy(stage)
    assert not any(c[1]=='deploy' for c in calls)


def test_copy_excludes_secrets_and_venv(tmp_path):
    src=tmp_path/'source'; src.mkdir()
    for name in ('.env','.secret.local','service-account.json','main.py'):
        (src/name).write_text('placeholder')
    (src/'venv').mkdir(); (src/'venv'/'python.exe').write_text('placeholder')
    dst=tmp_path/'copy'; d.copy_clean(src,dst)
    assert [p.name for p in dst.iterdir()]==['main.py']


@pytest.mark.parametrize('tracing',[False,True])
def test_generated_entry_only_exports_new_function(tracing):
    text=d.main_source('api_lc_123456abcd','123456abcd',tracing)
    compile(text,'main.py','exec')
    tree=ast.parse(text)
    exported=[n.name for n in tree.body if isinstance(n,ast.FunctionDef) and any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='on_request' for x in n.decorator_list)]
    assert exported==['api_lc_123456abcd']
    assert 'LANGSMITH_API_KEY' in text if tracing else 'LANGSMITH_API_KEY' not in text


def test_live_verifier_uses_only_new_url(monkeypatch):
    queue=[{"calls":[{"id":"a","name":"github"},{"id":"b","name":"wikipedia"}],"plan":"signed"},
           {"tool_ok":True,"receipt":"r1"},{"tool_ok":True,"receipt":"r2"},{"answer":"有來源的回答"}]
    requests=[]
    def open_request(req,timeout):
        requests.append(req)
        return io.BytesIO(json.dumps({"ok":True,"data":queue.pop(0)}).encode())
    monkeypatch.setattr(d,"urlopen",open_request)
    result=d.verify_ai("https://sam-lc-123456abcd.web.app","test",["github","wikipedia"])
    assert result['tools']==['github','wikipedia']
    assert all(r.full_url.startswith('https://sam-lc-123456abcd.web.app/api/') for r in requests)
    assert json.loads(requests[-1].data)['receipts']==['r1','r2']


def test_live_verifier_rejects_missing_tool(monkeypatch):
    monkeypatch.setattr(d,'urlopen',lambda *args,**kw:io.BytesIO(json.dumps({'ok':True,'data':{'calls':[{'name':'github'}]}}).encode()))
    with pytest.raises(RuntimeError):
        d.verify_ai('https://new.example','test',['github','wikipedia'])


def test_pending_langsmith_keeps_resource_identity(stage):
    original = dict(stage)
    result = d.enable_pending_langsmith(stage)
    assert result['langsmith'] is True
    for key in ('site','function','codebase','token','stage','project'):
        assert result[key] == original[key]
    assert stage['langsmith'] is False
    assert json.loads(d.STATE_FILE.read_text()) == result
    assert d.validate_state(result) == Path(stage['stage'])
    assert (Path(stage['stage'])/'before-enable-langsmith/main.py').exists()
    assert d.enable_pending_langsmith(result) == result


@pytest.mark.parametrize('flag',['created_site','preflight_done'])
def test_pending_switch_rejects_started_deployment(stage,flag):
    stage[flag]=True
    before=(Path(stage['stage'])/'functions/main.py').read_bytes()
    with pytest.raises(ValueError): d.enable_pending_langsmith(stage)
    assert (Path(stage['stage'])/'functions/main.py').read_bytes()==before


def test_pending_switch_restores_main_on_state_write_error(stage,monkeypatch):
    before=(Path(stage['stage'])/'functions/main.py').read_bytes()
    original=d.write_json
    failed=[]
    def write(path,value):
        if path==d.STATE_FILE and value.get('langsmith') and not failed:
            failed.append(True)
            raise OSError('simulated write error')
        return original(path,value)
    monkeypatch.setattr(d,'write_json',write)
    with pytest.raises(OSError): d.enable_pending_langsmith(stage)
    assert (Path(stage['stage'])/'functions/main.py').read_bytes()==before
    assert json.loads(d.STATE_FILE.read_text())['langsmith'] is False
