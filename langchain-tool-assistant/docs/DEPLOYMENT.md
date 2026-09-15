# Isolated Firebase deployment

The published example uses Firebase project `fakestoreapi-6c17e`, Hosting site `sam-lc-11a0f65437`, Function `api_lc_11a0f65437`, codebase `lc-11a0f65437`, and region `asia-east1`. The original site and `api` Function remain separate. This separates deployment targets, not billing, quotas or project-wide secrets.

## Reproduce in your own project

Prerequisites: a Firebase project with Blaze billing, deployment permissions, an existing reachable Hosting homepage for before/after comparison, Node.js/Firebase CLI and Python 3.13. Complete local tests first. The helper is intended to extend an existing site; it stops if the baseline homepage cannot be fetched. A brand-new Firebase project needs its own baseline site before this migration workflow.

From `langchain-tool-assistant`, replace the example project ID and baseline URL with yours:

```powershell
firebase login
firebase functions:secrets:set GROQ_API_KEY --project YOUR_PROJECT_ID
firebase functions:secrets:set LANGSMITH_API_KEY --project YOUR_PROJECT_ID
.\functions\venv\Scripts\python.exe deploy_isolated.py --project YOUR_PROJECT_ID --original-url https://YOUR_EXISTING_SITE.web.app --langsmith --prepare-only
.\functions\venv\Scripts\python.exe deploy_isolated.py --project YOUR_PROJECT_ID --original-url https://YOUR_EXISTING_SITE.web.app --langsmith
```

Omit the LangSmith secret command and `--langsmith` on both invocations if tracing is not needed. Supply key values only in hidden Firebase prompts. The helper also performs `firebase login` before Firebase operations. It freezes the source venv into a clean sibling deployment snapshot, creates a new venv, checks dependencies and imports the generated Function.

The generated `firebase.json` contains one uniquely named codebase and the Hosting target `langchain`; `.firebaserc` maps that target to a newly created site. The generated entry exports only `api_lc_<random token>`, has a 45-second request timeout and 512 MB memory, and binds required secrets. Hosting rewrites `/api/**` to that Function in `asia-east1`.

Actual writes are scoped to `firebase deploy --only functions:lc-<token>` and `firebase deploy --only hosting:langchain`, with an explicit project and generated config. Never replace those scopes with an unqualified deploy, `--force`, or a deletion command. Do not reuse someone else's state file.

## Resume and verify

Keep `deployment-state.json` beside the script and the sibling snapshot intact. Rerun the identical command to resume. This reuses the same generated resources and snapshot; editing the source directory does not refresh an existing snapshot. For later updates, review and maintain the known snapshot/config deliberately, or start a separately named new deployment from a clean script directory. Never delete state merely to fix a missing Secret.

After deployment the helper checks the new homepage and health identity, compares existing Function metadata and original homepage bytes, and runs a real single-tool and two-tool query. These last checks consume Groq quota. The local `DEPLOY-RESULT.json` includes results and answers; review before sharing. Metadata/homepage comparison is a bounded check, not proof that every old resource byte is unchanged. Manual factual, visual and LangSmith trace checks remain required.

## Known failures

- `functions:secrets:get` process exit `3221226505`: encountered on the maintainer's Windows machine; root cause was not established. The helper omits this redundant metadata call and still relies on actual Firebase deployment secret validation.
- Secret `LANGSMITH_API_KEY/versions/latest` HTTP 404: create a usable LangSmith secret in the same selected project, then resume. Local environment keys are not automatically cloud secrets. Do not paste a Groq key into the LangSmith prompt.
- Changing tracing options after creation is rejected. Decide tracing before starting; a pending, pre-creation snapshot can be upgraded by the helper, but an established deployment requires deliberate configuration review.
- Hosting alone succeeding does not prove the Function or AI works. Preserve failures and inspect the report.

Rollback only the new site's Hosting release or redeploy a reviewed known-good new Function snapshot. Never delete or roll back the original site as part of this workflow.

