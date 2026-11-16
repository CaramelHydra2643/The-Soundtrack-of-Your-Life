#!/bin/bash
# ============================================================================
# The Soundtrack of Your Life - Unix/Linux/macOS Run Script
# ============================================================================

set -e

echo ""
echo "================================================================"
echo "THE SOUNDTRACK OF YOUR LIFE - Launcher"
echo "================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}[ERROR]${NC} Virtual environment not found. Run setup first:"
    echo "  ./scripts/setup_unix.sh"
    echo ""
    exit 1
fi

# Activate virtual environment
echo "[1/4] Activating virtual environment..."
source .venv/bin/activate
echo "  [OK] Activated"
echo ""

# Check Ollama
echo "[2/4] Checking Ollama status..."

if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  [OK] Ollama is running"
    echo ""
else
    echo -e "  ${RED}[ERROR]${NC} Ollama not running"
    echo "  Start Ollama:"
    echo "    Linux: ollama serve &"
    echo "    macOS: ollama serve &"
    echo ""
    
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check knowledge base
echo "[3/4] Checking knowledge base..."

if [ -d "$HOME/.local/share/soundtrack-of-your-life/chroma_db" ] || [ -d "$HOME/Library/Application Support/The Soundtrack of Your Life/chroma_db" ]; then
    echo "  [OK] Knowledge base found"
    echo ""
else
    echo -e "  ${YELLOW}[WARNING]${NC} Knowledge base not built"
    echo "  Run: python scripts/build_knowledge_base.py"
    echo ""
    
    read -p "Build now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "  Building knowledge base..."
        python scripts/build_knowledge_base.py
        
        if [ $? -ne 0 ]; then
            echo -e "  ${RED}[ERROR]${NC} Knowledge base build failed"
            echo ""
            exit 1
        fi
    fi
fi

# Run health check
echo "[4/4] Running health check..."
python modules/health_check.py

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}[WARNING]${NC} Health check found issues"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Launch application
echo ""
echo "================================================================"
echo -e "${GREEN}LAUNCHING APPLICATION${NC}"
echo "================================================================"
echo ""

echo "Starting Streamlit..."
echo "The app will open in your browser automatically."
echo "Press Ctrl+C to stop the server."
echo ""

streamlit run app.py
