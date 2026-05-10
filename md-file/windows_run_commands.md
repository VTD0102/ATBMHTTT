# Chay demo tren Windows

File `demo.sh` la shell script cho Linux/Git Bash/WSL. Tren Windows co 2 cach chay:

1. Dung Git Bash hoac WSL de chay nguyen lenh `bash demo.sh`.
2. Dung PowerShell va chay tung lenh Python tuong duong.

## Chuan bi

Mo PowerShell tai thu muc goc du an:

```powershell
cd "D:\GIT REPO\btl-atbm\ATBMHTTT"
```

Kich hoat moi truong Python 3.10 da cai:

```powershell
.\.venv310\Scripts\activate
```

Neu PowerShell chan activate script, chay lenh nay mot lan trong cua so PowerShell hien tai:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv310\Scripts\activate
```

## Cach 1: Chay bang Git Bash hoac WSL

Neu may da cai Git for Windows, mo **Git Bash** tai thu muc goc du an va chay:

```bash
bash demo.sh
```

Chi chay phan tan cong:

```bash
bash demo.sh --attack-only
```

Chi chay phan phong thu va phuc hoi:

```bash
bash demo.sh --defend-only
```

Xem huong dan:

```bash
bash demo.sh --help
```

## Cach 2: Chay bang PowerShell tren Windows

Du an da co script PowerShell tuong duong `demo.sh`:

```powershell
.\demo.ps1
```

Chi chay phan tan cong:

```powershell
.\demo.ps1 -AttackOnly
```

Chi chay phan phong thu va phuc hoi:

```powershell
.\demo.ps1 -DefendOnly
```

Xem huong dan:

```powershell
.\demo.ps1 -Help
```

### Chay landing web

```powershell
cd "D:\GIT REPO\btl-atbm\ATBMHTTT\landing-web"
npm run dev
```

Mo trinh duyet tai:

```text
http://127.0.0.1:5173/
```

Quay lai thu muc goc:

```powershell
cd "D:\GIT REPO\btl-atbm\ATBMHTTT"
```

### Mo GUI tan cong gia lap

```powershell
.\.venv310\Scripts\python.exe .\manager-agent\fake_manager.py
```

### Chay kich ban tan cong

Lenh nay mo GUI ProManager gia lap. Sau khi nhap API key, du lieu demo trong `shop_data` se duoc chuyen sang trang thai `.encrypted`.

```powershell
.\.venv310\Scripts\python.exe .\manager-agent\fake_manager.py
```

### Giai ma shop_data

```powershell
.\.venv310\Scripts\python.exe .\defender\decryptor.py .\shop_data
```

### Quet phat hien ransomware

```powershell
.\.venv310\Scripts\python.exe .\defender\scanner.py .\shop_data
```

### Phan tich tinh file nghi ngo

Dung `PYTHONIOENCODING=utf-8` de tranh loi hien thi ky tu tren console Windows:

```powershell
$env:PYTHONIOENCODING = "utf-8"
.\.venv310\Scripts\python.exe .\defender\static_analyzer.py .\manager-agent\fake_manager.py
```

### Tao backup

```powershell
.\.venv310\Scripts\python.exe .\defender\backup_manager.py backup
```

### Xem danh sach backup

```powershell
.\.venv310\Scripts\python.exe .\defender\backup_manager.py list
```

### Restore backup

Thay ten file backup bang file thuc te trong thu muc `backups`.

```powershell
.\.venv310\Scripts\python.exe .\defender\backup_manager.py restore .\backups\backup_YYYYMMDD_HHMMSS.tar.gz
```

### Mo GUI phong thu

```powershell
.\.venv310\Scripts\python.exe .\defender\defender_gui.py
```

## PowerShell tuong duong voi cac mode trong demo.sh

### Tuong duong `bash demo.sh --attack-only`

```powershell
.\.venv310\Scripts\python.exe .\defender\backup_manager.py backup
Get-ChildItem .\shop_data
.\.venv310\Scripts\python.exe .\manager-agent\fake_manager.py
Get-ChildItem .\shop_data
```

### Tuong duong `bash demo.sh --defend-only`

```powershell
$env:PYTHONIOENCODING = "utf-8"
.\.venv310\Scripts\python.exe .\defender\static_analyzer.py .\manager-agent\fake_manager.py
.\.venv310\Scripts\python.exe .\defender\scanner.py .\shop_data
.\.venv310\Scripts\python.exe .\defender\decryptor.py .\shop_data
.\.venv310\Scripts\python.exe .\defender\backup_manager.py backup
.\.venv310\Scripts\python.exe .\defender\backup_manager.py list
Get-ChildItem .\shop_data
```

### Tuong duong `bash demo.sh`

Chay lan luot 2 nhom lenh:

1. `Tuong duong bash demo.sh --attack-only`
2. `Tuong duong bash demo.sh --defend-only`

## Luu y an toan

- Chi chay voi du lieu demo trong `shop_data`.
- Lenh tan cong/mo phong co the tao file `.encrypted`.
- Neu muon khoi phuc sau demo, chay:

```powershell
.\.venv310\Scripts\python.exe .\defender\decryptor.py .\shop_data
```
