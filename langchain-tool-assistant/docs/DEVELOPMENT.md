# Development: from direct Groq calls to LangChain

## Evolution

1. Preserve the original working `FakeStoreAPI` directory; develop in `FakeStoreAPI_LangChain`. The repository equivalent is the independent `langchain-tool-assistant` directory.
2. Retain public API adapters, input validation, the three-stage Flask protocol, temperature, plain-text presentation and Share.
3. Follow the classroom example: create `ChatGroq` with the Groq key and model `openai/gpt-oss-20b`; use `.invoke()` instead of manually posting completion JSON. Groq and LangSmith keys serve different services.
4. Bind the native `submit_api_plan` function through `bind_tools`. Its `calls` array describes every independently executable subtask. The `arguments_json` field is a compact JSON string; Python validates it against each API's actual rules before signing anything.
5. Normalize LangChain `AIMessage.tool_calls` into the existing frontend contract. This preserves staged UI requests and signed receipts without adopting an unbounded agent loop.
6. Use a dedicated summary system prompt after receipt validation. The summary invocation receives ordinary system/user messages containing verified data, without tool definitions or a stale instruction to call more tools.
7. Test one, two and four queries, clarification, invalid plans, errors and signed-receipt tampering before preparing a separate deployment snapshot.
8. Deploy only the generated codebase and Hosting target. Record live checks separately from mocked tests.

## Why the design changed

The multi-tool experiment produced `tool_use_failed: Tool choice is none, but model called a tool` at the summary stage. Reusing the planner's instructions conflicted with a summary call that had no tools. Separating planner and summarizer instructions removed that conflict; it does not make model failures impossible.

A later experiment returned just one query for a two-part request, and a more complex planning schema timed out. The v3 solution uses one compact plan function, explicitly asks for all independent tasks, rejects duplicate/unknown/invalid queries, and avoids `anyOf` nesting. Backend validation remains authoritative. A valid plan can still omit a semantic subtask, so acceptance must compare requested versus selected tools.

`ChatGroq` uses connect timeout 4 seconds, read/write 20 seconds, pool timeout 4 seconds and `max_retries=0`. These are phase limits, not a guaranteed total response time. Automatic repeated requests can hide delays and consume quota; failures instead remain visible. For GPT-OSS the invocation passes `reasoning_effort="low"`.

## Classroom starting point

Run `functions/venv/Scripts/python.exe examples/langsmith_example.py` from the project root (on Linux/macOS use `functions/venv/bin/python`). The [small example](../examples/langsmith_example.py) mirrors the supplied ChatGroq lesson before introducing planning and staged requests.

## LangSmith

Enable `LANGSMITH_TRACING=true`, set `LANGSMITH_API_KEY`, and optionally `LANGSMITH_PROJECT`. Invocations have `agent_route` / `agent_finish` names and `compact-plan-v3` tags. This provides model invocation traces; public `requests.get` calls are not automatically separate LangChain Tool spans. Python validates and executes the four APIs itself; the project uses a native plan schema, not four `@tool` objects or `AgentExecutor`.

Cloud deployment binds the LangSmith secret only when `--langsmith` is selected. The generated entry uses project `FakeStoreAPI-LangChain-Cloud` and synchronous callback handling. Never put keys in browser JavaScript, examples, Git history or traces. Review tracing data retention/access before sharing traces.

Official references: [ChatGroq](https://docs.langchain.com/oss/python/integrations/chat/groq), [LangSmith tracing](https://docs.langchain.com/langsmith/trace-with-langchain), [Groq local tool calling](https://console.groq.com/docs/tool-use/local-tool-calling).

---

# 開發過程：從直接呼叫 Groq 到 LangChain

## 演進步驟

1. 保留正常運作的 `FakeStoreAPI`，在 `FakeStoreAPI_LangChain` 開發；倉庫對應獨立的 `langchain-tool-assistant` 目錄。
2. 保留公開 API、參數驗證、Flask 三階段協定、Temperature、純文字呈現與 Share。
3. 延續課堂範例，以 Groq Key 與 `openai/gpt-oss-20b` 建立 `ChatGroq`，改用 `.invoke()`，取代自行 POST completion JSON。Groq 與 LangSmith Key 分屬不同服務。
4. 透過 `bind_tools` 綁定原生 `submit_api_plan`，在 `calls` 陣列列出所有可獨立執行的子任務。`arguments_json` 是精簡 JSON 字串，Python 仍須依每個 API 規則驗證，通過後才能簽章。
5. 將 LangChain 的 `AIMessage.tool_calls` 轉回既有前端格式，保留分段 UI 與簽章收據，不引入無限代理迴圈。
6. 收據驗證後使用專用摘要提示。摘要只收到一般 system／user 訊息與已驗證資料，不附工具定義，也不沿用要求繼續呼叫工具的舊指令。
7. 測試一、二、四項查詢、追問、無效計畫、錯誤與收據竄改，再建立獨立部署副本。
8. 僅部署產生的新 codebase 與 Hosting target，真實驗收與模擬測試分別記錄。

## 為什麼調整設計

多工具試驗曾在摘要階段回傳 `tool_use_failed: Tool choice is none, but model called a tool`。沿用規劃提示，卻沒有提供可用工具，造成指令衝突。拆開規劃與摘要提示可消除此衝突，但不代表模型永遠不會失敗。

後續試驗曾只為兩項需求規劃一項查詢，更複雜的計畫規格也發生逾時。v3 使用單一精簡計畫工具，明確要求涵蓋所有獨立需求，拒絕重複、未知或無效查詢，避免 `anyOf` 巢狀規格。後端驗證仍有最終決定權；合法計畫也可能漏掉語意上的子任務，驗收仍須比對需求與選用工具。

`ChatGroq` 設定連線 4 秒、讀取／寫入 20 秒、連線池等待 4 秒，`max_retries=0`。這是各階段限制，不保證整體回覆時間。自動重試可能掩蓋延遲與增加額度消耗，因此讓失敗保持可見；GPT-OSS 另傳入 `reasoning_effort="low"`。

## 課堂起點

在專案根目錄執行 `functions/venv/Scripts/python.exe examples/langsmith_example.py`；Linux／macOS 改用 `functions/venv/bin/python`。[簡短範例](../examples/langsmith_example.py)對照提供的 ChatGroq 課堂寫法，再逐步進入規劃與分段請求。

## LangSmith

啟用 `LANGSMITH_TRACING=true`、設定 `LANGSMITH_API_KEY`，可選填 `LANGSMITH_PROJECT`。呼叫名稱為 `agent_route`／`agent_finish`，標籤為 `compact-plan-v3`。這會追蹤模型呼叫；公開 API 的 `requests.get` 不會自動成為獨立 LangChain Tool span。四個 API 由 Python 驗證與執行，本專案使用原生計畫規格，並非四個 `@tool` 或 `AgentExecutor`。

雲端只在選擇 `--langsmith` 時綁定 LangSmith Secret。產生的入口使用 `FakeStoreAPI-LangChain-Cloud` 專案名稱與同步 callback 設定。不得把 Key 放入前端、範例、Git 紀錄或追蹤。分享追蹤前請核對資料保存與存取設定。

官方參考：[ChatGroq](https://docs.langchain.com/oss/python/integrations/chat/groq)、[LangSmith 追蹤](https://docs.langchain.com/langsmith/trace-with-langchain)、[Groq 本機工具呼叫](https://console.groq.com/docs/tool-use/local-tool-calling)。
