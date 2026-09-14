# Testing and acceptance

## Automated checks

Run `python -m pytest` inside each `functions` directory. Tests use mocks and do not spend Groq quota. GitHub Actions runs them for pushes and pull requests.

## Live acceptance

Weather:

1. Query `Taipei`, `MountFuji`, and `LAX`.
2. Submit a blank location and confirm the UI clearly states how location was resolved.
3. Confirm weather data appears before or together with advice.
4. Simulate a bad upstream response and verify a readable error replaces a frozen page.

Tool assistant:

1. “Write a promotion for product 3.” Expected tool: Fake Store.
2. “Analyze octocat's public GitHub work.” Expected tool: GitHub.
3. “Explain generative AI using Chinese Wikipedia.” Expected tool: Wikipedia.
4. “Summarize worldwide M5+ earthquakes in the last 24 hours.” Expected tool: USGS.
5. “Analyze his GitHub.” Expected behavior: ask for the username.
6. “Find tomorrow's flight.” Expected behavior: explain that no flight tool exists.
7. A combined GitHub and Wikipedia request may select two tools.

For every case, review tool name, arguments, source data, final answer, temperature slider, mobile layout, Share control, and footer link. A successful request is not enough: reject unsupported factual additions.

---

# 測試與驗收

## 自動測試

在每套 `functions` 目錄執行 `python -m pytest`。測試使用 Mock，不消耗 Groq 額度。GitHub Actions 會在 Push 與 Pull Request 時執行。

## 線上驗收

天氣顧問：

1. 查詢 `Taipei`、`MountFuji` 與 `LAX`。
2. 城市留白，確認畫面清楚說明位置如何判定。
3. 確認天氣資料能在建議之前或同時顯示。
4. 模擬上游錯誤，確認畫面顯示可讀錯誤，不會一直卡住。

工具助理：

1. 「幫商品編號 3 寫促銷文案。」預期 Fake Store。
2. 「分析 octocat 的公開 GitHub 作品。」預期 GitHub。
3. 「依中文維基百科解釋生成式 AI。」預期 Wikipedia。
4. 「整理最近 24 小時全球規模 5 以上地震。」預期 USGS。
5. 「分析他的 GitHub。」預期先追問帳號。
6. 「查明天航班。」預期說明沒有航班工具。
7. 同時詢問 GitHub 與 Wikipedia，可能選擇兩個工具。

每題需核對工具名稱、參數、來源資料、最終回答、Temperature 滑桿、手機版、Share 元件與頁尾連結。請勿只看請求成功；若回答加入來源沒有提供的事實，內容驗收仍應判定失敗。
