# Cach Thuat Toan Hoat Dong, Dau Ra Va Chuc Nang File

Tai lieu nay mo ta cach cac file chinh trong demo ATBMHTTT phoi hop voi nhau, dau vao/dau ra cua tung thuat toan, va luong xu ly tu luc nguoi dung chay phan mem gia mao den luc Defender phat hien, sao luu va khoi phuc du lieu.

> Luu y: day la mo phong hoc thuat trong sandbox. Khong chay voi du lieu that hoac thu muc ngoai pham vi demo.

## 1. Tong Quan Luong Hoat Dong

He thong gom 4 cum chinh:

| Cum | File/thu muc | Vai tro |
|---|---|---|
| Ung dung gia mao | `manager-agent/fake_manager.py` | Hien giao dien ProManager Suite gia mao va kich hoat ma hoa ngam |
| Man hinh doi tien chuoc | `manager-agent/fake_ransom.py` | Hien ransom note fullscreen, dem nguoc thoi gian, nhan ma demo |
| Du lieu nan nhan | `shop_data/` | Sandbox chua file mau nhu hoa don, hop dong, du lieu khach hang |
| Defender | `defender/*.py` | Quet, giam sat hanh vi, phan tich tinh, backup va giai ma/khoi phuc |

Luong tong quat:

```text
Nguoi dung chay fake_manager.py
  -> nhap API key bat ky
  -> fake_manager.py tao thread ma hoa ngam
  -> hien man hinh "Verifying license key..."
  -> hien dashboard ProManager gia
  -> sau vai giay mo fake_ransom.py
  -> Defender quet/giam sat thay file .encrypted
  -> tao canh bao, backup, khoi phuc bang backup hoac decryptor.py
```

## 2. Thuat Toan Ma Hoa Trong `fake_manager.py`

### File lien quan

- `manager-agent/fake_manager.py`
- `shop_data/`
- `defender/decryptor.py`

### Dau vao

Thuat toan nhan vao thu muc sandbox:

```python
trigger_encryption(VICTIM_SANDBOX)
```

Gia tri `VICTIM_SANDBOX` phu thuoc cach chay:

| Che do | Sandbox |
|---|---|
| Chay Python source | `../shop_data` |
| Chay ban dong goi exe | Thu muc chua file exe |

Neu sandbox rong, ham `_ensure_sandbox()` se tao san cac file mau nhu:

- `invoice_2024.txt`
- `customer_data.csv`
- `contract.txt`
- `api_config.json`
- `business_report.csv`
- `orders_2024.csv`
- `db_credentials.txt`
- `project_data.txt`

### Cac hang so chinh

| Hang so | Gia tri | Y nghia |
|---|---|---|
| `DEMO_HEADER` | `ATBMHTTT_DEMO_ENCRYPTED_V1\n` | Header danh dau file da bi ma hoa theo dinh dang demo |
| `DEMO_KEY` | `ATBMHTTT_WINDOWS_DEMO_KEY` | Key demo luu vao `.ransom_key` |
| `DEMO_ORIGINAL_EXT` | `.demo_original` | Duoi cua ban goc duoc giu lai |
| `DEMO_ENCRYPTED_EXT` | `.encrypted` | Duoi cua file bi khoa |
| `DEMO_SKIP_EXTENSIONS` | `.exe`, `.py`, `.ps1`, `.sh`, `.bat`, `.so`, `.dll` | Cac loai file bo qua de khong tu pha chinh chuong trinh |

### Cach thuat toan chay

1. Tao hoac ghi de file key:

```text
shop_data/.ransom_key
```

Noi dung la `DEMO_KEY`.

2. Duyet de quy toan bo file trong sandbox bang `os.walk()`.

3. Bo qua cac file khong can ma hoa:

- `.ransom_key`
- file da ket thuc bang `.encrypted`
- file da ket thuc bang `.demo_original`
- file co extension nam trong whitelist bo qua

