# Testing and troubleshooting

Run from this project's root:

```powershell
.\functions\venv\Scripts\python.exe -m pytest functions test_isolation.py
```

Tests use the actual LangChain/Groq SDK over an HTTP mock transport. They cover 1/2/4-query normalization, malformed JSON, duplicates, unsupported names, final-stage tool refusal, no automatic retry, clarification, temperature validation, signed receipt rejection, partial API failure and scoped deployment commands. Tests do not prove a live model selects the right tools. CI runs all three projects independently and never deploys Firebase.

## Manual acceptance

| Input or action | Required outcome |
|---|---|
| Analyze octocat's public GitHub work | One GitHub query, public facts only |
| Analyze his GitHub; then answer `octocat` | Ask first, then resolve from recent conversation |
| Analyze octocat and explain open-source software using Wikipedia | Two queries: GitHub + Wikipedia; finish verifies two receipts |
| Request product 3, octocat, Wikipedia AI, and M5+ last 24h | Four independently parameterized queries |
| Ask for tomorrow's flights | Explain unsupported tool |
| One API fails | Preserve raw successful data; explain failure without inventing facts |
| Drag temperature; submit again | Selected 0.1–1.0 value reaches model |
| Mobile layout and Share | Form remains usable; share URL only; footer works |

Use a fresh conversation for independent cases. Inspect requested tasks, selected tools, arguments, source data, answer and DEBUG. `Verified 1 results` is correct for one call; it is a failed two-tool acceptance if the question clearly needs two. Do not hardcode the number in the UI.

If the final stage returns `tool_use_failed`, confirm the dedicated summary path is installed; changing temperature or budget is not a direct fix. For HTTP 401, verify the key and deployed secret version. For 429, inspect rate limits and quota. For 504, identify route/execute/finish and elapsed time; do not increase timeouts blindly. Failed requests must release UI controls for retry.

For LangSmith, confirm `agent_route` and `agent_finish` in your selected tracing project. HTTP 200 from the application does not prove a trace was uploaded or an answer is factual. Save sanitized acceptance evidence separately from source code.

---

# 測試與疑難排解

在本專案根目錄執行：

```powershell
.\functions\venv\Scripts\python.exe -m pytest functions test_isolation.py
```

測試以真正的 LangChain／Groq SDK 搭配 HTTP 模擬傳輸，涵蓋一／二／四項查詢轉換、錯誤 JSON、重複與未知工具、摘要階段拒絕工具、不自動重試、追問、Temperature 驗證、收據拒絕、部分 API 失敗與部署指令限定。這不代表真實模型必定選對工具。CI 分開執行三套專案，完全不部署 Firebase。

## 人工驗收

| 輸入或操作 | 必須達成的結果 |
|---|---|
| 分析 octocat 的公開 GitHub 作品 | 一項 GitHub 查詢，只整理公開資料 |
| 分析他的 GitHub；再補充 `octocat` | 先追問，再依最近對話解析 |
| 分析 octocat，並依 Wikipedia 解釋開源軟體 | GitHub＋Wikipedia 兩項查詢，finish 驗證兩張收據 |
| 查商品 3、octocat、維基人工智慧、近 24 小時 M5 以上地震 | 四項查詢，各有獨立參數 |
| 查明天航班 | 說明沒有支援工具 |
| 一項 API 失敗 | 保留成功資料，說明失敗，不編造 |
| 拖動 Temperature 再送出 | 0.1–1.0 所選數值送至模型 |
| 手機版與 Share | 表單可用，只分享網址，署名連結正常 |

獨立案例請開新對話，檢查需求、選用工具、參數、來源、回答與 DEBUG。單查詢顯示「已驗證 1 項結果」正確；若需求明確包含兩項，則未通過雙工具驗收，不應在畫面硬改數字。

若摘要回傳 `tool_use_failed`，應確認專用摘要路徑已安裝，調 Temperature 或預算不能直接修正。HTTP 401 應驗證 Key 與雲端 Secret 版本；429 檢查限流及額度；504 先辨認 route／execute／finish 與耗時，不盲目增加等待時間。失敗後 UI 必須恢復可重試。

LangSmith 請確認指定追蹤專案內有 `agent_route` 與 `agent_finish`。應用 HTTP 200 不代表追蹤已上傳，也不代表回答真實。去識別化驗收證據請另存，不混入原始碼。
