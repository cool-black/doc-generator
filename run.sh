#!/usr/bin/env bash
# DocGen - Interactive document generation workflow
# Usage: bash run.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  DocGen - Document Generator${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Step 0: Check .env
if ! grep -q "sk-" .env 2>/dev/null && ! grep -q "sk-ant-" .env 2>/dev/null; then
    if grep -q "sk-your-api-key-here" .env 2>/dev/null; then
        echo -e "${RED}[!] Please edit .env file first and set your API key${NC}"
        echo -e "    File: ${PROJECT_DIR}/.env"
        echo ""
        exit 1
    fi
fi

echo -e "${GREEN}[✓] .env loaded${NC}"
echo ""

# Step 1: Ask for project name
read -p "Project name (e.g. agent-guide): " PROJECT_NAME
if [ -z "$PROJECT_NAME" ]; then
    echo "Project name required."
    exit 1
fi

# Check if project exists
if python -m doc_gen list 2>/dev/null | grep -q "$PROJECT_NAME"; then
    echo -e "${YELLOW}[i] Project '$PROJECT_NAME' already exists${NC}"
    echo ""
    echo "  1. Continue with existing project"
    echo "  2. Delete and recreate"
    echo "  3. Skip to export"
    read -p "Choose [1]: " CHOICE
    CHOICE=${CHOICE:-1}

    if [ "$CHOICE" = "2" ]; then
        python -m doc_gen delete "$PROJECT_NAME" <<< "y"
        echo ""
    elif [ "$CHOICE" = "3" ]; then
        echo -e "\n${GREEN}[Step 5/5] Exporting document...${NC}"
        python -m doc_gen export "$PROJECT_NAME"
        echo -e "\n${GREEN}Done!${NC}"
        exit 0
    fi
fi

# Step 2: Create project (interactive)
if ! python -m doc_gen list 2>/dev/null | grep -q "$PROJECT_NAME"; then
    echo -e "\n${GREEN}[Step 1/4] Creating project...${NC}"
    echo ""
    python -m doc_gen new "$PROJECT_NAME"
fi

# Step 3: Generate outline
echo -e "\n${GREEN}[Step 2/4] Generating outline...${NC}"
echo ""
python -m doc_gen generate "$PROJECT_NAME" --stage outline

# Step 4: Generate content
echo -e "\n${GREEN}[Step 3/4] Generating chapter content...${NC}"
echo ""
python -m doc_gen generate "$PROJECT_NAME" --stage content

# Step 5: Export
echo -e "\n${GREEN}[Step 4/4] Exporting final document...${NC}"
echo ""
python -m doc_gen export "$PROJECT_NAME"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  All done! Check the output file above.${NC}"
echo -e "${GREEN}========================================${NC}"
