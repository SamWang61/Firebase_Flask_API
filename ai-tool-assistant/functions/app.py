import hashlib
import json
import math
import os
import re
from datetime import datetime, timedelta, timezone
import requests
from flask import Flask, jsonify, request
from itsdangerous import URLSafeTimedSerializer, BadSignature

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
PUBLIC_TIMEOUT = (4, 10)
GROQ_TIMEOUT = (4, 20)
SYSTEM = """Select tools from the user's need; never ask the user to choose an API. Ask for missing product IDs, GitHub usernames, or Wikipedia topics. Default an unspecified earthquake query to 24 hours and magnitude 5. Refuse unsupported requests. Use only returned tool data. Never infer repository purposes, identity, personality, unlisted repositories, inventory, discounts, earthquake predictions, or safety. Wikipedia is one source, not complete fact-checking. Answer in Traditional Chinese plain text paragraphs or numbered lists. Never use Markdown tables, hash headings, bold markers, or code fences. / 依問題自主選工具，資料不足先追問；最終回答只能使用工具結果，採繁體中文純文字。"""

def tool(name, description, properties):
    return {"type":"function","function":{"name":name,"description":description,"parameters":{"type":"object","properties":properties,"required":list(properties),"additionalProperties":False}}}

TOOLS = [
    tool("fakestore","Get mock product 1–20 for copywriting / 取得模擬商品",{"product_id":{"type":"integer","minimum":1,"maximum":20}}),
    tool("github","Get public profile and six recently updated repositories / 取得公開 GitHub 資料",{"username":{"type":"string","maxLength":39}}),
    tool("wikipedia","Search one Chinese Wikipedia introduction / 搜尋中文維基百科",{"topic":{"type":"string","minLength":1,"maxLength":80}}),
    tool("usgs","Get up to ten worldwide earthquakes / 取得全球地震",{"hours":{"type":"integer","enum":[24,72,168,720]},"min_magnitude":{"type":"number","minimum":0,"maximum":10}}),
]

def debug(stage, message):
    item={"time":datetime.now(timezone.utc).isoformat(timespec="seconds"),"stage":stage,"message":message}
    print(f"[DEBUG] stage={stage} message={message}",flush=True)
    return item

def ok(data, logs):
    return jsonify({"ok":True,"data":data,"debug":logs})

def fail(message, logs, status=502):
    logs.append(debug("error",message))
    return jsonify({"ok":False,"error":message,"debug":logs}),status

def signer():
    key=os.getenv("GROQ_API_KEY","").strip()
    if not key:
        raise RuntimeError("GROQ_API_KEY is not configured / 尚未設定 GROQ_API_KEY")
    return URLSafeTimedSerializer(key,salt="ai-tools-v1")

def load_token(token, kind):
    if not isinstance(token,str) or len(token)>180000:
        raise ValueError()
    value=signer().loads(token,max_age=900)
    if value.get("kind")!=kind:
        raise ValueError()
    return value

def get_json(url, params=None, headers=None):
    base={"Accept":"application/json","User-Agent":"FirebaseFlaskAPILabs/1.0"}
    base.update(headers or {})
    response=requests.get(url,params=params,headers=base,timeout=PUBLIC_TIMEOUT)
    response.raise_for_status()
    return response.json()

def fetch_fakestore(args):
    pid=args["product_id"]
    data=get_json(f"https://fakestoreapi.com/products/{pid}")
    context=f"Title: {data.get('title')}\nPrice USD: {data.get('price')}\nCategory: {data.get('category')}\nRating: {data.get('rating')}\nDescription: {data.get('description')}\nSource: https://fakestoreapi.com/products/{pid}"
    return data,context

def fetch_github(args):
    username=args["username"]
    headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
    user=get_json(f"https://api.github.com/users/{username}",headers=headers)
    repos=get_json(f"https://api.github.com/users/{username}/repos",{"sort":"updated","per_page":6},headers)
    data={"profile":user,"recent_repositories":repos}
    rows=[f"{r.get('name')}; language={r.get('language') or 'not specified'}; stars={r.get('stargazers_count',0)}; url={r.get('html_url')}" for r in repos]
    context=f"Username: {user.get('login')}\nBio: {user.get('bio')}\nPublic repo count: {user.get('public_repos')}\nFollowers: {user.get('followers')}\nOnly six recently updated repositories are listed:\n"+"\n".join(rows)
    return data,context

def fetch_wikipedia(args):
    topic=args["topic"]
    headers={"User-Agent":"FirebaseFlaskAPILabs/1.0"}
    search=get_json("https://zh.wikipedia.org/w/api.php",{"action":"query","list":"search","srsearch":topic,"format":"json","utf8":1,"srlimit":1},headers)
    hits=search.get("query",{}).get("search",[])
    if not hits:
        raise ValueError("Wikipedia found no article / Wikipedia 找不到條目")
    title=hits[0]["title"]
    detail=get_json("https://zh.wikipedia.org/w/api.php",{"action":"query","prop":"extracts","exintro":1,"explaintext":1,"redirects":1,"titles":title,"format":"json","utf8":1},headers)
    page=next(iter(detail.get("query",{}).get("pages",{}).values()),{})
    source="https://zh.wikipedia.org/wiki/"+requests.utils.quote(title.replace(" ","_"),safe="")
    data={"title":page.get("title",title),"extract":page.get("extract",""),"url":source}
    return data,f"Title: {data['title']}\nExtract: {data['extract']}\nSource: {source}"

