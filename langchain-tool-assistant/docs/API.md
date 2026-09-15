# HTTP API and trust boundary

Responses use `{ok, data, debug}` on success and `{ok:false, error, debug}` on failure. A successful HTTP response from execute may contain `tool_ok:false`; always check the tool result.

| Endpoint | Request | Response data |
|---|---|---|
| `GET /api/health` | None | Service, implementation, version; cloud adds deployment/function identity |
| `POST /api/agent/route` | `question`, numeric `temperature`, optional `history` | `mode:reply` with answer, or `mode:tools`, signed `plan`, calls `{id,name,arguments}` |
| `POST /api/agent/execute` | `plan`, `call_id` | `receipt`, `tool`, `tool_ok`, raw `source`, summarized `result` |
| `POST /api/agent/finish` | `plan`, all `receipts` | Plain-text `answer`, model and temperature |

The client sends each call to execute, collects receipts and only then calls finish. Receipts bind the call ID and result to the SHA-256 of the signed plan. Finish rejects expired, tampered, duplicate, missing or cross-plan receipts before calling the model. Tokens expire in 15 minutes and use the server Groq key as signing material. Key rotation invalidates in-progress plans. Signed tokens are integrity-protected, not encrypted, and can be replayed within their validity window; this is not authentication or rate limiting.

Only allowlisted hosts can be fetched. The client cannot replace source results in finish. Failed APIs become signed failure records, allowing honest partial or unavailable answers. The summary contains up to 10,000 characters per tool; truncation can remove context. No database stores conversations; the browser retains the latest six messages in memory, and enabled LangSmith tracing may separately record requests.

The reference implements the staged assistant endpoints only; historical standalone `/api/data` and `/api/analyze` pages are not part of this third project. Use Project 2 for its original implementation.

---

# HTTP API 與信任邊界

成功回傳 `{ok, data, debug}`，失敗回傳 `{ok:false, error, debug}`。execute 即使 HTTP 成功，也可能包含 `tool_ok:false`，必須檢查工具結果。

| 端點 | 請求 | 回傳資料 |
|---|---|---|
| `GET /api/health` | 無 | 服務、實作與版本；雲端加上部署／Function 識別 |
| `POST /api/agent/route` | `question`、數值 `temperature`、選填 `history` | `mode:reply` 與回答，或 `mode:tools`、簽署 `plan`、`{id,name,arguments}` 呼叫 |
| `POST /api/agent/execute` | `plan`、`call_id` | `receipt`、`tool`、`tool_ok`、原始 `source`、整理後 `result` |
| `POST /api/agent/finish` | `plan`、全部 `receipts` | 純文字 `answer`、模型與 Temperature |

前端逐一執行呼叫，收齊收據後才送出 finish。收據將呼叫 ID 與結果綁定至簽署計畫的 SHA-256。finish 在呼叫模型前拒絕過期、竄改、重複、缺漏或跨計畫收據。Token 有效 15 分鐘，使用伺服器 Groq Key 簽章；換 Key 會使進行中的計畫失效。簽章保護完整性，不是加密，有效期間仍可重播，也不能代替登入或限流。

只能查詢允許清單內的主機，前端不能在 finish 替換資料。API 失敗也會簽成失敗紀錄，模型可誠實說明部分或全部資料無法取得。每個工具最多提供 10,000 字元，截斷可能使上下文減少。對話不存入資料庫；瀏覽器記憶體保留最近六則，啟用 LangSmith 時則可能另外記錄請求。

此參考版本只實作分段助理端點；歷史獨立練習頁 `/api/data` 與 `/api/analyze` 不屬於第三個子專案。原有實作請參考第二個子專案。
