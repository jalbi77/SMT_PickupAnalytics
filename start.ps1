$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) { throw 'Bitte zuerst die Installation gemäß README ausführen.' }
    & $python -m streamlit run main.py @args
    if ($LASTEXITCODE -ne 0) { throw "Streamlit beendet mit Exitcode $LASTEXITCODE" }
} finally { Pop-Location }
