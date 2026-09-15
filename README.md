# Firebase + Flask AI API Labs

[Live Weather Advisor](https://flaskapi-test01.web.app/) · [Live AI Tool Assistant](https://fakestoreapi-6c17e.web.app/)

Three production-style learning projects demonstrate how a Firebase Hosting frontend calls Python Flask on Cloud Functions, retrieves live public API data, and asks Groq-hosted LLMs to produce grounded Traditional Chinese answers.

## Projects

| Project | AI behavior | External data | Firebase project |
|---|---|---|---|
| Weather Advisor | Explains current weather and gives practical advice | wttr.in | `flaskapi-test01` |
| AI Tool Assistant | Selects the correct tool from a natural-language question | Fake Store, GitHub, Wikipedia, USGS | `fakestoreapi-6c17e` |

The second project follows local tool calling: the model chooses a tool and arguments, Python validates and executes the call, and the model receives the result before answering. Users do not manually select an API.

## Repository map

- `weather-advisor/`: deployable Firebase project for the weather application.
- `ai-tool-assistant/`: deployable Firebase project for autonomous tool selection.
- `langchain-tool-assistant/`: independent LangChain extension (Project 3).
- `docs/`: bilingual architecture, development, deployment, and testing guides.
- `deploy-all.ps1`: Windows deployment helper. It runs `firebase login` first.
- `.github/workflows/tests.yml`: syntax and unit-test automation.

## Quick start

1. Install Python 3.13, Node.js, and Firebase CLI.
2. Create `functions/venv` in each project and install its requirements.
3. Run the tests.
4. Set `GROQ_API_KEY` with Firebase Secret Manager.
5. Deploy from the selected project directory.

Never commit API keys, `.secret.local`, `.env`, or virtual environments. The deployed examples are educational demos; public APIs may change, throttle, or become unavailable.

Detailed guides: [Architecture](docs/ARCHITECTURE.md), [Development](docs/DEVELOPMENT.md), [Deployment](docs/DEPLOYMENT.md), [Testing](docs/TESTING.md), [Security](SECURITY.md).

## Third project: LangChain extension

[Live LangChain demonstration](https://sam-lc-11a0f65437.web.app/) · [Source and quick start](langchain-tool-assistant/README.md)

| Project | AI behavior | Data | Deployment |
|---|---|---|---|
| LangChain Tool Assistant | ChatGroq plans 1–4 queries; a dedicated invocation summarizes verified results | Fake Store, GitHub, Wikipedia, USGS | Separate Hosting, Function and codebase |

Read the [development journey](langchain-tool-assistant/docs/DEVELOPMENT.md), [isolated deployment](langchain-tool-assistant/docs/DEPLOYMENT.md), [API contract](langchain-tool-assistant/docs/API.md), [testing](langchain-tool-assistant/docs/TESTING.md) and [outcome evidence](langchain-tool-assistant/docs/RESULTS.md). This is a reproducible reference, not an exact export of the cloud source. The root deployment helper still targets Projects 1 and 2 only; use Project 3's own helper for LangChain.

---

# Firebase＋Flask AI API 實作

[AI 即時天氣顧問](https://flaskapi-test01.web.app/) · [AI 工具助理](https://fakestoreapi-6c17e.web.app/)

本倉庫收錄三套接近正式部署型態的教學專案：Firebase Hosting 提供前端，Python Flask 執行於 Cloud Functions，先取得公開 API 的即時資料，再由 Groq 上的 LLM 產生有資料依據的繁體中文回答。

## 專案內容

| 專案 | AI 行為 | 外部資料 | Firebase 專案 |
|---|---|---|---|
| 天氣顧問 | 解讀目前天氣並提供實用建議 | wttr.in | `flaskapi-test01` |
| AI 工具助理 | 從自然語言問題自主選擇工具 | Fake Store、GitHub、Wikipedia、USGS | `fakestoreapi-6c17e` |

第二套採 Local Tool Calling：模型先選擇工具及參數，Python 驗證後執行 API，再把結果交回模型回答。使用者不用手動選擇 API，這正是本次練習的核心。

## 倉庫結構

- `weather-advisor/`：AI 即時天氣顧問完整 Firebase 專案。
- `ai-tool-assistant/`：AI 自動選工具完整 Firebase 專案。
- `langchain-tool-assistant/`：第三專案，獨立 LangChain 延伸。
- `docs/`：雙語架構、開發、部署與測試說明。
- `deploy-all.ps1`：Windows 部署腳本，第一步先執行 `firebase login`。
- `.github/workflows/tests.yml`：語法與單元測試自動化。

## 快速開始

1. 安裝 Python 3.13、Node.js 與 Firebase CLI。
2. 在每套專案建立 `functions/venv` 並安裝 requirements。
3. 執行測試。
4. 透過 Firebase Secret Manager 設定 `GROQ_API_KEY`。
5. 進入要部署的專案目錄執行部署。

禁止提交 API Key、`.secret.local`、`.env` 或虛擬環境。展示網站屬教學示範，公開 API 仍可能改版、限流或暫停服務。

詳細文件：[系統架構](docs/ARCHITECTURE.md)、[開發流程](docs/DEVELOPMENT.md)、[部署指南](docs/DEPLOYMENT.md)、[測試指南](docs/TESTING.md)、[安全政策](SECURITY.md)。

## 第三個專案：LangChain 延伸

[LangChain 成果網站](https://sam-lc-11a0f65437.web.app/) · [原始碼與快速開始](langchain-tool-assistant/README.md)

| 專案 | AI 行為 | 資料 | 部署方式 |
|---|---|---|---|
| LangChain 工具助理 | ChatGroq 規劃 1–4 項查詢，專用呼叫整理已驗證結果 | Fake Store、GitHub、Wikipedia、USGS | 獨立 Hosting、Function 與 codebase |

請閱讀[開發歷程](langchain-tool-assistant/docs/DEVELOPMENT.md)、[隔離部署](langchain-tool-assistant/docs/DEPLOYMENT.md)、[API 協定](langchain-tool-assistant/docs/API.md)、[測試](langchain-tool-assistant/docs/TESTING.md)與[成果證據](langchain-tool-assistant/docs/RESULTS.md)。本專案屬可重現參考版本，不是雲端原始碼的精確匯出。根目錄部署腳本仍僅處理第一、第二專案，LangChain 請使用第三專案自身腳本。