4. Kiem tra an toan duong dan:

```text
real_path phai nam ben trong real_sandbox
```

Buoc nay ngan viec ma hoa nham file ngoai sandbox.

5. Doc du lieu goc o dang bytes.

6. Tao file moi:

```text
ten_file_goc + ".encrypted"
```

Noi dung file moi co dang:

```text
DEMO_HEADER + base64(noi_dung_goc)
```

7. Doi ten file goc thanh:

```text
ten_file_goc + ".demo_original"
```

Vi du:

```text
customer_data.csv
  -> customer_data.csv.encrypted
  -> customer_data.csv.demo_original
```

### Dau ra

Sau khi ma hoa, trong `shop_data/` se co:

| Dau ra | Mo ta |
|---|---|
| `*.encrypted` | File bi khoa theo dinh dang demo |
| `*.demo_original` | Ban goc duoc giu lai de phuc hoi trong demo |
| `.ransom_key` | Key demo |

Thuat toan hien tai la mo phong co the khoi phuc duoc, khong phai ransomware that. Du lieu goc khong bi xoa vinh vien ma duoc doi ten sang `.demo_original`.

## 3. Cach Giao Dien Gia Mao Kich Hoat Ma Hoa

File `fake_manager.py` tao ung dung `ProManagerApp` bang `tkinter`.

### Cac man hinh

| Man hinh | Ham | Chuc nang |
|---|---|---|
| Activation | `_show_activation()` | Yeu cau nhap API/license key |
| Verifying | `_show_verifying()` | Tao cam giac dang xac thuc license |
| Dashboard | `_show_dashboard()` | Hien ung dung quan ly du an gia |
| Ransom note | `_trigger_ransom()` | Dong dashboard va mo `fake_ransom.py` |

### Diem kich hoat

Khi nguoi dung bam `Activate License`, ham `_on_activate()` chay:

```text
threading.Thread(target=self._silent_encrypt, daemon=True).start()
```

Nghia la qua trinh ma hoa bat dau ngay sau khi submit API key, trong khi giao dien van tiep tuc hien man hinh xac thuc va dashboard gia de che giau hanh vi nen.

Sau khi dashboard hien thi, chuong trinh dat lich:

```text
self.root.after(3000, self._trigger_ransom)
```

Sau khoang 3 giay tren dashboard, cua so ransom note duoc mo.

## 4. File `fake_ransom.py` Hoat Dong Nhu The Nao

`fake_ransom.py` khong truc tiep ma hoa file. File nay chi tao giao dien doi tien chuoc.

### Chuc nang

- Mo cua so fullscreen.
- Hien thong bao file da bi ma hoa.
- Hien thong tin thanh toan gia lap.
- Hien tong tien chuoc `29,000,000 VND`.
- Dem nguoc tu gan 72 gio.
- Cho nhap ma giai khoa demo.

### Dau vao

Nguoi dung nhap chuoi vao o decrypt code.

### Xu ly

Ham `_check_code()` so sanh chuoi nguoi dung nhap voi:

```text
DEMO-SAFE-2024-TMDT
```

### Dau ra

| Truong hop | Dau ra |
|---|---|
| Nhap dung code | Hien thong bao code dung va goi y chay `python3 defender/decryptor.py shop_data/` |
| Nhap sai code | Hien thong bao sai va so lan thu con lai ngau nhien |

Luu y: nhap dung code tren giao dien ransom note chi hien thong bao. Viec khoi phuc file that su do `defender/decryptor.py` xu ly.

## 5. Thuat Toan Giai Ma/Khoi Phuc Trong `decryptor.py`

### Dau vao

Mac dinh, script nhan thu muc:

```text
shop_data/
```

Neu khong truyen tham so, duong dan mac dinh la `../shop_data`.

### Cach xu ly

Script duyet tat ca file ket thuc bang `.encrypted`.

Voi moi file:

