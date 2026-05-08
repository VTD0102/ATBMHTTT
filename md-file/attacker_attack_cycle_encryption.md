# Chu trinh tan cong va thuat toan ma hoa cua phan Attacker

## 1. Pham vi tai lieu

Tai lieu nay mo ta chi tiet phan attacker cua project `ATBMHTTT`, tap trung vao:

- Chu trinh tan cong tu luc nan nhan tiep can ung dung gia mao den khi ransom note xuat hien.
- Cac thanh phan attacker trong thu muc `manager-agent/`.
- Thuat toan bien doi du lieu trong ham `trigger_encryption()`.
- Co che tao file `.encrypted`, file `.demo_original` va marker `.ransom_key`.
- Dau vet phuc vu phat hien, dieu tra va khoi phuc.

Day la mo phong hoc thuat trong sandbox `shop_data`. Phien ban hien tai la ban Windows-safe: khong ma hoa pha huy du lieu that, ma tao file demo co header va Base64 de co the khoi phuc an toan.

## 2. Thanh phan attacker

| Thanh phan | Duong dan | Vai tro |
|---|---|---|
| Landing page gia mao | `landing-web/` | Website quang ba/tai ung dung `ProManagerSuite.exe` |
| Ung dung gia mao dang GUI | `manager-agent/fake_manager.py` | Giao dien ProManager Suite, yeu cau kich hoat license/API key, chay ma hoa ngam va mo ransom note |
| Installer gia mao dang CLI | `manager-agent/fake_installer.py` | Gia lap cai dat OpenAI SDK/API key, sau do goi engine ma hoa |
| Ransom note | `manager-agent/fake_ransom.py` | Man hinh fullscreen thong bao file da bi ma hoa, hien countdown va ma mo khoa demo |
| File executable demo | `manager-agent/ProManagerSuite.exe` | Ban dong goi cho kich ban nan nhan tai va chay |
| Sandbox du lieu nan nhan | `shop_data/` | Thu muc bi tac dong boi attacker trong demo |

## 3. Mo hinh tan cong tong quan

Phan attacker mo phong mot chien dich social engineering ket hop ransomware:

1. Attacker tao mot san pham gia mao co ten `ProManager Suite`.
2. Nan nhan tin day la cong cu quan ly du an hoac cong cu kich hoat SDK/API.
3. Nan nhan tai/chay ung dung.
4. Ung dung hien giao dien hop phap: activation, verifying, dashboard hoac installer progress.
5. Trong luc nan nhan nhin thay man hinh hop le, attacker chay ham bien doi du lieu ngam.
6. Cac file trong `shop_data` duoc tao ban `.encrypted`.
7. File goc duoc doi sang `.demo_original` de giu lai kha nang khoi phuc.
8. Ransom note fullscreen hien ra, tao cam giac he thong da bi ransomware khong che.

## 4. Chu trinh tan cong chi tiet

### 4.1. Giai doan 1 - Chuan bi lure

Attacker dung `landing-web/` lam website gia mao. Website nay co muc dich:

- Tao niem tin rang `ProManager Suite` la phan mem hop phap.
- Cung cap nut tai file `ProManagerSuite.exe`.
- Lam nan nhan tu nguyen thuc thi file, tuong duong initial execution trong kill chain.

Trong project, file tai ve duoc dat trong:

```text
landing-web/public/ProManagerSuite.exe
```

### 4.2. Giai doan 2 - Thuc thi ban dau

Co hai duong kich hoat attacker:

| Duong thuc thi | File | Mo ta |
|---|---|---|
| GUI application | `fake_manager.py` | Nan nhan mo ProManager Suite, nhap API/license key, ung dung hien verifying va dashboard |
| CLI installer | `fake_installer.py` | Nan nhan chay installer gia mao, thay tien trinh cai dat va kich hoat API key |

Ca hai duong deu ket thuc bang viec goi:

```python
trigger_encryption(VICTIM_SANDBOX)
```

