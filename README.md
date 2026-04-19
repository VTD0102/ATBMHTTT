# ShopSecure — Demo Bảo Vệ Malware cho Hệ Thống Thương Mại Điện Tử

Một bản demo hoàn chỉnh trên terminal cho bài thuyết trình **"Bảo Vệ Malware trong Hệ Thống Thương Mại Điện Tử"**.
Minh họa quét ClamAV, mã hóa AES-256, sao lưu tự động và tạo báo cáo HTML.

---

## Bắt Đầu Nhanh (3 lệnh)

```bash
# 1. Cài đặt tất cả các phụ thuộc (yêu cầu sudo)
sudo bash setup.sh

# 2. Tạo dữ liệu mô phỏng thương mại điện tử
bash generate_data.sh

# 3. Chạy bản demo bảo mật đầy đủ
bash secure_ecommerce.sh
```

---

## Cấu Trúc Thư Mục

```bash
.
├── website/              # Dữ liệu mô phỏng
│   ├── database/         # MySQL dump (users.sql)
│   └── customer-data/    # PII giả: customers.csv, payment_tokens.json
├── quarantine/           # Các tệp bị nhiễm được di chuyển tại đây
├── backup/
│   ├── daily/            # Khu vực tổ chức rsync
│   └── encrypted/        # Sao lưu mã hóa AES-256 cuối cùng (.gpg)
├── logs/                 # Nhật ký quét, cảnh báo, mã hóa, sao lưu
└── scripts/              # (Dành cho các tập lệnh tùy chỉnh)
```

---

## Tùy Chọn Tập Lệnh

| Cờ         | Mô Tả                                      |
|-------------|---------------------------------------------|
| `--fast`    | Bỏ qua tất cả độ trễ (chạy thử nhanh)       |
| `--verbose` | In đầu ra lệnh thô vào terminal             |
| `--help`    | Hiển thị cách sử dụng                       |

```bash
# Chế độ nhanh (không trễ, tốt cho kiểm tra)
bash secure_ecommerce.sh --fast

# Verbose + nhanh
bash secure_ecommerce.sh --fast --verbose
```

---

## Quy Trình Demo (5 Bước)

| Bước | Hành động               | Công cụ         | Thời gian |
|------|-------------------------|-----------------|-----------|
| 1    | Quét malware            | ClamAV          | ~30 s     |
| 2    | Cách ly mối đe dọa      | bash + mv       | ~15 s     |
| 3    | Mã hóa dữ liệu nhạy cảm | GPG AES-256     | ~30 s     |
| 4    | Sao lưu mã hóa          | rsync + tar + GPG | ~45 s   |
| 5    | Bảng điều khiển HTML    | Python/xdg      | ~20 s     |

---

## Những Gì Được Phát Hiện

Bản demo sử dụng **Tệp Thử Nghiệm Chống Virus EICAR Tiêu Chuẩn** — một chuỗi được công nhận trên toàn thế giới,
hoàn toàn vô hại mà tất cả các engine antivirus đều gắn cờ như virus thử nghiệm.

```
Tệp:    free_software.exe
Virus:  Eicar-Signature (tên ClamAV)
Hành động: Di chuyển đến quarantine/
```

> EICAR **không phải** là phần mềm độc hại thực sự. Nó là tiêu chuẩn thử nghiệm chính thức (eicar.org).

---

## Công Cụ Được Sử Dụng

| Công cụ    | Mục đích                              |
|------------|---------------------------------------|
| ClamAV     | Quét antivirus nguồn mở              |
| GPG        | Mã hóa đối xứng AES-256              |
| tar + gzip | Nén lưu trữ                          |
| rsync      | Đồng bộ sao lưu                      |
| sha256sum  | Xác minh tính toàn vẹn               |
| pv         | Trực quan hóa thanh tiến trình        |
| figlet     | Biểu ngữ nghệ thuật ASCII (tùy chọn) |

---

## Chạy Lại Bản Demo

Các tập lệnh là idempotent — `generate_data.sh` xóa và tạo lại tất cả dữ liệu mỗi lần chạy:

```bash
bash generate_data.sh && bash secure_ecommerce.sh
```

---

## Yêu Cầu

- Ubuntu 20.04 / 22.04 / 24.04 (hoặc dựa trên Debian)
- Truy cập Internet cho `sudo bash setup.sh` (cập nhật DB ClamAV)
- ~100 MB không gian đĩa

---

## Tệp Đầu Ra

Sau khi chạy đầy đủ, bạn sẽ tìm thấy trong thư mục gốc:

```
logs/
├── scan_<timestamp>.log         # Kết quả quét từng tệp
├── alert_<timestamp>.log        # Cảnh báo cách ly
├── encryption_<timestamp>.log   # Hash tệp được mã hóa
├── backup_<timestamp>.log       # Vị trí sao lưu + hash
└── security_report.html         # Bảng điều khiển tương tác (tự động mở)
```

---

## Chi Tiết Thêm

### Dữ Liệu Giả Được Tạo

- **6 tệp sạch:** hình ảnh sản phẩm, đơn đặt hàng, hóa đơn, nhãn vận chuyển
- **1 tệp EICAR:** Chuỗi kiểm tra malware tiêu chuẩn ngành (100% an toàn)
- **1 SQL dump:** Bảng người dùng và đơn đặt hàng mô phỏng
- **2 tệp PII:** CSV khách hàng có tên, email, số điện thoại, thẻ giả (4111-1111-1111-1111)
- **1 JSON:** Token thanh toán mô phỏng

### Đầu Ra Màu Sắc

```
🟢 Xanh   = THÀNH CÔNG, tệp sạch
🔴 Đỏ     = MALWARE PHÁT HIỆN, lỗi
🟡 Vàng   = CẢNH BÁO, đang xử lý
🔵 Xanh lam = THÔNG TIN
```

### Tính Năng Đặc Biệt

- ✅ Thanh tiến trình cho mỗi bước
- ✅ Dấu thời gian cho mỗi hành động
- ✅ Bảng tóm tắt với ký tự vẽ hộp
- ✅ Báo cáo HTML có thể tương tác
- ✅ Xác minh tính toàn vẹn SHA-256
- ✅ Có thể chạy nhiều lần
- ✅ Khoảng 2-3 phút runtime (hoàn hảo cho video)

---

## Bắt Đầu

```bash
# Bước 1: Cài đặt (yêu cầu sudo)
sudo bash setup.sh

# Bước 2: Tạo dữ liệu và chạy demo
bash generate_data.sh && bash secure_ecommerce.sh
```

---

## Cho Quay Video Thuyết Trình

- Sử dụng `--fast` để loại bỏ độ trễ: `bash secure_ecommerce.sh --fast`
- Dùng `--verbose` để xem chi tiết lệnh
- Báo cáo HTML tự động mở trong trình duyệt
- Nhật ký lưu trong thư mục `logs/`

**Thời gian chạy:** 2-3 phút (với chế độ bình thường, các tệp log được lưu lại)
