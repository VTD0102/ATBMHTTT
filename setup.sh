#!/bin/bash
# =============================================================================
# setup.sh - Install dependencies for E-commerce Security Demo
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║     E-COMMERCE SECURITY DEMO - SETUP INSTALLER          ║"
    echo "║         Malware Protection System v1.0                   ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info()    { echo -e "${BLUE}[INFO]${NC}    $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}    $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC}   $1"; }

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script requires sudo privileges to install packages."
        echo -e "  Please run: ${YELLOW}sudo bash setup.sh${NC}"
        exit 1
    fi
}

install_package() {
    local pkg=$1
    local display=$2
    echo -ne "  Installing ${display}... "
    if dpkg -s "$pkg" &>/dev/null 2>&1; then
        echo -e "${GREEN}already installed${NC}"
    else
        apt-get install -y -qq "$pkg" &>/dev/null
        echo -e "${GREEN}done${NC}"
    fi
}

print_banner
check_root

echo -e "${BOLD}[1/4] Updating package lists...${NC}"
apt-get update -qq
log_success "Package lists updated."

echo ""
echo -e "${BOLD}[2/4] Installing security & utility tools...${NC}"
install_package "clamav"       "ClamAV (antivirus engine)"
install_package "clamav-daemon" "ClamAV daemon"
install_package "gpg"          "GPG (encryption)"
install_package "pv"           "pv (pipe viewer / progress bars)"
install_package "rsync"        "rsync (backup sync)"
install_package "tar"          "tar (archiver)"
install_package "gzip"         "gzip (compression)"
install_package "figlet"       "figlet (ASCII banners)"
install_package "lolcat"       "lolcat (colorful output)"
install_package "bc"           "bc (math calculator)"
install_package "python3"      "python3 (HTML report server)"

echo ""
echo -e "${BOLD}[3/4] Updating ClamAV virus database...${NC}"
log_warn "This may take a few minutes on first run..."
systemctl stop clamav-freshclam 2>/dev/null || true
freshclam --quiet 2>/dev/null || freshclam 2>/dev/null || log_warn "freshclam update skipped (may already be current)"
log_success "Virus database updated."

echo ""
echo -e "${BOLD}[4/4] Making scripts executable...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$SCRIPT_DIR/generate_data.sh"  2>/dev/null || true
chmod +x "$SCRIPT_DIR/secure_ecommerce.sh" 2>/dev/null || true
log_success "Scripts are ready."

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║              SETUP COMPLETE! ALL TOOLS INSTALLED         ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Next steps:"
echo -e "  ${YELLOW}1.${NC} Run:  ${CYAN}bash generate_data.sh${NC}   # Create simulated e-commerce data"
echo -e "  ${YELLOW}2.${NC} Run:  ${CYAN}bash secure_ecommerce.sh${NC} # Launch the full security demo"
echo ""
echo -e "  Options: ${CYAN}--fast${NC} (skip delays) | ${CYAN}--verbose${NC} (detailed output)"
echo ""