1. Xac dinh ten file goc bang cach bo duoi `.encrypted`.

2. Doc noi dung file ma hoa.

3. Neu file bat dau bang `DEMO_HEADER`, day la dinh dang demo moi:

   - Neu ton tai file `.demo_original`, script doi ten file `.demo_original` ve ten goc.
   - Xoa file `.encrypted`.
   - In log da restore.

4. Neu khong co `.demo_original`, script giai Base64 phan sau header va ghi lai file goc.

5. Neu file khong co `DEMO_HEADER`, script thu dung Fernet voi key trong `.ransom_key`. Nhanh nay giu tuong thich voi cac ban demo cu.

### Dau ra

| Dau ra | Mo ta |
|---|---|
| File goc | Duoc khoi phuc lai ten va noi dung ban dau |
| File `.encrypted` | Bi xoa sau khi restore thanh cong |
| Log console | Dang `[DECRYPTOR] Restored: ten_file` |
| Tong ket | So file restore thanh cong va so loi |

Vi du:

```text
[DECRYPTOR] Restored: customer_data.csv
[DECRYPTOR] Result: 8 files restored, 0 errors.
```

## 6. Thuat Toan Quet Trong `scanner.py`

`scanner.py` la bo quet dua tren dau hieu file va entropy.

### Dau vao

Thu muc can quet:

```bash
python defender/scanner.py shop_data
```

Neu khong truyen tham so, script quet thu muc hien tai.

### Cac dau hieu phat hien

| Dau hieu | Dieu kien | Muc do |
|---|---|---|
| Extension dang nghi | File co duoi `.encrypted`, `.locked`, `.crypto`, `.crypt`, `.enc` | `HIGH` |
| Entropy cao | Entropy 4096 byte dau tien > `5.5` | `MEDIUM` |
| Signature simulator | Noi dung co chuoi `RANSOMWARE_SIMULATOR_DEMO_SAFE` | `CRITICAL` |

### Cach tinh entropy

Ham `calculate_entropy(data)` dem tan suat tung byte, sau do tinh Shannon entropy:

```text
entropy = -sum(p(byte) * log2(p(byte)))
```

File bi ma hoa hoac nen thuong co entropy cao hon file text thong thuong.

### Dau ra

Script tra ve danh sach finding gom:

```text
file, reason, severity, detail
```

Va in report ra console:

```text
[SCANNER] 2 threat(s) found:
  [1] HIGH | encrypted_extension
  [2] MEDIUM | high_entropy
```

## 7. Thuat Toan Giam Sat Hanh Vi Trong `behavior_monitor.py`

`behavior_monitor.py` phat hien thay doi file khi chay mot installer/chuong trinh nghi ngo.

### Dau vao

| Tham so | Mac dinh | Y nghia |
|---|---|---|
| `installer_script` | `manager-agent/fake_installer.py` | File nghi ngo se duoc chay |
| `watch_dir` | `shop_data/` | Thu muc can giam sat |
| `poll_interval` | `0.5` giay | Chu ky lay snapshot |

### Cach xu ly

1. Lay snapshot ban dau cua `watch_dir`: map `duong_dan_file -> kich_thuoc`.
2. Chay installer bang `subprocess.Popen()`.
3. Moi `0.5` giay lay snapshot moi.
4. So sanh snapshot truoc/sau:

| Dieu kien | Finding | Muc do |
|---|---|---|
| Xuat hien file moi ket thuc `.encrypted` | `new_encrypted_file` | `CRITICAL` |
| File ban dau bien mat | `file_deleted` | `HIGH` |

5. Neu co threat, kill process nghi ngo.

### Dau ra

- Danh sach threat.
- Log console canh bao.
- Exit code `1` neu phat hien threat.
- Mo trang prevention HTML neu co threat.

## 8. Phan Tich Tinh Trong `static_analyzer.py`