Official references: [multiple sites](https://firebase.google.com/docs/hosting/multisites), [codebases](https://firebase.google.com/docs/functions/organize-functions), [secrets](https://firebase.google.com/docs/functions/config-env), [Hosting rewrites](https://firebase.google.com/docs/hosting/functions).

---

# Firebase 隔離部署

展示版本使用 Firebase 專案 `fakestoreapi-6c17e`、Hosting `sam-lc-11a0f65437`、Function `api_lc_11a0f65437`、codebase `lc-11a0f65437`、區域 `asia-east1`。原站及 `api` Function 分開保留。這是部署目標隔離，帳務、額度與專案層級 Secret 仍共享。

## 在自己的專案重現

需要啟用 Blaze 的 Firebase 專案、部署權限、可連線的既有 Hosting 首頁作前後比對、Node.js／Firebase CLI 及 Python 3.13。先完成本機測試。腳本用於延伸既有網站，基準首頁無法讀取時會停止；全新 Firebase 專案應先建立自己的基準網站，才使用此遷移流程。

在 `langchain-tool-assistant` 目錄執行，將範例 Project ID 與基準網址換成自己的：

```powershell
firebase login
firebase functions:secrets:set GROQ_API_KEY --project YOUR_PROJECT_ID
firebase functions:secrets:set LANGSMITH_API_KEY --project YOUR_PROJECT_ID
.\functions\venv\Scripts\python.exe deploy_isolated.py --project YOUR_PROJECT_ID --original-url https://YOUR_EXISTING_SITE.web.app --langsmith --prepare-only
.\functions\venv\Scripts\python.exe deploy_isolated.py --project YOUR_PROJECT_ID --original-url https://YOUR_EXISTING_SITE.web.app --langsmith
```

不需要追蹤時，省略 LangSmith Secret 指令，以及兩次呼叫的 `--langsmith`。Key 只輸入 Firebase 的隱藏提示。腳本也會在 Firebase 操作前執行 `firebase login`。它會固定來源 venv 的套件版本，建立乾淨的相鄰部署副本、新 venv，檢查依賴並載入產生的 Function。

產生的 `firebase.json` 只有一個獨立 codebase 與 `langchain` Hosting target；`.firebaserc` 將該 target 對應至新建網站。入口只匯出 `api_lc_<隨機代碼>`，請求限制 45 秒、記憶體 512 MB，並綁定所需 Secret。Hosting 將 `/api/**` 導向 `asia-east1` 的新 Function。

實際写入限於 `firebase deploy --only functions:lc-<代碼>` 與 `firebase deploy --only hosting:langchain`，明確指定專案與產生的設定檔。不要改成未限定範圍的 deploy、`--force` 或刪除指令，也不要沿用他人的狀態檔。

## 續跑與驗收

保留腳本旁的 `deployment-state.json` 與相鄰部署副本，使用相同指令續跑。續跑會使用相同資源與快照；修改來源目錄不會自動更新已存在的部署副本。後續更新應明確維護已知快照與設定，或從乾淨腳本目錄建立另一個獨立部署。不要為了修復缺少 Secret 而刪除狀態檔。

部署後會檢查新站首頁與健康識別，比對既有 Function 中繼資料及原站首頁內容，再執行真實單工具與双工具查詢，最後兩項會消耗 Groq 額度。本機 `DEPLOY-RESULT.json` 含驗收結果與回答，分享前請檢查。中繼資料／首頁比對只涵蓋有限範圍，不代表所有舊資源逐位元完全不變；內容正確性、視覺及 LangSmith 追蹤仍須人工驗收。

## 已知部署問題

- Windows 曾發生 `functions:secrets:get` 結束碼 `3221226505`，根因未確認。腳本省略這項重複的中繼資料呼叫，仍由正式 Firebase deploy 驗證 Secret。
- `LANGSMITH_API_KEY/versions/latest` HTTP 404：在相同指定專案建立可用 LangSmith Secret，再續跑。本機 Key 不會自動成為雲端 Secret，也不能把 Groq Key 填入 LangSmith 提示。
- 建立資源後變更追蹤選項會被拒絕，應事先決定。尚未建立資源的副本可由腳本升級追蹤；已建立的部署必須另行審閱設定。
- Hosting 成功不等於 Function 與 AI 成功，必須保留錯誤並檢查報告。

回復版本時，只回復新站的 Hosting release 或重新部署已審閱的新 Function 正常快照，不刪除或回復原站。

官方參考：[多網站](https://firebase.google.com/docs/hosting/multisites)、[codebase](https://firebase.google.com/docs/functions/organize-functions)、[Secret](https://firebase.google.com/docs/functions/config-env)、[Hosting rewrite](https://firebase.google.com/docs/hosting/functions)。
