# ATBMHTTT - Demo phong chong ransomware cho du lieu TMDT

Du an demo hoc thuat cho mon **An Toan Bao Mat He Thong Thong Tin**. Kich ban mo phong mot ung dung quan ly gia mao, qua do ma hoa du lieu mau trong `shop_data/`, sau do dung cac cong cu phong thu de phat hien, giai ma va backup lai du lieu.

> **Demo only:** chi chay tren may local va chi tac dong vao thu muc sandbox `shop_data/`. Khong dung cac script nay tren du lieu that hoac moi truong production.

## Tong quan

| Thanh phan | Vai tro |
| --- | --- |
| `demo.sh` | Script dieu phoi demo: tan cong, quet, phuc hoi, backup |
| `manager-agent/` | Ung dung ProManager gia mao va ransomware simulator |
| `defender/` | Bo cong cu phat hien, giai ma va backup |
| `shop_data/` | Du lieu thuong mai dien tu mau dung lam sandbox |
| `backups/` | Cac ban backup `.tar.gz` duoc tao trong demo |

## Cau truc du an

```text
.
├── demo.sh
├── manager-agent/
│   ├── fake_manager.py          # GUI ProManager gia mao
│   ├── fake_installer.py        # Installer gia lap qua terminal
│   ├── fake_ransom.py           # Man hinh ransom note demo
│   └── ransomware_simulator.py  # Ma hoa/giai ma trong sandbox
├── defender/
│   ├── static_analyzer.py       # Quet tinh source/script dang nghi
│   ├── scanner.py               # Quet file da bi ma hoa/high entropy
│   ├── decryptor.py             # Giai ma file .encrypted bang .ransom_key
│   ├── backup_manager.py        # Tao/list/restore backup
│   └── rules/ransomware.yar     # YARA rules cho simulator
├── shop_data/
│   └── ...                      # Du lieu mau cua shop
└── backups/
    └── ...                      # Backup sinh ra khi demo
```

## Yeu cau

- Python 3.10+
- `cryptography`
- `yara-python` tuy chon, dung cho YARA scan trong `static_analyzer.py`
- `tkinter` neu muon chay giao dien GUI (`fake_manager.py`, `fake_ransom.py`)

Tren Ubuntu/Debian:

```bash
sudo apt install python3-tk
python3 -m pip install cryptography yara-python
```

Neu khong can YARA, co the chi cai:

```bash
python3 -m pip install cryptography
```

## Chay demo nhanh

```bash
bash demo.sh
```

Mac dinh, script chay day du cac buoc:

| Buoc | Noi dung |
| --- | --- |
| 1 | Backup du lieu trong `shop_data/` |
| 2 | Hien thi du lieu ban dau |
| 3 | Mo ung dung ProManager gia mao va kich hoat ma hoa trong sandbox |
| 4 | Hien thi ket qua sau tan cong |
| 5 | Phan tich tinh file tan cong |
| 6 | Quet `shop_data/` de tim dau hieu ransomware |
| 7 | Giai ma bang `.ransom_key` hoac restore tu backup |
| 8 | Tao backup moi sau phuc hoi |
| 9 | Hien thi ket qua cuoi |

## Cac che do chay

```bash
# Chay day du: attack + defense + recovery
bash demo.sh

# Chi chay phan tan cong
bash demo.sh --attack-only

# Chi chay phan phong thu va phuc hoi
bash demo.sh --defend-only

# Xem huong dan ngan
bash demo.sh --help
```

Luu y: `--attack-only` co the bien file plaintext trong `shop_data/` thanh file `.encrypted`. Hay chay `bash demo.sh --defend-only` hoac `python3 defender/decryptor.py shop_data` de phuc hoi sau khi demo.

## Chay tung cong cu

```bash
# Quet tinh file nghi ngo
python3 defender/static_analyzer.py manager-agent/fake_manager.py

# Quet du lieu sandbox
python3 defender/scanner.py shop_data

# Giai ma cac file .encrypted trong shop_data/
python3 defender/decryptor.py shop_data

# Tao backup
python3 defender/backup_manager.py backup

# Liet ke backup
python3 defender/backup_manager.py list

# Restore tu mot backup cu the
python3 defender/backup_manager.py restore backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

## Luong tan cong mo phong

1. Nguoi dung mo `manager-agent/fake_manager.py`.
2. Ung dung hien giao dien ProManager Suite gia mao va yeu cau API/license key.
3. Sau khi "activate", ung dung chuyen sang dashboard gia.
4. `RansomwareSimulator` ma hoa file trong `shop_data/` bang Fernet.
5. File goc bi thay bang file co duoi `.encrypted`.
6. Khoa giai ma duoc luu local trong `shop_data/.ransom_key`.
7. Man hinh ransom note demo duoc hien thi qua `fake_ransom.py`.

## Co che phong thu

| Cong cu | Cach phat hien |
| --- | --- |
| `static_analyzer.py` | YARA rules, chuoi nguy hiem, combo `cryptography` + `os.walk` + `os.remove` |
| `scanner.py` | Duoi file dang nghi (`.encrypted`, `.locked`, `.crypto`, `.crypt`, `.enc`), entropy cao, safety signature |
| `behavior_monitor.py` | Theo doi snapshot filesystem va phat hien file `.encrypted` moi hoac file goc bi xoa |
| `decryptor.py` | Doc `shop_data/.ransom_key` va khoi phuc file `.encrypted` |
| `backup_manager.py` | Tao, liet ke va restore backup `.tar.gz` |

Nguong entropy hien tai trong `scanner.py` la `5.5`. Simulator co safety marker `RANSOMWARE_SIMULATOR_DEMO_SAFE` de cac cong cu phong thu co the nhan dien day la mau demo.

## Du lieu va backup

- `shop_data/` la sandbox chua file mau nhu invoice, customer data, contract va cau hinh API.
- `demo.sh` tu tao backup truoc khi chay phan tan cong.
- `defender/backup_manager.py` tao archive trong `backups/`.
- Neu repo dang o trang thai co san file `.encrypted`, chay decryptor de khoi phuc plaintext:

```bash
python3 defender/decryptor.py shop_data
```

## Luu y an toan

- Chi dung cho muc dich hoc tap va trinh dien phong thu.
- Khong dua du lieu that vao `shop_data/`.
- Khong sua simulator de quet ngoai sandbox.
- Khong chia se hoac tai len mau da chinh sua theo huong co the gay hai.
- Sau moi lan demo, kiem tra lai `shop_data/` va `backups/` truoc khi commit.

## Trang thai test

Repo hien tai khong co test suite tu dong. Kiem tra co ban nen gom:

```bash
bash demo.sh --help
python3 defender/scanner.py shop_data

# Expected: phat hien CRITICAL va exit non-zero
python3 defender/static_analyzer.py manager-agent/ransomware_simulator.py
```