def fetch_usgs(args):
    start=datetime.now(timezone.utc)-timedelta(hours=args["hours"])
    feed=get_json("https://earthquake.usgs.gov/fdsnws/event/1/query",{"format":"geojson","starttime":start.isoformat(),"minmagnitude":args["min_magnitude"],"orderby":"magnitude","limit":10})
    events=[]
    for feature in feed.get("features",[]):
        prop=feature.get("properties",{})
        coords=feature.get("geometry",{}).get("coordinates",[None,None,None])
        events.append({"magnitude":prop.get("mag"),"place":prop.get("place"),"time":prop.get("time"),"url":prop.get("url"),"longitude":coords[0],"latitude":coords[1],"depth_km":coords[2]})
    data={"events":events,"query":args,"returned_count":len(events)}
    lines=[f"M{e['magnitude']}; {e['place']}; depth={e['depth_km']} km; source={e['url']}" for e in events]
    return data,f"Worldwide query: last {args['hours']} hours, minimum M{args['min_magnitude']}; up to 10 records sorted by magnitude.\n"+"\n".join(lines)

FETCHERS={"fakestore":fetch_fakestore,"github":fetch_github,"wikipedia":fetch_wikipedia,"usgs":fetch_usgs}

def validate(name,args):
    schema=next((x["function"]["parameters"] for x in TOOLS if x["function"]["name"]==name),None)
    if schema is None or not isinstance(args,dict) or set(args)!=set(schema["properties"]):
        raise ValueError()
    for key,rule in schema["properties"].items():
        value=args[key]
        if rule["type"]=="integer" and type(value) is not int:
            raise ValueError()
        if rule["type"]=="number" and (type(value) not in (int,float) or not math.isfinite(value)):
            raise ValueError()
        if rule["type"]=="string" and (not isinstance(value,str) or not value.strip() or len(value)>rule["maxLength"]):
            raise ValueError()
        if "minimum" in rule and not rule["minimum"]<=value<=rule["maximum"]:
            raise ValueError()
        if "enum" in rule and value not in rule["enum"]:
            raise ValueError()
    if name=="github" and not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?",args["username"]):
        raise ValueError()
    return args

def chat(messages, temperature, with_tools=False):
    key=os.getenv("GROQ_API_KEY","").strip()
    if not key:
        raise RuntimeError("GROQ_API_KEY is not configured / 尚未設定 GROQ_API_KEY")
    body={"model":os.getenv("GROQ_MODEL","openai/gpt-oss-20b"),"messages":messages,"temperature":temperature,"max_tokens":1200}
    if body["model"].startswith("openai/gpt-oss-"):
        body["reasoning_effort"]="low"
    if with_tools:
        body.update({"tools":TOOLS,"tool_choice":"auto"})
    response=requests.post("https://api.groq.com/openai/v1/chat/completions",headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},json=body,timeout=GROQ_TIMEOUT)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]

def plain(text):
    if not isinstance(text,str) or not text.strip():
        raise RuntimeError("Empty AI answer / AI 回覆為空")
    output=[]
    fence=chr(96)*3
    for line in text.splitlines():
        if line.strip().startswith((fence,"~~~")):
            continue
        line=re.sub(r"^\s{0,3}#{1,6}\s*","",line).replace("**","").replace("__","")
        if "|" in line:
            if re.fullmatch(r"[\s|:\-]+",line):
                continue
            line="；".join(x.strip() for x in line.strip().strip("|").split("|"))
        output.append(line)
    return "\n".join(output).strip()

@app.get("/api/health")
def health():
    return jsonify({"ok":True,"service":"ai-tool-assistant","version":"1.0"})

