$ErrorActionPreference = "Stop"

Write-Host "Sign in to Firebase first / 先登入 Firebase" -ForegroundColor Cyan
firebase login
if ($LASTEXITCODE -ne 0) { throw "Firebase login failed / Firebase 登入失敗" }

$projects = [ordered]@{
    "weather-advisor" = "flaskapi-test01"
    "ai-tool-assistant" = "fakestoreapi-6c17e"
}

firebase projects:list | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Project access check failed / 專案權限檢查失敗" }

foreach ($folder in $projects.Keys) {
    $path = Join-Path $PSScriptRoot $folder
    $python = Join-Path $path "functions\venv\Scripts\python.exe"
    if (!(Test-Path $python)) { throw "Missing $python; create venv first / 請先建立 venv" }
    & $python -m pytest (Join-Path $path "functions")
    if ($LASTEXITCODE -ne 0) { throw "Tests failed: $folder / 測試失敗" }
    Push-Location $path
    try {
        firebase deploy --only "functions,hosting" --project $projects[$folder]
        if ($LASTEXITCODE -ne 0) { throw "Deployment failed: $folder / 部署失敗" }
    } finally { Pop-Location }
}
Write-Host "Both deployments completed / 兩套專案部署完成" -ForegroundColor Green
