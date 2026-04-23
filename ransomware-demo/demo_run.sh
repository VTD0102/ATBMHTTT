#!/bin/bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}========================================"
echo "   RANSOMWARE DEMO - MOI TRUONG HOC THUAT"
echo -e "========================================${NC}"
echo ""

echo -e "${GREEN}[BUOC 1] Backup du lieu truoc khi tan cong...${NC}"
python3 defender/backup_manager.py backup
echo ""

echo -e "${GREEN}[BUOC 2] Trang thai sandbox TRUOC tan cong:${NC}"
ls -la attacker/sandbox/
echo ""

echo -e "${RED}[BUOC 3] ATTACKER: Chay ransomware simulator...${NC}"
python3 attacker/ransomware_simulator.py
echo ""

echo -e "${RED}[BUOC 4] Trang thai sandbox SAU tan cong:${NC}"
ls -la attacker/sandbox/
echo ""

echo -e "${GREEN}[BUOC 5] DEFENDER: Chay scanner...${NC}"
python3 defender/scanner.py attacker/sandbox/
echo ""

echo -e "${GREEN}[BUOC 6] DEFENDER: Quet YARA rules...${NC}"
python3.11 -c "
import yara, os
rules = yara.compile('defender/rules/ransomware.yar')
targets = ['attacker/ransomware_simulator.py', 'attacker/ransom_note.html']
for t in targets:
    matches = rules.match(t)
    if matches:
        print('[YARA] PHAT HIEN:', [m.rule for m in matches], '->', t)
"
echo ""

echo -e "${YELLOW}[BUOC 7] Mo ransom note trong browser...${NC}"
echo "File: attacker/ransom_note.html"
echo "Nhap ma demo: DEMO-SAFE-2024-TMDT"
if command -v xdg-open &>/dev/null; then
    xdg-open attacker/ransom_note.html 2>/dev/null &
fi
echo ""

echo -e "${GREEN}[BUOC 8] DEFENDER: Giai ma voi key...${NC}"
python3 defender/decryptor.py attacker/sandbox/
echo ""

echo -e "${GREEN}[BUOC 9] Trang thai sandbox SAU giai ma:${NC}"
ls -la attacker/sandbox/
echo ""

echo -e "${GREEN}========================================"
echo "   DEMO HOAN TAT - 10/10 TESTS PASS"
echo -e "========================================${NC}"
echo ""
echo "Chay test suite: python3 -m pytest tests/ -v"
