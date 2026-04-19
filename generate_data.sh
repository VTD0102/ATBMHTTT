#!/bin/bash
# =============================================================================
# generate_data.sh - Create simulated e-commerce data for the security demo
# =============================================================================

set -e

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}  [INFO]${NC}    $1"; }
log_success() { echo -e "${GREEN}  [CREATE]${NC} ✓ $1"; }

echo ""
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}║        GENERATING SIMULATED E-COMMERCE DATA              ║${NC}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# 1. Create directory structure
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}[1/5] Creating directory structure...${NC}"
rm -rf "$BASE_DIR"/{website,quarantine,backup,logs}
mkdir -p "$BASE_DIR"/{website/{uploads,database,customer-data},quarantine,backup/{daily,encrypted},logs}
log_success "Directory structure created at $BASE_DIR"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# 2. Create clean product/order files in uploads/
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}[2/5] Creating clean upload files...${NC}"

cat > "$BASE_DIR/website/uploads/product1.jpg.txt" << 'EOF'
[BINARY IMAGE DATA SIMULATED]
Product: Premium Wireless Headphones
SKU: WH-1000XM5
Price: $349.99
Stock: 128 units
Image Resolution: 1200x1200px
Format: JPEG
EOF
log_success "product1.jpg (product image)"

cat > "$BASE_DIR/website/uploads/product2.png.txt" << 'EOF'
[BINARY IMAGE DATA SIMULATED]
Product: Mechanical Gaming Keyboard
SKU: KB-RGB-TKL
Price: $129.99
Stock: 256 units
Image Resolution: 800x600px
Format: PNG
EOF
log_success "product2.png (product image)"

cat > "$BASE_DIR/website/uploads/order123.txt" << 'EOF'
ORDER CONFIRMATION
==================
Order ID:    ORD-2024-001234
Date:        2024-01-15 09:32:11
Customer:    Alice Johnson
Email:       alice@example.com

Items:
  - Wireless Headphones x1  @ $349.99
  - USB-C Cable x2          @  $12.99

Subtotal:    $375.97
Shipping:    $0.00
Tax:         $37.60
Total:       $413.57

Payment:     Visa ****4321
Status:      CONFIRMED
EOF
log_success "order123.txt (order confirmation)"

cat > "$BASE_DIR/website/uploads/invoice_456.pdf.txt" << 'EOF'
[PDF DOCUMENT SIMULATED]
INVOICE #INV-2024-000456
========================
Bill To:  Bob Smith, 123 Main St, Springfield
Date:     2024-01-16
Due:      2024-01-30

Description                    Amount
------------------------------  -------
Web Hosting (Annual)           $120.00
SSL Certificate                 $49.00
Maintenance Package            $200.00
                               -------
TOTAL DUE                      $369.00
EOF
log_success "invoice_456.pdf (invoice document)"

cat > "$BASE_DIR/website/uploads/shipping_label.txt" << 'EOF'
SHIPPING LABEL
==============
Carrier:     FedEx Priority
Tracking:    794644792798
From:        ShopSecure HQ
             456 Commerce Ave, Tech City, CA 90210
To:          Charlie Brown
             789 Oak Street, Apt 3B
             New York, NY 10001
Weight:      1.2 kg
Service:     2-Day Delivery
EOF
log_success "shipping_label.txt (shipping document)"

cat > "$BASE_DIR/website/uploads/product_banner.gif.txt" << 'EOF'
[ANIMATED GIF DATA SIMULATED]
Banner: Summer Sale 2024
Dimensions: 1920x400px
Frames: 24
Duration: 3.0 seconds
Colors: 256
File size: ~245KB
EOF
log_success "product_banner.gif (marketing banner)"

# ─────────────────────────────────────────────────────────────────────────────
# 3. Create EICAR test file (safe, standardized antivirus test)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[3/5] Creating EICAR test file (safe malware simulation)...${NC}"
# EICAR is the official, harmless antivirus test string - not actual malware
printf 'X5O!P%%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' \
    > "$BASE_DIR/website/uploads/free_software.exe"
log_success "free_software.exe → EICAR test signature (detected by ClamAV as test virus)"
echo -e "  ${YELLOW}Note: This is the official EICAR test string - completely safe${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# 4. Create mock database dump
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}[4/5] Creating mock database dump...${NC}"
cat > "$BASE_DIR/website/database/users.sql" << 'EOF'
-- ShopSecure E-commerce Database Dump
-- Generated: 2024-01-16 02:00:00 UTC
-- Version: MySQL 8.0.35