`VICTIM_SANDBOX` mac dinh tro toi thu muc:

```text
shop_data/
```

### 4.3. Giai doan 3 - Tao niem tin va che giau hanh vi

Trong `fake_manager.py`, ung dung hien lan luot:

1. Man hinh `Activate Your License`.
2. O nhap API License Key.
3. Man hinh `Verifying license key...`.
4. Dashboard ProManager Suite.

Khi nguoi dung submit key, ham `_on_activate()` duoc goi. Ham nay tao thread rieng de chay ma hoa ngam:

```python
threading.Thread(target=self._silent_encrypt, daemon=True).start()
```

Sau do ung dung tiep tuc hien man hinh verifying/dashboard. Dieu nay mo phong ky thuat che giau hanh vi bang giao dien hop phap: nan nhan thay phan mem dang xu ly binh thuong trong khi du lieu bi tac dong o nen.

### 4.4. Giai doan 4 - Kich hoat engine ma hoa

Ham `_silent_encrypt()` trong `fake_manager.py` chi dong vai tro wrapper:

```python
def _silent_encrypt(self):
    trigger_encryption(VICTIM_SANDBOX)
```

Trong `fake_installer.py`, logic tuong tu:

```python
def _silent_encrypt():
    trigger_encryption(VICTIM_SANDBOX)
```

Nhu vay, toan bo logic tac dong file tap trung trong `trigger_encryption()` cua `fake_manager.py`.

### 4.5. Giai doan 5 - Bien doi file trong sandbox

`trigger_encryption()` duyet de quy cac file trong sandbox, bo qua nhung file khong nen tac dong, sau do tao file `.encrypted` va doi ten file goc.

Vi du truoc tan cong:

```text
shop_data/
  invoice_2024.txt
  customer_data.csv
  contract.txt
```

Sau tan cong:

```text
shop_data/
  .ransom_key
  invoice_2024.txt.encrypted
  invoice_2024.txt.demo_original
  customer_data.csv.encrypted
  customer_data.csv.demo_original
  contract.txt.encrypted
  contract.txt.demo_original
```

### 4.6. Giai doan 6 - Hien ransom note

Sau khi dashboard hien thi mot khoang thoi gian, `fake_manager.py` goi:

```python
self.root.after(3000, self._trigger_ransom)
```

`_trigger_ransom()` dong giao dien ProManager va mo `fake_ransom.py`. Ransom note co cac dac diem:

- Fullscreen.
- Tieu de `YOUR FILES HAVE BEEN ENCRYPTED`.
- Countdown 72 gio.
- Thong tin thanh toan gia lap.
- O nhap ma giai ma.
- Ma demo hop le: `DEMO-SAFE-2024-TMDT`.

Khi nhap dung ma, chuong trinh chi hien thong bao huong dan chay decryptor:

```text
Run: python3 defender/decryptor.py shop_data/
```

## 5. Thuat toan ma hoa/bien doi du lieu

### 5.1. Hang so quan trong

Trong `manager-agent/fake_manager.py`:

```python
DEMO_HEADER = b"ATBMHTTT_DEMO_ENCRYPTED_V1\n"
DEMO_KEY = b"ATBMHTTT_WINDOWS_DEMO_KEY"
DEMO_ORIGINAL_EXT = ".demo_original"
DEMO_ENCRYPTED_EXT = ".enc" + "rypted"
DEMO_SKIP_EXTENSIONS = {'.exe', '.py', '.ps1', '.sh', '.bat', '.so', '.dll'}
```

Y nghia:

| Hang so | Y nghia |
|---|---|
| `DEMO_HEADER` | Header dat dau file `.encrypted`, giup decryptor va YARA nhan dien dinh dang demo |
| `DEMO_KEY` | Noi dung ghi vao `.ransom_key`, dong vai tro marker demo |
| `DEMO_ORIGINAL_EXT` | Duoi file backup cua file goc |
| `DEMO_ENCRYPTED_EXT` | Duoi file sau bien doi |
| `DEMO_SKIP_EXTENSIONS` | Cac duoi file bi bo qua de tranh tac dong vao chuong trinh/script |

