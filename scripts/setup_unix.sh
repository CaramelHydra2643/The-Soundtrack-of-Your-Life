#!/bin/bash
# ============================================================================
# The Soundtrack of Your Life - Unix/Linux/macOS Setup Script
# ============================================================================

set -e

echo ""
echo "================================================================"
echo "THE SOUNDTRACK OF YOUR LIFE - Unix/Linux/macOS Setup"
echo "================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "[1/9] Checking Python installation..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "  Found: $PYTHON_VERSION"
    
    # Extract version
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
        echo -e "  ${RED}[ERROR]${NC} Python 3.11+ required. Please upgrade."
        exit 1
    fi
    
    PYTHON_CMD=python3
else
    echo -e "  ${RED}[ERROR]${NC} Python 3 not found. Install from https://www.python.org/downloads/"
    exit 1
fi

# Check Git
echo ""
echo "[2/9] Checking Git installation..."

if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    echo "  Found: $GIT_VERSION"
else
    echo -e "  ${YELLOW}[WARNING]${NC} Git not found (optional)"
fi

# Check Ollama
echo ""
echo "[3/9] Checking Ollama installation..."

if command -v ollama &> /dev/null; then
    echo "  Found: Ollama installed"
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "  [OK] Ollama is running"
        
        # Check for qwen2.5:3b
        if ollama list | grep -q "qwen2.5:3b"; then
            echo "  [OK] Model qwen2.5:3b is available"
        else
            echo -e "  ${YELLOW}[WARNING]${NC} Model qwen2.5:3b not found"
            echo "  Run: ollama pull qwen2.5:3b"
        fi
    else
        echo -e "  ${YELLOW}[WARNING]${NC} Ollama not running. Start it with: ollama serve"
    fi
else
    echo -e "  ${RED}[ERROR]${NC} Ollama not installed"
    echo "  Install:"
    echo "    Linux: curl -fsSL https://ollama.com/install.sh | sh"
    echo "    macOS: brew install ollama"
    echo "  Then run: ollama pull qwen2.5:3b"
    
    read -p "  Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
echo ""
echo "[4/9] Creating virtual environment..."

if [ -d ".venv" ]; then
    echo "  [OK] Virtual environment already exists"
else
    $PYTHON_CMD -m venv .venv
    echo "  [OK] Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "[5/9] Activating virtual environment..."
source .venv/bin/activate
echo "  [OK] Virtual environment activated"

# Upgrade pip
echo ""
echo "[6/9] Upgrading pip..."
pip install --upgrade pip --quiet
echo "  [OK] Pip upgraded"

# Install dependencies
echo ""
echo "[7/9] Installing Python dependencies..."
echo "  This may take several minutes (downloading ~500MB)..."

if pip install -r requirements.txt --quiet; then
    echo "  [OK] Dependencies installed"
else
    echo -e "  ${RED}[ERROR]${NC} Failed to install dependencies"
    echo "  Try manually: pip install -r requirements.txt"
    exit 1
fi

# Create .env file
echo ""
echo "[8/9] Creating configuration file..."

if [ -f ".env" ]; then
    echo "  [OK] .env file already exists"
else
    cp .env.example .env
    echo "  [OK] Created .env from .env.example"
    echo "  You can edit .env to customize settings"
fi

# Create required directories
echo ""
echo "[9/9] Creating application directories..."

if $PYTHON_CMD -c "from config.settings import get_settings; get_settings().ensure_directories()" 2>/dev/null; then
    echo "  [OK] Application directories created"
else
    echo -e "  ${YELLOW}[WARNING]${NC} Could not create directories (will be created at runtime)"
fi

# Summary
echo ""
echo "================================================================"
echo -e "${GREEN}SETUP COMPLETE!${NC}"
echo "================================================================"

echo ""
echo "Next steps:"
echo "  1. Build knowledge base:"
echo "     python scripts/build_knowledge_base.py"
echo ""
echo "  2. Run the application:"
echo "     ./scripts/run_unix.sh"
echo "     OR"
echo "     streamlit run app.py"
echo ""
echo "  3. Run health check (optional):"
echo "     python modules/health_check.py"
echo ""
echo "================================================================"
echo ""
