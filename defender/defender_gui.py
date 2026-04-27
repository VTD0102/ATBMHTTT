import os
import sys
import math
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta

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
SB_FG   = 'rgba(255,255,255,.7)'
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

SF  = ('Segoe UI', 10)
SFB = ('Segoe UI', 10, 'bold')
SFS = ('Segoe UI', 9)
SFL = ('Segoe UI', 13, 'bold')
SFM = ('Segoe UI', 11, 'bold')
SFX = ('Segoe UI', 22, 'bold')

# ── Suspicious patterns ──────────────────────────────────────────────
_BAD_NAMES = {
    'promanagersuite', 'promanager suite', 'fake_manager',
    'fakeinstaller', 'fake_installer', 'ransomware',
}
_BAD_STRINGS = [
    b'RANSOMWARE_SIMULATOR_DEMO_SAFE',
    b'fernet.encrypt',
    b'Fernet.generate_key',
    b'.encrypted',
]
_SKIP_SCAN = {'.encrypted', '.tar', '.gz', '.zip', '.db', '.sqlite'}


# ── Analysis helpers ─────────────────────────────────────────────────
def _entropy(filepath: str, sample: int = 65536) -> float:
    try:
        with open(filepath, 'rb') as fh:
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


def _is_executable(filepath: str) -> bool:
    try:
        with open(filepath, 'rb') as fh:
            magic = fh.read(4)
        return magic[:2] == b'MZ' or magic[:4] == b'\x7fELF'
    except (IOError, PermissionError):
        return False