`static_analyzer.py` phat hien dau hieu doc hai ma khong can chay file.

### Dau vao

File can phan tich:

```bash
python defender/static_analyzer.py manager-agent/fake_installer.py
```

Neu khong truyen tham so, script mac dinh phan tich `manager-agent/fake_installer.py`.

### Cach phat hien

1. Neu co `yara-python` va file rule ton tai, compile `defender/rules/ransomware.yar` va match voi file.
2. Doc file dang text voi `errors="ignore"`.
3. Tim cac chuoi nguy hiem:

```text
RANSOMWARE_SIMULATOR_DEMO_SAFE
ATBMHTTT_DEMO_ENCRYPTED_V1
DEMO_ENCRYPTED_EXT
.encrypt(
fernet.encrypt
Fernet.generate_key
```

4. Kiem tra combo nghi ngo:

```text
cryptography + os.walk + os.remove
```

### Dau ra

Finding dang:

```text
file, reason, severity, detail
```

Neu co finding `CRITICAL`, chuong trinh thoat voi exit code `1`.

## 9. Backup Va Restore Trong `backup_manager.py`

`backup_manager.py` dung `tarfile` de dong goi va khoi phuc sandbox.

### Backup

Lenh:

```bash
python defender/backup_manager.py backup
```

Xu ly:

1. Tao ten file theo timestamp:

```text
backup_YYYYMMDD_HHMMSS.tar.gz
```

2. Neu trung ten trong cung giay, them hau to `_1`, `_2`, ...
3. Nen toan bo `shop_data/` vao thu muc `backups/`.
4. In ten file va kich thuoc.

### List

Lenh:

```bash
python defender/backup_manager.py list
```

Dau ra la danh sach file `backup_*.tar.gz` trong `backups/`.

### Restore

Lenh:

```bash
python defender/backup_manager.py restore backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

Xu ly:

1. Giai nen archive vao `shop_data/`.
2. Neu archive co thu muc con `shop_data`, script dua file con ra truc tiep thu muc restore.
3. In log da restore.

## 10. Dau Ra Cuoi Cung Cua Toan He Thong

| Giai doan | Dau ra de quan sat |
|---|---|
| Chay ung dung gia mao | Cua so ProManager Suite activation/verifying/dashboard |
| Ma hoa ngam | File `.encrypted`, file `.demo_original`, file `.ransom_key` |
| Ransom note | Cua so fullscreen doi tien chuoc va countdown |
| Quet thu cong | Report finding tren console |
| Giam sat hanh vi | Threat list va process bi kill khi co hanh vi ma hoa |
| Backup | File `.tar.gz` trong `backups/` |
| Giai ma/khoi phuc | File goc duoc tra lai, `.encrypted` bi xoa |

## 11. Cach Chay Kiem Thu Nhanh

### Tao backup truoc demo

```bash
python defender/backup_manager.py backup
```

### Chay ung dung gia mao

```bash
python manager-agent/fake_manager.py
```

Nhap API key bat ky, vi du:

```text
sk-demo-test
```

### Quet sandbox sau khi bi ma hoa

```bash
python defender/scanner.py shop_data
```

### Khoi phuc bang decryptor

```bash
python defender/decryptor.py shop_data
```

### Liet ke backup

```bash
python defender/backup_manager.py list
```

## 12. Ghi Chu Ve An Toan Va Gioi Han

- Demo hien tai co co che giu ban goc bang `.demo_original`, nen co the restore nhanh.
- `fake_ransom.py` chi hien giao dien doi tien chuoc, khong ma hoa file.
- `scanner.py` phat hien dua tren heuristic, nen co the co false positive voi file nen hoac file nhi phan co entropy cao.
- `behavior_monitor.py` phu hop de minh hoa detection theo thay doi filesystem, khong thay the EDR/HIDS that.
- `backup_manager.py` restore truc tiep vao sandbox, nen nen tao backup sach truoc moi lan demo.
