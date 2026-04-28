import os
import sys
import math
import time
import threading
import subprocess
from datetime import datetime, timedelta

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from cryptography.fernet import Fernet, InvalidToken

_base = os.path.dirname(os.path.abspath(__file__))
_root = os.path.abspath(os.path.join(_base, '..'))
sys.path.insert(0, _base)
from backup_manager import BackupManager

# ── Theme ────────────────────────────────────────────────────────────
BG      = '#f1f5f9'
CARD    = '#ffffff'
SIDEBAR = '#0f172a'
SB2     = '#1e293b'
SB_ACT  = '#334155'
BORDER  = '#e2e8f0'
TEXT    = '#0f172a'
MUTED   = '#64748b'
GRN     = '#10b981'
GRN_BG  = '#dcfce7'
GRN_FG  = '#166534'
RED     = '#ef4444'
RED_BG  = '#fee2e2'
RED_FG  = '#991b1b'
AMB     = '#f59e0b'
AMB_BG  = '#fef3c7'
AMB_FG  = '#92400e'
ACCENT  = '#6366f1'
ACC_BG  = '#ede9fe'
ACC_FG  = '#4338ca'
BLU     = '#3b82f6'
BLU_BG  = '#dbeafe'
BLU_FG  = '#1d4ed8'

SF  = ('Segoe UI', 10)
SFB = ('Segoe UI', 10, 'bold')
SFS = ('Segoe UI', 9)
SFL = ('Segoe UI', 13, 'bold')
SFM = ('Segoe UI', 11, 'bold')
SFX = ('Segoe UI', 20, 'bold')

# ── IR Phases (ransomware-specific) ─────────────────────────────────
IR_PHASES = [
    ('preparation',    '1. Chuẩn bị',        '🛡'),
    ('identification', '2. Phát hiện',        '🔍'),
    ('containment',    '3. Cô lập',           '🔒'),
    ('eradication',    '4. Tiêu diệt',        '🗑'),
    ('recovery',       '5. Phục hồi',         '🔓'),
    ('lessons',        '6. Rút kinh nghiệm',  '📊'),
]

# ── Suspicious patterns ──────────────────────────────────────────────
_BAD_PROCS  = ['ProManagerSuite', 'fake_manager', 'fake_ransom', 'ransomware_simulator']
_BAD_NAMES  = {'promanagersuite', 'fake_manager', 'fakeinstaller', 'ransomware'}
_BAD_STR    = [b'RANSOMWARE_SIMULATOR_DEMO_SAFE', b'fernet.encrypt', b'Fernet.generate_key']
_SKIP_SCAN  = {'.encrypted', '.tar', '.gz', '.zip', '.db'}
_VICTIM_DIR = os.path.join(_root, 'shop_data')


# ── Helpers ──────────────────────────────────────────────────────────
def _entropy(path: str, sample: int = 65536) -> float:
    try:
        with open(path, 'rb') as fh:
            data = fh.read(sample)
        if not data:
            return 0.0
        freq = [0] * 256
        for b in data:
            freq[b] += 1
        n = len(data)
        return -sum((c / n) * math.log2(c / n) for c in freq if c)
    except (IOError, PermissionError):
        return 0.0


def _is_executable(path: str) -> bool:
    try:
        with open(path, 'rb') as fh:
            magic = fh.read(4)
        return magic[:2] == b'MZ' or magic[:4] == b'\x7fELF'
    except (IOError, PermissionError):
        return False


def _running_bad_procs() -> list:
    found = []
    for name in _BAD_PROCS:
        try:
            r = subprocess.run(['pgrep', '-f', name], capture_output=True, text=True)
            if r.returncode == 0 and r.stdout.strip():
                found.append(name)
        except FileNotFoundError:
            pass
    return found


def _count_encrypted(directory: str) -> int:
    try:
        return sum(1 for f in os.listdir(directory) if f.endswith('.encrypted'))
    except (FileNotFoundError, PermissionError):
        return 0


def analyze_file(path: str) -> list:
    findings = []
    name = os.path.basename(path).lower()
    ext  = os.path.splitext(name)[1]
    if ext in _SKIP_SCAN:
        return findings
    if any(bad in name for bad in _BAD_NAMES):
        findings.append({'severity': 'CRITICAL', 'reason': 'suspicious_name',
                         'detail': f'Tên khớp pattern ransomware: {os.path.basename(path)}'})
    is_exe = ext in ('.exe', '.elf', '.bin') or _is_executable(path)
    if is_exe:
        ent = _entropy(path)
        if ent > 7.2:
            findings.append({'severity': 'HIGH', 'reason': 'packed_executable',
                             'detail': f'Entropy cao ({ent:.2f} bits) — có thể bị đóng gói'})
        elif ent > 6.5:
            findings.append({'severity': 'MEDIUM', 'reason': 'suspicious_executable',
                             'detail': f'Entropy bất thường ({ent:.2f} bits)'})
    if ext in ('.py', '.sh', '.bat', '.ps1') and not is_exe:
        try:
            with open(path, 'rb') as fh:
                content = fh.read(1 << 20)
            for sig in _BAD_STR:
                if sig in content:
                    findings.append({'severity': 'CRITICAL', 'reason': 'dangerous_string',
                                     'detail': f'Chuỗi nguy hiểm: {sig.decode(errors="replace")}'})
                    break
        except (IOError, PermissionError):
            pass
    return findings


def scan_directory(directory: str, callback=None) -> list:
    results = []
    try:
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for fname in files:
                path = os.path.join(root, fname)
                findings = analyze_file(path)
                for f in findings:
                    f['file'] = path
                results.extend(findings)
                if callback:
                    callback(path)
    except PermissionError:
        pass
    return results


