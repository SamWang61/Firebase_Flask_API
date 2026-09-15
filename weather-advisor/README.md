# Weather Advisor

Live site: https://flaskapi-test01.web.app/

This Firebase project retrieves current conditions from wttr.in and sends the data to Groq for Traditional Chinese advice. The location accepts a city, MountFuji, LAX, or blank input. Blank input attempts forwarded client IP and otherwise falls back to Taipei. Routes: GET /api/health and POST /api/weather. Temperature: 0.1–1.0, default 0.3.

See ../docs/DEPLOYMENT.md and ../docs/TESTING.md.

## Other learning projects

This remains Project 1. Project 2 introduces autonomous tool selection; [Project 3](../langchain-tool-assistant/README.md) extends that design through LangChain and LangSmith without changing this weather application's code or deployment target.

---

# AI 即時天氣顧問

正式網站：https://flaskapi-test01.web.app/

此 Firebase 專案從 wttr.in 取得目前天氣，再由 Groq 產生繁體中文建議。位置可輸入城市、MountFuji、LAX 或留白。留白時嘗試使用轉送的使用者 IP，無法取得時以台北備援，因此不宣稱是裝置精準定位。路由為 GET /api/health 與 POST /api/weather。Temperature 範圍 0.1–1.0，預設 0.3。

部署與測試請參閱 ../docs/DEPLOYMENT.md 與 ../docs/TESTING.md。

## 其他教學專案

本程式仍為第一專案。第二專案示範自主工具選擇；[第三專案](../langchain-tool-assistant/README.md)透過 LangChain 與 LangSmith 延伸該設計，不更動天氣程式與部署目標。
