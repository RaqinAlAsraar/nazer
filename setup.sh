#!/bin/bash

# Nazer Global Installer Script
# Developer: @RaqinAlAsraar

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

INSTALL_DIR="$HOME/.nazer"
VENV_DIR="$INSTALL_DIR/venv"
BIN_DIR="/usr/local/bin"

echo -e "${CYAN}[*] Starting Nazer Installation...${NC}"

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[-] Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}[+] Python 3 detected.${NC}"

# 2. Check for python3-venv (Required on Debian/Kali/Ubuntu for virtual environments)
if ! python3 -m venv --help &> /dev/null; then
    echo -e "${RED}[-] python3-venv is missing. Installing it now (requires sudo)...${NC}"
    sudo apt-get update && sudo apt-get install -y python3-venv
fi
echo -e "${GREEN}[+] Python virtual environment support detected.${NC}"

# 3. Check if nazer.py exists in the current directory
if [ ! -f "nazer.py" ]; then
    echo -e "${RED}[-] nazer.py not found in the current directory!${NC}"
    echo -e "Please run this script from the folder containing nazer.py."
    exit 1
fi

# 4. Create isolated installation directory
echo -e "${CYAN}[*] Setting up isolated environment in $INSTALL_DIR...${NC}"
mkdir -p "$INSTALL_DIR"
cp nazer.py "$INSTALL_DIR/nazer.py"

# 5. Create Virtual Environment and install dependencies
echo -e "${CYAN}[*] Installing dependencies (mitmproxy, rich) in backend...${NC}"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install mitmproxy rich --quiet
echo -e "${GREEN}[+] Dependencies installed successfully.${NC}"

# 6. Create the global executable wrapper
echo -e "${CYAN}[*] Creating global 'nazer' command...${NC}"
WRAPPER_SCRIPT="/tmp/nazer"
cat << 'EOF' > "$WRAPPER_SCRIPT"
#!/bin/bash
# Nazer Wrapper Script
NAZER_DIR="$HOME/.nazer"
"$NAZER_DIR/venv/bin/python" "$NAZER_DIR/nazer.py" "$@"
EOF

chmod +x "$WRAPPER_SCRIPT"

# 7. Move to a global PATH directory
if [ -w "$BIN_DIR" ]; then
    mv "$WRAPPER_SCRIPT" "$BIN_DIR/nazer"
else
    echo -e "${CYAN}[*] Requesting sudo privileges to link command globally to $BIN_DIR...${NC}"
    sudo mv "$WRAPPER_SCRIPT" "$BIN_DIR/nazer"
fi

echo -e "\n${GREEN}==========================================${NC}"
echo -e "${GREEN}[✔] Setup Complete!${NC}"
echo -e "${CYAN}You can now run Nazer from any directory by typing:${NC}"
echo -e "    ${GREEN}nazer${NC}"
echo -e "    ${GREEN}nazer -d example.com${NC}"
echo -e "${GREEN}==========================================${NC}\n"
