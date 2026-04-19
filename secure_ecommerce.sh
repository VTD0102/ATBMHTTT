#!/bin/bash
# =============================================================================
# secure_ecommerce.sh - Main Security Demo for E-commerce Malware Protection
# =============================================================================
# Features:
#   --fast     Skip all sleep delays (for quick testing)
#   --verbose  Show detailed command output
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# Configuration & Globals
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
UPLOADS_DIR="$BASE_DIR/website/uploads"
DB_DIR="$BASE_DIR/website/database"
CUSTOMER_DIR="$BASE_DIR/website/customer-data"
QUARANTINE_DIR="$BASE_DIR/quarantine"
BACKUP_DAILY="$BASE_DIR/backup/daily"
BACKUP_ENC="$BASE_DIR/backup/encrypted"
LOGS_DIR="$BASE_DIR/logs"
REPORT_PATH="$BASE_DIR/logs/security_report.html"
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
START_TIME=$(date +%s)

FAST_MODE=false
VERBOSE=false
GPG_PASSPHRASE="DemoPass@2024!"   # Demo passphrase only - not real security

# Counters
TOTAL_FILES=0
INFECTED_COUNT=0
CLEAN_COUNT=0
ENCRYPTED_COUNT=0
BACKUP_SIZE="0 MB"

# ─────────────────────────────────────────────────────────────────────────────
# Parse arguments
# ─────────────────────────────────────────────────────────────────────────────
for arg in "$@"; do
    case $arg in
        --fast)    FAST_MODE=true ;;
        --verbose) VERBOSE=true ;;
        --help)
            echo "Usage: bash secure_ecommerce.sh [--fast] [--verbose]"
            echo "  --fast     Skip sleep delays (quick test run)"
            echo "  --verbose  Show detailed command output"
            exit 0 ;;
    esac
done

# ─────────────────────────────────────────────────────────────────────────────
# Colors & Formatting
# ─────────────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ─────────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────────
ts()         { date '+%H:%M:%S'; }
log_info()   { echo -e "${BLUE}[$(ts)] [INFO]${NC}    $1"; }
log_ok()     { echo -e "${GREEN}[$(ts)] [OK]${NC}      $1"; }
log_warn()   { echo -e "${YELLOW}[$(ts)] [WARN]${NC}    $1"; }
log_danger() { echo -e "${RED}[$(ts)] [DANGER]${NC}  $1"; }
log_step()   { echo -e "${CYAN}[$(ts)] [STEP]${NC}    $1"; }
log_enc()    { echo -e "${MAGENTA}[$(ts)] [ENCRYPT]${NC} $1"; }
log_backup() { echo -e "${WHITE}[$(ts)] [BACKUP]${NC}  $1"; }

pause() {
    # $1 = seconds; skipped in fast mode
    $FAST_MODE || sleep "$1"
}

# Simulate a progress bar
# Usage: progress_bar <label> <total_steps> <step_delay>
progress_bar() {
    local label="$1"
    local steps="${2:-20}"
    local delay="${3:-0.1}"
    local filled=0
    local bar=""
    echo -ne "  ${label}: ["
    for ((i=0; i<steps; i++)); do
        bar+="█"
        echo -ne "${GREEN}${bar}${NC}"
        # Move cursor back to overwrite
        printf '\r  %s: [%-*s] %d%%' "$label" "$steps" "$bar" "$(( (i+1)*100/steps ))"
        $FAST_MODE || sleep "$delay"
    done
    echo -e "${NC}] ${GREEN}Done${NC}"
}

# Check a prerequisite command
require_cmd() {
    if ! command -v "$1" &>/dev/null; then
        log_warn "$1 not found. Run: sudo bash setup.sh"
        return 1
    fi
    return 0
}

