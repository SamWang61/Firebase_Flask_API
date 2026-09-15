# Project 3: LangChain API Tool Assistant

[Published demonstration](https://sam-lc-11a0f65437.web.app/) · [Original demonstration](https://fakestoreapi-6c17e.web.app/) · [Repository overview](../README.md)

This project extends the original Flask four-API assistant with LangChain `ChatGroq`, native tool binding, a compact multi-query plan, and optional LangSmith traces. A user asks a question; the model proposes API queries; Python validates and executes them; a separate model invocation summarizes verified results. No keyword router substitutes for the model's decision.

This is a reproducible repository reference, assembled from Project 2's API/frontend source and the v3 adapter used in the development session. It is not a byte-for-byte export of the maintainer's deployed Windows directory. See [provenance and results](docs/RESULTS.md) before comparing versions.

## Capabilities

| Tool | Parameters | Scope |
|---|---|---|
| `fakestore` | `product_id`: integer 1–20 | One mock product; no real stock or offers |
| `github` | `username`: valid public username | Profile and up to six recently updated public repositories |
| `wikipedia` | `topic`: 1–80 characters | One Chinese Wikipedia introduction and source |
| `usgs` | `hours`: 24/72/168/720; `min_magnitude`: 0–10 | Up to ten worldwide events sorted by magnitude; no prediction |

One plan contains 1–4 independent queries, including different queries for the same API. Missing input triggers clarification. History retains up to six text messages. Temperature ranges from 0.1 to 1.0 (default 0.3). Final answers use Traditional Chinese plain text. DEBUG exposes tools, parameters, responses and errors, not private model reasoning. Share sends the page URL only.

## Local quick start

Use Python 3.13 and run from this directory. Dependencies are installed in an independent environment:

```powershell
py -3.13 -m venv functions/venv
.\functions\venv\Scripts\python.exe -m pip install -r functions/requirements-dev.txt
.\functions\venv\Scripts\python.exe -m pytest functions test_isolation.py
.\functions\venv\Scripts\python.exe run_local.py
```

Open http://127.0.0.1:5000. Enter your Groq key in the hidden terminal prompt. The launcher does not save it. On Linux/macOS use `python3` and `functions/venv/bin/python` instead. The app does not automatically load `.env` files.

For optional tracing, set `$env:LANGSMITH_TRACING="true"` and `$env:LANGSMITH_PROJECT="My-LangChain-Lab"` before launching; it will prompt separately for a LangSmith key. Traces can contain questions and retrieved data. See [development](docs/DEVELOPMENT.md).

## Reading order

1. [Development and LangChain design](docs/DEVELOPMENT.md)
2. [HTTP contracts and verified results](docs/API.md)
3. [Isolated Firebase deployment](docs/DEPLOYMENT.md)
4. [Testing and troubleshooting](docs/TESTING.md)
5. [Final outcome and evidence](docs/RESULTS.md)

Do not use the repository-root `deploy-all.ps1` for this project. The isolated helper creates a new Hosting site, Function and codebase in your explicitly selected Firebase project. It does not publish to the demonstration URL by default.

---

# 第三個子專案：LangChain API 工具助理

[LangChain 成果網站](https://sam-lc-11a0f65437.web.app/) · [原版成果網站](https://fakestoreapi-6c17e.web.app/) · [倉庫總覽](../README.md)

本專案將原有 Flask 四 API 助理延伸為 LangChain 應用：使用 `ChatGroq`、原生工具綁定、精簡多查詢計畫，以及選用的 LangSmith 追蹤。使用者提問後，由模型提出 API 查詢，Python 驗證與執行，再由獨立模型呼叫整理已驗證結果，沒有用關鍵字路由代替模型判斷。

這是可重現的倉庫參考版本，整合第二個子專案的 API／前端原始碼與開發過程使用的 v3 adapter，並非維護者 Windows 已部署目錄的逐位元匯出。比較版本前請先閱讀[來源與成果紀錄](docs/RESULTS.md)。

## 能力範圍

| 工具 | 參數 | 範圍 |
|---|---|---|
| `fakestore` | `product_id`：整數 1–20 | 單筆模擬商品，不能代表真實庫存或優惠 |
| `github` | `username`：有效公開帳號 | 簡介與最多六個近期更新的公開倉庫 |
| `wikipedia` | `topic`：1–80 字 | 一個中文維基百科條目簡介與來源 |
| `usgs` | `hours`：24／72／168／720；`min_magnitude`：0–10 | 全球最多十筆事件，依規模排序，不預測地震 |

每個計畫含 1–4 項獨立查詢，也可對同一 API 使用不同條件。資訊不足先追問，保留最近六則文字訊息。Temperature 為 0.1–1.0，預設 0.3。回答使用繁體中文純文字。DEBUG 顯示工具、參數、回應與錯誤，不顯示模型內部思考；Share 僅分享網址。

## 本機快速開始

使用 Python 3.13，在本目錄建立獨立環境：

```powershell
py -3.13 -m venv functions/venv
.\functions\venv\Scripts\python.exe -m pip install -r functions/requirements-dev.txt
.\functions\venv\Scripts\python.exe -m pytest functions test_isolation.py
.\functions\venv\Scripts\python.exe run_local.py
```

開啟 http://127.0.0.1:5000，在終端機隱藏提示輸入 Groq Key，啟動器不會存檔。Linux／macOS 改用 `python3` 與 `functions/venv/bin/python`。程式不會自動讀取 `.env`。

若啟用追蹤，先設定 `$env:LANGSMITH_TRACING="true"` 與 `$env:LANGSMITH_PROJECT="My-LangChain-Lab"`；啟動時會另外要求 LangSmith Key。追蹤可能包含問題與取得的資料，詳見[開發指南](docs/DEVELOPMENT.md)。

## 建議閱讀順序

1. [開發過程與 LangChain 設計](docs/DEVELOPMENT.md)
2. [HTTP 協定與結果驗證](docs/API.md)
3. [Firebase 隔離部署](docs/DEPLOYMENT.md)
4. [測試與疑難排解](docs/TESTING.md)
5. [最終成果與驗收證據](docs/RESULTS.md)

本專案不要使用倉庫根目錄的 `deploy-all.ps1`。隔離部署腳本只在您明確指定的 Firebase 專案建立新 Hosting、Function 與 codebase，不會預設發布至展示網站。
