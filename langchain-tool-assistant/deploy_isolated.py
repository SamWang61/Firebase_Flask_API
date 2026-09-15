"""Deploy to new Firebase resources / 部署到全新的 Firebase 資源。"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

PROJECT = "fakestoreapi-6c17e"
ORIGINAL_URL = f"https://{PROJECT}.web.app"
DEFAULT_SOURCE = str(Path(__file__).resolve().parent)
PACKAGE = Path(__file__).resolve().parent
STATE_FILE = PACKAGE / "deployment-state.json"
EXCLUDED_DIRS = {"venv", ".venv", "__pycache__", ".pytest_cache", ".git", ".firebase", "node_modules"}


def run(args, cwd=None, capture=False):
    proc = subprocess.run([str(x) for x in args], cwd=cwd, check=False,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None,
                          text=True, encoding="utf-8", errors="replace")
    if proc.returncode:
        # Do not echo captured output: it may contain environment information.
        # 不回顯截取內容，避免輸出環境資訊。
        raise RuntimeError(f"指令失敗：{Path(str(args[0])).name} {args[1]}，結束碼 {proc.returncode}")
    return proc.stdout if capture else ""


def write_json(path, value):
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def excluded(path):
    name = path.name.lower()
    return (name.startswith(".") or path.suffix.lower() in {".zip", ".pyc", ".pyo", ".pem", ".key", ".log"}
            or "service-account" in name or "service_account" in name or "firebase-adminsdk" in name)


def copy_clean(source, target):
    target.mkdir(parents=True, exist_ok=False)
    for item in source.iterdir():
        if item.is_symlink():
            raise ValueError(f"來源包含連結，請先核對：{item.name}")
        if item.name in EXCLUDED_DIRS or excluded(item):
            continue
        if item.is_dir():
            copy_clean(item, target / item.name)
        else:
            shutil.copy2(item, target / item.name)


def main_source(function_id, deployment_id, langsmith):
    secrets = ["GROQ_API_KEY"] + (["LANGSMITH_API_KEY"] if langsmith else [])
    return f'''"""Isolated cloud entry / 獨立雲端入口。"""
import os
from firebase_functions import https_fn, options
from flask import request
os.environ["LAB_TYPE"] = "fakestore"
os.environ["LANGSMITH_TRACING"] = {str("true" if langsmith else "false")!r}
os.environ["LANGSMITH_PROJECT"] = "FakeStoreAPI-LangChain-Cloud"
os.environ["LANGCHAIN_CALLBACKS_BACKGROUND"] = "false"
from app import app

@app.after_request
def identify_deployment(response):
    if request.path == "/api/health" and response.is_json:
        payload = response.get_json()
        if isinstance(payload, dict):
            payload.update(implementation="langchain", deployment_id={deployment_id!r}, function_id={function_id!r})
            response.set_data(app.json.dumps(payload))
            response.headers["Cache-Control"] = "no-store"
    return response

@https_fn.on_request(region="asia-east1", timeout_sec=45,
                    memory=options.MemoryOption.MB_512, secrets={secrets!r})
def {function_id}(req: https_fn.Request) -> https_fn.Response:
    with app.request_context(req.environ):
        return app.full_dispatch_request()
'''


def config_for(token, runtime):
    return {
        "functions": [{"source": "functions", "codebase": f"lc-{token}", "runtime": runtime,
                       "ignore": ["venv", ".venv", "__pycache__", ".git", ".env*", ".secret*", "*.log"]}],
        "hosting": {"target": "langchain", "public": "public", "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
                    "rewrites": [{"source": "/api/**", "function": {"functionId": f"api_lc_{token}", "region": "asia-east1"}}],
                    "headers": [{"source": "/api/**", "headers": [{"key": "Cache-Control", "value": "no-store"}]}]},
    }


def prepare(source, langsmith=False):
    source = source.resolve()
    if source.name not in ("FakeStoreAPI_LangChain", "langchain-tool-assistant"):
        raise ValueError("來源必須是 FakeStoreAPI_LangChain，不能使用原版")
    for relative in ("functions/app.py", "functions/agent.py", "functions/langchain_adapter_v3.py", "public/index.html"):
        if not (source / relative).is_file():
            raise ValueError(f"缺少已驗收新版檔案：{relative}")
    if "langchain_adapter_v3" not in (source / "functions/agent.py").read_text(encoding="utf-8-sig"):
        raise ValueError("來源尚未套用驗收成功的v3 adapter")
    py = source / ("functions/venv/Scripts/python.exe" if os.name == "nt" else "functions/venv/bin/python")
    if not py.is_file():
        raise ValueError("找不到新版 functions/venv/Scripts/python.exe")
    version = json.loads(run([py, "-c", "import sys,json; print(json.dumps(list(sys.version_info[:2])))"], capture=True))
    if version not in ([3,10], [3,11], [3,12], [3,13]):
        raise ValueError(f"需要確認目前Python版本的Firebase支援：{version}")
    token = uuid.uuid4().hex[:10]
    stage = source.parent / ("FakeStoreAPI_LangChain_Deploy_" + token)
    stage.mkdir(exist_ok=False)
    copy_clean(source / "functions", stage / "functions")
    copy_clean(source / "public", stage / "public")
    site, function, codebase = f"sam-lc-{token}", f"api_lc_{token}", f"lc-{token}"
    config = config_for(token, f"python{version[0]}{version[1]}")
    write_json(stage / "firebase.json", config)
    write_json(stage / ".firebaserc", {"projects":{"default":PROJECT}, "targets":{PROJECT:{"hosting":{"langchain":[site]}}}})
    main = main_source(function, token, langsmith)
    compile(main, "main.py", "exec")
    (stage / "functions/main.py").write_text(main, encoding="utf-8")
    # Freeze the working environment instead of silently upgrading packages.
    # 固定已驗收環境的版本，不自動升級套件。
    freeze = run([py, "-m", "pip", "freeze"], capture=True)
    lines = [x.strip() for x in freeze.splitlines() if x.strip()]
    if not lines or any(not re.fullmatch(r"[A-Za-z0-9_.-]+==[A-Za-z0-9_.+!\-]+", x) for x in lines):
        raise ValueError("已驗收環境含本機或非固定版本依賴；已停止，未部署")
    (stage / "functions/requirements.txt").write_text("\n".join(lines)+"\n", encoding="utf-8")
    # Block obvious local API endpoints; static external links are not rewritten.
    # 檢查本機API位址，不任意改寫原有導覽與分享連結。
    for file in (stage / "public").rglob("*"):
        if file.suffix.lower() in {".js", ".html"}:
            content = file.read_text(encoding="utf-8-sig")
            if re.search(r"https?://(?:127\.0\.0\.1|localhost)(?::\d+)?", content):
                raise ValueError(f"網頁含本機位址，請先確認API根路徑：{file.name}；未部署")
    run([py, "-m", "venv", stage / "functions/venv"])
    staged_py = stage / ("functions/venv/Scripts/python.exe" if os.name == "nt" else "functions/venv/bin/python")
    run([staged_py, "-m", "pip", "install", "-r", "requirements.txt"], cwd=stage / "functions")
    run([staged_py, "-m", "pip", "check"])
    run([staged_py, "-c", "import main; print('Isolated Function import OK')"], cwd=stage / "functions")
    state = {"project":PROJECT, "source":str(source), "stage":str(stage), "token":token, "site":site,
             "function":function, "codebase":codebase, "langsmith":langsmith, "created_site":False, "preflight_done":False}
    write_json(STATE_FILE, state)
    print(f"部署副本已準備：{stage}\n預定網址（尚未部署）：https://{site}.web.app\n新Function：{function}\n新codebase：{codebase}")
    return state


def validate_state(state):
    token = state.get("token", "")
    if not re.fullmatch(r"[a-f0-9]{10}", token) or state.get("project") != PROJECT:
        raise ValueError("部署狀態不正確")
    expected = {"site":f"sam-lc-{token}", "function":f"api_lc_{token}", "codebase":f"lc-{token}"}
    if any(state.get(k) != v for k,v in expected.items()):
        raise ValueError("新資源名稱不符合隔離規則")
    stage = Path(state["stage"])
    config = json.loads((stage / "firebase.json").read_text(encoding="utf-8-sig"))
    runtime = config["functions"][0]["runtime"]
    if config != config_for(token, runtime):
        raise ValueError("部署設定已更動，停止以免指向舊資源")
    rc = json.loads((stage / ".firebaserc").read_text(encoding="utf-8-sig"))
    if rc != {"projects":{"default":PROJECT}, "targets":{PROJECT:{"hosting":{"langchain":[state["site"]]}}}}:
        raise ValueError("Hosting target對應不正確")
    expected_main = main_source(state["function"], token, state["langsmith"])
    if (stage / "functions/main.py").read_text(encoding="utf-8") != expected_main:
        raise ValueError("雲端入口已更動，停止部署")
    return stage


def function_records(payload):
    if payload.get("status") != "success":
        raise ValueError("無法取得Function清單")
    records = payload.get("result")
    if isinstance(records, dict):
        records = records.get("functions")
    if not isinstance(records, list) or any(not isinstance(r,dict) or not r.get("id") for r in records):
        raise ValueError("Function清單格式無法安全辨識，已停止")
    return records


def enable_pending_langsmith(state):
    """Change tracing only before cloud creation / 僅在建立雲端資源前切換追蹤。"""
    stage = validate_state(state)
    if state["langsmith"]:
        return state
    if state.get("created_site") or state.get("preflight_done"):
        raise ValueError("本次續跑修正只適用於尚未建立新站的部署副本")
    main = stage / "functions/main.py"
    previous_main = main.read_bytes()
    previous_state = dict(state)
    backup = stage / "before-enable-langsmith"
    backup.mkdir(exist_ok=False)
    (backup / "main.py").write_bytes(previous_main)
    write_json(backup / "deployment-state.json", previous_state)
    changed = dict(state, langsmith=True)
    text = main_source(state["function"], state["token"], True)
    compile(text, str(main), "exec")
    try:
        main.write_text(text, encoding="utf-8")
        validate_state(changed)
        write_json(STATE_FILE, changed)
    except Exception:
        main.write_bytes(previous_main)
        write_json(STATE_FILE, previous_state)
        raise
    print("已在原部署副本啟用LangSmith；網址、Function及codebase名稱不變。")
    return changed


def get_bytes(url):
    with urlopen(url, timeout=45) as response:
        return response.read()


def verify_ai(new_url, question, expected):
    def post(path, payload):
        req = Request(new_url + path, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                      headers={"Content-Type":"application/json"}, method="POST")
        with urlopen(req, timeout=45) as response:
            result = json.load(response)
        if result.get("ok") is not True or not isinstance(result.get("data"),dict):
            raise RuntimeError(f"新站AI驗收未通過：{path}")
        return result["data"]
    planned = post("/api/agent/route", {"question":question,"temperature":0.3,"history":[]})
    calls = planned.get("calls", [])
    names = [c.get("name") for c in calls]
    if sorted(names) != sorted(expected):
        raise RuntimeError(f"新站工具選擇未涵蓋測試需求：取得 {names}，預期 {expected}")
    receipts=[]
    for call in calls:
        executed=post("/api/agent/execute", {"plan":planned["plan"],"call_id":call["id"]})
        if executed.get("tool_ok") is not True:
            raise RuntimeError(f"新站外部API驗收失敗：{call['name']}")
        receipts.append(executed["receipt"])
    finished=post("/api/agent/finish", {"plan":planned["plan"],"receipts":receipts})
    answer=finished.get("answer")
    if not isinstance(answer,str) or not answer.strip():
        raise RuntimeError("新站AI回答為空白")
    return {"tools":names,"answer_nonempty":True,"answer":answer}


def deploy(state):
    stage = validate_state(state)
    firebase = shutil.which("firebase")
    if not firebase:
        raise RuntimeError("找不到Firebase CLI。請先執行 npm install -g firebase-tools，再重跑")
    # Explicit login precedes all Firebase operations.
    # 所有Firebase操作前明確執行登入。
    run([firebase, "login"], cwd=stage)
    def command(*args, capture=False):
        return run([firebase, *args, "--project", PROJECT], cwd=stage, capture=capture)
    def listing():
        return function_records(json.loads(command("functions:list", "--json", capture=True)))
    before = listing()
    if not state["preflight_done"]:
        if any(r["id"] == state["function"] or r.get("codebase") == state["codebase"] or r.get("labels", {}).get("firebase-functions-codebase") == state["codebase"] for r in before):
            raise ValueError("新Function或codebase已存在，已停止，不覆蓋")
        state["before_functions"] = before
        state["old_home_sha256"] = hashlib.sha256(get_bytes(ORIGINAL_URL + "/")).hexdigest()
        # Firebase deploy still validates secret existence/access. Avoid a redundant
        # metadata CLI invocation that crashed on the user's Windows machine.
        # Secret存在性與存取權仍交由Firebase部署檢查，不忽略任何部署錯誤。
        print("Secret將由Firebase正式部署流程驗證；不另執行functions:secrets:get。")
        state["preflight_done"] = True
        write_json(STATE_FILE, state)
    if not state["created_site"]:
        # Creation must succeed; an existing site is never adopted implicitly.
        # 必須新建成功，不自動採用既有網站。
        command("hosting:sites:create", state["site"])
        state["created_site"] = True
        write_json(STATE_FILE, state)
    validate_state(state)
    command("deploy", "--only", f"functions:{state['codebase']}", "--config", "firebase.json")
    command("deploy", "--only", "hosting:langchain", "--config", "firebase.json")
    new_url = f"https://{state['site']}.web.app"
    health = json.loads(get_bytes(new_url + "/api/health"))
    if health.get("deployment_id") != state["token"] or health.get("function_id") != state["function"] or health.get("ok") is not True:
        raise RuntimeError("部署指令已完成，但新站健康檢查未通過，不能視為驗收成功")
    get_bytes(new_url + "/")
    after = listing()
    index = {(r["id"], r.get("region")):r for r in after}
    old = state["before_functions"]
    unchanged = all(index.get((r["id"], r.get("region"))) == r for r in old)
    homepage_unchanged = hashlib.sha256(get_bytes(ORIGINAL_URL + "/")).hexdigest() == state["old_home_sha256"]
    report = {"new_url":new_url, "health":health, "existing_function_metadata_unchanged":unchanged,
              "old_homepage_bytes_unchanged":homepage_unchanged, "live_ai_test":"pending"}
    write_json(stage / "DEPLOY-RESULT.json", report)
    if not unchanged or not homepage_unchanged:
        raise RuntimeError("新站已上線，但舊站或Function中繼資料比對不同；請查看DEPLOY-RESULT.json，不再部署")
    try:
        report["live_ai_test"] = {
            "single":verify_ai(new_url,"分析 octocat 的公開作品",["github"]),
            "multiple":verify_ai(new_url,"分析 octocat 的公開作品，並查維基百科對開源軟體的介紹",["github","wikipedia"]),
        }
    except Exception as exc:
        report["live_ai_test"] = {"status":"failed", "reason":str(exc)}
        write_json(stage / "DEPLOY-RESULT.json", report)
        raise RuntimeError(f"新站已部署，舊資源比對一致，但AI驗收尚未通過：{exc}") from exc
    write_json(stage / "DEPLOY-RESULT.json", report)
    print(f"新站已部署且健康檢查通過：{new_url}")
    print("舊站首頁內容與原有Function清單中繼資料比對一致。")
    print("單項與兩项API＋AI流程已通過；請再人工核對回答內容與網頁外觀。")
    print(f"部署報告：{stage / 'DEPLOY-RESULT.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="Your Firebase project ID / 您的 Firebase 專案 ID")
    parser.add_argument("--original-url", help="Existing site to compare / 要比對的既有網站")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--langsmith", action="store_true", help="Use an already-created LANGSMITH_API_KEY secret")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    PROJECT = args.project
    ORIGINAL_URL = (args.original_url or f"https://{PROJECT}.web.app").rstrip("/")
    try:
        if STATE_FILE.exists():
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            validate_state(state)
            if args.langsmith and not state["langsmith"]:
                state = enable_pending_langsmith(state)
            print(f"沿用部署副本：{state['stage']}\n預定網址：https://{state['site']}.web.app")
        else:
            state = prepare(Path(args.source), args.langsmith)
        if not args.prepare_only:
            deploy(state)
    except Exception as exc:
        print(f"已停止：{exc}", file=sys.stderr)
        print("沒有執行刪除或回復舊站操作。已成功建立的新資源會保留，可修正後重跑。", file=sys.stderr)
        sys.exit(1)
