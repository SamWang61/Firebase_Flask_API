# Security

## Reporting

Do not open a public issue containing API keys, tokens, billing information, or personal data. Revoke an exposed key immediately, rotate the Firebase secret, and report only sanitized reproduction steps.

## Controls in this repository

- Groq credentials are read from Firebase Secret Manager.
- External hosts are fixed in server code; user input never becomes an arbitrary URL.
- Input lengths, types, ranges, and tool names are validated.
- Tool plans are signed and expire after 15 minutes.
- Model output is rendered with `textContent`.
- Error responses avoid returning secrets or exception internals.

This is an educational project, not a complete production security boundary. Before public production use, add App Check or authentication, rate limiting, usage monitoring, budget alerts, abuse controls, and a privacy notice.

## LangChain tracing and deployment

LangSmith tracing is opt-in and may record prompts, model responses and source data. Review access and retention before enabling it. Signed plans/receipts are not encrypted and can be replayed before expiry; do not treat them as authentication. Secret rotation can affect other functions bound to the same secret in the project. Separate Hosting and codebase names do not separate billing or project-wide access. See [the trust boundary](langchain-tool-assistant/docs/API.md).

---

# 安全政策

## 問題回報

請勿在公開 Issue 張貼 API Key、Token、帳務資料或個人資料。若金鑰外洩，應立即撤銷、更新 Firebase Secret，並只提供已去識別化的重現步驟。

## 本倉庫的安全控制

- Groq 金鑰由 Firebase Secret Manager 讀取。
- 外部主機固定於後端程式，使用者輸入不會變成任意網址。
- 驗證輸入長度、型別、範圍與工具名稱。
- 工具計畫含簽章，15 分鐘後失效。
- 模型回答以 `textContent` 顯示。
- 錯誤回覆不暴露金鑰與例外內部資訊。

本專案是教學作品，並非完整正式環境安全邊界。若要長期公開服務，請增加 App Check 或登入、限流、用量監控、預算警示、防濫用措施與隱私聲明。

## LangChain 追蹤與部署

LangSmith 追蹤需自行啟用，可能記錄提示、模型回覆與來源資料，啟用前請核對存取與保存設定。簽章計畫／收據不是加密，期限內可能重播，不能當成登入驗證。同專案共用 Secret 的其他 Function 也可能受金鑰輪替影響。獨立 Hosting 與 codebase 名稱不代表帳務或專案權限隔離，詳見[信任邊界](langchain-tool-assistant/docs/API.md)。