@app.post("/api/agent/route")
def route():
    logs=[debug("route","AI tool selection started / AI 開始選擇工具")]
    try:
        payload=request.get_json(silent=True)
        question=payload.get("question") if isinstance(payload,dict) else None
        temperature=payload.get("temperature",0.3) if isinstance(payload,dict) else None
        history=payload.get("history",[]) if isinstance(payload,dict) else None
        if not isinstance(question,str) or not question.strip() or len(question)>1000:
            raise ValueError()
        if type(temperature) not in (int,float) or not 0.1<=temperature<=1:
            raise ValueError()
        if not isinstance(history,list) or len(history)>6:
            raise ValueError()
        messages=[{"role":"system","content":SYSTEM}]
        for item in history:
            if not isinstance(item,dict) or item.get("role") not in ("user","assistant") or not isinstance(item.get("content"),str) or len(item["content"])>4000:
                raise ValueError()
            messages.append({"role":item["role"],"content":item["content"]})
        messages.append({"role":"user","content":question})
        message=chat(messages,temperature,True)
        calls=message.get("tool_calls") or []
        if not calls:
            return ok({"mode":"reply","answer":plain(message.get("content")),"calls":[]},logs)
        if not isinstance(calls,list) or len(calls)>4:
            raise ValueError()
        clean=[]
        for call in calls:
            name=call["function"]["name"]
            args=validate(name,json.loads(call["function"]["arguments"]))
            clean.append({"id":call["id"],"type":"function","function":{"name":name,"arguments":json.dumps(args,ensure_ascii=False)}})
        messages.append({"role":"assistant","content":None,"tool_calls":clean})
        token=signer().dumps({"kind":"plan","messages":messages,"calls":clean,"temperature":temperature})
        visible=[{"id":c["id"],"name":c["function"]["name"],"arguments":json.loads(c["function"]["arguments"])} for c in clean]
        return ok({"mode":"tools","plan":token,"calls":visible},logs)
    except (ValueError,TypeError,KeyError,json.JSONDecodeError):
        return fail("Invalid input or tool arguments / 輸入或工具參數不正確",logs,400)
    except requests.Timeout:
        return fail("Groq timeout during routing / Groq 選擇工具逾時",logs,504)
    except requests.HTTPError as exc:
        status=exc.response.status_code if exc.response is not None else 502
        return fail(f"Groq HTTP {status}",logs,502)
    except RuntimeError as exc:
        return fail(str(exc),logs,503)

@app.post("/api/agent/execute")
def execute():
    logs=[debug("execute","Tool execution started / 開始執行工具")]
    try:
        payload=request.get_json(silent=True)
        if not isinstance(payload,dict):
            raise ValueError()
        plan=load_token(payload.get("plan"),"plan")
        selected=next((c for c in plan["calls"] if c["id"]==payload.get("call_id")),None)
        if selected is None:
            raise ValueError()
        name=selected["function"]["name"]
        args=validate(name,json.loads(selected["function"]["arguments"]))
        try:
            source,context=FETCHERS[name](args)
            result={"ok":True,"context":context[:10000]}
        except requests.Timeout:
            source,result=None,{"ok":False,"error":f"{name} timeout / 外部 API 逾時"}
        except (requests.RequestException,ValueError,KeyError,IndexError):
            source,result=None,{"ok":False,"error":f"{name} returned unusable data / 外部資料無法使用"}
        digest=hashlib.sha256(payload["plan"].encode()).hexdigest()
        receipt=signer().dumps({"kind":"receipt","plan_hash":digest,"id":selected["id"],"content":result})
        return ok({"tool":name,"tool_ok":result["ok"],"source":source,"result":result,"receipt":receipt},logs)
    except (BadSignature,ValueError,TypeError,KeyError,json.JSONDecodeError):
        return fail("Expired or modified plan / 流程過期或遭修改",logs,400)
    except RuntimeError as exc:
        return fail(str(exc),logs,503)

@app.post("/api/agent/finish")
def finish():
    logs=[debug("finish","Final answer started / 開始整理回答")]
    try:
        payload=request.get_json(silent=True)
        if not isinstance(payload,dict):
            raise ValueError()
        plan=load_token(payload.get("plan"),"plan")
        tokens=payload.get("receipts")
        if not isinstance(tokens,list) or len(tokens)!=len(plan["calls"]):
            raise ValueError()
        digest=hashlib.sha256(payload["plan"].encode()).hexdigest()
        records={}
        for token in tokens:
            receipt=load_token(token,"receipt")
            if receipt["plan_hash"]!=digest or receipt["id"] in records:
                raise ValueError()
            records[receipt["id"]]=receipt["content"]
        messages=plan["messages"]
        messages[0]["content"]+=" Every fact must be explicit in this turn's tool results; say when data is insufficient. / 每項事實必須有本輪工具資料依據。"
        for call in plan["calls"]:
            if call["id"] not in records:
                raise ValueError()
            messages.append({"role":"tool","tool_call_id":call["id"],"content":json.dumps(records[call["id"]],ensure_ascii=False)})
        message=chat(messages,plan["temperature"])
        return ok({"answer":plain(message.get("content")),"temperature":plan["temperature"],"model":os.getenv("GROQ_MODEL","openai/gpt-oss-20b")},logs)
    except (BadSignature,ValueError,TypeError,KeyError):
        return fail("Invalid plan or receipts / 計畫或收據不正確",logs,400)
    except requests.Timeout:
        return fail("Groq timeout during final answer / Groq 整理回答逾時",logs,504)
    except requests.HTTPError as exc:
        status=exc.response.status_code if exc.response is not None else 502
        return fail(f"Groq HTTP {status}",logs,502)
    except RuntimeError as exc:
        return fail(str(exc),logs,503)
