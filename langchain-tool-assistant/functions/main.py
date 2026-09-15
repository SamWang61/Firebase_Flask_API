"""Reference entry; deployment generates a unique export / 參考入口，部署時產生獨立名稱。"""
from firebase_functions import https_fn, options
from app import app

@https_fn.on_request(region="asia-east1", timeout_sec=45, memory=options.MemoryOption.MB_512, secrets=["GROQ_API_KEY"])
def api_langchain_reference(req: https_fn.Request) -> https_fn.Response:
    with app.request_context(req.environ):
        return app.full_dispatch_request()
