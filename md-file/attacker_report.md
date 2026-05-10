# Bao cao phan Attacker

## 1. Muc tieu

Phan attacker trong du an mo phong mot kich ban tan cong social engineering ket hop ransomware trong moi truong hoc tap. Muc tieu la minh hoa cach nan nhan co the bi lua chay mot phan mem gia mao, sau do du lieu demo trong `shop_data` bi chuyen sang trang thai `.encrypted`.

Day la mo phong phuc vu mon An Toan Bao Mat He Thong Thong Tin, chi chay tren du lieu mau cua du an, khong dung tren du lieu that.

## 2. Thanh phan chinh

| File | Vai tro |
|---|---|
| `manager-agent/fake_manager.py` | GUI ProManager Suite gia mao, hien thi man hinh kich hoat, dashboard va kich hoat qua trinh tan cong |
| `manager-agent/fake_installer.py` | CLI installer gia mao, mo phong cai dat SDK/API key roi kich hoat tan cong |
| `manager-agent/fake_ransom.py` | Man hinh thong bao ransom note sau khi du lieu bi chuyen trang thai |
| `manager-agent/ProManagerSuite.exe` | File executable gia lap de nan nhan tai/chay trong kich ban demo |
| `landing-web/` | Website React/Vite gia mao de phat tan file ProManagerSuite |
| `shop_data/` | Thu muc du lieu nan nhan dung lam sandbox |

## 3. Luong tan cong

1. Nan nhan truy cap landing page gia mao.
2. Nan nhan tai hoac chay ProManager Suite.
3. Chuong trinh hien thi giao dien kich hoat license/API key.
4. Sau khi nhap key, chuong trinh hien thi trang thai dang xac minh.
5. Qua trinh tan cong chay ngam tren `shop_data`.
6. Cac file du lieu demo duoc tao ban `.encrypted`.
7. File goc duoc doi thanh `.demo_original` de co the phuc hoi trong demo Windows-safe.
8. Man hinh ransom note duoc hien thi de minh hoa tac dong cua ransomware.

## 4. Co che mo phong tren Windows

Ban Windows-safe khong dung ma hoa ransomware that. Thay vao do:

- Tao file co duoi `.encrypted` de scanner co the phat hien.
- Giu ban goc voi duoi `.demo_original`.
- Tao file `.ransom_key` lam marker demo.
- `defender/decryptor.py` co the khoi phuc file goc tu `.demo_original`.

Co che nay giup demo van the hien dung luong tan cong/phong thu nhung giam kha nang bi Windows Defender chan nhu cac mau ransomware that.

## 5. Cac ham quan trong

### `trigger_encryption(sandbox_dir)`

Nam trong `manager-agent/fake_manager.py`.

Chuc nang:

- Dam bao `shop_data` co du lieu mau.
- Tao marker `.ransom_key`.
- Duyet cac file trong sandbox.
- Bo qua cac file chuong trinh nhu `.py`, `.exe`, `.ps1`, `.dll`.
- Tao file `.encrypted`.
- Doi file goc thanh `.demo_original`.

### `_silent_encrypt()`

Nam trong `fake_manager.py` va `fake_installer.py`.

Chuc nang:

- Goi `trigger_encryption()` de chay tan cong ngam.
- Trong GUI, ham nay duoc goi bang thread rieng de giao dien van tiep tuc hien thi.

### `_trigger_ransom()`

Nam trong `fake_manager.py`.

Chuc nang:

- Mo `fake_ransom.py`.
- Hien thi thong bao nan nhan da bi ma hoa du lieu.

## 6. Cach chay phan attacker tren Windows

Mo PowerShell tai thu muc goc du an:

```powershell
cd "D:\GIT REPO\btl-atbm\ATBMHTTT"
```

Kich hoat moi truong Python:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv310\Scripts\activate
```

Chay rieng phan attacker:

```powershell
.\demo.ps1 -AttackOnly
```

Hoac chay truc tiep GUI attacker:

```powershell
.\.venv310\Scripts\python.exe .\manager-agent\fake_manager.py
```

Hoac chay installer gia mao:

```powershell
.\.venv310\Scripts\python.exe .\manager-agent\fake_installer.py
```

## 7. Dau hieu sau khi tan cong

Sau khi attacker chay thanh cong, trong `shop_data` se co cac dau hieu:

| Dau hieu | Y nghia |
|---|---|
| `.ransom_key` | Marker demo cho qua trinh tan cong |
| `*.encrypted` | File du lieu da bi chuyen trang thai |
| `*.demo_original` | Ban goc duoc giu lai de phuc hoi trong demo |

Kiem tra bang PowerShell:

```powershell
Get-ChildItem .\shop_data -Force
```

## 8. Phuc hoi sau tan cong

Chay decryptor:

```powershell
.\.venv310\Scripts\python.exe .\defender\decryptor.py .\shop_data
```

Hoac chay mode phong thu:

```powershell
.\demo.ps1 -DefendOnly
```

Ket qua mong doi:

- File `.encrypted` bi xoa.
- File `.demo_original` duoc doi lai thanh file goc.
- Du lieu trong `shop_data` quay ve trang thai doc duoc.

## 9. Gia tri minh hoa trong bao cao

Phan attacker minh hoa cac diem sau:

- Social engineering: phan mem gia mao danh vao niem tin cua nguoi dung.
- Initial execution: nan nhan tu chay chuong trinh.
- Defense evasion trong demo: tien trinh tan cong chay ngam sau man hinh loading.
- Impact: file trong thu muc du lieu bi chuyen sang trang thai khong su dung truc tiep.
- Detection: defender co the phat hien qua duoi `.encrypted`, entropy/signature va YARA rule.
- Recovery: decryptor/backup giup khoi phuc du lieu.

## 10. Gioi han va an toan

- Chi chay trong thu muc sandbox `shop_data`.
- Khong dua du lieu that vao `shop_data`.
- Khong sua code de quet ra ngoai sandbox.
- Ban Windows-safe khong phai ransomware that, chi la mo phong co the phuc hoi.
- Muc dich la hoc tap, trinh bay quy trinh tan cong va phong thu.
