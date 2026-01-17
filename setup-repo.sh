#!/bin/bash
#
# Clearphone Repository Setup Script
# This script creates the proper directory structure and moves files
# from the current docs directory to the new repository structure.
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Clearphone Repository Setup${NC}"
echo "================================"
echo ""

# Define paths
OLD_DIR="/Users/glw907/Desktop/clearphone-docs"
NEW_DIR="$HOME/Documents/GitHub/clearphone"

# Check if old directory exists
if [ ! -d "$OLD_DIR" ]; then
    echo "Error: Source directory $OLD_DIR not found"
    exit 1
fi

# Check if new directory already exists
if [ -d "$NEW_DIR" ]; then
    echo "Warning: $NEW_DIR already exists"
    read -p "Do you want to remove it and start fresh? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$NEW_DIR"
        echo "Removed existing directory"
    else
        echo "Aborting setup"
        exit 1
    fi
fi

# Create base directory (with parents)
echo -e "${GREEN}Creating base directory...${NC}"
mkdir -p "$NEW_DIR"
echo "Created: $NEW_DIR"

# Create Python package structure
echo -e "${GREEN}Creating Python package structure...${NC}"
mkdir -p "$NEW_DIR/clearphone/core"
mkdir -p "$NEW_DIR/clearphone/api"
mkdir -p "$NEW_DIR/tests/unit"
mkdir -p "$NEW_DIR/tests/integration"

# Create __init__.py files
echo -e "${GREEN}Creating __init__.py files...${NC}"
cat > "$NEW_DIR/clearphone/__init__.py" << 'EOF'
"""Clearphone - Configure Android phones for minimal distraction."""

__version__ = "0.1.0"
EOF

touch "$NEW_DIR/clearphone/core/__init__.py"
touch "$NEW_DIR/clearphone/api/__init__.py"

# Move existing documentation and data
echo -e "${GREEN}Moving existing files...${NC}"
mv "$OLD_DIR/device-profiles" "$NEW_DIR/"
mv "$OLD_DIR/apps" "$NEW_DIR/"
mv "$OLD_DIR/docs" "$NEW_DIR/"
mv "$OLD_DIR/README.md" "$NEW_DIR/"
mv "$OLD_DIR/CLAUDE.md" "$NEW_DIR/"
mv "$OLD_DIR/LICENSE" "$NEW_DIR/"

# Check for guides directory
if [ -d "$OLD_DIR/guides" ]; then
    mv "$OLD_DIR/guides" "$NEW_DIR/"
fi

echo ""
echo -e "${BLUE}Setup complete!${NC}"
echo ""
echo "Directory structure created at: $NEW_DIR"
echo ""
echo "Next steps:"
echo "  1. cd $NEW_DIR"
echo "  2. Review the structure"
echo "  3. Let Claude create the remaining files:"
echo "     - pyproject.toml"
echo "     - .gitignore"
echo "     - CONTRIBUTING.md"
echo "     - CODE_OF_CONDUCT.md"
echo ""
echo "After that, you'll be ready to:"
echo "  git init"
echo "  git add ."
echo "  git commit -m 'Initial commit: Project documentation and structure'"
echo ""