# ── Main App ─────────────────────────────────────────────────────────
class DefenderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('DefenderPro — Ransomware Incident Response')
        if sys.platform == 'win32':
            self.root.state('zoomed')
        else:
            self.root.attributes('-zoomed', True)
        self.root.configure(bg=BG)

        # IR phase status
        self._phase = {k: 'pending' for k, _, _ in IR_PHASES}
        self._phase['preparation'] = 'done'

        # State
        self._active_panel = None
        self._log_lines    = []
        self._scan_results = []
        self._scan_count   = 0
        self._threat_count = 0
        self._encrypted_count    = tk.IntVar(value=0)
        self._bad_procs_var      = tk.StringVar(value='Không có')
        self._ransom_key_present = False
        self._incident_actions   = []
        self._under_attack       = False   # flag: đã kích hoạt auto-respond chưa
        self._attack_banner_var  = tk.StringVar(value='')

        # Backup vars
        self._backup_on  = tk.BooleanVar(value=True)
        self._interval_h = tk.IntVar(value=6)
        self._src_dir    = tk.StringVar(value=_VICTIM_DIR)
        self._bak_dir    = tk.StringVar(value=os.path.join(_root, 'backups'))
        self._scan_dir   = tk.StringVar(value=_root)
        self._next_backup = None
        self._bk_job     = None

        self._build_layout()
        self._show('dashboard')
        self._reschedule()
        self._tick()
        threading.Thread(target=self._watch_loop, daemon=True).start()

    # ── Layout ──────────────────────────────────────────────────────
    def _build_layout(self):
        sb = tk.Frame(self.root, bg=SIDEBAR, width=230)
        sb.pack(side='left', fill='y')
        sb.pack_propagate(False)
        self._sb = sb

        tk.Label(sb, text='🛡', font=('Segoe UI', 26), bg=SIDEBAR, fg='#fff').pack(pady=(20, 0))
        tk.Label(sb, text='DefenderPro', font=('Segoe UI', 13, 'bold'), bg=SIDEBAR, fg='#fff').pack()
        tk.Label(sb, text='Ransomware IR System', font=('Segoe UI', 8), bg=SIDEBAR, fg='#94a3b8').pack(pady=(2, 14))
        tk.Frame(sb, bg=SB2, height=1).pack(fill='x')

        self._nav_btns = {}
        nav_items = [
            ('🏠', 'Dashboard',       'dashboard'),
            ('🔍', 'Phát hiện (HIDS)', 'detect'),
            ('🔒', 'Cô lập & Tiêu diệt', 'contain'),
            ('🔓', 'Phục hồi',         'recover'),
            ('📊', 'Báo cáo sự cố',    'report'),
            ('📋', 'Log',              'log'),
        ]
        for icon, label, key in nav_items:
            btn = tk.Button(sb, text=f'  {icon}  {label}',
                            font=('Segoe UI', 10), relief='flat', bd=0,
                            bg=SIDEBAR, fg='#cbd5e1', cursor='hand2',
                            anchor='w', padx=16, pady=10,
                            activebackground=SB_ACT, activeforeground='#fff',
                            command=lambda k=key: self._show(k))
            btn.pack(fill='x')
            self._nav_btns[key] = btn

        tk.Frame(sb, bg=SIDEBAR).pack(fill='both', expand=True)
        tk.Frame(sb, bg=SB2, height=1).pack(fill='x')
        tk.Label(sb, text='⚠  DEMO ONLY — Academic', font=('Segoe UI', 8, 'bold'),
                 bg=SIDEBAR, fg='#f87171', pady=8).pack()

        tk.Frame(self.root, bg=BORDER, width=1).pack(side='left', fill='y')
        self._content = tk.Frame(self.root, bg=BG)
        self._content.pack(side='left', fill='both', expand=True)

        sb_bar = tk.Frame(self.root, bg=SB2, height=28)
        sb_bar.pack(side='bottom', fill='x')
        self._status_var = tk.StringVar(value='Sẵn sàng')
        tk.Label(sb_bar, textvariable=self._status_var, font=('Segoe UI', 9),
                 bg=SB2, fg='#94a3b8', padx=14).pack(side='left')
        self._clock_var = tk.StringVar()
        tk.Label(sb_bar, textvariable=self._clock_var, font=('Segoe UI', 9),
                 bg=SB2, fg='#64748b', padx=14).pack(side='right')

    def _clear_content(self):
        for w in self._content.winfo_children():
            w.destroy()

    def _show(self, key: str):
        if self._active_panel == key:
            return
        self._active_panel = key
        for k, btn in self._nav_btns.items():
            active = (k == key)
            btn.config(bg=SB_ACT if active else SIDEBAR,
                       fg='#fff' if active else '#cbd5e1',
                       font=('Segoe UI', 10, 'bold') if active else ('Segoe UI', 10))
        self._clear_content()
        getattr(self, f'_panel_{key}')()

    # ── UI helpers ───────────────────────────────────────────────────
    def _topbar(self, title: str, subtitle: str = ''):
        bar = tk.Frame(self._content, bg=CARD, padx=24, pady=14)
        bar.pack(fill='x')
        tk.Label(bar, text=title, font=SFL, bg=CARD, fg=TEXT).pack(anchor='w')
        if subtitle:
            tk.Label(bar, text=subtitle, font=SFS, bg=CARD, fg=MUTED).pack(anchor='w')
        tk.Frame(self._content, bg=BORDER, height=1).pack(fill='x')

    def _card(self, parent, **kw) -> tk.Frame:
        wrap = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        wrap.pack(**kw)
        inner = tk.Frame(wrap, bg=CARD, padx=18, pady=14)
        inner.pack(fill='both', expand=True)
        return inner

    def _stat_card(self, parent, icon, value_var, label, fg, bg_color):
        outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        outer.pack(side='left', fill='both', expand=True, padx=(0, 10))
        c = tk.Frame(outer, bg=CARD, padx=14, pady=12)
        c.pack(fill='both', expand=True)
        tk.Label(c, text=icon, font=('Segoe UI', 18), bg=CARD, fg=fg).pack(anchor='w')
        if isinstance(value_var, tk.Variable):
            tk.Label(c, textvariable=value_var, font=('Segoe UI', 15, 'bold'), bg=CARD, fg=fg).pack(anchor='w')
        else:
            tk.Label(c, text=value_var, font=('Segoe UI', 15, 'bold'), bg=CARD, fg=fg).pack(anchor='w')
        tk.Label(c, text=label, font=SFS, bg=CARD, fg=MUTED).pack(anchor='w')

    # ── Attack banner (top of content) ──────────────────────────────
    def _show_attack_banner(self):
        if not hasattr(self, '_attack_banner_frame'):
            return
        for w in self._attack_banner_frame.winfo_children():
            w.destroy()
        if self._under_attack:
            box = tk.Frame(self._attack_banner_frame, bg='#dc2626', padx=16, pady=10)
            box.pack(fill='x')
            tk.Label(box, text='🔴  PHÁT HIỆN TẤN CÔNG RANSOMWARE — Đang cô lập và bảo vệ...',
                     font=('Segoe UI', 11, 'bold'), bg='#dc2626', fg='#ffffff').pack(side='left')
            tk.Button(box, text='Xem chi tiết →', font=('Segoe UI', 10, 'bold'),
                      bg='#ffffff', fg='#dc2626', relief='flat', bd=0, padx=12, pady=4,
                      cursor='hand2', command=lambda: self._show('contain')).pack(side='right')

    # ── 1. DASHBOARD ─────────────────────────────────────────────────
    def _panel_dashboard(self):
        self._topbar('Dashboard', 'Quy trình ứng phó sự cố ransomware (NIST IR Framework)')
        # Attack banner slot (shown when under attack)
        self._attack_banner_frame = tk.Frame(self._content, bg=BG)
        self._attack_banner_frame.pack(fill='x')
        self._show_attack_banner()

        scroll_canvas = tk.Canvas(self._content, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(self._content, orient='vertical', command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        scroll_canvas.pack(fill='both', expand=True)
        body = tk.Frame(scroll_canvas, bg=BG, padx=22, pady=16)
        win = scroll_canvas.create_window((0, 0), window=body, anchor='nw')
        body.bind('<Configure>', lambda e: scroll_canvas.configure(
            scrollregion=scroll_canvas.bbox('all')))
        scroll_canvas.bind('<Configure>', lambda e: scroll_canvas.itemconfig(win, width=e.width))

        # IR Phase tracker
        phase_card = self._card(body, fill='x', pady=(0, 16))
        tk.Label(phase_card, text='CÁC GIAI ĐOẠN ỨNG PHÓ SỰ CỐ', font=('Segoe UI', 9, 'bold'),
                 bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 12))
        self._phase_labels = {}
        prow = tk.Frame(phase_card, bg=CARD)
        prow.pack(fill='x')
        for key, label, icon in IR_PHASES:
            col = tk.Frame(prow, bg=CARD)
            col.pack(side='left', fill='both', expand=True, padx=(0, 6))
            status = self._phase[key]
            fg  = GRN if status == 'done' else AMB if status == 'active' else MUTED
            bg2 = GRN_BG if status == 'done' else AMB_BG if status == 'active' else '#f8fafc'
            box = tk.Frame(col, bg=bg2, padx=8, pady=10)
            box.pack(fill='x')
            tk.Label(box, text=icon, font=('Segoe UI', 16), bg=bg2, fg=fg).pack()
            tk.Label(box, text=label, font=('Segoe UI', 8, 'bold'), bg=bg2, fg=fg,
                     wraplength=90, justify='center').pack()
            mark = '✓' if status == 'done' else '●' if status == 'active' else '○'
            lbl = tk.Label(box, text=mark, font=('Segoe UI', 11, 'bold'), bg=bg2, fg=fg)
            lbl.pack()
            self._phase_labels[key] = (box, lbl, col)

        # Real-time threat status
        srow = tk.Frame(body, bg=BG)
        srow.pack(fill='x', pady=(0, 14))
        self._dash_enc_var    = tk.StringVar(value=str(_count_encrypted(_VICTIM_DIR)))
        self._dash_proc_var   = tk.StringVar(value='Không có')
        self._dash_key_var    = tk.StringVar(value='Không có')
        self._dash_status_var = tk.StringVar(value='Đang giám sát...')

        enc_cnt = _count_encrypted(_VICTIM_DIR)
        s_fg = RED if enc_cnt > 0 else GRN
        self._stat_card(srow, '📁', self._dash_enc_var, 'File bị mã hóa', s_fg, RED_BG if enc_cnt else GRN_BG)
        self._stat_card(srow, '⚙',  self._dash_proc_var, 'Tiến trình độc hại', RED, RED_BG)
        self._stat_card(srow, '🔑', self._dash_key_var,  'Khóa giải mã (.ransom_key)', AMB, AMB_BG)
        self._stat_card(srow, '🛡', self._dash_status_var, 'Trạng thái hệ thống', ACCENT, ACC_BG)

        # Quick action buttons
        qa_card = self._card(body, fill='x', pady=(0, 14))
        tk.Label(qa_card, text='HÀNH ĐỘNG NHANH', font=('Segoe UI', 9, 'bold'),
                 bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 10))
        brow = tk.Frame(qa_card, bg=CARD)
        brow.pack(fill='x')
        for txt, cmd, bg, fg in [
            ('🔍  Phát hiện ngay', lambda: self._show('detect'),  ACCENT, '#fff'),
            ('🔒  Cô lập ngay',    lambda: self._show('contain'), RED,    '#fff'),
            ('🔓  Phục hồi',       lambda: self._show('recover'), GRN,    '#fff'),
            ('📊  Xem báo cáo',    lambda: self._show('report'),  SB2,    '#fff'),
        ]:
            tk.Button(brow, text=txt, font=SFB, bg=bg, fg=fg,
                      relief='flat', bd=0, padx=16, pady=8, cursor='hand2',
                      activebackground=SIDEBAR, activeforeground='#fff',
                      command=cmd).pack(side='left', padx=(0, 8))

        # Ransomware detection guide
        guide_card = self._card(body, fill='x', pady=(0, 14))
        tk.Label(guide_card, text='DẤU HIỆU NHẬN BIẾT RANSOMWARE (HIDS — Nhóm 4)',
                 font=('Segoe UI', 9, 'bold'), bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 10))
        signs = [
            ('🔴', 'Disk I/O tăng vọt',        'Nhiều file bị đọc/ghi liên tục trong thời gian ngắn'),
            ('🔴', 'Hàng loạt file đổi đuôi',  'File .txt → .txt.encrypted, .csv → .csv.encrypted'),
            ('🔴', 'Xuất hiện file khóa',       '.ransom_key lưu khóa mã hóa trong thư mục nạn nhân'),
            ('🟠', 'Tiến trình lạ chiếm CPU',   'Executable không rõ nguồn gốc đang chạy nền'),
            ('🟠', 'GUI yêu cầu tiền chuộc',    'Màn hình ransom note xuất hiện, yêu cầu thanh toán'),
        ]
        for dot, title, desc in signs:
            row = tk.Frame(guide_card, bg=CARD)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=dot, font=SF, bg=CARD).pack(side='left')
            tk.Label(row, text=f'  {title}:', font=SFB, bg=CARD, fg=TEXT).pack(side='left')
            tk.Label(row, text=f'  {desc}', font=SFS, bg=CARD, fg=MUTED).pack(side='left')

        # Recent log
        log_card = self._card(body, fill='x')
        tk.Label(log_card, text='HOẠT ĐỘNG GẦN ĐÂY', font=('Segoe UI', 9, 'bold'),
                 bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 8))
        self._dash_log_frame = tk.Frame(log_card, bg=CARD)
        self._dash_log_frame.pack(fill='x')
        self._refresh_dash_log()

    def _refresh_dash_log(self):
        if not hasattr(self, '_dash_log_frame'):
            return
        for w in self._dash_log_frame.winfo_children():
            w.destroy()
        for line in reversed(self._log_lines[-6:]):
            clr = RED if any(x in line for x in ['[NGUY HIỂM]', '[CẢNH BÁO]', '[LỖI]']) else \
                  GRN if any(x in line for x in ['[OK]', '[BACKUP]', '[PHỤC HỒI]']) else MUTED
            tk.Label(self._dash_log_frame, text=line, font=('Courier New', 9),
                     bg=CARD, fg=clr, anchor='w').pack(fill='x')

    def _update_dashboard_stats(self):
        if self._active_panel != 'dashboard':
            return
        enc = _count_encrypted(_VICTIM_DIR)
        procs = _running_bad_procs()
        key_exists = os.path.exists(os.path.join(_VICTIM_DIR, '.ransom_key'))
        if hasattr(self, '_dash_enc_var'):
            self._dash_enc_var.set(str(enc))
            self._dash_proc_var.set(', '.join(procs) if procs else 'Không có')
            self._dash_key_var.set('Tìm thấy ✓' if key_exists else 'Không có')
            if enc > 0 or procs:
                self._dash_status_var.set(f'⚠  PHÁT HIỆN MỐI ĐE DOẠ')
            else:
                self._dash_status_var.set('Đang bảo vệ ✓')
        self._update_phase_display()

    def _update_phase_display(self):
        if not hasattr(self, '_phase_labels'):
            return
        for key, label, icon in IR_PHASES:
            if key not in self._phase_labels:
                continue
            box, lbl, _ = self._phase_labels[key]
            status = self._phase[key]
            fg  = GRN if status == 'done' else AMB if status == 'active' else MUTED
            bg2 = GRN_BG if status == 'done' else AMB_BG if status == 'active' else '#f8fafc'
            mark = '✓' if status == 'done' else '●' if status == 'active' else '○'
            box.config(bg=bg2)
            lbl.config(text=mark, fg=fg, bg=bg2)
            for child in box.winfo_children():
                try:
                    child.config(bg=bg2, fg=fg)
                except Exception:
                    pass

    def _advance_phase(self, key: str):
        self._phase[key] = 'done'
        self.root.after(0, self._update_phase_display)

    # ── 2. PHÁT HIỆN (HIDS — Nhóm 4) ────────────────────────────────
    def _panel_detect(self):
        self._topbar('Phát hiện — HIDS', 'Giám sát tiến trình, file mã hóa, entropy và chữ ký nguy hiểm')
        self._phase['identification'] = 'active'
        body = tk.Frame(self._content, bg=BG, padx=22, pady=14)
        body.pack(fill='both', expand=True)

        # Real-time indicators
        ri = self._card(body, fill='x', pady=(0, 12))
        tk.Label(ri, text='CHỈ SỐ THỜI GIAN THỰC', font=('Segoe UI', 9, 'bold'),
                 bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 10))
        irow = tk.Frame(ri, bg=CARD)
        irow.pack(fill='x')

        self._det_enc_var  = tk.StringVar()
        self._det_proc_var = tk.StringVar()
        self._det_key_var  = tk.StringVar()
        self._refresh_detect_indicators()

        for var, label, fg in [
            (self._det_enc_var,  'File .encrypted', RED),
            (self._det_proc_var, 'Tiến trình độc hại', RED),
            (self._det_key_var,  'Ransom key', AMB),
        ]:
            box = tk.Frame(irow, bg=RED_BG if fg == RED else AMB_BG, padx=14, pady=10)
            box.pack(side='left', fill='both', expand=True, padx=(0, 8))
            bg2 = RED_BG if fg == RED else AMB_BG
            tk.Label(box, textvariable=var, font=('Segoe UI', 14, 'bold'), bg=bg2, fg=fg).pack()
            tk.Label(box, text=label, font=SFS, bg=bg2, fg=fg).pack()

        # File scan
        sc = self._card(body, fill='x', pady=(0, 12))
        tk.Label(sc, text='QUÉT FILE — Chữ ký & Entropy (Signature-based + Anomaly-based)',
                 font=('Segoe UI', 9, 'bold'), bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 8))
        drow = tk.Frame(sc, bg=CARD)
        drow.pack(fill='x', pady=(0, 8))
        dir_e = tk.Entry(drow, textvariable=self._scan_dir, font=SF, bg='#f8faff', fg=TEXT,
                         relief='flat', highlightthickness=1,
                         highlightbackground=BORDER, highlightcolor=ACCENT)
        dir_e.pack(side='left', fill='x', expand=True, ipady=6, padx=(0, 8))
        tk.Button(drow, text='Chọn', font=SFS, bg=BG, fg=ACCENT, relief='flat', bd=0,
                  padx=10, pady=5, cursor='hand2',
                  command=lambda: self._pick_dir(self._scan_dir)).pack(side='left')
        ctrl = tk.Frame(sc, bg=CARD)
        ctrl.pack(fill='x')
        self._scan_btn = tk.Button(ctrl, text='🔍  Bắt đầu quét', font=SFB,
                                    bg=ACCENT, fg='#fff', relief='flat', bd=0,
                                    padx=18, pady=8, cursor='hand2',
                                    command=self._start_scan)
        self._scan_btn.pack(side='left')
        self._scan_pbar = ttk.Progressbar(ctrl, mode='indeterminate', length=200)
        self._scan_status = tk.Label(ctrl, text='', font=SFS, bg=CARD, fg=MUTED)
        self._scan_status.pack(side='left', padx=12)

        # Results treeview
        rc = self._card(body, fill='both', expand=True)
        hdr = tk.Frame(rc, bg=CARD)
        hdr.pack(fill='x', pady=(0, 8))
        tk.Label(hdr, text='KẾT QUẢ', font=('Segoe UI', 9, 'bold'), bg=CARD, fg=MUTED).pack(side='left')
        self._det_summary = tk.Label(hdr, text='', font=SFS, bg=CARD, fg=MUTED)
        self._det_summary.pack(side='right')
        cols = ('severity', 'reason', 'file', 'detail')
        style = ttk.Style()
        style.configure('Det.Treeview', rowheight=26, font=('Segoe UI', 9),
                         background=CARD, fieldbackground=CARD, foreground=TEXT)
        style.configure('Det.Treeview.Heading', font=('Segoe UI', 9, 'bold'), background=BG)
        style.map('Det.Treeview', background=[('selected', ACC_BG)])
        self._tree = ttk.Treeview(rc, columns=cols, show='headings',
                                   style='Det.Treeview', height=12)
        for col, w, lbl in [('severity',90,'Mức độ'),('reason',130,'Loại'),
                              ('file',280,'File'),('detail',380,'Chi tiết')]:
            self._tree.heading(col, text=lbl)
            self._tree.column(col, width=w, minwidth=60)
        self._tree.tag_configure('CRITICAL', foreground=RED_FG,  background=RED_BG)
        self._tree.tag_configure('HIGH',     foreground=AMB_FG,  background=AMB_BG)
        self._tree.tag_configure('MEDIUM',   foreground=ACC_FG,  background=ACC_BG)
        vsb = ttk.Scrollbar(rc, orient='vertical', command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

    def _refresh_detect_indicators(self):
        enc   = _count_encrypted(_VICTIM_DIR)
        procs = _running_bad_procs()
        key   = os.path.exists(os.path.join(_VICTIM_DIR, '.ransom_key'))
        if hasattr(self, '_det_enc_var'):
            self._det_enc_var.set(f'{enc} file')
            self._det_proc_var.set(', '.join(procs) if procs else 'Không có')
            self._det_key_var.set('Tìm thấy' if key else 'Không có')

    def _pick_dir(self, var: tk.StringVar):
        d = filedialog.askdirectory(initialdir=var.get())
        if d:
            var.set(d)

    def _start_scan(self):
        d = self._scan_dir.get()
        if not os.path.isdir(d):
            messagebox.showerror('Lỗi', f'Thư mục không tồn tại:\n{d}')
            return
        self._scan_btn.config(state='disabled', text='Đang quét...')
        self._scan_pbar.pack(side='left')
        self._scan_pbar.start(12)
        for row in self._tree.get_children():
            self._tree.delete(row)
        threading.Thread(target=self._run_scan, args=(d,), daemon=True).start()

    def _run_scan(self, directory: str):
        count = [0]
        def cb(path):
            count[0] += 1
            self.root.after(0, lambda: self._scan_status.config(
                text=f'Quét: {os.path.basename(path)[:50]}'))
        results = scan_directory(directory, callback=cb)
        self.root.after(0, lambda: self._finish_scan(results, count[0]))

    def _finish_scan(self, results: list, total: int):
        self._scan_pbar.stop()
        self._scan_pbar.pack_forget()
        self._scan_btn.config(state='normal', text='🔍  Bắt đầu quét')
        self._scan_results = results
        self._scan_count   = total
        self._threat_count = len(results)
        for f in results:
            sev = f.get('severity', 'MEDIUM')
            short = '...' + f['file'][-42:] if len(f['file']) > 45 else f['file']
            self._tree.insert('', 'end',
                values=(sev, f.get('reason', ''), short, f.get('detail', '')),
                tags=(sev,))
        txt = f'⚠  {len(results)} mối đe doạ' if results else '✓  Sạch'
        self._det_summary.config(text=f'{txt}  |  {total} file', fg=RED if results else GRN)
        self._scan_status.config(text='Hoàn tất', fg=GRN)
        lvl = 'CẢNH BÁO' if results else 'OK'
        self._log(f'[{lvl}] Quét xong — {len(results)} mối đe doạ / {total} file')
        self._incident_actions.append(f'Quét phát hiện {len(results)} mối đe doạ trong {total} file')
        if results:
            self._advance_phase('identification')
            crit = [r for r in results if r.get('severity') == 'CRITICAL']
            if crit:
                self._alert(
                    f'Phát hiện {len(crit)} mối đe doạ NGHIÊM TRỌNG!\n\n'
                    f'File: {os.path.basename(crit[0]["file"])}\n'
                    f'Lý do: {crit[0].get("detail","")}\n\n'
                    f'→ Chuyển sang panel Cô lập ngay!'
                )

    # ── 3. CÔ LẬP & TIÊU DIỆT ───────────────────────────────────────
    def _panel_contain(self):
        self._topbar('Cô lập & Tiêu diệt', 'Ngăn chặn lây lan — xóa bỏ mã độc (Containment + Eradication)')
        body = tk.Frame(self._content, bg=BG, padx=22, pady=14)
        body.pack(fill='both', expand=True)

        # WARNING banner
        warn_box = tk.Frame(body, bg=RED_BG, padx=16, pady=12)
        warn_box.pack(fill='x', pady=(0, 14))
        tk.Label(warn_box, text='⚠  TUYỆT ĐỐI KHÔNG TẮT NGUỒN MÁY CHỦ',
                 font=('Segoe UI', 11, 'bold'), bg=RED_BG, fg=RED_FG).pack(anchor='w')
        tk.Label(warn_box, text='Tắt nguồn sẽ làm mất khóa giải mã đang lưu trong RAM '
                                 'và xóa dấu vết mã độc, gây khó khăn cho điều tra (Forensics).',
                 font=SFS, bg=RED_BG, fg=RED_FG, wraplength=700, justify='left').pack(anchor='w')

        # Step 1: Bật chế độ bảo trì
        s1 = self._card(body, fill='x', pady=(0, 12))
        tk.Label(s1, text='BƯỚC 1 — Ngắt giao dịch (Maintenance Mode)',
                 font=('Segoe UI', 10, 'bold'), bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 6))
        tk.Label(s1, text='Dừng mọi giao dịch mới, ngăn mã độc tiếp tục thu thập dữ liệu khách hàng.',
                 font=SFS, bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 8))
        self._maint_var = tk.StringVar(value='⚪  Chưa kích hoạt')
        self._maint_lbl = tk.Label(s1, textvariable=self._maint_var,
                                    font=SFB, bg=CARD, fg=MUTED)
        self._maint_lbl.pack(anchor='w', pady=(0, 8))
        tk.Button(s1, text='🔴  Bật Maintenance Mode', font=SFB,
                  bg=AMB, fg='#fff', relief='flat', bd=0, padx=16, pady=8,
                  cursor='hand2', command=self._enable_maintenance).pack(anchor='w')

        # Step 2: Kill processes
        s2 = self._card(body, fill='x', pady=(0, 12))
        tk.Label(s2, text='BƯỚC 2 — Dừng tiến trình độc hại',
                 font=('Segoe UI', 10, 'bold'), bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 6))
        tk.Label(s2, text='Buộc dừng ProManagerSuite và các tiến trình liên quan đang chạy.',
                 font=SFS, bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 8))
        self._proc_status = tk.Label(s2, text='', font=SFS, bg=CARD, fg=MUTED)
        self._proc_status.pack(anchor='w', pady=(0, 6))
        self._check_procs_display()
        tk.Button(s2, text='⛔  Dừng tất cả tiến trình độc hại', font=SFB,
                  bg=RED, fg='#fff', relief='flat', bd=0, padx=16, pady=8,
                  cursor='hand2', command=self._kill_bad_procs).pack(anchor='w')

        # Step 3: Quarantine malware
        s3 = self._card(body, fill='x', pady=(0, 12))
        tk.Label(s3, text='BƯỚC 3 — Cô lập file mã độc (Eradication)',
                 font=('Segoe UI', 10, 'bold'), bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 6))
        tk.Label(s3, text='Di chuyển ProManagerSuite.exe sang thư mục quarantine để tiêu diệt.',
                 font=SFS, bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 8))
        self._quar_status = tk.Label(s3, text='', font=SFS, bg=CARD, fg=MUTED)
        self._quar_status.pack(anchor='w', pady=(0, 6))
        btn_row = tk.Frame(s3, bg=CARD)
        btn_row.pack(anchor='w')
        tk.Button(btn_row, text='🗑  Quarantine ProManagerSuite.exe', font=SFB,
                  bg=RED, fg='#fff', relief='flat', bd=0, padx=16, pady=8,
                  cursor='hand2', command=self._quarantine_exe).pack(side='left', padx=(0, 8))
        tk.Button(btn_row, text='📂  Mở thư mục quarantine', font=SF,
                  bg=BG, fg=ACCENT, relief='flat', bd=0, padx=12, pady=8,
                  cursor='hand2', command=self._open_quarantine_dir).pack(side='left')

        # Step 4: Network isolation note
        s4 = self._card(body, fill='x')
        tk.Label(s4, text='BƯỚC 4 — Cô lập mạng (Ghi chú thực tế)',
                 font=('Segoe UI', 10, 'bold'), bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 6))
        notes = [
            '• Rút cáp mạng vật lý hoặc ngắt kết nối vSwitch của máy chủ bị nhiễm.',
            '• Mục đích: Chặn Ransomware gửi dữ liệu khách hàng ra ngoài (tống tiền kép).',
            '• Trong môi trường demo này: mô phỏng bằng cách tạo file NETWORK_ISOLATED.flag.',
        ]
        for note in notes:
            tk.Label(s4, text=note, font=SFS, bg=CARD, fg=MUTED, anchor='w').pack(fill='x')
        tk.Button(s4, text='🌐  Mô phỏng ngắt mạng', font=SFB,
                  bg=BLU, fg='#fff', relief='flat', bd=0, padx=16, pady=8,
                  cursor='hand2', command=self._simulate_network_isolate).pack(anchor='w', pady=(10, 0))

    def _check_procs_display(self):
        procs = _running_bad_procs()
        if procs:
            self._proc_status.config(
                text=f'⚠  Đang chạy: {", ".join(procs)}', fg=RED)
        else:
            self._proc_status.config(text='✓  Không có tiến trình độc hại nào đang chạy.', fg=GRN)

    def _enable_maintenance(self):
        flag = os.path.join(_root, 'MAINTENANCE.flag')
        with open(flag, 'w') as fh:
            fh.write(f'Maintenance mode enabled at {datetime.now()}\n')
        self._maint_var.set('🔴  Đang bảo trì — Giao dịch đã ngưng')
        self._maint_lbl.config(fg=RED)
        self._log('[OK] Bật Maintenance Mode — giao dịch đã ngưng')
        self._incident_actions.append('Bật Maintenance Mode — ngăn giao dịch mới')

    def _kill_bad_procs(self):
        killed = []
        for name in _BAD_PROCS:
            try:
                r = subprocess.run(['pkill', '-f', name], capture_output=True)
                if r.returncode == 0:
                    killed.append(name)
            except FileNotFoundError:
                pass
        if killed:
            msg = f'Đã dừng: {", ".join(killed)}'
            self._log(f'[OK] {msg}')
            self._incident_actions.append(f'Dừng tiến trình: {", ".join(killed)}')
            messagebox.showinfo('Thành công', msg)
        else:
            messagebox.showinfo('Thông báo', 'Không tìm thấy tiến trình độc hại nào đang chạy.')
        self._check_procs_display()
        self._advance_phase('containment')

    def _quarantine_exe(self):
        qdir = os.path.join(_root, 'quarantine')
        os.makedirs(qdir, exist_ok=True)
        exe   = os.path.join(_root, 'manager-agent', 'ProManagerSuite.exe')
        dest  = os.path.join(qdir, f'ProManagerSuite.exe.quarantine_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        if not os.path.exists(exe):
            messagebox.showwarning('Không tìm thấy',
                                   f'Không tìm thấy file exe tại:\n{exe}')
            return
        if not messagebox.askyesno('Xác nhận',
                f'Di chuyển ProManagerSuite.exe sang quarantine?\n\n{exe}\n→ {dest}'):
            return
        import shutil
        shutil.move(exe, dest)
        self._log(f'[OK] Quarantine: ProManagerSuite.exe → {os.path.basename(dest)}')
        self._incident_actions.append('Quarantine ProManagerSuite.exe')
        self._quar_status.config(text=f'✓  Đã quarantine: {os.path.basename(dest)}', fg=GRN)
        self._advance_phase('eradication')

    def _open_quarantine_dir(self):
        qdir = os.path.join(_root, 'quarantine')
        os.makedirs(qdir, exist_ok=True)
        try:
            subprocess.Popen(['xdg-open', qdir])
        except Exception:
            messagebox.showinfo('Quarantine', f'Thư mục:\n{qdir}')

    def _simulate_network_isolate(self):
        flag = os.path.join(_root, 'NETWORK_ISOLATED.flag')
        with open(flag, 'w') as fh:
            fh.write(f'Network isolated at {datetime.now()}\n')
        self._log('[OK] Mô phỏng ngắt mạng — NETWORK_ISOLATED.flag đã tạo')
        self._incident_actions.append('Mô phỏng cô lập mạng')
        messagebox.showinfo('Cô lập mạng',
                            '✓  Đã tạo NETWORK_ISOLATED.flag\n\n'
                            'Trong thực tế: rút cáp mạng hoặc\nngắt vSwitch của máy chủ bị nhiễm.')

    # ── 4. PHỤC HỒI ─────────────────────────────────────────────────
    def _panel_recover(self):
        self._topbar('Phục hồi', 'Giải mã dữ liệu và khôi phục từ backup sạch (Recovery)')
        body = tk.Frame(self._content, bg=BG, padx=22, pady=14)
        body.pack(fill='both', expand=True)

        # Decrypt
        dc = self._card(body, fill='x', pady=(0, 12))
        tk.Label(dc, text='PHƯƠNG ÁN 1 — Giải mã bằng .ransom_key',
                 font=('Segoe UI', 10, 'bold'), bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 4))
        tk.Label(dc,
                 text='Dùng khi tìm thấy file .ransom_key trong thư mục bị mã hóa. '
                      'Trong thực tế ransomware dùng RSA, giải mã gần như bất khả — '
                      'demo này dùng Fernet (symmetric) nên có thể giải mã trực tiếp.',
                 font=SFS, bg=CARD, fg=MUTED, wraplength=700, justify='left').pack(anchor='w', pady=(0, 10))

        dr = tk.Frame(dc, bg=CARD)
        dr.pack(fill='x', pady=(0, 8))
        self._dec_dir = tk.StringVar(value=_VICTIM_DIR)
        e = tk.Entry(dr, textvariable=self._dec_dir, font=SF, bg='#f8faff', fg=TEXT,
                     relief='flat', highlightthickness=1, highlightbackground=BORDER, highlightcolor=GRN)
        e.pack(side='left', fill='x', expand=True, ipady=6, padx=(0, 8))
        tk.Button(dr, text='Chọn', font=SFS, bg=BG, fg=GRN, relief='flat', bd=0,
                  padx=10, pady=5, cursor='hand2',
                  command=lambda: self._pick_dir(self._dec_dir)).pack(side='left')

        btn_row = tk.Frame(dc, bg=CARD)
        btn_row.pack(fill='x')
        tk.Button(btn_row, text='🔓  Giải mã ngay', font=SFB,
                  bg=GRN, fg='#fff', relief='flat', bd=0, padx=16, pady=8,
                  cursor='hand2', command=self._run_decrypt).pack(side='left', padx=(0, 10))
        self._dec_status = tk.Label(btn_row, text='', font=SFS, bg=CARD, fg=MUTED)
        self._dec_status.pack(side='left')

        # Backup config
        bc = self._card(body, fill='x', pady=(0, 12))
        tk.Label(bc, text='PHƯƠNG ÁN 2 — Restore từ backup sạch',
                 font=('Segoe UI', 10, 'bold'), bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 4))
        tk.Label(bc, text='Dùng khi không có .ransom_key hoặc khóa sai. '
                           'Đảm bảo backup được lưu độc lập và không bị mã độc chạm tới.',
                 font=SFS, bg=CARD, fg=MUTED, wraplength=700, justify='left').pack(anchor='w', pady=(0, 10))

        def dir_row(lbl, var):
            r = tk.Frame(bc, bg=CARD)
            r.pack(fill='x', pady=(0, 6))
            tk.Label(r, text=lbl, font=SFB, bg=CARD, fg=TEXT, width=16, anchor='w').pack(side='left')
            tk.Entry(r, textvariable=var, font=SF, bg='#f8faff', fg=TEXT,
                     relief='flat', highlightthickness=1,
                     highlightbackground=BORDER, highlightcolor=ACCENT
                     ).pack(side='left', fill='x', expand=True, ipady=6, padx=(0, 8))
            tk.Button(r, text='Chọn', font=SFS, bg=BG, fg=ACCENT, relief='flat', bd=0,
                      padx=10, pady=5, cursor='hand2',
                      command=lambda v=var: self._pick_dir(v)).pack(side='left')

        dir_row('Thư mục nguồn:', self._src_dir)
        dir_row('Thư mục backup:', self._bak_dir)

        # Backup schedule
        srow = tk.Frame(bc, bg=CARD)
        srow.pack(fill='x', pady=(6, 0))
        tk.Label(srow, text='Backup định kỳ:', font=SFB, bg=CARD, fg=TEXT, width=16, anchor='w').pack(side='left')
        for h, lbl in [(1,'1h'),(3,'3h'),(6,'6h'),(12,'12h'),(24,'24h')]:
            tk.Radiobutton(srow, text=lbl, variable=self._interval_h, value=h,
                           font=SF, bg=CARD, activebackground=CARD, selectcolor=ACC_BG,
                           command=self._reschedule).pack(side='left', padx=(0, 10))
        tk.Checkbutton(srow, text='Tự động', variable=self._backup_on,
                        font=SF, bg=CARD, activebackground=CARD, selectcolor=ACC_BG,
                        command=self._reschedule).pack(side='left', padx=(10, 0))

        brow = tk.Frame(bc, bg=CARD)
        brow.pack(fill='x', pady=(10, 0))
        tk.Button(brow, text='💾  Backup ngay', font=SFB,
                  bg=ACCENT, fg='#fff', relief='flat', bd=0, padx=16, pady=8,
                  cursor='hand2', command=lambda: threading.Thread(
                      target=self._run_backup, daemon=True).start()).pack(side='left', padx=(0, 8))
        self._bk_status_lbl = tk.Label(brow, text='', font=SFS, bg=CARD, fg=MUTED)
        self._bk_status_lbl.pack(side='left')
        self._next_bk_lbl = tk.Label(brow, text=self._next_backup_str(), font=SFS, bg=CARD, fg=AMB_FG)
        self._next_bk_lbl.pack(side='right')

        # Backup history
        hc = self._card(body, fill='both', expand=True)
        tk.Label(hc, text='LỊCH SỬ BACKUP', font=('Segoe UI', 9, 'bold'),
                 bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 8))
        self._bk_list_frame = tk.Frame(hc, bg=CARD)
        self._bk_list_frame.pack(fill='both', expand=True)
        self._refresh_backup_list()

    def _run_decrypt(self):
        directory = self._dec_dir.get()
        key_file  = os.path.join(directory, '.ransom_key')
        if not os.path.isdir(directory):
            messagebox.showerror('Lỗi', f'Thư mục không tồn tại:\n{directory}')
            return
        if not os.path.exists(key_file):
            messagebox.showerror('Không có khóa',
                                 f'Không tìm thấy .ransom_key trong:\n{directory}\n\n'
                                 f'Hãy dùng Phương án 2 (restore từ backup).')
            return
        if not messagebox.askyesno('Xác nhận giải mã',
                f'Giải mã tất cả file .encrypted trong:\n{directory}\n\nTiếp tục?'):
            return
        self._dec_status.config(text='Đang giải mã...', fg=AMB)
        threading.Thread(target=self._decrypt_thread, args=(directory, key_file), daemon=True).start()

    def _decrypt_thread(self, directory: str, key_file: str):
        try:
            with open(key_file, 'rb') as fh:
                key = fh.read()
            fernet = Fernet(key)
            count, errors = 0, 0
            for root, _, files in os.walk(directory):
                for fname in files:
                    if not fname.endswith('.encrypted'):
                        continue
                    enc_path = os.path.join(root, fname)
                    orig_path = enc_path[:-len('.encrypted')]
                    try:
                        with open(enc_path, 'rb') as fh:
                            data = fernet.decrypt(fh.read())
                        with open(orig_path, 'wb') as fh:
                            fh.write(data)
                        os.remove(enc_path)
                        count += 1
                    except InvalidToken:
                        errors += 1
            msg = f'{count} file đã khôi phục, {errors} lỗi'
            self._log(f'[PHỤC HỒI] Giải mã xong — {msg}')
            self._incident_actions.append(f'Giải mã Fernet: {msg}')
            self.root.after(0, lambda: self._dec_status.config(
                text=f'✓  {msg}', fg=GRN))
            self._advance_phase('recovery')
            if errors == 0:
                self.root.after(0, lambda: messagebox.showinfo(
                    'Giải mã thành công', f'✓  {count} file đã được khôi phục.'))
        except Exception as e:
            self._log(f'[LỖI] Giải mã thất bại: {e}')
            self.root.after(0, lambda: self._dec_status.config(text=f'Lỗi: {e}', fg=RED))

    def _refresh_backup_list(self):
        if not hasattr(self, '_bk_list_frame'):
            return
        for w in self._bk_list_frame.winfo_children():
            w.destroy()
        mgr = BackupManager(self._src_dir.get(), self._bak_dir.get())
        backups = mgr.list_backups()
        if not backups:
            tk.Label(self._bk_list_frame, text='Chưa có backup nào.',
                     font=SFS, bg=CARD, fg=MUTED).pack(anchor='w')
            return
        for bk in reversed(backups[-10:]):
            row = tk.Frame(self._bk_list_frame, bg=BORDER, padx=1, pady=1)
            row.pack(fill='x', pady=(0, 4))
            inner = tk.Frame(row, bg=CARD, padx=10, pady=7)
            inner.pack(fill='x')
            size_kb = os.path.getsize(bk) / 1024
            tk.Label(inner, text=f'💾  {os.path.basename(bk)}',
                     font=SF, bg=CARD, fg=TEXT).pack(side='left')
            tk.Label(inner, text=f'{size_kb:.0f} KB',
                     font=SFS, bg=CARD, fg=MUTED).pack(side='left', padx=10)
            tk.Button(inner, text='Khôi phục', font=SFS, bg=AMB_BG, fg=AMB_FG,
                      relief='flat', bd=0, padx=10, pady=3, cursor='hand2',
                      command=lambda b=bk: self._restore(b)).pack(side='right')

    def _restore(self, backup_path: str):
        if not messagebox.askyesno('Xác nhận',
                f'Khôi phục từ:\n{os.path.basename(backup_path)}\n\n'
                f'Dữ liệu hiện tại sẽ bị ghi đè. Tiếp tục?'):
            return
        try:
            mgr = BackupManager(self._src_dir.get(), self._bak_dir.get())
            mgr.restore(backup_path, self._src_dir.get())
            self._log(f'[PHỤC HỒI] Restore thành công: {os.path.basename(backup_path)}')
            self._incident_actions.append(f'Restore từ backup: {os.path.basename(backup_path)}')
            self._advance_phase('recovery')
            messagebox.showinfo('Thành công', f'✓  Dữ liệu đã được phục hồi từ:\n{os.path.basename(backup_path)}')
        except Exception as e:
            self._log(f'[LỖI] Restore thất bại: {e}')
            messagebox.showerror('Lỗi', str(e))

    # ── 5. BÁO CÁO SỰ CỐ (Lessons Learned) ─────────────────────────
    def _panel_report(self):
        self._topbar('Báo cáo sự cố', 'Tổng hợp sự cố + rút kinh nghiệm (Lessons Learned)')
        body = tk.Frame(self._content, bg=BG, padx=22, pady=14)
        body.pack(fill='both', expand=True)

        # Summary card
        sc = self._card(body, fill='x', pady=(0, 12))
        tk.Label(sc, text='TÓM TẮT SỰ CỐ', font=('Segoe UI', 10, 'bold'),
                 bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 10))
        enc  = _count_encrypted(_VICTIM_DIR)
        procs = _running_bad_procs()
        key_ex = os.path.exists(os.path.join(_VICTIM_DIR, '.ransom_key'))
        rows = [
            ('Loại mã độc',          'Ransomware (giả lập ProManager Suite)'),
            ('Thư mục bị ảnh hưởng', _VICTIM_DIR),
            ('File bị mã hóa',       f'{enc} file .encrypted'),
            ('Tiến trình độc hại',   ', '.join(procs) if procs else 'Đã dừng'),
            ('Khóa giải mã',         'Tìm thấy' if key_ex else 'Không có / Đã xoá'),
            ('Thời gian phát hiện',  datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ]
        for k, v in rows:
            r = tk.Frame(sc, bg=CARD)
            r.pack(fill='x', pady=2)
            tk.Label(r, text=f'{k}:', font=SFB, bg=CARD, fg=TEXT, width=22, anchor='w').pack(side='left')
            tk.Label(r, text=v, font=SF, bg=CARD, fg=MUTED).pack(side='left')

        # IR phases summary
        ph_card = self._card(body, fill='x', pady=(0, 12))
        tk.Label(ph_card, text='TIẾN ĐỘ CÁC GIAI ĐOẠN IR', font=('Segoe UI', 10, 'bold'),
                 bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 10))
        for key, label, icon in IR_PHASES:
            status = self._phase[key]
            fg  = GRN if status == 'done' else AMB if status == 'active' else MUTED
            mark = '✓' if status == 'done' else '●' if status == 'active' else '○'
            r = tk.Frame(ph_card, bg=CARD)
            r.pack(fill='x', pady=2)
            tk.Label(r, text=f'{mark}  {icon} {label}', font=SFB, bg=CARD, fg=fg).pack(side='left')

        # Actions taken
        ac_card = self._card(body, fill='x', pady=(0, 12))
        tk.Label(ac_card, text='CÁC HÀNH ĐỘNG ĐÃ THỰC HIỆN', font=('Segoe UI', 10, 'bold'),
                 bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 8))
        if self._incident_actions:
            for i, act in enumerate(self._incident_actions, 1):
                tk.Label(ac_card, text=f'  {i}. {act}', font=SF, bg=CARD, fg=TEXT,
                         anchor='w').pack(fill='x')
        else:
            tk.Label(ac_card, text='  Chưa có hành động nào được ghi lại.',
                     font=SF, bg=CARD, fg=MUTED).pack(anchor='w')

        # Lessons Learned
        ll = self._card(body, fill='x', pady=(0, 12))
        tk.Label(ll, text='RÚT KINH NGHIỆM (Lessons Learned)', font=('Segoe UI', 10, 'bold'),
                 bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 8))
        lessons = [
            ('Cập nhật chữ ký',    'Bổ sung pattern "promanagersuite" vào YARA rules và IDS/IPS'),
            ('Vá lỗ hổng',         'Không tải và chạy file exe từ nguồn không xác minh'),
            ('Tăng cường backup',  'Backup offline cách ly khỏi mạng, tần suất ít nhất 1 lần/ngày'),
            ('Cập nhật Playbook',  'Ghi lại vector tấn công (social engineering qua email/web)'),
            ('Đào tạo nhân viên',  'Nâng cao nhận thức: không kích hoạt phần mềm lạ dù có API key'),
        ]
        for title, desc in lessons:
            r = tk.Frame(ll, bg=CARD)
            r.pack(fill='x', pady=3)
            tk.Label(r, text=f'→  {title}:', font=SFB, bg=CARD, fg=ACCENT, width=20, anchor='w').pack(side='left')
            tk.Label(r, text=desc, font=SF, bg=CARD, fg=TEXT).pack(side='left')

        # Export
        exp = tk.Frame(body, bg=BG)
        exp.pack(fill='x')
        tk.Button(exp, text='📄  Xuất báo cáo ra file', font=SFB,
                  bg=ACCENT, fg='#fff', relief='flat', bd=0, padx=18, pady=9,
                  cursor='hand2', command=self._export_report).pack(side='left')
        self._advance_phase('lessons')

    def _export_report(self):
        path = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text file', '*.txt'), ('All', '*.*')],
            initialfile=f'incident_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt',
            initialdir=_root)
        if not path:
            return
        enc  = _count_encrypted(_VICTIM_DIR)
        lines = [
            '=' * 60,
            'BÁO CÁO SỰ CỐ AN TOÀN THÔNG TIN — RANSOMWARE',
            '=' * 60,
            f'Thời gian tạo báo cáo : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f'Loại mã độc           : Ransomware (ProManager Suite)',
            f'Thư mục bị ảnh hưởng : {_VICTIM_DIR}',
            f'File bị mã hóa        : {enc}',
            '',
            'TIẾN ĐỘ ỨNG PHÓ:',
        ]
        for key, label, icon in IR_PHASES:
            status = self._phase[key]
            mark = '[DONE]' if status == 'done' else '[ACTIVE]' if status == 'active' else '[PENDING]'
            lines.append(f'  {mark} {label}')
        lines += ['', 'HÀNH ĐỘNG ĐÃ THỰC HIỆN:']
        for i, act in enumerate(self._incident_actions, 1):
            lines.append(f'  {i}. {act}')
        lines += ['', 'LOG SỰ CỐ:']
        lines.extend(f'  {l}' for l in self._log_lines)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines))
        self._log(f'[OK] Xuất báo cáo: {os.path.basename(path)}')
        messagebox.showinfo('Thành công', f'Báo cáo đã được lưu:\n{path}')

    # ── 6. LOG ──────────────────────────────────────────────────────
    def _panel_log(self):
        self._topbar('Log hoạt động', 'Toàn bộ sự kiện phát hiện, cô lập và phục hồi')
        body = tk.Frame(self._content, bg=BG, padx=22, pady=14)
        body.pack(fill='both', expand=True)
        lc = self._card(body, fill='both', expand=True)
        hdr = tk.Frame(lc, bg=CARD)
        hdr.pack(fill='x', pady=(0, 8))
        tk.Label(hdr, text='EVENT LOG', font=('Segoe UI', 9, 'bold'),
                 bg=CARD, fg=MUTED).pack(side='left')
        tk.Button(hdr, text='Xóa log', font=SFS, bg=RED_BG, fg=RED_FG,
                  relief='flat', bd=0, padx=10, pady=3, cursor='hand2',
                  command=self._clear_log).pack(side='right')
        self._log_text = tk.Text(lc, font=('Courier New', 10), bg='#0d1117', fg='#e6edf3',
                                  relief='flat', state='disabled', wrap='word')
        vsb = ttk.Scrollbar(lc, orient='vertical', command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=vsb.set)
        self._log_text.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        self._redraw_log()

    def _redraw_log(self):
        if not hasattr(self, '_log_text'):
            return
        self._log_text.config(state='normal')
        self._log_text.delete('1.0', 'end')
        for line in self._log_lines:
            tag = 'err'  if any(x in line for x in ['[NGUY HIỂM]', '[CẢNH BÁO]', '[LỖI]']) else \
                  'ok'   if any(x in line for x in ['[OK]', '[BACKUP]', '[PHỤC HỒI]']) else 'info'
            self._log_text.insert('end', line + '\n', tag)
        self._log_text.tag_config('err',  foreground='#f87171')
        self._log_text.tag_config('ok',   foreground='#4ade80')
        self._log_text.tag_config('info', foreground='#94a3b8')
        self._log_text.config(state='disabled')
        self._log_text.see('end')

    def _clear_log(self):
        self._log_lines.clear()
        self._redraw_log()

    # ── Background watcher (HIDS) ────────────────────────────────────
    def _watch_loop(self):
        prev_enc = _count_encrypted(_VICTIM_DIR)
        while True:
            time.sleep(2)
            enc = _count_encrypted(_VICTIM_DIR)
            if enc > prev_enc and not self._under_attack:
                delta = enc - prev_enc
                self._log(f'[NGUY HIỂM] {delta} file mới bị mã hóa! (Tổng: {enc})')
                self._phase['identification'] = 'active'
                self._under_attack = True
                self.root.after(0, self._auto_respond)
            elif enc > prev_enc:
                delta = enc - prev_enc
                self._log(f'[NGUY HIỂM] Thêm {delta} file bị mã hóa (Tổng: {enc})')
            prev_enc = enc
            self.root.after(0, self._update_dashboard_stats)
            if self._active_panel == 'detect':
                self.root.after(0, self._refresh_detect_indicators)

    def _auto_respond(self):
        """Tự động ứng phó khi phát hiện ransomware: kill → backup → alert."""
        self._log('[NGUY HIỂM] Kích hoạt ứng phó tự động...')
        self._incident_actions.append('HIDS phát hiện ransomware — kích hoạt auto-respond')

        # 1. Hiện banner đỏ trên dashboard
        if self._active_panel == 'dashboard':
            self._show_attack_banner()

        # 2. Kill các tiến trình độc hại
        killed = []
        for name in _BAD_PROCS:
            try:
                r = subprocess.run(['pkill', '-f', name], capture_output=True)
                if r.returncode == 0:
                    killed.append(name)
            except FileNotFoundError:
                pass
        if killed:
            self._log(f'[OK] Tự động dừng tiến trình: {", ".join(killed)}')
            self._incident_actions.append(f'Auto-kill tiến trình: {", ".join(killed)}')
            self._advance_phase('containment')
        else:
            self._log('[OK] Không tìm thấy tiến trình đang chạy — có thể đã tự thoát')
            self._advance_phase('containment')

        # 3. Bật maintenance mode tự động
        flag = os.path.join(_root, 'MAINTENANCE.flag')
        with open(flag, 'w') as fh:
            fh.write(f'Auto maintenance mode at {datetime.now()}\n')
        self._log('[OK] Tự động bật Maintenance Mode')
        self._incident_actions.append('Auto Maintenance Mode')
        self._advance_phase('eradication')

        # 4. Backup khẩn cấp
        self._log('[BACKUP] Bắt đầu backup khẩn cấp dữ liệu...')
        threading.Thread(target=self._run_backup, daemon=True).start()

        # 5. Alert popup
        enc = _count_encrypted(_VICTIM_DIR)
        self.root.after(800, lambda: messagebox.showwarning(
            '🔴  CẢNH BÁO — Ransomware Detected',
            f'Hệ thống HIDS phát hiện tấn công ransomware!\n\n'
            f'📁  {enc} file đã bị mã hóa\n\n'
            f'Đã tự động thực hiện:\n'
            f'  ✓ Dừng tiến trình độc hại\n'
            f'  ✓ Bật Maintenance Mode\n'
            f'  ✓ Backup khẩn cấp dữ liệu\n\n'
            f'→ Chuyển sang "Phục hồi" để giải mã dữ liệu.'
        ))

    # ── Backup logic ─────────────────────────────────────────────────
    def _run_backup(self):
        src, bak = self._src_dir.get(), self._bak_dir.get()
        if not os.path.isdir(src):
            self._log(f'[LỖI] Thư mục nguồn không tồn tại: {src}')
            return
        try:
            os.makedirs(bak, exist_ok=True)
            mgr  = BackupManager(src, bak)
            path = mgr.backup()
            size = os.path.getsize(path) / 1024
            self._log(f'[BACKUP] {os.path.basename(path)} ({size:.0f} KB)')
            self._incident_actions.append(f'Backup định kỳ: {os.path.basename(path)}')
            self.root.after(0, self._try_refresh_backup_list)
            if hasattr(self, '_bk_status_lbl'):
                self.root.after(0, lambda: self._bk_status_lbl.config(
                    text=f'✓ {datetime.now().strftime("%H:%M:%S")}', fg=GRN))
        except Exception as e:
            self._log(f'[LỖI] Backup thất bại: {e}')

    def _try_refresh_backup_list(self):
        if self._active_panel == 'recover' and hasattr(self, '_bk_list_frame'):
            self._refresh_backup_list()
        if self._active_panel == 'dashboard' and hasattr(self, '_dash_log_frame'):
            self._refresh_dash_log()

    def _reschedule(self):
        if hasattr(self, '_bk_job') and self._bk_job:
            try:
                self.root.after_cancel(self._bk_job)
            except Exception:
                pass
        if self._backup_on.get():
            ms = self._interval_h.get() * 3600 * 1000
            self._next_backup = datetime.now() + timedelta(hours=self._interval_h.get())
            self._bk_job = self.root.after(ms, self._auto_backup)
        else:
            self._next_backup = None
            self._bk_job = None

    def _auto_backup(self):
        self._log(f'[BACKUP] Tự động ({self._interval_h.get()}h)')
        threading.Thread(target=self._run_backup, daemon=True).start()
        self._reschedule()

    def _next_backup_str(self) -> str:
        if not self._backup_on.get() or not self._next_backup:
            return 'Đã tắt' if not self._backup_on.get() else '—'
        delta = self._next_backup - datetime.now()
        if delta.total_seconds() <= 0:
            return 'Đang chạy...'
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s   = divmod(rem, 60)
        return f'Backup tiếp: {h:02d}:{m:02d}:{s:02d}'

    # ── Helpers ──────────────────────────────────────────────────────
    def _log(self, msg: str):
        ts   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f'[{ts}]  {msg}'
        self._log_lines.append(line)
        self._status_var.set(msg[:90])
        self.root.after(0, self._redraw_log)
        if self._active_panel == 'dashboard' and hasattr(self, '_dash_log_frame'):
            self.root.after(0, self._refresh_dash_log)

    def _alert(self, msg: str):
        self.root.after(0, lambda: messagebox.showwarning('⚠  CẢNH BÁO', msg))

    def _tick(self):
        self._clock_var.set(datetime.now().strftime('%H:%M:%S  %d/%m/%Y'))
        if self._active_panel == 'recover' and hasattr(self, '_next_bk_lbl'):
            self._next_bk_lbl.config(text=self._next_backup_str())
        self.root.after(1000, self._tick)

    def run(self):
        self._log('[OK] DefenderPro khởi động — Giai đoạn Chuẩn bị hoàn tất')
        self.root.mainloop()


if __name__ == '__main__':
    DefenderApp().run()
