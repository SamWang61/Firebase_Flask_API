"""Run on loopback only / 僅在本機啟動。"""
import getpass
import os
import sys
from pathlib import Path
from flask import send_from_directory
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"functions"))
if not os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"]=getpass.getpass("Groq API Key (hidden / 隱藏輸入): ").strip()
if os.getenv("LANGSMITH_TRACING", "false").lower()=="true" and not os.getenv("LANGSMITH_API_KEY"):
    os.environ["LANGSMITH_API_KEY"]=getpass.getpass("LangSmith API Key (hidden / 隱藏輸入): ").strip()
from app import app
@app.get("/")
def index():
    return send_from_directory(ROOT/"public","index.html")
@app.get("/<path:name>")
def static_file(name):
    return send_from_directory(ROOT/"public",name)
if __name__=="__main__":
    app.run(host="127.0.0.1",port=5000,debug=False)
