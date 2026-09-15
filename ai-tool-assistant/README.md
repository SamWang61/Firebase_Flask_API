# AI Tool Assistant

Live site: https://fakestoreapi-6c17e.web.app/

The user asks one natural-language question. Groq chooses from Fake Store, GitHub, Chinese Wikipedia, and USGS tools. Python validates each call and returns signed receipts for a grounded final answer. Capability cards only fill examples; they do not choose the API. DEBUG shows stages, tools, arguments, and HTTP results—not hidden reasoning. Share sends only the page URL.

Routes: GET /api/health, POST /api/agent/route, POST /api/agent/execute, POST /api/agent/finish.

## Related Project 3

The [LangChain extension](../langchain-tool-assistant/README.md) preserves this project and demonstrates ChatGroq, compact multi-query planning, dedicated summaries and isolated Firebase deployment. Compare [development decisions](../langchain-tool-assistant/docs/DEVELOPMENT.md) before migrating.

---

# AI 工具助理

正式網站：https://fakestoreapi-6c17e.web.app/

使用者輸入自然語言問題，Groq 從 Fake Store、GitHub、中文 Wikipedia 與 USGS 選擇工具。Python 驗證呼叫，再以簽署收據把資料交回模型回答。能力卡只填入範例，不會指定 API。DEBUG 顯示階段、工具、參數及 HTTP 結果，不顯示模型隱藏思考。Share 只分享頁面網址。

路由：GET /api/health、POST /api/agent/route、POST /api/agent/execute、POST /api/agent/finish。

## 相關的第三專案

[LangChain 延伸](../langchain-tool-assistant/README.md)保留本專案，示範 ChatGroq、精簡多查詢規劃、專用摘要與 Firebase 隔離部署。遷移前請參考[開發決策](../langchain-tool-assistant/docs/DEVELOPMENT.md)。