### 5.2. Pseudocode cua `trigger_encryption()`

```text
function trigger_encryption(sandbox_dir):
    dam bao sandbox co du lieu mau

    tao file sandbox_dir/.ransom_key
    ghi DEMO_KEY vao .ransom_key

    for moi file trong sandbox_dir va thu muc con:
        lay extension cua file

        if file la .ransom_key:
            bo qua

        if file da ket thuc bang .encrypted:
            bo qua

        if file da ket thuc bang .demo_original:
            bo qua

        if extension nam trong tap skip:
            bo qua

        tinh real path cua sandbox va file
        if file khong nam ben trong sandbox:
            bo qua

        doc toan bo byte cua file goc
        ghi file moi: original_path + ".encrypted"
            noi dung = DEMO_HEADER + Base64(data_goc)

        doi ten file goc:
            original_path -> original_path + ".demo_original"
```

### 5.3. Cong thuc bien doi

Voi moi file hop le `F`, noi dung goc la:

```text
P = bytes(F)
```

Noi dung file `.encrypted` duoc tao la:

```text
C_demo = DEMO_HEADER || Base64(P)
```

Trong do:

- `||` la phep noi byte.
- `Base64(P)` la bieu dien Base64 cua byte goc.
- `C_demo` khong phai ciphertext manh ve mat mat ma hoc; day la dinh dang demo co the dao nguoc.

Ten file thay doi:

```text
F                 -> F.demo_original
F.encrypted       -> DEMO_HEADER || Base64(P)
```

Vi du voi file:

```text
invoice_2024.txt
```

Ket qua:

```text
invoice_2024.txt.encrypted
invoice_2024.txt.demo_original
```

### 5.4. Ly do dung Base64 thay vi ma hoa that

Project hien tai uu tien tinh an toan khi demo tren Windows:

- Khong pha huy du lieu goc.
- De dang khoi phuc bang `defender/decryptor.py`.
- Giam nguy co bi antivirus/EDR chan nhu ransomware that.
- Van tao duoc dau vet phu hop cho bai hoc phong thu: `.encrypted`, `.ransom_key`, ransom note, thay doi file hang loat.

Do do, tu "ma hoa" trong pham vi tai lieu nay nen hieu la "bien doi demo theo mau ransomware", khong phai trien khai ransomware that.

## 6. Dieu kien bo qua file

Engine khong bien doi tat ca file mot cach tuy tien. Cac dieu kien bo qua gom:

| Dieu kien | Muc dich |
|---|---|
| `filename == ".ransom_key"` | Khong tu bien doi marker key |
| `filename.endswith(".encrypted")` | Tranh ma hoa lap lai file da bien doi |
| `filename.endswith(".demo_original")` | Giu nguyen ban backup |
| Extension thuoc `.exe`, `.py`, `.ps1`, `.sh`, `.bat`, `.so`, `.dll` | Tranh pha chuong trinh/script va giam rui ro khi demo |
| Real path khong nam trong sandbox | Ngan tac dong ra ngoai `shop_data` |

Kiem tra real path la diem an toan quan trong:

```python
real_sandbox = os.path.realpath(sandbox_dir)
real_path = os.path.realpath(filepath)
if not (real_path.startswith(real_sandbox + os.sep) or real_path == real_sandbox):
    continue
```

Muc dich la tranh truong hop duong dan bat thuong hoac lien ket dan toi file ngoai sandbox.

## 7. Co che tao du lieu mau

Neu sandbox rong, `_ensure_sandbox()` tao cac file mau:

