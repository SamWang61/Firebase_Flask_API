# Development workflow

1. Define the user outcome and acceptance questions.
2. Build and test the public API adapter before adding an LLM.
3. Add Flask routes with validation, timeouts, and structured errors.
4. Add grounded prompts or tool schemas.
5. Build a responsive frontend with visible stage feedback.
6. Test normal, missing-input, unsupported-tool, timeout, and upstream-error paths.
7. Store secrets, deploy Functions and Hosting, then verify the live URLs.
8. Review answer accuracy manually; HTTP 200 proves delivery, not truth.

The projects evolved from a single black-box request into staged requests after real 404 and 504 failures. DEBUG entries intentionally show application stages and HTTP outcomes, not hidden chain-of-thought.

## Local commands

Windows PowerShell:

```powershell
cd weather-advisor\functions
py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest
```

Repeat for `ai-tool-assistant/functions`. Start emulators from the selected project root:

```powershell
firebase emulators:start --only functions,hosting
```

## LangChain development track

Project 3 preserves the original source and adds an independent environment and launcher. Study [its development guide](../langchain-tool-assistant/docs/DEVELOPMENT.md) for the ChatGroq migration, multi-query schema, summary-prompt correction and LangSmith configuration. Start with [its quick start](../langchain-tool-assistant/README.md); it does not require modifying the original two projects.

---

# 開發流程

1. 定義使用者成果與驗收問題。
2. 先完成並測試公開 API 轉接，再加入 LLM。
3. 建立含輸入驗證、逾時與結構化錯誤的 Flask 路由。
4. 加入有資料約束的提示詞或工具規格。
5. 建立響應式前端並顯示階段回饋。
6. 測試正常、資料不足、不支援工具、逾時與上游錯誤。
7. 設定 Secret，部署 Functions 與 Hosting，再驗證正式網址。
8. 人工檢查回答內容；HTTP 200 只證明送達，不代表內容一定正確。

專案在實際發生 404 與 504 後，從單一黑盒請求調整為分段請求。DEBUG 顯示應用階段與 HTTP 結果，不呈現模型隱藏思考過程。

## 本機指令

Windows PowerShell：

```powershell
cd weather-advisor\functions
py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest
```

`ai-tool-assistant/functions` 亦執行相同步驟。再從選定專案根目錄啟動 Emulator：

```powershell
firebase emulators:start --only functions,hosting
```

## LangChain 開發路線

第三專案保留原始程式，另設獨立環境與啟動器。[開發指南](../langchain-tool-assistant/docs/DEVELOPMENT.md)說明 ChatGroq 改写、多查詢規格、摘要提示修正與 LangSmith 設定。請從[快速開始](../langchain-tool-assistant/README.md)進入，不必修改原有兩套程式。