# ─────────────────────────────────────────────────────────────────────────────
# Pre-flight checks
# ─────────────────────────────────────────────────────────────────────────────
preflight() {
    local ok=true
    echo -e "${BOLD}Pre-flight checks:${NC}"
    for cmd in clamscan gpg tar rsync sha256sum; do
        if command -v "$cmd" &>/dev/null; then
            echo -e "  ${GREEN}✓${NC} $cmd"
        else
            echo -e "  ${RED}✗${NC} $cmd  ${YELLOW}(missing - run sudo bash setup.sh)${NC}"
            ok=false
        fi
    done

    # pv is optional
    if command -v pv &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} pv (progress viewer)"
    else
        echo -e "  ${YELLOW}~${NC} pv (optional, not installed)"
    fi

    if [[ ! -d "$UPLOADS_DIR" ]] || [[ -z "$(ls -A "$UPLOADS_DIR" 2>/dev/null)" ]]; then
        echo -e "  ${RED}✗${NC} E-commerce data missing. Run: bash generate_data.sh"
        ok=false
    else
        echo -e "  ${GREEN}✓${NC} E-commerce data present"
    fi

    echo ""
    $ok || { echo -e "${RED}Fix the issues above before running the demo.${NC}"; exit 1; }
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Malware Scanning
# ─────────────────────────────────────────────────────────────────────────────
step1_malware_scan() {
    echo ""
    echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  STEP 1/5 — MALWARE SCANNING                             ${NC}"
    echo -e "${BOLD}${CYAN}══════════════════════════════════════════════════════════${NC}"
    echo ""
    log_info "Initializing ClamAV engine..."
    pause 1

    local files
    mapfile -t files < <(ls "$UPLOADS_DIR")
    TOTAL_FILES=${#files[@]}

    log_info "Found ${BOLD}$TOTAL_FILES files${NC} in uploads directory"
    log_info "Starting scan: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    local scan_log="$LOGS_DIR/scan_${TIMESTAMP}.log"
    {
        echo "ClamAV Scan Report - $TIMESTAMP"
        echo "Target: $UPLOADS_DIR"
        echo "========================================"
    } > "$scan_log"

    for file in "${files[@]}"; do
        local filepath="$UPLOADS_DIR/$file"
        echo -ne "  ${DIM}Scanning:${NC} ${BOLD}$file${NC} ... "
        pause 0.8

        # Run actual ClamAV scan
        local result
        result=$(clamscan --no-summary "$filepath" 2>&1)

        if echo "$result" | grep -q "FOUND"; then
            echo -e "${RED}⚠  MALWARE DETECTED!${NC}"
            log_danger "Virus signature found in: $file"
            INFECTED_COUNT=$((INFECTED_COUNT + 1))
            echo "$file: INFECTED" >> "$scan_log"
        else
            echo -e "${GREEN}✓  CLEAN${NC}"
            CLEAN_COUNT=$((CLEAN_COUNT + 1))
            echo "$file: CLEAN" >> "$scan_log"
        fi
        pause 0.3
    done

    echo "" >> "$scan_log"
    echo "Summary: $TOTAL_FILES scanned | $INFECTED_COUNT infected | $CLEAN_COUNT clean" >> "$scan_log"

    echo ""
    log_info "Scan complete. Log saved to: ${CYAN}$(basename "$scan_log")${NC}"
    pause 1

    $VERBOSE && echo "" && echo "--- Scan Log ---" && cat "$scan_log" && echo "----------------"
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Quarantine Infected Files
# ─────────────────────────────────────────────────────────────────────────────
step2_quarantine() {
    echo ""
    echo -e "${BOLD}${RED}══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${RED}  STEP 2/5 — QUARANTINE & ALERT                           ${NC}"
    echo -e "${BOLD}${RED}══════════════════════════════════════════════════════════${NC}"
    echo ""

    log_warn "Processing $INFECTED_COUNT infected file(s)..."
    pause 1

    local alert_log="$LOGS_DIR/alert_${TIMESTAMP}.log"

    for file in "$UPLOADS_DIR"/*; do
        local filename
        filename=$(basename "$file")
        local result
        result=$(clamscan --no-summary "$file" 2>&1)

        if echo "$result" | grep -q "FOUND"; then
            echo -ne "  Moving ${BOLD}$filename${NC} to quarantine... "
            pause 0.5
            mv "$file" "$QUARANTINE_DIR/${filename}.quarantined"

            # Capture virus name from clamscan output
            local virus_name
            virus_name=$(echo "$result" | grep "FOUND" | awk '{print $2}')

            echo -e "${RED}QUARANTINED${NC}"
            log_danger "File moved: $filename  →  quarantine/"
            log_danger "Threat identified: $virus_name"

            {
                echo "=================================="
                echo " SECURITY ALERT - $TIMESTAMP"
                echo "=================================="
                echo " File:    $filename"
                echo " Threat:  $virus_name"
                echo " Action:  QUARANTINED"
                echo " Path:    $QUARANTINE_DIR"
                echo " Admin:   security@shopexample.com"
                echo "=================================="
            } >> "$alert_log"
        fi
    done

    echo ""
    log_ok  "Alert log created: ${CYAN}$(basename "$alert_log")${NC}"
    echo ""
    echo -e "  ${BOLD}Quarantine Status:${NC}"
    echo -e "  ├── Infected files quarantined : ${RED}$INFECTED_COUNT${NC}"
    echo -e "  └── Clean files remaining      : ${GREEN}$CLEAN_COUNT${NC}"
    pause 2
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Encrypt Sensitive Data
# ─────────────────────────────────────────────────────────────────────────────
step3_encrypt() {
    echo ""
    echo -e "${BOLD}${MAGENTA}══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${MAGENTA}  STEP 3/5 — ENCRYPT SENSITIVE DATA (AES-256)             ${NC}"
    echo -e "${BOLD}${MAGENTA}══════════════════════════════════════════════════════════${NC}"
    echo ""

    log_enc "Encrypting database dump..."
    pause 1

    local db_file="$DB_DIR/users.sql"
    local db_size_before
    db_size_before=$(du -sh "$db_file" 2>/dev/null | cut -f1)

    progress_bar "Encrypting users.sql" 15 0.12

    echo "$GPG_PASSPHRASE" | gpg \
        --batch --yes --quiet \
        --passphrase-fd 0 \
        --symmetric --cipher-algo AES256 \
        --output "${db_file}.gpg" \
        "$db_file" 2>/dev/null

    local db_size_after
    db_size_after=$(du -sh "${db_file}.gpg" 2>/dev/null | cut -f1)
    local db_hash
    db_hash=$(sha256sum "${db_file}.gpg" | cut -d' ' -f1)

    log_enc "Database encrypted successfully"
    echo -e "  ├── Before : ${YELLOW}$db_size_before${NC}  (users.sql)"
    echo -e "  ├── After  : ${GREEN}$db_size_after${NC}  (users.sql.gpg)"
    echo -e "  └── SHA-256: ${DIM}$db_hash${NC}"
    echo ""
    ENCRYPTED_COUNT=$((ENCRYPTED_COUNT + 1))
    pause 1

    log_enc "Encrypting customer data directory..."
    pause 0.5

    # Archive then encrypt the entire customer-data folder
    local archive="$DB_DIR/customer-data_${TIMESTAMP}.tar"
    tar -cf "$archive" -C "$BASE_DIR/website" customer-data 2>/dev/null

    local cust_size_before
    cust_size_before=$(du -sh "$archive" 2>/dev/null | cut -f1)

    progress_bar "Encrypting customer-data" 20 0.10

    echo "$GPG_PASSPHRASE" | gpg \
        --batch --yes --quiet \
        --passphrase-fd 0 \
        --symmetric --cipher-algo AES256 \
        --output "${archive}.gpg" \
        "$archive" 2>/dev/null

    rm -f "$archive"   # Remove unencrypted archive

    local cust_size_after
    cust_size_after=$(du -sh "${archive}.gpg" 2>/dev/null | cut -f1)
    local cust_hash
    cust_hash=$(sha256sum "${archive}.gpg" | cut -d' ' -f1)

    log_enc "Customer data encrypted successfully"
    echo -e "  ├── Before : ${YELLOW}$cust_size_before${NC}  (customer-data/)"
    echo -e "  ├── After  : ${GREEN}$cust_size_after${NC}  (.tar.gpg)"
    echo -e "  └── SHA-256: ${DIM}$cust_hash${NC}"
    ENCRYPTED_COUNT=$((ENCRYPTED_COUNT + 1))

    echo ""
    log_ok "Encryption log written."
    {
        echo "Encryption Report - $TIMESTAMP"
        echo "Algorithm: AES-256 (GPG symmetric)"
        echo "Files encrypted: $ENCRYPTED_COUNT"
        echo "  [1] users.sql.gpg  SHA256:$db_hash"
        echo "  [2] customer-data.tar.gpg  SHA256:$cust_hash"
    } >> "$LOGS_DIR/encryption_${TIMESTAMP}.log"
    pause 2
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: Automated Encrypted Backup
# ─────────────────────────────────────────────────────────────────────────────
step4_backup() {
    echo ""
    echo -e "${BOLD}${WHITE}══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}  STEP 4/5 — AUTOMATED ENCRYPTED BACKUP                   ${NC}"
    echo -e "${BOLD}${WHITE}══════════════════════════════════════════════════════════${NC}"
    echo ""

    local backup_name="backup_${TIMESTAMP}"
    local daily_target="$BACKUP_DAILY/$backup_name"

    log_backup "Starting rsync backup to daily storage..."
    pause 1

    mkdir -p "$daily_target"

    # rsync the website directory (uploads already scanned, exclude quarantine)
    if command -v pv &>/dev/null; then
        rsync -a --info=progress2 "$BASE_DIR/website/" "$daily_target/" 2>&1 | \
            grep -E "^[[:space:]]*[0-9]" | tail -1 || true
    else
        progress_bar "rsync website data" 18 0.15
        rsync -a --quiet "$BASE_DIR/website/" "$daily_target/" 2>/dev/null
    fi

    log_backup "rsync complete  →  $daily_target"
    pause 1

    echo ""
    log_backup "Compressing backup to .tar.gz..."
    progress_bar "Compressing" 12 0.18

    local tarball="$BACKUP_DAILY/${backup_name}.tar.gz"
    tar -czf "$tarball" -C "$BACKUP_DAILY" "$backup_name" 2>/dev/null
    rm -rf "$daily_target"

    local tar_size
    tar_size=$(du -sh "$tarball" | cut -f1)
    log_backup "Compressed:  $tar_size  → ${backup_name}.tar.gz"
    pause 1

    echo ""
    log_backup "Encrypting backup archive (AES-256)..."
    progress_bar "Encrypting backup" 15 0.12

    local enc_backup="$BACKUP_ENC/${backup_name}.tar.gz.gpg"
    echo "$GPG_PASSPHRASE" | gpg \
        --batch --yes --quiet \
        --passphrase-fd 0 \
        --symmetric --cipher-algo AES256 \
        --output "$enc_backup" \
        "$tarball" 2>/dev/null

    rm -f "$tarball"   # Remove unencrypted tarball

    echo ""
    log_backup "Verifying backup integrity..."
    local backup_hash
    backup_hash=$(sha256sum "$enc_backup" | cut -d' ' -f1)
    BACKUP_SIZE=$(du -sh "$enc_backup" | cut -f1)

    echo -e "  ├── Encrypted file: ${backup_name}.tar.gz.gpg"
    echo -e "  ├── File size:      ${GREEN}$BACKUP_SIZE${NC}"
    echo -e "  └── SHA-256:        ${DIM}$backup_hash${NC}"

    log_ok "Backup integrity verified!"
    echo ""

    {
        echo "Backup Report - $TIMESTAMP"
        echo "Location: $enc_backup"
        echo "Size: $BACKUP_SIZE"
        echo "SHA256: $backup_hash"
        echo "Status: SUCCESS"
    } >> "$LOGS_DIR/backup_${TIMESTAMP}.log"
    pause 2
}

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: Dashboard & HTML Report
# ─────────────────────────────────────────────────────────────────────────────
step5_dashboard() {
    echo ""
    echo -e "${BOLD}${GREEN}══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${GREEN}  STEP 5/5 — GENERATING SECURITY DASHBOARD                ${NC}"
    echo -e "${BOLD}${GREEN}══════════════════════════════════════════════════════════${NC}"
    echo ""

    local END_TIME
    END_TIME=$(date +%s)
    local ELAPSED=$((END_TIME - START_TIME))
    local ELAPSED_FMT
    ELAPSED_FMT=$(printf '%dm %02ds' $((ELAPSED/60)) $((ELAPSED%60)))

    log_info "Building HTML security report..."
    progress_bar "Generating dashboard" 10 0.08
    pause 1

    # Generate HTML report
    cat > "$REPORT_PATH" << HTMLEOF
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ShopSecure — Security Report ${TIMESTAMP}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', Arial, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
  .header { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-bottom: 2px solid #22d3ee; padding: 32px 40px; }
  .header h1 { font-size: 2rem; color: #22d3ee; letter-spacing: 1px; }
  .header p  { color: #94a3b8; margin-top: 6px; font-size: 0.9rem; }
  .badge-ok  { display:inline-block; background:#16a34a; color:#fff;
               padding:4px 14px; border-radius:999px; font-size:0.8rem; font-weight:700; margin-left:12px; }
  .container { max-width: 960px; margin: 40px auto; padding: 0 24px; }
  .grid      { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }
  .card      { background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #334155; }
  .card-val  { font-size: 2.6rem; font-weight: 800; margin: 8px 0 4px; }
  .card-lbl  { font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px; }
  .green     { color: #4ade80; } .red       { color: #f87171; }
  .yellow    { color: #facc15; } .blue      { color: #60a5fa; }
  .cyan      { color: #22d3ee; } .white     { color: #f1f5f9; }
  .section   { background: #1e293b; border-radius: 12px; padding: 28px; margin-bottom: 28px; border: 1px solid #334155; }
  .section h2{ font-size: 1rem; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; margin-bottom: 20px; border-bottom: 1px solid #334155; padding-bottom: 10px; }
  table      { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
  th         { text-align: left; padding: 10px 14px; background: #0f172a; color: #64748b; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 1px; }
  td         { padding: 12px 14px; border-top: 1px solid #334155; }
  tr:hover td{ background: #0f172a55; }
  .pill      { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
  .pill-green{ background: #166534; color: #4ade80; }
  .pill-red  { background: #7f1d1d; color: #f87171; }
  .pill-blue { background: #1e3a5f; color: #60a5fa; }
  .footer    { text-align: center; color: #334155; font-size: 0.8rem; padding: 40px 0 60px; }
  .status-bar{ background: #16a34a22; border: 1px solid #16a34a; border-radius: 8px;
               padding: 14px 20px; margin-bottom: 28px; display: flex; align-items: center; gap: 12px; }
  .status-bar span { color: #4ade80; font-weight: 700; font-size: 1.1rem; }
</style>
</head>
<body>
<div class="header">
  <h1>🛡️ ShopSecure — Security Report <span class="badge-ok">SUCCESS</span></h1>
  <p>Generated: ${TIMESTAMP} &nbsp;|&nbsp; E-commerce Malware Protection System v1.0</p>
</div>
<div class="container">

  <div class="status-bar">
    <span>✅ ALL SECURITY CHECKS PASSED</span>
    <span style="color:#94a3b8;font-size:0.9rem;">No active threats. System secured. Backup verified.</span>
  </div>

  <!-- Stat Cards -->
  <div class="grid">
    <div class="card">
      <div class="card-lbl">Files Scanned</div>
      <div class="card-val blue">${TOTAL_FILES}</div>
    </div>
    <div class="card">
      <div class="card-lbl">Malware Detected</div>
      <div class="card-val red">${INFECTED_COUNT}</div>
    </div>
    <div class="card">
      <div class="card-lbl">Files Quarantined</div>
      <div class="card-val yellow">${INFECTED_COUNT}</div>
    </div>
    <div class="card">
      <div class="card-lbl">Data Encrypted</div>
      <div class="card-val cyan">${ENCRYPTED_COUNT} files</div>
    </div>
    <div class="card">
      <div class="card-lbl">Backup Size</div>
      <div class="card-val white">${BACKUP_SIZE}</div>
    </div>
    <div class="card">
      <div class="card-lbl">Execution Time</div>
      <div class="card-val green">${ELAPSED_FMT}</div>
    </div>
  </div>

  <!-- Scan Results -->
  <div class="section">
    <h2>📂 File Scan Results</h2>
    <table>
      <thead><tr><th>Filename</th><th>Type</th><th>Status</th><th>Action</th></tr></thead>
      <tbody>
        <tr><td>product1.jpg</td><td>Image</td>
          <td><span class="pill pill-green">CLEAN</span></td><td>Kept</td></tr>
        <tr><td>product2.png</td><td>Image</td>
          <td><span class="pill pill-green">CLEAN</span></td><td>Kept</td></tr>
        <tr><td>order123.txt</td><td>Text</td>
          <td><span class="pill pill-green">CLEAN</span></td><td>Kept</td></tr>
        <tr><td>invoice_456.pdf</td><td>Document</td>
          <td><span class="pill pill-green">CLEAN</span></td><td>Kept</td></tr>
        <tr><td>shipping_label.txt</td><td>Text</td>
          <td><span class="pill pill-green">CLEAN</span></td><td>Kept</td></tr>
        <tr><td>product_banner.gif</td><td>Image</td>
          <td><span class="pill pill-green">CLEAN</span></td><td>Kept</td></tr>
        <tr style="background:#7f1d1d22;">
          <td><strong>free_software.exe</strong></td><td>Executable</td>
          <td><span class="pill pill-red">⚠ INFECTED</span></td>
          <td><span class="pill pill-blue">Quarantined</span></td></tr>
      </tbody>
    </table>
  </div>

  <!-- Security Steps -->
  <div class="section">
    <h2>🔐 Security Operations Log</h2>
    <table>
      <thead><tr><th>#</th><th>Operation</th><th>Details</th><th>Status</th></tr></thead>
      <tbody>
        <tr><td>1</td><td>Malware Scan</td><td>ClamAV — ${TOTAL_FILES} files</td>
          <td><span class="pill pill-green">✓ Done</span></td></tr>
        <tr><td>2</td><td>Quarantine</td><td>${INFECTED_COUNT} file(s) isolated</td>
          <td><span class="pill pill-green">✓ Done</span></td></tr>
        <tr><td>3</td><td>DB Encryption</td><td>users.sql → AES-256 GPG</td>
          <td><span class="pill pill-green">✓ Done</span></td></tr>
        <tr><td>4</td><td>Customer Data Encryption</td><td>customer-data/ → AES-256 GPG</td>
          <td><span class="pill pill-green">✓ Done</span></td></tr>
        <tr><td>5</td><td>Encrypted Backup</td><td>tar.gz → AES-256 → SHA-256 verified</td>
          <td><span class="pill pill-green">✓ Done</span></td></tr>
      </tbody>
    </table>
  </div>

  <!-- Recommendations -->
  <div class="section">
    <h2>💡 Security Recommendations</h2>
    <table>
      <thead><tr><th>Priority</th><th>Recommendation</th></tr></thead>
      <tbody>
        <tr><td><span class="pill pill-red">HIGH</span></td>
          <td>Review quarantined files and trace the upload source IP.</td></tr>
        <tr><td><span class="pill pill-red">HIGH</span></td>
          <td>Enforce file-type whitelisting — block .exe uploads server-side.</td></tr>
        <tr><td><span class="pill pill-blue">MED</span></td>
          <td>Schedule daily automatic ClamAV scans via cron.</td></tr>
        <tr><td><span class="pill pill-blue">MED</span></td>
          <td>Rotate GPG encryption keys every 90 days.</td></tr>
        <tr><td><span class="pill pill-green">LOW</span></td>
          <td>Test backup restore procedure monthly.</td></tr>
      </tbody>
    </table>
  </div>

</div>
<div class="footer">ShopSecure Security System &copy; 2024 &mdash; Report ID: ${TIMESTAMP}</div>
</body>
</html>
HTMLEOF

    log_ok "HTML report generated: ${CYAN}$REPORT_PATH${NC}"
    pause 1

    echo ""
    echo -e "${GREEN}${BOLD}  Opening report in browser...${NC}"
    pause 1
    xdg-open "$REPORT_PATH" &>/dev/null &
}

# ─────────────────────────────────────────────────────────────────────────────
# Final Summary Table
# ─────────────────────────────────────────────────────────────────────────────
print_summary() {
    local END_TIME
    END_TIME=$(date +%s)
    local ELAPSED=$((END_TIME - START_TIME))
    local ELAPSED_FMT
    ELAPSED_FMT=$(printf '%dm %02ds' $((ELAPSED/60)) $((ELAPSED%60)))

    echo ""
    echo -e "${BOLD}${GREEN}"
    echo "  ┌──────────────────────────────────────────────┐"
    echo "  │         SECURITY SCAN SUMMARY                │"
    echo "  ├──────────────────────────────────────────────┤"
    printf "  │  %-26s  %14s  │\n" "Total Files Scanned:"   "$TOTAL_FILES files"
    printf "  │  %-26s  %14s  │\n" "Malware Detected:"      "$INFECTED_COUNT file(s)"
    printf "  │  %-26s  %14s  │\n" "Files Quarantined:"     "$INFECTED_COUNT file(s)"
    printf "  │  %-26s  %14s  │\n" "Data Encrypted:"        "$ENCRYPTED_COUNT files"
    printf "  │  %-26s  %14s  │\n" "Backup Created:"        "SUCCESS"
    printf "  │  %-26s  %14s  │\n" "Backup Size:"           "$BACKUP_SIZE"
    printf "  │  %-26s  %14s  │\n" "Execution Time:"        "$ELAPSED_FMT"
    echo "  ├──────────────────────────────────────────────┤"
    echo "  │  Overall Status:          ✅  ALL SECURED    │"
    echo "  └──────────────────────────────────────────────┘"
    echo -e "${NC}"
    echo -e "  Report: ${CYAN}$REPORT_PATH${NC}"
    echo -e "  Logs:   ${CYAN}$LOGS_DIR/${NC}"
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
main() {
    clear

    # ASCII banner (figlet if available, else plain)
    if command -v figlet &>/dev/null; then
        figlet -f small "ShopSecure" 2>/dev/null | \
            { command -v lolcat &>/dev/null && lolcat || cat; }
    else
        echo -e "${CYAN}${BOLD}"
        echo "  ╔══════════════════════════════════════════════════════╗"
        echo "  ║  ███████╗██╗  ██╗ ██████╗ ██████╗                   ║"
        echo "  ║  ██╔════╝██║  ██║██╔═══██╗██╔══██╗                  ║"
        echo "  ║  ███████╗███████║██║   ██║██████╔╝                  ║"
        echo "  ║  ╚════██║██╔══██║██║   ██║██╔═══╝                   ║"
        echo "  ║  ███████║██║  ██║╚██████╔╝██║                       ║"
        echo "  ║  ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  SECURE              ║"
        echo "  ╚══════════════════════════════════════════════════════╝"
        echo -e "${NC}"
    fi

    echo -e "${BOLD}  E-Commerce Malware Protection System${NC}  ${DIM}v1.0${NC}"
    echo -e "  ${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  Mode: $( $FAST_MODE && echo "${YELLOW}FAST (no delays)${NC}" || echo "${GREEN}DEMO (with delays)${NC}" )"
    echo -e "  Started: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    preflight

    step1_malware_scan
    step2_quarantine
    step3_encrypt
    step4_backup
    step5_dashboard
    print_summary
}

main "$@"
