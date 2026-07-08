#!/bin/bash
# Configuration Manager - Toggle long-term memory feature

echo "========================================"
echo "AI Assistant - Configuration Manager"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "[ERROR] .env file not found"
    echo "Please run install.sh first"
    exit 1
fi

echo "Current configuration:"
echo ""

# Check MEM0_API_KEY in .env
if grep -q "^MEM0_API_KEY=" .env; then
    echo "[MEMORY] Long-term memory: ENABLED (MEM0_API_KEY configured)"
    CURRENT_STATE="enabled"
elif grep -q "^# MEM0_API_KEY=" .env; then
    echo "[MEMORY] Long-term memory: DISABLED (MEM0_API_KEY commented out)"
    CURRENT_STATE="disabled"
else
    echo "[MEMORY] Long-term memory: DISABLED (no MEM0_API_KEY)"
    CURRENT_STATE="disabled"
fi
echo ""

echo "What would you like to do?"
echo ""
echo "1. Enable long-term memory"
echo "2. Disable long-term memory"
echo "3. Check status only (exit)"
echo ""
read -p "Enter choice (1-3): " CHOICE

if [ "$CHOICE" = "1" ]; then
    echo ""
    echo "[INFO] Enabling long-term memory..."
    echo ""
    echo "To enable long-term memory, you need:"
    echo "1. MEM0_API_KEY from https://app.mem0.ai/"
    echo "2. Uncomment and fill the key in .env file"
    echo ""
    echo "Opening .env file for editing..."
    ${EDITOR:-nano} .env
    echo ""
    echo "After saving:"
    echo "- Make sure MEM0_API_KEY=your_key_here is uncommented"
    echo "- Restart the application"
    echo ""
elif [ "$CHOICE" = "2" ]; then
    echo ""
    echo "[INFO] Disabling long-term memory..."
    # Comment out MEM0_API_KEY in .env
    sed -i.bak 's/^MEM0_API_KEY=/# MEM0_API_KEY=/' .env
    echo "[OK] Long-term memory disabled"
    echo "Restart the application for changes to take effect"
    echo ""
elif [ "$CHOICE" = "3" ]; then
    echo ""
    echo "[INFO] No changes made"
    echo ""
else
    echo ""
    echo "[ERROR] Invalid choice"
    echo ""
fi