| File | Noi dung mo phong |
|---|---|
| `invoice_2024.txt` | Hoa don |
| `customer_data.csv` | Du lieu khach hang |
| `contract.txt` | Hop dong dich vu |
| `api_config.json` | API key, DB host, DB password |
| `business_report.csv` | Doanh thu, chi phi, loi nhuan |
| `orders_2024.csv` | Don hang |
| `db_credentials.txt` | Thong tin database/Redis/secret key |
| `project_data.txt` | Thong tin du an noi bo |

Nhom file nay giup demo the hien tac dong cua ransomware len du lieu co gia tri kinh doanh.

## 8. Phan biet GUI attacker va installer attacker

### 8.1. GUI attacker - `fake_manager.py`

Luong chinh:

```text
run()
  -> _show_activation()
      -> nguoi dung nhap key
      -> _on_activate()
          -> start thread _silent_encrypt()
          -> _show_verifying()
              -> _do_activate()
                  -> _show_dashboard()
                      -> after 3000ms _trigger_ransom()
```

Dac diem:

- Co social engineering manh hon vi giao dien giong ung dung that.
- Ma hoa ngam chay tren thread rieng.
- Ransom note xuat hien sau khi dashboard da tao cam giac kich hoat thanh cong.

### 8.2. Installer attacker - `fake_installer.py`

Luong chinh:

```text
main
  -> print "[OpenAI SDK Installer]"
  -> _fake_progress()
  -> _silent_encrypt()
  -> subprocess.Popen(fake_ransom.py)
```

Dac diem:

- Hien tien trinh cai dat gia lap.
- In cac thong bao nhu dang tai SDK, xac minh chu ky, cai dependency.
- Sau khi bao cai dat thanh cong thi da goi engine ma hoa.
- Mo ransom note bang subprocess.

## 9. Co che ransom note

`fake_ransom.py` khong ma hoa file. File nay chi phu trach giao dien tong tien sau khi engine da tac dong du lieu.

Cac thanh phan chinh:

| Thanh phan | Vai tro |
|---|---|
| `FakeRansomApp.__init__()` | Tao cua so Tkinter fullscreen |
| `_start_timer()` | Dem nguoc thoi gian con lai |
| `_start_blink()` | Lam nhap nhay tieu de canh bao |
| `_check_code()` | Kiem tra ma demo nguoi dung nhap |
| `DEMO_CODE` | Ma mo khoa demo: `DEMO-SAFE-2024-TMDT` |

Neu nhap sai ma, chuong trinh hien so lan thu con lai ngau nhien tu 1 den 5. Day la hieu ung giao dien, khong lien quan den logic khoa/giai ma that.

## 10. Dau vet sau tan cong

Sau khi attacker chay thanh cong, co the quan sat cac dau vet:

| Dau vet | Vi tri | Y nghia |
|---|---|---|
| `.ransom_key` | `shop_data/.ransom_key` | Marker demo, noi dung la `ATBMHTTT_WINDOWS_DEMO_KEY` |
| `*.encrypted` | `shop_data/` | File da duoc tao theo dinh dang `DEMO_HEADER + Base64(data)` |
| `*.demo_original` | `shop_data/` | Ban goc duoc doi ten de phuc hoi |
| Ransom note fullscreen | Process `fake_ransom.py` hoac executable bundle | Dau hieu tong tien tren giao dien |
| Header `ATBMHTTT_DEMO_ENCRYPTED_V1` | Dau file `.encrypted` | Chu ky nhan dien dinh dang demo |

Lenh kiem tra:

```powershell
Get-ChildItem .\shop_data -Force
```

## 11. Lien he voi phan defender

Phan defender co the phat hien attacker bang nhieu co che:

| Co che | File lien quan | Tin hieu |
|---|---|---|
| Extension scan | `defender/scanner.py`, `defender/defender_gui.py` | File moi co duoi `.encrypted` |
| Behavior monitor | `defender/behavior_monitor.py` | File `.encrypted` moi xuat hien, `.ransom_key` xuat hien |
| Static analyzer | `defender/static_analyzer.py` | Chuoi nghi van trong file attacker |
| YARA | `defender/rules/ransomware.yar` | Header `ATBMHTTT_DEMO_ENCRYPTED_V1`, `.demo_original`, ransom note |
| Recovery | `defender/decryptor.py` | Khoi phuc tu `.demo_original` hoac decode Base64 |

