import os
from firebase_functions import https_fn, options
from app import app

@https_fn.on_request(
    region="asia-east1",
    timeout_sec=45,
    memory=options.MemoryOption.MB_256,
    secrets=["GROQ_API_KEY"],
)
def api(req: https_fn.Request) -> https_fn.Response:
    with app.request_context(req.environ):
        return app.full_dispatch_request()