def analyze_file(filepath: str) -> list:
    findings = []
    name = os.path.basename(filepath).lower()
    ext  = os.path.splitext(name)[1]

    if ext in _SKIP_SCAN:
        return findings

    # ── Name match ──────────────────────────────────────────
    if any(bad in name for bad in _BAD_NAMES):
        findings.append({
            'severity': 'CRITICAL', 'reason': 'suspicious_name',
            'detail': f'Tên file khớp mẫu ransomware đã biết: {os.path.basename(filepath)}',
        })

    # ── Executable + entropy ─────────────────────────────────
    is_exe = ext in ('.exe', '.elf', '.bin') or _is_executable(filepath)
    if is_exe:
        ent = _entropy(filepath)
        if ent > 7.2:
            findings.append({
                'severity': 'HIGH', 'reason': 'packed_executable',
                'detail': f'Executable có entropy cao ({ent:.2f} bits) — có thể bị đóng gói/mã hóa',
            })
        elif ent > 6.5:
            findings.append({
                'severity': 'MEDIUM', 'reason': 'suspicious_executable',
                'detail': f'Executable có entropy bất thường ({ent:.2f} bits)',
            })

    # ── String scan (text/script files) ─────────────────────
    if ext in ('.py', '.js', '.sh', '.bat', '.ps1', '.vbs', '') and not is_exe:
        try:
            with open(filepath, 'rb') as fh:
                content = fh.read(1 << 20)  # max 1 MB
            for sig in _BAD_STRINGS:
                if sig in content:
                    findings.append({
                        'severity': 'CRITICAL', 'reason': 'dangerous_string',
                        'detail': f'Chuỗi nguy hiểm: {sig.decode(errors="replace")}',
                    })
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
                if findings:
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
        self.root.title('DefenderPro — Ransomware Protection Suite')
        self.root.state('zoomed') if sys.platform == 'win32' else \
            self.root.attributes('-zoomed', True)
        self.root.configure(bg=BG)

        # State
        self._active_panel  = None
        self._log_lines     = []
        self._scan_results  = []
        self._backup_on     = tk.BooleanVar(value=True)
        self._interval_h    = tk.IntVar(value=6)
        self._scan_dir      = tk.StringVar(value=_root)
        self._src_dir       = tk.StringVar(value=os.path.join(_root, 'shop_data'))
        self._bak_dir       = tk.StringVar(value=os.path.join(_root, 'backups'))
        self._next_backup   = None
        self._last_scan_ts  = None
        self._scan_count    = 0
        self._threat_count  = 0

        self._build_layout()
        self._show('dashboard')
        self._start_backup_loop()
        self._tick()

    # ── Layout ──────────────────────────────────────────────────────
    def _build_layout(self):
        # Sidebar
        self._sb = tk.Frame(self.root, bg=SIDEBAR, width=220)
        self._sb.pack(side='left', fill='y')
        self._sb.pack_propagate(False)

        tk.Label(self._sb, text='🛡', font=('Segoe UI', 28),
                 bg=SIDEBAR, fg='#ffffff').pack(pady=(22, 0))
        tk.Label(self._sb, text='DefenderPro',
                 font=('Segoe UI', 14, 'bold'), bg=SIDEBAR, fg='#ffffff').pack()
        tk.Label(self._sb, text='Ransomware Protection Suite',
                 font=('Segoe UI', 8), bg=SIDEBAR, fg='#94a3b8').pack(pady=(2, 16))
        tk.Frame(self._sb, bg=SB2, height=1).pack(fill='x')

        self._nav_btns = {}
        for icon, label, key in [
            ('◉', 'Dashboard', 'dashboard'),
            ('🔍', 'Scanner',   'scanner'),
            ('💾', 'Backup',    'backup'),
            ('📋', 'Log',       'log'),
        ]:
            btn = tk.Button(
                self._sb, text=f'  {icon}  {label}',
                font=('Segoe UI', 11), relief='flat', bd=0,
                bg=SIDEBAR, fg='#cbd5e1', cursor='hand2',
                anchor='w', padx=20, pady=11,
                activebackground=SB_ACT, activeforeground='#ffffff',
                command=lambda k=key: self._show(k),
            )
            btn.pack(fill='x')
            self._nav_btns[key] = btn

        tk.Frame(self._sb, bg=SIDEBAR).pack(fill='both', expand=True)
        tk.Frame(self._sb, bg=SB2, height=1).pack(fill='x')
        tk.Label(self._sb, text='⚠  DEMO ONLY',
                 font=('Segoe UI', 8, 'bold'), bg=SIDEBAR, fg='#f87171',
                 pady=10).pack()

        # Content
        tk.Frame(self.root, bg=BORDER, width=1).pack(side='left', fill='y')
        self._content = tk.Frame(self.root, bg=BG)
        self._content.pack(side='left', fill='both', expand=True)

        # Status bar
        self._status_var = tk.StringVar(value='Sẵn sàng')
        sb = tk.Frame(self.root, bg=SB2, height=28)
        sb.pack(side='bottom', fill='x')
        tk.Label(sb, textvariable=self._status_var,
                 font=('Segoe UI', 9), bg=SB2, fg='#94a3b8',
                 padx=14).pack(side='left')
        self._clock_var = tk.StringVar()
        tk.Label(sb, textvariable=self._clock_var,
                 font=('Segoe UI', 9), bg=SB2, fg='#64748b',
                 padx=14).pack(side='right')

        # Panels (built lazily)
        self._panels = {}

    def _clear_content(self):
        for w in self._content.winfo_children():
            w.destroy()

    def _show(self, key: str):
        if self._active_panel == key:
            return
        self._active_panel = key
        for k, btn in self._nav_btns.items():
            btn.config(bg=SB_ACT if k == key else SIDEBAR,
                       fg='#ffffff' if k == key else '#cbd5e1',
                       font=('Segoe UI', 11, 'bold') if k == key else ('Segoe UI', 11))
        self._clear_content()
        getattr(self, f'_panel_{key}')()

    # ── Topbar helper ────────────────────────────────────────────────
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

    # ── DASHBOARD ───────────────────────────────────────────────────
    def _panel_dashboard(self):
        self._topbar('Dashboard', 'Tổng quan hệ thống bảo vệ')
        body = tk.Frame(self._content, bg=BG, padx=22, pady=18)
        body.pack(fill='both', expand=True)

        # Stat cards row
        srow = tk.Frame(body, bg=BG)
        srow.pack(fill='x', pady=(0, 18))

        self._dash_threat_var = tk.StringVar(value=str(self._threat_count))
        self._dash_scan_var   = tk.StringVar(value=str(self._scan_count))
        self._dash_status_var = tk.StringVar(
            value='Đang bảo vệ' if self._threat_count == 0 else f'{self._threat_count} mối đe doạ!')
        self._dash_backup_var = tk.StringVar(value=self._next_backup_str())

        stat_data = [
            ('🛡', 'Trạng thái', self._dash_status_var,
             GRN if self._threat_count == 0 else RED,
             GRN_BG if self._threat_count == 0 else RED_BG),
            ('🔍', 'File đã quét', self._dash_scan_var,   ACCENT, ACC_BG),
            ('⚠',  'Mối đe doạ',  self._dash_threat_var,
             RED if self._threat_count else GRN,
             RED_BG if self._threat_count else GRN_BG),
            ('💾', 'Backup tiếp theo', self._dash_backup_var, AMB, AMB_BG),
        ]
        for icon, lbl, var, fg, bg in stat_data:
            outer = tk.Frame(srow, bg=BORDER, padx=1, pady=1)
            outer.pack(side='left', fill='both', expand=True, padx=(0, 12))
            c = tk.Frame(outer, bg=CARD, padx=16, pady=14)
            c.pack(fill='both', expand=True)
            tk.Label(c, text=icon, font=('Segoe UI', 20), bg=CARD, fg=fg).pack(anchor='w')
            tk.Label(c, textvariable=var, font=('Segoe UI', 15, 'bold'), bg=CARD, fg=fg).pack(anchor='w')
            tk.Label(c, text=lbl, font=SFS, bg=CARD, fg=MUTED).pack(anchor='w')

        # Quick actions
        qrow = tk.Frame(body, bg=BG)
        qrow.pack(fill='x', pady=(0, 18))
        for txt, cmd, bg, fg in [
            ('🔍  Quét ngay', lambda: self._show('scanner'), ACCENT, '#fff'),
            ('💾  Backup ngay', self._quick_backup, GRN, '#fff'),
            ('📋  Xem log', lambda: self._show('log'), SB2, '#fff'),
        ]:
            tk.Button(qrow, text=txt, font=SFB, bg=bg, fg=fg,
                      relief='flat', bd=0, padx=20, pady=9, cursor='hand2',
                      activebackground=SIDEBAR, activeforeground='#fff',
                      command=cmd).pack(side='left', padx=(0, 10))

        # Recent log
        lcard = self._card(body, fill='x', expand=True)
        tk.Label(lcard, text='HOẠT ĐỘNG GẦN ĐÂY', font=('Segoe UI', 9, 'bold'),
                 bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 10))
        self._dash_log_frame = tk.Frame(lcard, bg=CARD)
        self._dash_log_frame.pack(fill='both', expand=True)
        self._refresh_dash_log()

    def _refresh_dash_log(self):
        for w in self._dash_log_frame.winfo_children():
            w.destroy()
        entries = self._log_lines[-8:][::-1]
        if not entries:
            tk.Label(self._dash_log_frame, text='Chưa có hoạt động nào.',
                     font=SFS, bg=CARD, fg=MUTED).pack(anchor='w')
        for line in entries:
            clr = RED if '[CẢNH BÁO]' in line or '[NGUY HIỂM]' in line else \
                  GRN if '[OK]' in line or '[BACKUP]' in line else MUTED
            tk.Label(self._dash_log_frame, text=line, font=('Courier New', 9),
                     bg=CARD, fg=clr, anchor='w').pack(fill='x')

    def _next_backup_str(self) -> str:
        if not self._backup_on.get():
            return 'Đã tắt'
        if not self._next_backup:
            return '—'
        delta = self._next_backup - datetime.now()
        if delta.total_seconds() <= 0:
            return 'Đang chạy...'
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s   = divmod(rem, 60)
        return f'{h:02d}:{m:02d}:{s:02d}'

    def _quick_backup(self):
        threading.Thread(target=self._run_backup, daemon=True).start()

    # ── SCANNER ─────────────────────────────────────────────────────
    def _panel_scanner(self):
        self._topbar('Scanner', 'Phát hiện phần mềm độc hại và ransomware')
        body = tk.Frame(self._content, bg=BG, padx=22, pady=16)
        body.pack(fill='both', expand=True)

        # Directory picker
        dc = self._card(body, fill='x', pady=(0, 14))
        tk.Label(dc, text='Thư mục cần quét', font=SFB, bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 6))
        drow = tk.Frame(dc, bg=CARD)
        drow.pack(fill='x')
        dir_entry = tk.Entry(drow, textvariable=self._scan_dir, font=SF,
                             bg='#f8faff', fg=TEXT, relief='flat',
                             highlightthickness=1, highlightbackground=BORDER,
                             highlightcolor=ACCENT)
        dir_entry.pack(side='left', fill='x', expand=True, ipady=7, padx=(0, 8))
        tk.Button(drow, text='Chọn thư mục', font=SF, bg=BG, fg=ACCENT,
                  relief='flat', bd=0, padx=12, pady=7, cursor='hand2',
                  command=self._pick_scan_dir).pack(side='left')

        # Controls
        ctrl = tk.Frame(dc, bg=CARD)
        ctrl.pack(fill='x', pady=(10, 0))
        self._scan_btn = tk.Button(ctrl, text='🔍  Bắt đầu quét', font=SFB,
                                    bg=ACCENT, fg='#fff', relief='flat', bd=0,
                                    padx=20, pady=9, cursor='hand2',
                                    command=self._start_scan)
        self._scan_btn.pack(side='left')
        self._scan_status = tk.Label(ctrl, text='', font=SFS, bg=CARD, fg=MUTED)
        self._scan_status.pack(side='left', padx=14)
        self._scan_pbar = ttk.Progressbar(ctrl, mode='indeterminate', length=220)

        # Results
        rc = self._card(body, fill='both', expand=True)
        hdr = tk.Frame(rc, bg=CARD)
        hdr.pack(fill='x', pady=(0, 10))
        tk.Label(hdr, text='KẾT QUẢ QUÉT', font=('Segoe UI', 9, 'bold'),
                 bg=CARD, fg=MUTED).pack(side='left')
        self._result_summary = tk.Label(hdr, text='', font=SFS, bg=CARD, fg=MUTED)
        self._result_summary.pack(side='right')

        # Treeview
        cols = ('severity', 'reason', 'file', 'detail')
        style = ttk.Style()
        style.configure('Scan.Treeview', rowheight=28, font=('Segoe UI', 9),
                         background=CARD, fieldbackground=CARD, foreground=TEXT)
        style.configure('Scan.Treeview.Heading', font=('Segoe UI', 9, 'bold'),
                         background=BG, foreground=MUTED)
        style.map('Scan.Treeview', background=[('selected', ACC_BG)],
                  foreground=[('selected', ACC_FG)])
        self._tree = ttk.Treeview(rc, columns=cols, show='headings',
                                   style='Scan.Treeview', height=14)
        for col, w, label in [
            ('severity', 90,  'Mức độ'),
            ('reason',   130, 'Loại'),
            ('file',     300, 'File'),
            ('detail',   380, 'Chi tiết'),
        ]:
            self._tree.heading(col, text=label)
            self._tree.column(col, width=w, minwidth=60)
        self._tree.tag_configure('CRITICAL', foreground=RED_FG, background=RED_BG)
        self._tree.tag_configure('HIGH',     foreground=AMB_FG, background=AMB_BG)
        self._tree.tag_configure('MEDIUM',   foreground=ACC_FG, background=ACC_BG)

        vsb = ttk.Scrollbar(rc, orient='vertical', command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

    def _pick_scan_dir(self):
        d = filedialog.askdirectory(initialdir=self._scan_dir.get())
        if d:
            self._scan_dir.set(d)

    def _start_scan(self):
        d = self._scan_dir.get()
        if not os.path.isdir(d):
            messagebox.showerror('Lỗi', f'Thư mục không tồn tại:\n{d}')
            return
        self._scan_btn.config(state='disabled', text='Đang quét...')
        self._scan_pbar.pack(side='left')
        self._scan_pbar.start(12)
        self._scan_status.config(text='Đang quét...')
        for row in self._tree.get_children():
            self._tree.delete(row)
        self._scan_results = []
        threading.Thread(target=self._run_scan, args=(d,), daemon=True).start()

    def _run_scan(self, directory: str):
        count = [0]
        def cb(path):
            count[0] += 1
            short = os.path.basename(path)
            self.root.after(0, lambda: self._scan_status.config(text=f'Quét: {short[:50]}'))

        results = scan_directory(directory, callback=cb)
        self.root.after(0, lambda: self._finish_scan(results, count[0]))

    def _finish_scan(self, results: list, total: int):
        self._scan_pbar.stop()
        self._scan_pbar.pack_forget()
        self._scan_btn.config(state='normal', text='🔍  Bắt đầu quét')
        self._scan_results = results
        self._scan_count   = total
        self._threat_count = len(results)
        self._last_scan_ts = datetime.now()

        tag_map = {'CRITICAL': 'CRITICAL', 'HIGH': 'HIGH', 'MEDIUM': 'MEDIUM'}
        for f in results:
            sev = f.get('severity', 'MEDIUM')
            short_file = '...' + f['file'][-45:] if len(f['file']) > 48 else f['file']
            self._tree.insert('', 'end',
                values=(sev, f.get('reason',''), short_file, f.get('detail','')),
                tags=(tag_map.get(sev, 'MEDIUM'),))

        threat_txt = f'⚠  {len(results)} mối đe doạ' if results else '✓  Không phát hiện mối đe doạ'
        clr = RED if results else GRN
        self._result_summary.config(text=f'{threat_txt}  |  {total} file đã quét', fg=clr)
        self._scan_status.config(text='Hoàn tất', fg=GRN)

        level = 'CẢNH BÁO' if results else 'OK'
        self._log(f'[{level}] Quét xong — {len(results)} mối đe doạ / {total} file')

        if results:
            crit = [r for r in results if r.get('severity') == 'CRITICAL']
            if crit:
                f = crit[0]
                self._alert(
                    f"Phát hiện {len(crit)} mối đe doạ NGHIÊM TRỌNG!\n\n"
                    f"File: {os.path.basename(f['file'])}\n"
                    f"Lý do: {f.get('detail','')}\n\n"
                    f"Khuyến cáo: Xóa file ngay và khôi phục dữ liệu từ backup."
                )

    # ── BACKUP ──────────────────────────────────────────────────────
    def _panel_backup(self):
        self._topbar('Backup', 'Sao lưu dữ liệu định kỳ và khôi phục')
        body = tk.Frame(self._content, bg=BG, padx=22, pady=16)
        body.pack(fill='both', expand=True)

        # Config card
        cc = self._card(body, fill='x', pady=(0, 14))
        tk.Label(cc, text='CẤU HÌNH BACKUP', font=('Segoe UI', 9, 'bold'),
                 bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 12))

        def dir_row(label, var):
            r = tk.Frame(cc, bg=CARD)
            r.pack(fill='x', pady=(0, 8))
            tk.Label(r, text=label, font=SFB, bg=CARD, fg=TEXT, width=18, anchor='w').pack(side='left')
            e = tk.Entry(r, textvariable=var, font=SF, bg='#f8faff', fg=TEXT,
                         relief='flat', highlightthickness=1,
                         highlightbackground=BORDER, highlightcolor=ACCENT)
            e.pack(side='left', fill='x', expand=True, ipady=6, padx=(0, 8))
            tk.Button(r, text='Chọn', font=SFS, bg=BG, fg=ACCENT,
                      relief='flat', bd=0, padx=10, pady=5, cursor='hand2',
                      command=lambda v=var: self._pick_dir(v)).pack(side='left')

        dir_row('Thư mục nguồn:', self._src_dir)
        dir_row('Thư mục lưu:',   self._bak_dir)

        # Schedule
        sched = tk.Frame(cc, bg=CARD)
        sched.pack(fill='x', pady=(4, 0))
        tk.Label(sched, text='Chu kỳ backup:', font=SFB, bg=CARD, fg=TEXT,
                 width=18, anchor='w').pack(side='left')
        for h, label in [(1,'1 giờ'),(3,'3 giờ'),(6,'6 giờ'),(12,'12 giờ'),(24,'24 giờ')]:
            tk.Radiobutton(sched, text=label, variable=self._interval_h, value=h,
                           font=SF, bg=CARD, fg=TEXT, activebackground=CARD,
                           selectcolor=ACC_BG,
                           command=self._reschedule).pack(side='left', padx=(0, 12))

        auto_row = tk.Frame(cc, bg=CARD)
        auto_row.pack(fill='x', pady=(10, 0))
        tk.Checkbutton(auto_row, text='Bật backup tự động', variable=self._backup_on,
                        font=SF, bg=CARD, fg=TEXT, activebackground=CARD,
                        selectcolor=ACC_BG,
                        command=self._reschedule).pack(side='left')
        self._next_bk_label = tk.Label(auto_row, text='', font=SFS, bg=CARD, fg=AMB_FG)
        self._next_bk_label.pack(side='left', padx=(16, 0))

        # Manual buttons
        btn_row = tk.Frame(cc, bg=CARD)
        btn_row.pack(fill='x', pady=(12, 0))
        tk.Button(btn_row, text='💾  Backup ngay', font=SFB,
                  bg=GRN, fg='#fff', relief='flat', bd=0, padx=18, pady=9,
                  cursor='hand2', command=self._quick_backup).pack(side='left')
        self._bk_status = tk.Label(btn_row, text='', font=SFS, bg=CARD, fg=MUTED)
        self._bk_status.pack(side='left', padx=14)

        # History
        hc = self._card(body, fill='both', expand=True)
        tk.Label(hc, text='LỊCH SỬ BACKUP', font=('Segoe UI', 9, 'bold'),
                 bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 10))
        self._bk_list_frame = tk.Frame(hc, bg=CARD)
        self._bk_list_frame.pack(fill='both', expand=True)
        self._refresh_backup_list()

    def _pick_dir(self, var: tk.StringVar):
        d = filedialog.askdirectory(initialdir=var.get())
        if d:
            var.set(d)

    def _refresh_backup_list(self):
        for w in self._bk_list_frame.winfo_children():
            w.destroy()
        bak_dir = self._bak_dir.get()
        mgr = BackupManager(self._src_dir.get(), bak_dir)
        backups = mgr.list_backups()
        if not backups:
            tk.Label(self._bk_list_frame, text='Chưa có backup nào.',
                     font=SFS, bg=CARD, fg=MUTED).pack(anchor='w')
            return
        for bk in reversed(backups[-12:]):
            row = tk.Frame(self._bk_list_frame, bg=BORDER, padx=1, pady=1)
            row.pack(fill='x', pady=(0, 5))
            inner = tk.Frame(row, bg=CARD, padx=10, pady=7)
            inner.pack(fill='x')
            size_kb = os.path.getsize(bk) / 1024
            bname = os.path.basename(bk)
            tk.Label(inner, text=f'💾  {bname}', font=SF, bg=CARD, fg=TEXT,
                     anchor='w').pack(side='left')
            tk.Label(inner, text=f'{size_kb:.0f} KB', font=SFS,
                     bg=CARD, fg=MUTED).pack(side='left', padx=(12, 0))
            tk.Button(inner, text='Khôi phục', font=SFS, bg=AMB_BG, fg=AMB_FG,
                      relief='flat', bd=0, padx=10, pady=3, cursor='hand2',
                      command=lambda b=bk: self._restore(b)).pack(side='right')

    def _restore(self, backup_path: str):
        if not messagebox.askyesno('Xác nhận khôi phục',
                f'Khôi phục từ:\n{os.path.basename(backup_path)}\n\n'
                f'Dữ liệu hiện tại trong thư mục nguồn sẽ bị ghi đè. Tiếp tục?'):
            return
        try:
            mgr = BackupManager(self._src_dir.get(), self._bak_dir.get())
            mgr.restore(backup_path, self._src_dir.get())
            self._log(f'[OK] Khôi phục thành công từ: {os.path.basename(backup_path)}')
            messagebox.showinfo('Khôi phục thành công',
                                f'Dữ liệu đã được khôi phục từ:\n{os.path.basename(backup_path)}')
        except Exception as e:
            self._log(f'[LỖI] Khôi phục thất bại: {e}')
            messagebox.showerror('Lỗi', str(e))

    # ── LOG ─────────────────────────────────────────────────────────
    def _panel_log(self):
        self._topbar('Log hoạt động', 'Toàn bộ lịch sử quét và backup')
        body = tk.Frame(self._content, bg=BG, padx=22, pady=16)
        body.pack(fill='both', expand=True)
        lc = self._card(body, fill='both', expand=True)

        hdr = tk.Frame(lc, bg=CARD)
        hdr.pack(fill='x', pady=(0, 8))
        tk.Label(hdr, text='LOG', font=('Segoe UI', 9, 'bold'),
                 bg=CARD, fg=MUTED).pack(side='left')
        tk.Button(hdr, text='Xóa log', font=SFS, bg=RED_BG, fg=RED_FG,
                  relief='flat', bd=0, padx=10, pady=3, cursor='hand2',
                  command=self._clear_log).pack(side='right')

        self._log_text = tk.Text(lc, font=('Courier New', 10), bg='#0d1117', fg='#e6edf3',
                                  relief='flat', state='disabled', wrap='word',
                                  insertbackground='#fff')
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
            tag = 'err' if '[CẢNH BÁO]' in line or '[NGUY HIỂM]' in line or '[LỖI]' in line else \
                  'ok'  if '[OK]' in line or '[BACKUP]' in line else 'info'
            self._log_text.insert('end', line + '\n', tag)
        self._log_text.tag_config('err',  foreground='#f87171')
        self._log_text.tag_config('ok',   foreground='#4ade80')
        self._log_text.tag_config('info', foreground='#94a3b8')
        self._log_text.config(state='disabled')
        self._log_text.see('end')

    def _clear_log(self):
        self._log_lines.clear()
        self._redraw_log()

    # ── Backup logic ─────────────────────────────────────────────────
    def _run_backup(self):
        src = self._src_dir.get()
        bak = self._bak_dir.get()
        if not os.path.isdir(src):
            self._log(f'[LỖI] Thư mục nguồn không tồn tại: {src}')
            return
        try:
            os.makedirs(bak, exist_ok=True)
            mgr = BackupManager(src, bak)
            path = mgr.backup()
            size = os.path.getsize(path) / 1024
            self._log(f'[BACKUP] Tạo xong: {os.path.basename(path)} ({size:.0f} KB)')
            self.root.after(0, lambda: self._bk_status.config(
                text=f'✓ Backup xong lúc {datetime.now().strftime("%H:%M:%S")}', fg=GRN))
            self.root.after(0, self._try_refresh_backup_list)
        except Exception as e:
            self._log(f'[LỖI] Backup thất bại: {e}')

    def _try_refresh_backup_list(self):
        if self._active_panel == 'backup' and hasattr(self, '_bk_list_frame'):
            self._refresh_backup_list()
        if self._active_panel == 'dashboard' and hasattr(self, '_dash_log_frame'):
            self._refresh_dash_log()

    def _start_backup_loop(self):
        self._reschedule()

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
        self._log(f'[BACKUP] Backup tự động ({self._interval_h.get()}h)')
        threading.Thread(target=self._run_backup, daemon=True).start()
        self._reschedule()

    # ── Helpers ──────────────────────────────────────────────────────
    def _log(self, msg: str):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f'[{ts}]  {msg}'
        self._log_lines.append(line)
        self._status_var.set(msg[:80])
        self.root.after(0, self._redraw_log)
        if self._active_panel == 'dashboard' and hasattr(self, '_dash_log_frame'):
            self.root.after(0, self._refresh_dash_log)

    def _alert(self, msg: str):
        self.root.after(0, lambda: messagebox.showwarning('⚠  CẢNH BÁO BẢO MẬT', msg))

    def _tick(self):
        self._clock_var.set(datetime.now().strftime('%H:%M:%S  %d/%m/%Y'))
        if hasattr(self, '_next_bk_label') and self._active_panel == 'backup':
            txt = self._next_backup_str()
            self._next_bk_label.config(
                text=f'Backup tiếp theo: {txt}' if self._backup_on.get() else 'Backup tự động: Đã tắt')
        if hasattr(self, '_dash_backup_var') and self._active_panel == 'dashboard':
            self._dash_backup_var.set(self._next_backup_str())
        self.root.after(1000, self._tick)

    def run(self):
        self._log('[OK] DefenderPro khởi động thành công')
        self.root.mainloop()


if __name__ == '__main__':
    DefenderApp().run()
