#!/bin/bash
# AI Assistant - Linux/macOS Quick Install Script

echo "========================================"
echo "AI Assistant - Quick Install"
echo "========================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python not found. Please install Python 3.10+"
    exit 1
fi

echo "[1/5] Detected Python version:"
python3 --version
echo ""

# Create virtual environment
echo "[2/5] Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        exit 1
    fi
    echo "[OK] Virtual environment created"
else
    echo "[SKIP] Virtual environment already exists"
fi
echo ""

# Activate and install dependencies
echo "[3/5] Installing dependencies..."
source .venv/bin/activate
python -m ensurepip --upgrade > /dev/null 2>&1
python -m pip install --upgrade pip > /dev/null 2>&1
python -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi
echo "[OK] Dependencies installed"
echo ""

# Copy config template
echo "[4/5] Configuration setup..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[INFO] Created .env config file"
    echo ""
    echo "[IMPORTANT] Edit .env file and fill in your API keys:"
    echo "  - DEEPSEEK_API_KEY (Required)"
    echo "  - QIANFAN_API_KEY (Required)"
    echo "  - EMBEDDING_API_KEY (Required)"
    echo "  - MEM0_API_KEY (Optional - for long-term memory)"
    echo ""
else
    echo "[OK] Config file already exists"
fi
echo ""

# Ask about long-term memory feature
echo "[5/5] Optional Feature Configuration..."
echo ""
echo "Do you want to enable long-term memory feature?"
echo "(Requires MEM0_API_KEY from https://app.mem0.ai/)"
echo ""
read -p "Enable long-term memory? (y/N): " ENABLE_MEMORY

if [[ "$ENABLE_MEMORY" =~ ^[Yy]$ ]]; then
    echo ""
    echo "[INFO] Long-term memory will be ENABLED"
    echo "Please configure MEM0_API_KEY in .env file"
    echo ""
    # Update gateway.py to enable memory
    sed -i.bak 's/use_memory=False/use_memory=True/g' gateway.py
    echo "[OK] Updated gateway.py: use_memory=True"
else
    echo ""
    echo "[INFO] Long-term memory will be DISABLED (default)"
    echo "You can enable it later by:"
    echo "  1. Configure MEM0_API_KEY in .env"
    echo "  2. Change use_memory=False to True in gateway.py"
fi
echo ""

echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env file and fill in API keys"
if [[ "$ENABLE_MEMORY" =~ ^[Yy]$ ]]; then
    echo "  2. Get MEM0_API_KEY from https://app.mem0.ai/"
    echo "  3. Run: source .venv/bin/activate"
    echo "  4. Run: python main.py"
else
    echo "  2. Run: source .venv/bin/activate"
    echo "  3. Run: python main.py"
fi
echo ""
echo "For help, see README.md or QUICKSTART.md"
echo ""
