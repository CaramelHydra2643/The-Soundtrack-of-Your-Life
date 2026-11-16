# ============================================================================
# The Soundtrack of Your Life - Windows Setup Script
# ============================================================================

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "THE SOUNDTRACK OF YOUR LIFE - Windows Setup" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

# Check Python version
Write-Host "[1/9] Checking Python installation..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Found: $pythonVersion" -ForegroundColor Green
    
    # Extract version number
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Host "  [ERROR] Python 3.11+ required. Please upgrade from https://www.python.org/downloads/" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "  [ERROR] Python not found. Install from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Check Git
Write-Host "`n[2/9] Checking Git installation..." -ForegroundColor Yellow

try {
    $gitVersion = git --version 2>&1
    Write-Host "  Found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "  [WARNING] Git not found (optional for cloning). Download from https://git-scm.com/" -ForegroundColor DarkYellow
}

# Check Ollama
Write-Host "`n[3/9] Checking Ollama installation..." -ForegroundColor Yellow

try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction Stop
    $modelCount = $ollamaCheck.models.Count
    Write-Host "  [OK] Ollama is running with $modelCount model(s)" -ForegroundColor Green
    
    # Check for qwen2.5:3b
    $hasQwen = $ollamaCheck.models | Where-Object { $_.name -eq "qwen2.5:3b" }
    
    if ($hasQwen) {
        Write-Host "  [OK] Model qwen2.5:3b is available" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] Model qwen2.5:3b not found" -ForegroundColor DarkYellow
        Write-Host "  Run: ollama pull qwen2.5:3b" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "  [ERROR] Ollama not running or not installed" -ForegroundColor Red
    Write-Host "  Install from: https://ollama.com/download/windows" -ForegroundColor Yellow
    Write-Host "  After installation, run: ollama pull qwen2.5:3b" -ForegroundColor Yellow
    
    $continue = Read-Host "  Continue setup anyway? (y/n)"
    if ($continue -ne 'y') {
        exit 1
    }
}

# Create virtual environment
Write-Host "`n[4/9] Creating virtual environment..." -ForegroundColor Yellow

if (Test-Path ".venv") {
    Write-Host "  [OK] Virtual environment already exists" -ForegroundColor Green
} else {
    try {
        python -m venv .venv
        Write-Host "  [OK] Virtual environment created" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "`n[5/9] Activating virtual environment..." -ForegroundColor Yellow

try {
    & .venv\Scripts\Activate.ps1
    Write-Host "  [OK] Virtual environment activated" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "  You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}

# Upgrade pip
Write-Host "`n[6/9] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "  [OK] Pip upgraded" -ForegroundColor Green

# Install dependencies
Write-Host "`n[7/9] Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "  This may take several minutes (downloading ~500MB)..." -ForegroundColor DarkYellow

try {
    pip install -r requirements.txt --quiet
    Write-Host "  [OK] Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Failed to install dependencies" -ForegroundColor Red
    Write-Host "  Try manually: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Create .env file
Write-Host "`n[8/9] Creating configuration file..." -ForegroundColor Yellow

if (Test-Path ".env") {
    Write-Host "  [OK] .env file already exists" -ForegroundColor Green
} else {
    try {
        Copy-Item ".env.example" ".env"
        Write-Host "  [OK] Created .env from .env.example" -ForegroundColor Green
        Write-Host "  You can edit .env to customize settings" -ForegroundColor DarkYellow
    } catch {
        Write-Host "  [ERROR] Failed to create .env file" -ForegroundColor Red
    }
}

# Create required directories
Write-Host "`n[9/9] Creating application directories..." -ForegroundColor Yellow

try {
    python -c "from config.settings import get_settings; get_settings().ensure_directories()"
    Write-Host "  [OK] Application directories created" -ForegroundColor Green
} catch {
    Write-Host "  [WARNING] Could not create directories (will be created at runtime)" -ForegroundColor DarkYellow
}

# Summary
Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Build knowledge base:" -ForegroundColor White
Write-Host "     python scripts\build_knowledge_base.py" -ForegroundColor Gray
Write-Host "`n  2. Run the application:" -ForegroundColor White
Write-Host "     .\scripts\run_windows.ps1" -ForegroundColor Gray
Write-Host "     OR" -ForegroundColor DarkGray
Write-Host "     streamlit run app.py" -ForegroundColor Gray

Write-Host "`n  3. Run health check (optional):" -ForegroundColor White
Write-Host "     python modules\health_check.py" -ForegroundColor Gray

Write-Host "`n================================================================`n" -ForegroundColor Cyan
