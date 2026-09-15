# Firebase deployment

Prerequisites: Firebase CLI, Python 3.13, Blaze billing, access to both Firebase projects, and a valid Groq key.

## Secret setup

Run once per project. Paste the key only into the Firebase CLI prompt:

```powershell
firebase login
cd weather-advisor
firebase functions:secrets:set GROQ_API_KEY --project flaskapi-test01
cd ..\ai-tool-assistant
firebase functions:secrets:set GROQ_API_KEY --project fakestoreapi-6c17e
```

## Deployment

From the repository root:

```powershell
.\deploy-all.ps1
```

The script deliberately runs `firebase login` before preflight checks and deploys each project with an explicit project ID. Do not put the key in `.firebaserc`, source code, GitHub Actions, screenshots, or verification JSON.

After deployment, open both live URLs with a hard refresh and run the tests in [TESTING.md](TESTING.md). Container image retention is an operational cost setting; 365 days is valid but may retain storage charges longer than necessary.

## Rollback

Use Firebase Console release history to roll Hosting back. Functions require deploying a known-good Git commit. Record the commit SHA used for every classroom submission.

## Project 3 deployment scope

The commands above manage the two original sites only. Do not add LangChain to their broad deployment loop. Follow [isolated deployment](../langchain-tool-assistant/docs/DEPLOYMENT.md) for a new Hosting site, Function and codebase, explicit project selection, optional LangSmith secret and resumable snapshot. The same Firebase project still shares quotas and billing.

---

# Firebase 部署

必要條件：Firebase CLI、Python 3.13、Blaze 方案、兩個 Firebase 專案權限及有效 Groq Key。

## 設定 Secret

每個專案執行一次，金鑰只貼入 Firebase CLI 提示：

```powershell
firebase login
cd weather-advisor
firebase functions:secrets:set GROQ_API_KEY --project flaskapi-test01
cd ..\ai-tool-assistant
firebase functions:secrets:set GROQ_API_KEY --project fakestoreapi-6c17e
```

## 部署

從倉庫根目錄執行：

```powershell
.\deploy-all.ps1
```

腳本會刻意先執行 `firebase login`，才進行前置檢查，並使用明確 Project ID 逐一部署。請勿將金鑰放入 `.firebaserc`、程式碼、GitHub Actions、截圖或驗收 JSON。

部署後以強制重新整理開啟兩個正式網址，再依 [測試指南](TESTING.md) 驗收。Container image 保留 365 天是有效設定，但可能比必要期間保留更多儲存費用。

## 回復版本

Hosting 可使用 Firebase Console 的版本紀錄回復。Functions 應重新部署已知正常的 Git Commit；每次課程繳交都應記錄部署所用 Commit SHA。

## 第三專案部署範圍

上方指令只管理原有兩站，不要將 LangChain 加入原本全面部署迴圈。請依[隔離部署指南](../langchain-tool-assistant/docs/DEPLOYMENT.md)建立新 Hosting、Function 與 codebase，明確指定專案，設定選用 LangSmith Secret 並保留可續跑快照。同一 Firebase 專案仍共享帳務與額度。