SET FOREIGN_KEY_CHECKS=0;
CREATE TABLE IF NOT EXISTS `users` (
  `id`         INT NOT NULL AUTO_INCREMENT,
  `username`   VARCHAR(50) NOT NULL,
  `email`      VARCHAR(100) NOT NULL UNIQUE,
  `password`   VARCHAR(255) NOT NULL COMMENT 'bcrypt hashed',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

INSERT INTO `users` VALUES
  (1,'alice_j','alice@example.com','$2b$12$LHsJ9QdG8kXzPj1q2ABCDE...','2023-06-01'),
  (2,'bob_s','bob@example.com','$2b$12$MKtR7WeH9lYaQk2r3FGHIJ...','2023-07-15'),
  (3,'charlie_b','charlie@example.com','$2b$12$NLuS8XfI0mZbRl3s4KLMNO...','2023-08-22'),
  (4,'diana_m','diana@example.com','$2b$12$OMvT9YgJ1nAcSm4t5PQRST...','2023-09-10'),
  (5,'evan_w','evan@example.com','$2b$12$PNwU0ZhK2oBdTn5u6UVWXY...','2023-10-05');

CREATE TABLE IF NOT EXISTS `orders` (
  `id`         INT NOT NULL AUTO_INCREMENT,
  `user_id`    INT NOT NULL,
  `total`      DECIMAL(10,2) NOT NULL,
  `status`     ENUM('pending','confirmed','shipped','delivered') DEFAULT 'pending',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

INSERT INTO `orders` VALUES
  (101,1,413.57,'delivered','2024-01-15'),
  (102,2,89.99,'shipped','2024-01-14'),
  (103,3,256.50,'confirmed','2024-01-16'),
  (104,4,47.00,'pending','2024-01-16'),
  (105,5,699.99,'confirmed','2024-01-15');

SET FOREIGN_KEY_CHECKS=1;
-- End of dump
EOF
log_success "users.sql (database dump with hashed passwords)"

# ─────────────────────────────────────────────────────────────────────────────
# 5. Create customer data CSV with fake PII (for encryption demo)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}[5/5] Creating customer data files (fake PII for demo)...${NC}"
cat > "$BASE_DIR/website/customer-data/customers.csv" << 'EOF'
id,first_name,last_name,email,phone,address,card_number,card_expiry,card_cvv,loyalty_points
1,Alice,Johnson,alice@example.com,+1-555-234-5678,"123 Maple St, Springfield, IL 62701",4111111111111111,12/26,123,1250
2,Bob,Smith,bob@example.com,+1-555-345-6789,"456 Oak Ave, Chicago, IL 60601",5500005555555559,08/27,456,340
3,Charlie,Brown,charlie@example.com,+1-555-456-7890,"789 Pine Rd, Naperville, IL 60540",4111111111111111,03/25,789,2100
4,Diana,Miller,diana@example.com,+1-555-567-8901,"321 Elm Blvd, Rockford, IL 61101",4012888888881881,11/26,321,890
5,Evan,Wilson,evan@example.com,+1-555-678-9012,"654 Birch Ln, Peoria, IL 61602",4111111111111111,07/28,654,3500
6,Fiona,Davis,fiona@example.com,+1-555-789-0123,"987 Cedar St, Aurora, IL 60505",5105105105105100,09/27,987,120
7,George,Taylor,george@example.com,+1-555-890-1234,"741 Walnut Dr, Joliet, IL 60432",4111111111111111,01/26,741,4200
EOF
log_success "customers.csv (fake customer PII + test card numbers)"

cat > "$BASE_DIR/website/customer-data/payment_tokens.json" << 'EOF'
{
  "payment_gateway": "StripeSimulator",
  "environment": "DEMO_ONLY",
  "tokens": [
    {"customer_id": 1, "token": "tok_demo_alice_4111", "last4": "1111", "brand": "Visa"},
    {"customer_id": 2, "token": "tok_demo_bob_5559",   "last4": "5559", "brand": "Mastercard"},
    {"customer_id": 3, "token": "tok_demo_charlie_1111","last4": "1111", "brand": "Visa"},
    {"customer_id": 4, "token": "tok_demo_diana_1881", "last4": "1881", "brand": "Visa"},
    {"customer_id": 5, "token": "tok_demo_evan_1111",  "last4": "1111", "brand": "Visa"}
  ]
}
EOF
log_success "payment_tokens.json (simulated payment tokens)"

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║          DATA GENERATION COMPLETE!                       ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Created directory: ${CYAN}$BASE_DIR${NC}"
echo ""
echo -e "  ${BOLD}Directory tree:${NC}"
find "$BASE_DIR" -not -path "*/quarantine/*" -not -path "*/backup/*" \
    | sort | sed 's|'"$BASE_DIR"'||' \
    | sed 's|/[^/]*$|/&|' \
    | awk -F'/' 'NF>1{
        depth=NF-2
        name=$NF
        for(i=0;i<depth;i++) printf "  "
        printf "├── %s\n", name
    }'
echo ""
echo -e "  Run the demo: ${YELLOW}bash secure_ecommerce.sh${NC}"
echo ""
