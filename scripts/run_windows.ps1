# ============================================================================
# The Soundtrack of Your Life - Windows Run Script
# ============================================================================

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "THE SOUNDTRACK OF YOUR LIFE - Launcher" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "[ERROR] Virtual environment not found. Run setup first:" -ForegroundColor Red
    Write-Host "  .\scripts\setup_windows.ps1`n" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "[1/4] Activating virtual environment..." -ForegroundColor Yellow

try {
    & .venv\Scripts\Activate.ps1
    Write-Host "  [OK] Activated`n" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Failed to activate. Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`n" -ForegroundColor Red
    exit 1
}

# Check Ollama
Write-Host "[2/4] Checking Ollama status..." -ForegroundColor Yellow

try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  [OK] Ollama is running`n" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Ollama not running" -ForegroundColor Red
    Write-Host "  Start Ollama or install from: https://ollama.com/download/windows`n" -ForegroundColor Yellow
    
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y') {
        exit 1
    }
}

# Check knowledge base
Write-Host "[3/4] Checking knowledge base..." -ForegroundColor Yellow

$appDataPath = [Environment]::GetFolderPath('LocalApplicationData')
$chromaPath = Join-Path $appDataPath "The Soundtrack of Your Life\chroma_db"

if (Test-Path $chromaPath) {
    Write-Host "  [OK] Knowledge base found`n" -ForegroundColor Green
} else {
    Write-Host "  [WARNING] Knowledge base not built" -ForegroundColor DarkYellow
    Write-Host "  Run: python scripts\build_knowledge_base.py`n" -ForegroundColor Yellow
    
    $build = Read-Host "Build now? (y/n)"
    if ($build -eq 'y') {
        Write-Host "  Building knowledge base..." -ForegroundColor Yellow
        python scripts\build_knowledge_base.py
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [ERROR] Knowledge base build failed`n" -ForegroundColor Red
            exit 1
        }
    }
}

# Run health check
Write-Host "[4/4] Running health check..." -ForegroundColor Yellow
python modules\health_check.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[WARNING] Health check found issues" -ForegroundColor DarkYellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y') {
        exit 1
    }
}

# Launch application
Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "LAUNCHING APPLICATION" -ForegroundColor Green
Write-Host "================================================================`n" -ForegroundColor Cyan

Write-Host "Starting Streamlit..." -ForegroundColor Yellow
Write-Host "The app will open in your browser automatically." -ForegroundColor DarkGray
Write-Host "Press Ctrl+C to stop the server.`n" -ForegroundColor DarkGray

streamlit run app.py