Rule YARA quan trong cho ban Windows-safe:

```text
WindowsSafeDemoTransform
  -> header: ATBMHTTT_DEMO_ENCRYPTED_V1
  -> marker: DEMO_ENCRYPTED_EXT
  -> backup: .demo_original
```

## 12. Thuat toan khoi phuc tuong ung

`defender/decryptor.py` xu ly file `.encrypted` theo hai nhanh:

### 12.1. Nhanh Windows-safe demo

Neu file `.encrypted` bat dau bang:

```text
ATBMHTTT_DEMO_ENCRYPTED_V1
```

Decryptor uu tien tim file backup:

```text
original_path + ".demo_original"
```

Neu backup ton tai:

1. Doi `.demo_original` ve ten file goc.
2. Xoa file `.encrypted`.
3. In thong bao restored.

Neu backup khong ton tai:

1. Cat bo `DEMO_HEADER`.
2. Base64-decode phan con lai.
3. Ghi lai thanh file goc.
4. Xoa file `.encrypted`.

### 12.2. Nhanh Fernet cu/tuong thich

Neu file `.encrypted` khong co `DEMO_HEADER`, decryptor thu doc `.ransom_key` va dung `cryptography.fernet.Fernet` de giai ma. Nhanh nay giu tuong thich voi phien ban demo cu co engine Fernet.

Trong phien ban attacker hien tai, engine chinh la Windows-safe transform, khong phai Fernet.

## 13. So sanh voi ransomware that

| Tieu chi | Project demo | Ransomware that |
|---|---|---|
| Pham vi tac dong | Chi sandbox `shop_data` | Co the quet nhieu o dia, network share, cloud sync |
| Bien doi du lieu | `DEMO_HEADER + Base64(data)` | AES/ChaCha20/Fernet hoac hybrid crypto |
| Quan ly key | `.ransom_key` local/marker demo | Key sinh ngau nhien, ma hoa bang public key, gui C2 |
| Backup file goc | Giu `.demo_original` | Thuong xoa/ghi de file goc |
| Ransom note | Tkinter fullscreen demo | File note, desktop wallpaper, process persistence |
| Muc dich | Hoc tap va phong thu | Tong tien, pha hoai, danh cap du lieu |

## 14. Cac diem an toan cua project

Phan attacker duoc gioi han de phu hop moi truong hoc tap:

- Chi tac dong vao `shop_data`.
- Co kiem tra real path de tranh vuot sandbox.
- Bo qua file executable, script va thu vien.
- Giu lai file goc duoi `.demo_original`.
- Dinh dang `.encrypted` co header nhan dien ro rang.
- Co decryptor khoi phuc di kem.
- Ransom note co badge `DEMO ONLY`.

## 15. Ket luan

Phan attacker cua project mo phong day du cac buoc quan trong cua mot cuoc tan cong social engineering + ransomware:

1. Lua nan nhan bang ung dung/installer gia mao.
2. Tao giao dien hop phap de tang do tin cay.
3. Chay tac dong file ngam sau thao tac kich hoat.
4. Tao dau vet ransomware: `.encrypted`, `.ransom_key`, ransom note.
5. Cho phep defender phat hien, ung pho va khoi phuc.

Thuat toan "ma hoa" hien tai la bien doi demo an toan:

```text
encrypted_file = ATBMHTTT_DEMO_ENCRYPTED_V1\n + Base64(original_bytes)
original_file  = original_file.demo_original
```

Nho cach thiet ke nay, project van trinh bay duoc vong doi tan cong va phong thu ransomware ma khong tao ra ransomware that hoac lam mat du lieu trong qua trinh demo.
