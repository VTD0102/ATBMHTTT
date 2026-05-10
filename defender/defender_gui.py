import os
import sys
import math
import time
import threading
import re
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

SF  = ('Segoe UI', 16)
SFB = ('Segoe UI', 16, 'bold')
SFS = ('Segoe UI', 15)
SFL = ('Segoe UI', 21, 'bold')
SFM = ('Segoe UI', 19, 'bold')
SFX = ('Segoe UI', 32, 'bold')

# ── IR Phases ────────────────────────────────────────────────────────
IR_PHASES = [
    ('preparation',    '1. Chuẩn bị',          '🛡'),
    ('identification', '2. Phát hiện',          '🔍'),
    ('containment',    '3. Cô lập',             '🔒'),
    ('emergency_bak',  '4. Backup khẩn cấp',    '💾'),
    ('assessment',     '5. Đánh giá thiệt hại', '📋'),
    ('recovery',       '6. Khôi phục',          '♻'),
    ('lessons',        '7. Rút kinh nghiệm',    '📊'),
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


def _list_encrypted(directory: str) -> list:
    try:
        return sorted(f for f in os.listdir(directory) if f.endswith('.encrypted'))
    except (FileNotFoundError, PermissionError):
        return []


def _count_total_files(directory: str) -> int:
    try:
        return sum(1 for f in os.listdir(directory) if not f.startswith('.'))
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
        self._active_panel     = None
        self._log_lines        = []
        self._scan_results     = []
        self._scan_count       = 0
        self._threat_count     = 0
        self._under_attack        = False
        self._incident_actions    : list = []
        self._attack_start_enc    = 0   # encrypted count when attack began
        self._attack_detected_at  = None
        self._emergency_backup_path = None

        # Live attack events: list of (timestamp_str, message, event_type)
        # event_type: 'attack' | 'defense' | 'info' | 'warning'
        self._attack_events = []

        # Backup vars
        self._backup_on  = tk.BooleanVar(value=True)
        self._interval_h = tk.IntVar(value=6)
        self._max_backups = tk.IntVar(value=5)
        self._src_dir    = tk.StringVar(value=_VICTIM_DIR)
        self._bak_dir    = tk.StringVar(value=os.path.join(_root, 'backups'))
        self._scan_dir   = tk.StringVar(value=_root)
        self._next_backup = None
        self._bk_job      = None
        self._last_bk_time = None
        self._last_bk_name = ''
        try:
            _existing = BackupManager(self._src_dir.get(), self._bak_dir.get()).list_backups()
            if _existing:
                self._last_bk_name = os.path.basename(_existing[-1])
                self._last_bk_time = datetime.fromtimestamp(os.path.getmtime(_existing[-1]))
        except Exception:
            pass

        self._build_layout()
        self._show('dashboard')
        self._reschedule()
        self._tick()
        threading.Thread(target=self._watch_loop, daemon=True).start()

    # ── Layout ──────────────────────────────────────────────────────
    def _build_layout(self):
        sb = tk.Frame(self.root, bg=SIDEBAR, width=290)
        sb.pack(side='left', fill='y')
        sb.pack_propagate(False)
        self._sb = sb

        tk.Label(sb, text='🛡', font=('Segoe UI', 40), bg=SIDEBAR, fg='#fff').pack(pady=(20, 0))
        tk.Label(sb, text='DefenderPro', font=('Segoe UI', 21, 'bold'), bg=SIDEBAR, fg='#fff').pack()
        tk.Label(sb, text='Ransomware HIDS System', font=('Segoe UI', 14), bg=SIDEBAR, fg='#94a3b8').pack(pady=(2, 14))
        tk.Frame(sb, bg=SB2, height=1).pack(fill='x')

        self._nav_btns = {}
        nav_items = [
            ('🏠', 'Dashboard',           'dashboard'),
            ('🔍', 'Phát hiện (HIDS)',    'detect'),
            ('🔒', 'Cô lập & Tiêu diệt', 'contain'),
            ('💾', 'Backup & Khôi phục',  'backup'),
            ('📊', 'Báo cáo sự cố',       'report'),
            ('⏱', 'Timeline sự cố',      'timeline'),
            ('📋', 'Log',                  'log'),
        ]
        for icon, label, key in nav_items:
            btn = tk.Button(sb, text=f'  {icon}  {label}',
                            font=('Segoe UI', 16), relief='flat', bd=0,
                            bg=SIDEBAR, fg='#cbd5e1', cursor='hand2',
                            anchor='w', padx=18, pady=14,
                            activebackground=SB_ACT, activeforeground='#fff',
                            command=lambda k=key: self._show(k))
            btn.pack(fill='x')
            self._nav_btns[key] = btn

        tk.Frame(sb, bg=SIDEBAR).pack(fill='both', expand=True)
        tk.Frame(sb, bg=SB2, height=1).pack(fill='x')
        tk.Label(sb, text='⚠  DEMO ONLY — Academic', font=('Segoe UI', 14, 'bold'),
                 bg=SIDEBAR, fg='#f87171', pady=8).pack()

        tk.Frame(self.root, bg=BORDER, width=1).pack(side='left', fill='y')
        self._content = tk.Frame(self.root, bg=BG)
        self._content.pack(side='left', fill='both', expand=True)

        sb_bar = tk.Frame(self.root, bg=SB2, height=38)
        sb_bar.pack(side='bottom', fill='x')
        self._status_var = tk.StringVar(value='Sẵn sàng')
        tk.Label(sb_bar, textvariable=self._status_var, font=('Segoe UI', 15),
                 bg=SB2, fg='#94a3b8', padx=14).pack(side='left')
        self._clock_var = tk.StringVar()
        tk.Label(sb_bar, textvariable=self._clock_var, font=('Segoe UI', 15),
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
                       font=('Segoe UI', 16, 'bold') if active else ('Segoe UI', 16))
        self._clear_content()
        getattr(self, f'_panel_{key}')()

    # ── UI helpers ───────────────────────────────────────────────────
    def _topbar(self, title: str, subtitle: str = ''):
        bar = tk.Frame(self._content, bg=CARD, padx=28, pady=18)
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

    def _stat_card(self, parent, icon, value_var, label, fg):
        outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        outer.pack(side='left', fill='both', expand=True, padx=(0, 8))
        c = tk.Frame(outer, bg=CARD, padx=14, pady=12)
        c.pack(fill='both', expand=True)
        tk.Label(c, text=icon, font=('Segoe UI', 28), bg=CARD, fg=fg).pack(anchor='w')
        if isinstance(value_var, tk.Variable):
            tk.Label(c, textvariable=value_var, font=('Segoe UI', 24, 'bold'), bg=CARD, fg=fg).pack(anchor='w')
        else:
            tk.Label(c, text=value_var, font=('Segoe UI', 24, 'bold'), bg=CARD, fg=fg).pack(anchor='w')
        tk.Label(c, text=label, font=SFS, bg=CARD, fg=MUTED).pack(anchor='w')

    # ── 1. DASHBOARD ─────────────────────────────────────────────────
    def _panel_dashboard(self):
        self._topbar('Dashboard — Live Monitor',
                     'Theo dõi tấn công & quá trình phòng thủ theo thời gian thực')

        _sw = tk.Frame(self._content, bg=BG)
        _sw.pack(fill='both', expand=True)
        _sw.grid_rowconfigure(0, weight=1)
        _sw.grid_columnconfigure(0, weight=1)
        scroll_canvas = tk.Canvas(_sw, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(_sw, orient='vertical', command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky='ns')
        scroll_canvas.grid(row=0, column=0, sticky='nsew')
        body = tk.Frame(scroll_canvas, bg=BG, padx=22, pady=16)
        win = scroll_canvas.create_window((0, 0), window=body, anchor='nw')
        body.bind('<Configure>', lambda e: scroll_canvas.configure(
            scrollregion=scroll_canvas.bbox('all')))
        scroll_canvas.bind('<Configure>', lambda e: scroll_canvas.itemconfig(win, width=e.width))

        # ── IR Phase tracker ──────────────────────────────────────────
        phase_card = self._card(body, fill='x', pady=(0, 14))
        tk.Label(phase_card, text='QUY TRÌNH ỨNG PHÓ SỰ CỐ (NIST IR)', font=(
            'Segoe UI', 9, 'bold'), bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 10))
        self._phase_labels = {}
        prow = tk.Frame(phase_card, bg=CARD)
        prow.pack(fill='x')
        for key, label, icon in IR_PHASES:
            col = tk.Frame(prow, bg=CARD)
            col.pack(side='left', fill='both', expand=True, padx=(0, 5))
            status = self._phase[key]
            fg  = GRN if status == 'done' else AMB if status == 'active' else MUTED
            bg2 = GRN_BG if status == 'done' else AMB_BG if status == 'active' else '#f8fafc'
            box = tk.Frame(col, bg=bg2, padx=6, pady=8)
            box.pack(fill='x')
            tk.Label(box, text=icon, font=('Segoe UI', 24), bg=bg2, fg=fg).pack()
            tk.Label(box, text=label, font=('Segoe UI', 14, 'bold'), bg=bg2, fg=fg,
                     wraplength=120, justify='center').pack()
            mark = '✓' if status == 'done' else '●' if status == 'active' else '○'
            lbl = tk.Label(box, text=mark, font=('Segoe UI', 19, 'bold'), bg=bg2, fg=fg)
            lbl.pack()
            self._phase_labels[key] = (box, lbl)

        # ── Stat row ──────────────────────────────────────────────────
        srow = tk.Frame(body, bg=BG)
        srow.pack(fill='x', pady=(0, 14))
        self._dash_enc_var    = tk.StringVar(value=str(_count_encrypted(_VICTIM_DIR)))
        self._dash_total_var  = tk.StringVar(value=str(_count_total_files(_VICTIM_DIR)))
        self._dash_proc_var   = tk.StringVar(value='Không có')
        self._dash_status_var = tk.StringVar(value='Đang giám sát...')

        enc_cnt = _count_encrypted(_VICTIM_DIR)
        self._stat_card(srow, '🔴', self._dash_enc_var,   'File bị mã hóa',    RED if enc_cnt else MUTED)
        self._stat_card(srow, '📁', self._dash_total_var, 'Tổng file dữ liệu', TEXT)
        self._stat_card(srow, '⚙',  self._dash_proc_var,  'Tiến trình độc hại', RED)
        self._stat_card(srow, '🛡', self._dash_status_var, 'Trạng thái hệ thống', ACCENT)

        # ── Two-column live area ──────────────────────────────────────
        cols_frame = tk.Frame(body, bg=BG)
        cols_frame.pack(fill='both', expand=True)

        # Left: Live Attack Feed
        left = tk.Frame(cols_frame, bg=BORDER, padx=1, pady=1)
        left.pack(side='left', fill='both', expand=True)
        left_inner = tk.Frame(left, bg='#0d1117', padx=12, pady=10)
        left_inner.pack(fill='both', expand=True)

        hdr_l = tk.Frame(left_inner, bg='#0d1117')
        hdr_l.pack(fill='x', pady=(0, 6))
        self._attack_status_dot = tk.Label(hdr_l, text='●', font=('Segoe UI', 19),
                                            bg='#0d1117', fg='#4ade80')
        self._attack_status_dot.pack(side='left')
        tk.Label(hdr_l, text='  LIVE ATTACK FEED',
                 font=('Segoe UI', 15, 'bold'), bg='#0d1117', fg='#e6edf3').pack(side='left')
        tk.Button(hdr_l, text='Xóa', font=('Segoe UI', 14), bg='#21262d', fg='#64748b',
                  relief='flat', bd=0, padx=6, pady=2, cursor='hand2',
                  command=self._clear_attack_feed).pack(side='right')

        self._live_feed = tk.Text(left_inner, font=('Courier New', 15),
                                   bg='#0d1117', fg='#e6edf3', relief='flat',
                                   state='disabled', wrap='word', height=18)
        feed_vsb = ttk.Scrollbar(left_inner, orient='vertical', command=self._live_feed.yview)
        self._live_feed.configure(yscrollcommand=feed_vsb.set)
        self._live_feed.pack(side='left', fill='both', expand=True)
        feed_vsb.pack(side='right', fill='y')

        # Refresh live feed
        self._refresh_live_feed()
        self._update_defense_steps()


    def _clear_attack_feed(self):
        self._attack_events.clear()
        self._refresh_live_feed()

    def _emit_event(self, msg: str, etype: str = 'info'):
        ts = datetime.now().strftime('%H:%M:%S')
        self._attack_events.append((ts, msg, etype))
        self.root.after(0, self._refresh_live_feed)

    def _refresh_live_feed(self):
        if not hasattr(self, '_live_feed') or not self._live_feed.winfo_exists():
            return
        self._live_feed.config(state='normal')
        self._live_feed.delete('1.0', 'end')

        color_map = {
            'attack':  '#f87171',
            'defense': '#4ade80',
            'warning': '#fbbf24',
            'info':    '#94a3b8',
            'ok':      '#4ade80',
        }
        if not self._attack_events:
            self._live_feed.insert('end', 'Đang giám sát... chưa có sự kiện.\n', 'info')
        else:
            for ts, msg, etype in self._attack_events[-50:]:
                tag = etype if etype in color_map else 'info'
                self._live_feed.insert('end', f'[{ts}] {msg}\n', tag)
            self._live_feed.see('end')

        for tag, color in color_map.items():
            self._live_feed.tag_config(tag, foreground=color)
        self._live_feed.config(state='disabled')

    def _update_defense_steps(self):
        if not hasattr(self, '_defense_step_labels'):
            return
        for key, (dot, lbl) in self._defense_step_labels.items():
            status = self._phase.get(key, 'pending')
            fg = GRN if status == 'done' else AMB if status == 'active' else MUTED
            mark = '✓' if status == 'done' else '●' if status == 'active' else '○'
            dot.config(text=mark, fg=fg)
            lbl.config(fg=fg)
        # Update damage summary
        enc = _count_encrypted(_VICTIM_DIR)
        total = _count_total_files(_VICTIM_DIR)
        if hasattr(self, '_damage_enc_var'):
            self._damage_enc_var.set(f'{enc}/{total} file bị mã hóa')
            if self._emergency_backup_path and os.path.exists(self._emergency_backup_path):
                self._damage_safe_var.set('💾 Backup khẩn cấp: có')
                self._damage_msg_var.set(
                    'Có thể khôi phục dữ liệu từ backup. '
                    'File bị mã hóa TRƯỚC khi backup sẽ mất nếu không có key.'
                )
            elif enc > 0:
                self._damage_safe_var.set('⚠ Chưa có backup khẩn cấp')
                self._damage_msg_var.set(
                    'Không có backup: tất cả file bị mã hóa '
                    'sẽ mất nếu không trả tiền chuộc!'
                )

    def _update_phase_display(self):
        if not hasattr(self, '_phase_labels'):
            return
        for key, label, icon in IR_PHASES:
            if key not in self._phase_labels:
                continue
            box, lbl = self._phase_labels[key]
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
        self.root.after(0, self._update_defense_steps)

    def _set_phase_active(self, key: str):
        self._phase[key] = 'active'
        self.root.after(0, self._update_phase_display)
        self.root.after(0, self._update_defense_steps)

    def _update_dashboard_stats(self):
        enc   = _count_encrypted(_VICTIM_DIR)
        total = _count_total_files(_VICTIM_DIR)
        procs = _running_bad_procs()
        if hasattr(self, '_dash_enc_var'):
            self._dash_enc_var.set(str(enc))
            self._dash_total_var.set(str(total))
            self._dash_proc_var.set(', '.join(procs) if procs else 'Không có')
            if enc > 0 or procs:
                self._dash_status_var.set('⚠  ĐANG BỊ TẤN CÔNG')
            else:
                self._dash_status_var.set('Đang bảo vệ ✓')
        if hasattr(self, '_damage_enc_var'):
            self._damage_enc_var.set(f'{enc} file bị mã hóa')

    # ── 2. PHÁT HIỆN (HIDS) ──────────────────────────────────────────
    def _panel_detect(self):
        self._topbar('Phát hiện — HIDS',
                     'Giám sát tiến trình, file mã hóa, entropy và chữ ký nguy hiểm')
        self._set_phase_active('identification')
        body = tk.Frame(self._content, bg=BG, padx=22, pady=14)
        body.pack(fill='both', expand=True)

        # Real-time indicators
        ri = self._card(body, fill='x', pady=(0, 12))
        tk.Label(ri, text='CHỈ SỐ THỜI GIAN THỰC', font=('Segoe UI', 15, 'bold'),
                 bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 10))
        irow = tk.Frame(ri, bg=CARD)
        irow.pack(fill='x')

        self._det_enc_var  = tk.StringVar()
        self._det_proc_var = tk.StringVar()
        self._det_key_var  = tk.StringVar()
        self._refresh_detect_indicators()

        for var, label, fg in [
            (self._det_enc_var,  'File .encrypted phát hiện', RED),
            (self._det_proc_var, 'Tiến trình độc hại', RED),
            (self._det_key_var,  'Ransom key (attacker)', AMB),
        ]:
            box = tk.Frame(irow, bg=RED_BG if fg == RED else AMB_BG, padx=14, pady=10)
            box.pack(side='left', fill='both', expand=True, padx=(0, 8))
            bg2 = RED_BG if fg == RED else AMB_BG
            tk.Label(box, textvariable=var, font=('Segoe UI', 14, 'bold'), bg=bg2, fg=fg).pack()
            tk.Label(box, text=label, font=SFS, bg=bg2, fg=fg).pack()

        # Cách phát hiện
        how_card = self._card(body, fill='x', pady=(0, 12))
        tk.Label(how_card, text='CÁC PHƯƠNG PHÁP PHÁT HIỆN (HIDS — Nhóm 4)',
                 font=('Segoe UI', 15, 'bold'), bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 10))
        methods = [
            ('🔴', 'Signature-based',  'Tên file/string khớp pattern ransomware đã biết'),
            ('🔴', 'Extension scan',   'Phát hiện hàng loạt file đổi đuôi → .encrypted'),
            ('🟠', 'Anomaly-based',    'Entropy cao bất thường (>7.2 bits) → file bị nén/mã hóa'),
            ('🟠', 'Behavior-based',   'File bị đọc rồi xóa liên tục (Disk I/O spike)'),
            ('🔵', 'Process monitor',  'Tiến trình lạ đang chạy (pgrep pattern matching)'),
        ]
        for dot, method, desc in methods:
            row = tk.Frame(how_card, bg=CARD)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=dot, font=SF, bg=CARD).pack(side='left')
            tk.Label(row, text=f'  {method}:', font=SFB, bg=CARD, fg=TEXT, width=18, anchor='w').pack(side='left')
            tk.Label(row, text=desc, font=SFS, bg=CARD, fg=MUTED).pack(side='left')

        # File scan
        sc = self._card(body, fill='x', pady=(0, 12))
        tk.Label(sc, text='QUÉT FILE THỦ CÔNG — Chữ ký & Entropy',
                 font=('Segoe UI', 15, 'bold'), bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 8))
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
        self._scan_pbar   = ttk.Progressbar(ctrl, mode='indeterminate', length=200)
        self._scan_status = tk.Label(ctrl, text='', font=SFS, bg=CARD, fg=MUTED)
        self._scan_status.pack(side='left', padx=12)

        # Results treeview
        rc = self._card(body, fill='both', expand=True)
        hdr = tk.Frame(rc, bg=CARD)
        hdr.pack(fill='x', pady=(0, 8))
        tk.Label(hdr, text='KẾT QUẢ PHÁT HIỆN', font=('Segoe UI', 15, 'bold'), bg=CARD, fg=MUTED).pack(side='left')
        self._det_summary = tk.Label(hdr, text='', font=SFS, bg=CARD, fg=MUTED)
        self._det_summary.pack(side='right')
        cols = ('severity', 'reason', 'file', 'detail')
        style = ttk.Style()
        style.configure('Det.Treeview', rowheight=42, font=('Segoe UI', 15),
                         background=CARD, fieldbackground=CARD, foreground=TEXT)
        style.configure('Det.Treeview.Heading', font=('Segoe UI', 15, 'bold'), background=BG)
        style.map('Det.Treeview', background=[('selected', ACC_BG)])
        self._tree = ttk.Treeview(rc, columns=cols, show='headings',
                                   style='Det.Treeview', height=10)
        for col, w, lbl in [('severity', 90, 'Mức độ'), ('reason', 130, 'Loại'),
                              ('file', 280, 'File'), ('detail', 380, 'Chi tiết')]:
            self._tree.heading(col, text=lbl)
            self._tree.column(col, width=w, minwidth=60)
        self._tree.tag_configure('CRITICAL', foreground=RED_FG,  background=RED_BG)
        self._tree.tag_configure('HIGH',     foreground=AMB_FG,  background=AMB_BG)
        self._tree.tag_configure('MEDIUM',   foreground=ACC_FG,  background=ACC_BG)
        vsb2 = ttk.Scrollbar(rc, orient='vertical', command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb2.set)
        self._tree.pack(side='left', fill='both', expand=True)
        vsb2.pack(side='right', fill='y')

    def _refresh_detect_indicators(self):
        enc   = _count_encrypted(_VICTIM_DIR)
        procs = _running_bad_procs()
        key   = os.path.exists(os.path.join(_VICTIM_DIR, '.ransom_key'))
        if hasattr(self, '_det_enc_var'):
            self._det_enc_var.set(f'{enc} file')
            self._det_proc_var.set(', '.join(procs) if procs else 'Không có')
            self._det_key_var.set('⚠ Tìm thấy' if key else 'Không có')

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
            sev   = f.get('severity', 'MEDIUM')
            short = '...' + f['file'][-42:] if len(f['file']) > 45 else f['file']
            self._tree.insert('', 'end',
                values=(sev, f.get('reason', ''), short, f.get('detail', '')),
                tags=(sev,))
        txt = f'⚠  {len(results)} mối đe doạ' if results else '✓  Sạch'
        self._det_summary.config(text=f'{txt}  |  {total} file', fg=RED if results else GRN)
        self._scan_status.config(text='Hoàn tất', fg=GRN)
        lvl = 'CẢNH BÁO' if results else 'OK'
        self._log(f'[{lvl}] Quét xong — {len(results)} mối đe doạ / {total} file')
        self._record_action(f'Quét thủ công: {len(results)} mối đe doạ trong {total} file', 'info')
        if results:
            self._advance_phase('identification')
            crit = [r for r in results if r.get('severity') == 'CRITICAL']
            if crit:
                self.root.after(0, lambda: messagebox.showwarning(
                    '⚠  CẢNH BÁO',
                    f'Phát hiện {len(crit)} mối đe doạ NGHIÊM TRỌNG!\n\n'
                    f'File: {os.path.basename(crit[0]["file"])}\n'
                    f'Lý do: {crit[0].get("detail", "")}\n\n'
                    f'→ Chuyển sang "Cô lập & Tiêu diệt" ngay!'
                ))

    # ── 3. CÔ LẬP & TIÊU DIỆT ───────────────────────────────────────
    def _panel_contain(self):
        self._topbar('Cô lập & Tiêu diệt',
                     'Ngăn chặn lây lan — Kill process — Xóa bỏ mã độc')
        body = tk.Frame(self._content, bg=BG, padx=22, pady=14)
        body.pack(fill='both', expand=True)

        # Warning
        warn_box = tk.Frame(body, bg=RED_BG, padx=16, pady=12)
        warn_box.pack(fill='x', pady=(0, 14))
        tk.Label(warn_box, text='⚠  TUYỆT ĐỐI KHÔNG TẮT NGUỒN MÁY CHỦ',
                 font=('Segoe UI', 19, 'bold'), bg=RED_BG, fg=RED_FG).pack(anchor='w')
        tk.Label(warn_box,
                 text='Tắt nguồn sẽ mất dấu vết mã độc trong RAM và gây khó khăn cho điều tra pháp y.',
                 font=SFS, bg=RED_BG, fg=RED_FG, wraplength=900, justify='left').pack(anchor='w')

        # Step 1: Maintenance mode
        s1 = self._card(body, fill='x', pady=(0, 10))
        tk.Label(s1, text='BƯỚC 1 — Ngắt giao dịch (Maintenance Mode)',
                 font=('Segoe UI', 16, 'bold'), bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 4))
        tk.Label(s1, text='Dừng mọi giao dịch mới, ngăn mã độc tiếp tục thu thập dữ liệu khách hàng.',
                 font=SFS, bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 8))
        self._maint_var = tk.StringVar(value='⚪  Chưa kích hoạt')
        self._maint_lbl = tk.Label(s1, textvariable=self._maint_var, font=SFB, bg=CARD, fg=MUTED)
        self._maint_lbl.pack(anchor='w', pady=(0, 8))
        if os.path.exists(os.path.join(_root, 'MAINTENANCE.flag')):
            self._maint_var.set('🔴  Đang bảo trì — Giao dịch đã ngưng')
            self._maint_lbl.config(fg=RED)
        tk.Button(s1, text='🔴  Bật Maintenance Mode', font=SFB,
                  bg=AMB, fg='#fff', relief='flat', bd=0, padx=16, pady=8,
                  cursor='hand2', command=self._enable_maintenance).pack(anchor='w')

        # Step 2: Kill processes
        s2 = self._card(body, fill='x', pady=(0, 10))
        tk.Label(s2, text='BƯỚC 2 — Dừng tiến trình độc hại',
                 font=('Segoe UI', 16, 'bold'), bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 4))
        tk.Label(s2, text='Buộc dừng ProManagerSuite và các tiến trình liên quan đang chạy.',
                 font=SFS, bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 8))
        self._proc_status = tk.Label(s2, text='', font=SFS, bg=CARD, fg=MUTED)
        self._proc_status.pack(anchor='w', pady=(0, 6))
        self._check_procs_display()
        tk.Button(s2, text='⛔  Dừng tất cả tiến trình độc hại', font=SFB,
                  bg=RED, fg='#fff', relief='flat', bd=0, padx=16, pady=8,
                  cursor='hand2', command=self._kill_bad_procs).pack(anchor='w')

        # Step 3: Quarantine
        s3 = self._card(body, fill='x', pady=(0, 10))
        tk.Label(s3, text='BƯỚC 3 — Cô lập file mã độc (Eradication)',
                 font=('Segoe UI', 16, 'bold'), bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 4))
        tk.Label(s3, text='Di chuyển ProManagerSuite.exe sang thư mục quarantine để tiêu diệt.',
                 font=SFS, bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 8))
        self._quar_status = tk.Label(s3, text='', font=SFS, bg=CARD, fg=MUTED)
        self._quar_status.pack(anchor='w', pady=(0, 6))
        brow = tk.Frame(s3, bg=CARD)
        brow.pack(anchor='w')
        tk.Button(brow, text='🗑  Quarantine ProManagerSuite.exe', font=SFB,
                  bg=RED, fg='#fff', relief='flat', bd=0, padx=16, pady=8,
                  cursor='hand2', command=self._quarantine_exe).pack(side='left', padx=(0, 8))
        tk.Button(brow, text='📂  Mở thư mục quarantine', font=SF,
                  bg=BG, fg=ACCENT, relief='flat', bd=0, padx=12, pady=8,
                  cursor='hand2', command=self._open_quarantine_dir).pack(side='left')

        # Step 4: Network isolation
        s4 = self._card(body, fill='x')
        tk.Label(s4, text='BƯỚC 4 — Cô lập mạng (Ghi chú thực tế)',
                 font=('Segoe UI', 16, 'bold'), bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 4))
        notes = [
            '• Rút cáp mạng vật lý hoặc ngắt vSwitch của máy chủ bị nhiễm.',
            '• Mục đích: Chặn Ransomware gửi dữ liệu ra ngoài (Double Extortion).',
            '• Demo: mô phỏng bằng cách tạo file NETWORK_ISOLATED.flag.',
        ]
        for note in notes:
            tk.Label(s4, text=note, font=SFS, bg=CARD, fg=MUTED, anchor='w').pack(fill='x')
        tk.Button(s4, text='🌐  Mô phỏng ngắt mạng', font=SFB,
                  bg=BLU, fg='#fff', relief='flat', bd=0, padx=16, pady=8,
                  cursor='hand2', command=self._simulate_network_isolate).pack(anchor='w', pady=(10, 0))

    def _check_procs_display(self):
        procs = _running_bad_procs()
        if procs:
            self._proc_status.config(text=f'⚠  Đang chạy: {", ".join(procs)}', fg=RED)
        else:
            self._proc_status.config(text='✓  Không có tiến trình độc hại nào đang chạy.', fg=GRN)

    def _enable_maintenance(self):
        flag = os.path.join(_root, 'MAINTENANCE.flag')
        with open(flag, 'w') as fh:
            fh.write(f'Maintenance mode enabled at {datetime.now()}\n')
        self._maint_var.set('🔴  Đang bảo trì — Giao dịch đã ngưng')
        self._maint_lbl.config(fg=RED)
        self._log('[OK] Bật Maintenance Mode — giao dịch đã ngưng')
        self._record_action('Bật Maintenance Mode', 'defense')

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
            self._record_action(f'Dừng tiến trình: {", ".join(killed)}', 'defense')
            self._advance_phase('containment')
            messagebox.showinfo('Thành công', msg)
        else:
            messagebox.showinfo('Thông báo', 'Không tìm thấy tiến trình độc hại nào đang chạy.')
        self._check_procs_display()

    def _quarantine_exe(self):
        qdir = os.path.join(_root, 'quarantine')
        os.makedirs(qdir, exist_ok=True)
        exe  = os.path.join(_root, 'manager-agent', 'ProManagerSuite.exe')
        dest = os.path.join(qdir, f'ProManagerSuite.exe.quarantine_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        if not os.path.exists(exe):
            messagebox.showwarning('Không tìm thấy', f'Không tìm thấy file exe tại:\n{exe}')
            return
        if not messagebox.askyesno('Xác nhận',
                f'Di chuyển ProManagerSuite.exe sang quarantine?\n\n{exe}\n→ {dest}'):
            return
        import shutil
        shutil.move(exe, dest)
        self._log(f'[OK] Quarantine: ProManagerSuite.exe → {os.path.basename(dest)}')
        self._record_action('Quarantine ProManagerSuite.exe', 'defense')
        self._quar_status.config(text=f'✓  Đã quarantine: {os.path.basename(dest)}', fg=GRN)

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
        self._record_action('Mô phỏng cô lập mạng', 'defense')
        messagebox.showinfo('Cô lập mạng',
                            '✓  Đã tạo NETWORK_ISOLATED.flag\n\n'
                            'Trong thực tế: rút cáp mạng hoặc\nngắt vSwitch của máy chủ bị nhiễm.')

    # ── 4. BACKUP & KHÔI PHỤC ───────────────────────────────────────
    def _panel_backup(self):
        self._topbar('Backup & Khôi phục',
                     'Backup định kỳ là phòng thủ cuối cùng — Khôi phục từ backup sạch')
        body = tk.Frame(self._content, bg=BG, padx=22, pady=14)
        body.pack(fill='both', expand=True)

        # Damage status
        enc   = _count_encrypted(_VICTIM_DIR)
        total = _count_total_files(_VICTIM_DIR)
        dmg_bg = RED_BG if enc > 0 else GRN_BG
        dmg_fg = RED_FG if enc > 0 else GRN_FG
        dmg_box = tk.Frame(body, bg=dmg_bg, padx=16, pady=12)
        dmg_box.pack(fill='x', pady=(0, 14))
        if enc > 0:
            tk.Label(dmg_box,
                     text=f'🔴  {enc} file đã bị mã hóa — Chỉ có backup trước tấn công mới khôi phục được!',
                     font=('Segoe UI', 19, 'bold'), bg=dmg_bg, fg=dmg_fg).pack(anchor='w')
            tk.Label(dmg_box,
                     text='Không có key của kẻ tấn công → file bị mã hóa sẽ mất vĩnh viễn trừ khi có backup sạch.',
                     font=SFS, bg=dmg_bg, fg=dmg_fg, wraplength=950).pack(anchor='w')
        else:
            tk.Label(dmg_box,
                     text='✓  Dữ liệu hiện tại an toàn — Backup ngay để phòng khi bị tấn công!',
                     font=('Segoe UI', 19, 'bold'), bg=dmg_bg, fg=dmg_fg).pack(anchor='w')

        # Backup management
        bc = self._card(body, fill='x', pady=(0, 12))
        tk.Label(bc, text='BACKUP ĐỊNH KỲ — Phòng thủ chủ động',
                 font=('Segoe UI', 16, 'bold'), bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 4))
        tk.Label(bc, text='Backup định kỳ là BIỆN PHÁP PHÒNG THỦ HIỆU QUẢ NHẤT chống ransomware. '
                           'Backup phải được lưu tách biệt khỏi mạng nội bộ (offline backup).',
                 font=SFS, bg=CARD, fg=MUTED, wraplength=950).pack(anchor='w', pady=(0, 10))

        def dir_row(lbl_text, var):
            r = tk.Frame(bc, bg=CARD)
            r.pack(fill='x', pady=(0, 6))
            tk.Label(r, text=lbl_text, font=SFB, bg=CARD, fg=TEXT, width=18, anchor='w').pack(side='left')
            tk.Entry(r, textvariable=var, font=SF, bg='#f8faff', fg=TEXT,
                     relief='flat', highlightthickness=1,
                     highlightbackground=BORDER, highlightcolor=ACCENT
                     ).pack(side='left', fill='x', expand=True, ipady=6, padx=(0, 8))
            tk.Button(r, text='Chọn', font=SFS, bg=BG, fg=ACCENT, relief='flat', bd=0,
                      padx=10, pady=5, cursor='hand2',
                      command=lambda v=var: self._pick_dir(v)).pack(side='left')

        dir_row('Thư mục nguồn:', self._src_dir)
        dir_row('Thư mục backup:', self._bak_dir)

        srow = tk.Frame(bc, bg=CARD)
        srow.pack(fill='x', pady=(6, 0))
        tk.Label(srow, text='Backup định kỳ:', font=SFB, bg=CARD, fg=TEXT, width=18, anchor='w').pack(side='left')
        for h, lbl in [(1, '1h'), (3, '3h'), (6, '6h'), (12, '12h'), (24, '24h')]:
            tk.Radiobutton(srow, text=lbl, variable=self._interval_h, value=h,
                           font=SF, bg=CARD, activebackground=CARD, selectcolor=ACC_BG,
                           command=self._reschedule).pack(side='left', padx=(0, 10))
        tk.Checkbutton(srow, text='Tự động', variable=self._backup_on,
                        font=SF, bg=CARD, activebackground=CARD, selectcolor=ACC_BG,
                        command=self._reschedule).pack(side='left', padx=(10, 0))

        mrow = tk.Frame(bc, bg=CARD)
        mrow.pack(fill='x', pady=(4, 0))
        tk.Label(mrow, text='Giữ lại tối đa:', font=SFB, bg=CARD, fg=TEXT, width=18, anchor='w').pack(side='left')
        tk.Spinbox(mrow, from_=1, to=20, textvariable=self._max_backups, font=SF,
                   width=4, bg='#f8faff', fg=TEXT, relief='flat',
                   highlightthickness=1, highlightbackground=BORDER,
                   highlightcolor=ACCENT).pack(side='left', padx=(0, 6), ipady=4)
        tk.Label(mrow, text='bản backup gần nhất  (áp dụng cho lần backup tiếp theo)',
                 font=SFS, bg=CARD, fg=MUTED).pack(side='left')

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

        # Backup history + restore
        hc = self._card(body, fill='x', pady=(0, 12))
        hdr = tk.Frame(hc, bg=CARD)
        hdr.pack(fill='x', pady=(0, 8))
        tk.Label(hdr, text='LỊCH SỬ BACKUP — Chọn để khôi phục', font=('Segoe UI', 15, 'bold'),
                 bg=CARD, fg=MUTED).pack(side='left')
        tk.Label(hdr, text='Khôi phục từ backup = 100% dữ liệu tại thời điểm backup',
                 font=SFS, bg=CARD, fg=GRN_FG).pack(side='right')
        self._bk_list_frame = tk.Frame(hc, bg=CARD)
        self._bk_list_frame.pack(fill='x')
        self._refresh_backup_list()

        # ── Demo: Giải mã bằng key kẻ tấn công ──────────────────────
        sep = tk.Frame(body, bg=AMB_BG, padx=16, pady=10)
        sep.pack(fill='x', pady=(6, 0))
        tk.Label(sep, text='━━━  CHỈ DÀNH CHO DEMO  ━━━', font=('Segoe UI', 15, 'bold'),
                 bg=AMB_BG, fg=AMB_FG).pack(anchor='w')
        tk.Label(sep,
                 text='Trong thực tế: sau khi trả tiền chuộc, kẻ tấn công gửi key giải mã. '
                      'Ô bên dưới mô phỏng bước này. Key hợp lệ là nội dung file shop_data/.ransom_key.',
                 font=SFS, bg=AMB_BG, fg=AMB_FG, wraplength=950).pack(anchor='w')

        kc = self._card(body, fill='x', pady=(0, 0))
        tk.Label(kc, text='🔑 GIẢI MÃ BẰNG KEY CỦA KẺ TẤN CÔNG (sau khi trả tiền chuộc)',
                 font=('Segoe UI', 16, 'bold'), bg=CARD, fg=AMB_FG).pack(anchor='w', pady=(0, 6))
        tk.Label(kc, text='Nhập key nhận được từ kẻ tấn công để giải mã file:',
                 font=SFS, bg=CARD, fg=MUTED).pack(anchor='w', pady=(0, 6))

        key_row = tk.Frame(kc, bg=CARD)
        key_row.pack(fill='x', pady=(0, 8))
        self._ransom_key_var = tk.StringVar()
        ke = tk.Entry(key_row, textvariable=self._ransom_key_var, font=('Courier New', 15),
                      bg='#f8faff', fg=TEXT, relief='flat', highlightthickness=1,
                      highlightbackground=AMB, highlightcolor=AMB, show='*')
        ke.pack(side='left', fill='x', expand=True, ipady=6, padx=(0, 8))
        tk.Button(key_row, text='Hiện', font=SFS, bg=AMB_BG, fg=AMB_FG, relief='flat', bd=0,
                  padx=8, pady=5, cursor='hand2',
                  command=lambda: ke.config(show='' if ke.cget('show') == '*' else '*')).pack(side='left', padx=(0, 6))
        tk.Button(key_row, text='Demo Key?', font=SFS, bg=BG, fg=MUTED, relief='flat', bd=0,
                  padx=8, pady=5, cursor='hand2',
                  command=self._show_demo_key_hint).pack(side='left')

        decrypt_row = tk.Frame(kc, bg=CARD)
        decrypt_row.pack(fill='x')
        tk.Button(decrypt_row, text='🔓  Giải mã với key này', font=SFB,
                  bg=AMB, fg='#fff', relief='flat', bd=0, padx=16, pady=8,
                  cursor='hand2', command=self._decrypt_with_entered_key).pack(side='left', padx=(0, 10))
        self._dec_status = tk.Label(decrypt_row, text='', font=SFS, bg=CARD, fg=MUTED)
        self._dec_status.pack(side='left')

    def _show_demo_key_hint(self):
        key_file = os.path.join(_VICTIM_DIR, '.ransom_key')
        if os.path.exists(key_file):
            with open(key_file, 'rb') as fh:
                key = fh.read().decode('utf-8', errors='replace').strip()
            messagebox.showinfo('Demo Key',
                                f'Key hiện tại (nội dung .ransom_key):\n\n{key}\n\n'
                                f'Trong thực tế, chỉ kẻ tấn công có key này.\n'
                                f'Dùng để demo quá trình giải mã sau khi trả tiền chuộc.')
        else:
            messagebox.showinfo('Demo Key', 'Chưa có .ransom_key — chạy tấn công trước.')

    def _decrypt_with_entered_key(self):
        key_str = self._ransom_key_var.get().strip()
        if not key_str:
            messagebox.showerror('Thiếu key', 'Vui lòng nhập key từ kẻ tấn công.')
            return
        directory = _VICTIM_DIR
        enc_files = [f for f in os.listdir(directory) if f.endswith('.encrypted')]
        if not enc_files:
            messagebox.showinfo('Thông báo', 'Không có file .encrypted nào để giải mã.')
            return
        if not messagebox.askyesno('Xác nhận',
                f'Giải mã {len(enc_files)} file trong {directory}\nbằng key đã nhập?\n\nTiếp tục?'):
            return
        self._dec_status.config(text='Đang giải mã...', fg=AMB)
        threading.Thread(target=self._decrypt_thread,
                         args=(directory, key_str), daemon=True).start()

    def _decrypt_thread(self, directory: str, key_str: str):
        try:
            key_bytes = key_str.encode('utf-8') if isinstance(key_str, str) else key_str
            fernet = Fernet(key_bytes)
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
                        self._emit_event(f'✓ Giải mã: {os.path.basename(orig_path)}', 'defense')
                    except InvalidToken:
                        errors += 1
            msg = f'{count} file đã giải mã, {errors} lỗi'
            if errors > 0:
                self._log(f'[CẢNH BÁO] Giải mã một phần — {msg} (key sai hoặc file hỏng)')
            else:
                self._log(f'[OK] Giải mã thành công — {msg}')
            self._record_action(f'Giải mã bằng key attacker: {msg}', 'warning')
            self.root.after(0, lambda: self._dec_status.config(
                text=f'{"✓" if errors == 0 else "⚠"}  {msg}',
                fg=GRN if errors == 0 else AMB))
            if errors > 0:
                self.root.after(0, lambda: messagebox.showwarning(
                    'Key không đúng hoàn toàn',
                    f'{errors} file không thể giải mã — key có thể sai.\n\n'
                    f'{count} file đã giải mã thành công.'))
            else:
                self.root.after(0, lambda: messagebox.showinfo(
                    '✓ Giải mã thành công',
                    f'{count} file đã được khôi phục.\n\n'
                    f'(Mô phỏng: sau khi trả tiền chuộc cho kẻ tấn công)'))
        except Exception as e:
            msg = f'Key không hợp lệ: {e}'
            self._log(f'[LỖI] {msg}')
            self.root.after(0, lambda: self._dec_status.config(text=f'Lỗi: {e}', fg=RED))
            self.root.after(0, lambda: messagebox.showerror('Key không hợp lệ',
                                                              f'{e}\n\nKey phải là Fernet key hợp lệ (44 ký tự base64).'))

    def _refresh_backup_list(self):
        if not hasattr(self, '_bk_list_frame'):
            return
        for w in self._bk_list_frame.winfo_children():
            w.destroy()
        mgr     = BackupManager(self._src_dir.get(), self._bak_dir.get())
        backups = mgr.list_backups()
        if not backups:
            tk.Label(self._bk_list_frame, text='Chưa có backup nào. Nhấn "Backup ngay" để tạo backup đầu tiên.',
                     font=SFS, bg=CARD, fg=AMB_FG).pack(anchor='w')
            return
        for bk in reversed(backups[-10:]):
            row = tk.Frame(self._bk_list_frame, bg=BORDER, padx=1, pady=1)
            row.pack(fill='x', pady=(0, 4))
            inner = tk.Frame(row, bg=CARD, padx=10, pady=7)
            inner.pack(fill='x')
            size_kb = os.path.getsize(bk) / 1024
            is_emergency = 'emergency' in os.path.basename(bk)
            icon = '🚨' if is_emergency else '💾'
            label = f'{icon}  {os.path.basename(bk)}'
            lbl_fg = AMB_FG if is_emergency else TEXT
            tk.Label(inner, text=label, font=SF, bg=CARD, fg=lbl_fg).pack(side='left')
            tk.Label(inner, text=f'{size_kb:.0f} KB', font=SFS, bg=CARD, fg=MUTED).pack(side='left', padx=10)
            tk.Button(inner, text='Khôi phục từ backup', font=SFS, bg=GRN_BG, fg=GRN_FG,
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
            self._log(f'[OK] Restore thành công từ backup: {os.path.basename(backup_path)}')
            self._record_action(f'Restore từ backup: {os.path.basename(backup_path)}', 'defense')
            self._emit_event(f'✓ Dữ liệu đã được khôi phục từ backup', 'defense')
            messagebox.showinfo('Khôi phục thành công',
                                f'✓  Dữ liệu đã được khôi phục từ:\n{os.path.basename(backup_path)}')
            self._refresh_backup_list()
        except Exception as e:
            self._log(f'[LỖI] Restore thất bại: {e}')
            messagebox.showerror('Lỗi', str(e))

    # ── 5. BÁO CÁO ──────────────────────────────────────────────────
    def _panel_report(self):
        self._topbar('Báo cáo sự cố', 'Tổng hợp thiệt hại + rút kinh nghiệm (Lessons Learned)')
        self._advance_phase('lessons')
        body = tk.Frame(self._content, bg=BG, padx=22, pady=14)
        body.pack(fill='both', expand=True)

        _rw = tk.Frame(body, bg=BG)
        _rw.pack(fill='both', expand=True)
        _rw.grid_rowconfigure(0, weight=1)
        _rw.grid_columnconfigure(0, weight=1)
        scroll_canvas = tk.Canvas(_rw, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(_rw, orient='vertical', command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky='ns')
        scroll_canvas.grid(row=0, column=0, sticky='nsew')
        inner = tk.Frame(scroll_canvas, bg=BG)
        win = scroll_canvas.create_window((0, 0), window=inner, anchor='nw')
        inner.bind('<Configure>', lambda e: scroll_canvas.configure(
            scrollregion=scroll_canvas.bbox('all')))
        scroll_canvas.bind('<Configure>', lambda e: scroll_canvas.itemconfig(win, width=e.width))

        # Damage assessment
        enc    = _count_encrypted(_VICTIM_DIR)
        total  = _count_total_files(_VICTIM_DIR)
        procs  = _running_bad_procs()
        bkps   = BackupManager(self._src_dir.get(), self._bak_dir.get()).list_backups()

        da = self._card(inner, fill='x', pady=(0, 12))
        tk.Label(da, text='ĐÁNH GIÁ THIỆT HẠI', font=('Segoe UI', 16, 'bold'), bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 10))

        dmg_bg = RED_BG if enc > 0 else GRN_BG
        dmg_fg = RED_FG if enc > 0 else GRN_FG
        dmg = tk.Frame(da, bg=dmg_bg, padx=12, pady=10)
        dmg.pack(fill='x', pady=(0, 10))
        if enc > 0:
            tk.Label(dmg, text=f'⚠  {enc} file bị mã hóa — MẤT VĨNH VIỄN nếu không có backup hoặc key!',
                     font=SFB, bg=dmg_bg, fg=dmg_fg).pack(anchor='w')
        else:
            tk.Label(dmg, text='✓  Không có file bị mã hóa',
                     font=SFB, bg=dmg_bg, fg=dmg_fg).pack(anchor='w')

        # Encrypted files list
        enc_list = _list_encrypted(_VICTIM_DIR)
        if enc_list:
            tk.Label(da, text='File bị mã hóa:', font=SFB, bg=CARD, fg=RED_FG).pack(anchor='w', pady=(0, 4))
            for f in enc_list:
                orig = f[:-len('.encrypted')]
                tk.Label(da, text=f'  🔒  {orig}  →  {f}',
                         font=('Courier New', 15), bg=CARD, fg=RED_FG).pack(anchor='w')

        rows = [
            ('Loại mã độc',          'Ransomware (ProManager Suite)'),
            ('Thư mục bị ảnh hưởng', _VICTIM_DIR),
            ('File bị mã hóa',       f'{enc} file'),
            ('File an toàn',         f'{total} file'),
            ('Số backup hiện có',    f'{len(bkps)} backup'),
            ('Tiến trình độc hại',   ', '.join(procs) if procs else 'Đã dừng'),
            ('Thời gian báo cáo',    datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ]
        tk.Frame(da, bg=BORDER, height=1).pack(fill='x', pady=8)
        for k, v in rows:
            r = tk.Frame(da, bg=CARD)
            r.pack(fill='x', pady=2)
            tk.Label(r, text=f'{k}:', font=SFB, bg=CARD, fg=TEXT, width=24, anchor='w').pack(side='left')
            tk.Label(r, text=v, font=SF, bg=CARD, fg=MUTED).pack(side='left')

        # IR phases
        ph = self._card(inner, fill='x', pady=(0, 12))
        tk.Label(ph, text='TIẾN ĐỘ CÁC GIAI ĐOẠN ỨNG PHÓ', font=('Segoe UI', 16, 'bold'),
                 bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 10))
        for key, label, icon in IR_PHASES:
            status = self._phase[key]
            fg   = GRN if status == 'done' else AMB if status == 'active' else MUTED
            mark = '✓' if status == 'done' else '●' if status == 'active' else '○'
            r = tk.Frame(ph, bg=CARD)
            r.pack(fill='x', pady=2)
            tk.Label(r, text=f'{mark}  {icon} {label}', font=SFB, bg=CARD, fg=fg).pack(side='left')

        # Actions
        ac = self._card(inner, fill='x', pady=(0, 12))
        tk.Label(ac, text='CÁC HÀNH ĐỘNG ĐÃ THỰC HIỆN', font=('Segoe UI', 16, 'bold'),
                 bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 8))
        if self._incident_actions:
            for i, (ts, act, cat) in enumerate(self._incident_actions, 1):
                tk.Label(ac, text=f'  {i}. {act}', font=SF, bg=CARD, fg=TEXT, anchor='w').pack(fill='x')
        else:
            tk.Label(ac, text='  Chưa có hành động nào được ghi lại.',
                     font=SF, bg=CARD, fg=MUTED).pack(anchor='w')

        # Lessons learned
        ll = self._card(inner, fill='x', pady=(0, 12))
        tk.Label(ll, text='RÚT KINH NGHIỆM (Lessons Learned)', font=('Segoe UI', 16, 'bold'),
                 bg=CARD, fg=TEXT).pack(anchor='w', pady=(0, 8))
        lessons = [
            ('Không chạy .exe lạ',   'Không tải và kích hoạt phần mềm từ nguồn không xác minh'),
            ('Backup 3-2-1',         '3 bản copy, 2 loại media khác nhau, 1 bản off-site (offline)'),
            ('Cập nhật YARA rules',  'Bổ sung pattern "promanagersuite" vào IDS/IPS ngay'),
            ('Nâng cao nhận thức',   'Đào tạo nhân viên: phishing, social engineering'),
            ('Cập nhật IR Playbook', 'Ghi lại vector tấn công (web download → exe → encrypt)'),
            ('Test backup định kỳ',  'Backup vô dụng nếu không thể restore — test thường xuyên!'),
        ]
        for title, desc in lessons:
            r = tk.Frame(ll, bg=CARD)
            r.pack(fill='x', pady=3)
            tk.Label(r, text=f'→  {title}:', font=SFB, bg=CARD, fg=ACCENT, width=22, anchor='w').pack(side='left')
            tk.Label(r, text=desc, font=SF, bg=CARD, fg=TEXT).pack(side='left')

        # Export
        exp = tk.Frame(inner, bg=BG)
        exp.pack(fill='x', pady=(6, 0))
        tk.Button(exp, text='📄  Xuất báo cáo ra file', font=SFB,
                  bg=ACCENT, fg='#fff', relief='flat', bd=0, padx=18, pady=9,
                  cursor='hand2', command=self._export_report).pack(side='left')

    def _export_report(self):
        path = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text file', '*.txt'), ('All', '*.*')],
            initialfile=f'incident_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt',
            initialdir=_root)
        if not path:
            return
        enc  = _count_encrypted(_VICTIM_DIR)
        bkps = BackupManager(self._src_dir.get(), self._bak_dir.get()).list_backups()
        lines = [
            '=' * 60,
            'BÁO CÁO SỰ CỐ AN TOÀN THÔNG TIN — RANSOMWARE',
            '=' * 60,
            f'Thời gian tạo : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f'Loại mã độc   : Ransomware (ProManager Suite giả mạo)',
            f'Thư mục nạn nhân: {_VICTIM_DIR}',
            f'File bị mã hóa: {enc}',
            f'Số backup sẵn có: {len(bkps)}',
            '',
            'TIẾN ĐỘ ỨNG PHÓ:',
        ]
        for key, label, icon in IR_PHASES:
            status = self._phase[key]
            mark = '[DONE]' if status == 'done' else '[ACTIVE]' if status == 'active' else '[PENDING]'
            lines.append(f'  {mark} {icon} {label}')
        lines += ['', 'HÀNH ĐỘNG ĐÃ THỰC HIỆN:']
        for i, (ts, act, cat) in enumerate(self._incident_actions, 1):
            lines.append(f'  {i}. [{ts.strftime("%H:%M:%S")}] {act}')
        lines += ['', 'EVENT LOG:']
        lines.extend(f'  {l}' for l in self._log_lines)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines))
        self._log(f'[OK] Xuất báo cáo: {os.path.basename(path)}')
        messagebox.showinfo('Thành công', f'Báo cáo đã được lưu:\n{path}')

    # ── 6. LOG ──────────────────────────────────────────────────────
    def _panel_log(self):
        self._topbar('Log hoạt động', 'Toàn bộ sự kiện phát hiện, cô lập và phòng thủ')
        body = tk.Frame(self._content, bg=BG, padx=22, pady=14)
        body.pack(fill='both', expand=True)
        lc = self._card(body, fill='both', expand=True)
        hdr = tk.Frame(lc, bg=CARD)
        hdr.pack(fill='x', pady=(0, 8))
        tk.Label(hdr, text='EVENT LOG', font=('Segoe UI', 15, 'bold'), bg=CARD, fg=MUTED).pack(side='left')
        tk.Button(hdr, text='Xóa log', font=SFS, bg=RED_BG, fg=RED_FG,
                  relief='flat', bd=0, padx=10, pady=3, cursor='hand2',
                  command=self._clear_log).pack(side='right')
        self._log_text = tk.Text(lc, font=('Courier New', 16), bg='#0d1117', fg='#e6edf3',
                                  relief='flat', state='disabled', wrap='word')
        vsb = ttk.Scrollbar(lc, orient='vertical', command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=vsb.set)
        self._log_text.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        self._redraw_log()

    def _redraw_log(self):
        if not hasattr(self, '_log_text') or not self._log_text.winfo_exists():
            return
        self._log_text.config(state='normal')
        self._log_text.delete('1.0', 'end')
        for line in self._log_lines:
            tag = 'err'  if any(x in line for x in ['[NGUY HIỂM]', '[CẢNH BÁO]', '[LỖI]']) else \
                  'ok'   if any(x in line for x in ['[OK]', '[BACKUP]']) else 'info'
            self._log_text.insert('end', line + '\n', tag)
        self._log_text.tag_config('err',  foreground='#f87171')
        self._log_text.tag_config('ok',   foreground='#4ade80')
        self._log_text.tag_config('info', foreground='#94a3b8')
        self._log_text.config(state='disabled')
        self._log_text.see('end')

    def _clear_log(self):
        self._log_lines.clear()
        self._redraw_log()

    # ── 7. TIMELINE ──────────────────────────────────────────────────
    def _panel_timeline(self):
        self._topbar('Timeline sự cố',
                     'Dòng thời gian ứng phó — T+Xs kể từ khi phát hiện tấn công')
        body = tk.Frame(self._content, bg=BG, padx=22, pady=14)
        body.pack(fill='both', expand=True)
        _sw = tk.Frame(body, bg=BG)
        _sw.pack(fill='both', expand=True)
        _sw.grid_rowconfigure(0, weight=1)
        _sw.grid_columnconfigure(0, weight=1)
        sc = tk.Canvas(_sw, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(_sw, orient='vertical', command=sc.yview)
        sc.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky='ns')
        sc.grid(row=0, column=0, sticky='nsew')
        self._timeline_body = tk.Frame(sc, bg=BG, padx=8, pady=8)
        win = sc.create_window((0, 0), window=self._timeline_body, anchor='nw')
        self._timeline_body.bind('<Configure>',
            lambda e: sc.configure(scrollregion=sc.bbox('all')))
        sc.bind('<Configure>', lambda e: sc.itemconfig(win, width=e.width))
        self._redraw_timeline()

    def _redraw_timeline(self):
        if not hasattr(self, '_timeline_body') or not self._timeline_body.winfo_exists():
            return
        for w in self._timeline_body.winfo_children():
            w.destroy()

        _cat_color = {'attack': RED, 'defense': GRN, 'warning': AMB, 'info': MUTED}

        if not self._incident_actions:
            tk.Label(self._timeline_body,
                     text='Chưa có sự kiện. Timeline tự cập nhật khi tấn công xảy ra.',
                     font=SF, bg=BG, fg=MUTED).pack(anchor='w', pady=20)
            return

        t0 = self._attack_detected_at
        for ts, text, cat in self._incident_actions:
            row = tk.Frame(self._timeline_body, bg=BG)
            row.pack(fill='x', pady=2)

            if t0 is not None:
                delta = int((ts - t0).total_seconds())
                badge = f'T{"+" if delta >= 0 else ""}{delta}s'
            else:
                badge = ts.strftime('%H:%M:%S')

            tk.Label(row, text=badge, font=('Courier New', 14),
                     bg=BG, fg=MUTED, width=10, anchor='e').pack(side='left')
            tk.Label(row, text='●', font=SFS,
                     bg=BG, fg=_cat_color.get(cat, MUTED), padx=6).pack(side='left')
            tk.Label(row, text=text, font=SF, bg=BG, fg=TEXT,
                     anchor='w', wraplength=900).pack(side='left', fill='x', expand=True)

    # ── Background watcher (HIDS — per-file tracking) ────────────────
    def _watch_loop(self):
        # Build initial state
        try:
            known_encrypted = set(
                os.path.join(_VICTIM_DIR, f)
                for f in os.listdir(_VICTIM_DIR)
                if f.endswith('.encrypted')
            )
        except Exception:
            known_encrypted = set()

        while True:
            time.sleep(1)
            try:
                current = set(
                    os.path.join(_VICTIM_DIR, f)
                    for f in os.listdir(_VICTIM_DIR)
                    if f.endswith('.encrypted')
                )
            except Exception:
                current = known_encrypted.copy()

            new_files = current - known_encrypted

            for fpath in sorted(new_files):
                fname = os.path.basename(fpath)
                orig  = fname[:-len('.encrypted')]
                self._emit_event(f'⚠ ENCRYPT: {orig} → {fname}', 'attack')
                self._log(f'[NGUY HIỂM] File bị mã hóa: {fname}')

            if new_files and not self._under_attack:
                self._attack_detected_at = datetime.now()
                self._under_attack = True
                self._attack_start_enc = len(known_encrypted)
                self.root.after(0, self._auto_respond)
            elif new_files and self._under_attack:
                # Still encrypting after auto-respond triggered
                self.root.after(0, self._update_defense_steps)

            known_encrypted = current

            # Periodic UI refresh
            self.root.after(0, self._update_dashboard_stats)
            self.root.after(0, self._update_defense_steps)
            if self._active_panel == 'detect':
                self.root.after(0, self._refresh_detect_indicators)

    # ── Auto-respond: step-by-step visual defense ────────────────────
    def _auto_respond(self):
        self._emit_event('━━━ HIDS PHÁT HIỆN TẤN CÔNG RANSOMWARE ━━━', 'warning')
        self._log('[NGUY HIỂM] HIDS kích hoạt ứng phó tự động!')
        self._record_action('HIDS phát hiện ransomware — kích hoạt auto-respond', 'attack')
        self._set_phase_active('identification')

        STEP_DELAY = 10000  # ms giữa mỗi bước — điều chỉnh ở đây nếu muốn nhanh/chậm hơn

        def step1():
            self._emit_event('', 'info')
            self._emit_event('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'warning')
            self._emit_event('🔴  HIDS PHÁT HIỆN TẤN CÔNG RANSOMWARE!', 'attack')
            self._emit_event('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'warning')
            self._emit_event('', 'info')
            self._emit_event('🔍 [BƯỚC 1/4] Xác nhận & Phân loại mối đe dọa', 'warning')
            self._emit_event('   Phương pháp phát hiện: Extension scan (.encrypted)', 'info')
            self._emit_event('   Phương pháp phát hiện: Disk I/O bất thường (đọc → xóa)', 'info')
            enc = _count_encrypted(_VICTIM_DIR)
            self._emit_event(f'   Kết quả: {enc} file đã bị mã hóa tính đến thời điểm này', 'attack')
            self._emit_event('   → Xác nhận: ĐÂY LÀ TẤN CÔNG RANSOMWARE', 'attack')
            self._advance_phase('identification')
            self.root.after(STEP_DELAY, step2)

        def step2():
            self._emit_event('', 'info')
            self._emit_event('🔒 [BƯỚC 2/4] Cô lập — Dừng tiến trình độc hại', 'defense')
            self._emit_event('   Mục đích: Ngăn tiến trình tiếp tục mã hóa thêm file', 'info')
            killed = []
            for name in _BAD_PROCS:
                try:
                    r = subprocess.run(['pkill', '-f', name], capture_output=True)
                    if r.returncode == 0:
                        killed.append(name)
                except FileNotFoundError:
                    pass
            if killed:
                for k in killed:
                    self._emit_event(f'   → pkill {k}: THÀNH CÔNG ✓', 'defense')
                self._log(f'[OK] Auto-kill tiến trình: {", ".join(killed)}')
                self._record_action(f'Auto-kill: {", ".join(killed)}', 'defense')
            else:
                self._emit_event('   → Không tìm thấy tiến trình đang chạy', 'info')
                self._emit_event('   (Tiến trình có thể đã tự thoát sau khi mã hóa xong)', 'info')
                self._log('[OK] Không tìm thấy tiến trình — có thể đã tự thoát')
            self._advance_phase('containment')
            # Bật maintenance mode
            flag = os.path.join(_root, 'MAINTENANCE.flag')
            with open(flag, 'w') as fh:
                fh.write(f'Auto maintenance mode at {datetime.now()}\n')
            self._emit_event('   → Bật Maintenance Mode: giao dịch mới đã bị dừng ✓', 'defense')
            self._log('[OK] Auto Maintenance Mode')
            self._record_action('Auto Maintenance Mode', 'defense')
            self.root.after(STEP_DELAY, step3)

        def step3():
            self._emit_event('', 'info')
            self._emit_event('💾 [BƯỚC 3/4] Backup khẩn cấp dữ liệu còn lại', 'defense')
            self._emit_event('   Mục đích: Lưu toàn bộ file CHƯA bị mã hóa vào backup', 'info')
            self._emit_event('   Lưu ý: File ĐÃ bị mã hóa vẫn sẽ có trong backup này', 'warning')
            self._emit_event('   → Đang tạo archive tar.gz...', 'info')
            self._set_phase_active('emergency_bak')
            self._log('[BACKUP] Bắt đầu backup khẩn cấp...')
            threading.Thread(target=_do_emergency_backup, daemon=True).start()

        def _do_emergency_backup():
            src, bak = self._src_dir.get(), self._bak_dir.get()
            try:
                os.makedirs(bak, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                archive_name = f'backup_emergency_{timestamp}.tar.gz'
                archive_path = os.path.join(bak, archive_name)
                import tarfile
                with tarfile.open(archive_path, 'w:gz') as tar:
                    tar.add(src, arcname=os.path.basename(src))
                self._emergency_backup_path = archive_path
                size_kb = os.path.getsize(archive_path) / 1024
                self._log(f'[BACKUP] Backup khẩn cấp: {archive_name} ({size_kb:.0f} KB)')
                self._record_action(f'Backup khẩn cấp: {archive_name}', 'defense')
                self.root.after(0, lambda: self._emit_event(
                    f'   → Backup xong: {archive_name} ({size_kb:.0f} KB) ✓', 'defense'))
                self._advance_phase('emergency_bak')
                self.root.after(0, self._try_refresh_backup_list)
                self.root.after(STEP_DELAY, step4)
            except Exception as e:
                self._log(f'[LỖI] Backup khẩn cấp thất bại: {e}')
                self.root.after(0, lambda: self._emit_event(
                    f'   → BACKUP THẤT BẠI: {e}', 'attack'))
                self.root.after(STEP_DELAY, step4)

        def step4():
            enc   = _count_encrypted(_VICTIM_DIR)
            total = _count_total_files(_VICTIM_DIR)
            safe  = total - enc
            self._emit_event('', 'info')
            self._emit_event('📋 [BƯỚC 4/4] Đánh giá mức độ thiệt hại', 'warning')
            self._emit_event(f'   File bị mã hóa (MẤT):  {enc} file', 'attack' if enc else 'info')
            self._emit_event(f'   File còn nguyên vẹn:    {safe} file', 'defense')
            self._emit_event('', 'info')
            if self._emergency_backup_path:
                self._emit_event('   Backup khẩn cấp: CÓ ✓', 'defense')
                self._emit_event('   → Có thể khôi phục phần dữ liệu chưa bị mã hóa', 'defense')
                self._emit_event('   → File bị mã hóa TRƯỚC backup: vẫn mất nếu không có key', 'warning')
            else:
                self._emit_event('   Backup khẩn cấp: KHÔNG CÓ ✗', 'attack')
                self._emit_event('   → Tất cả file bị mã hóa sẽ mất nếu không trả tiền chuộc!', 'attack')
            self._emit_event('', 'info')
            self._emit_event('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'defense')
            self._emit_event('✓  QUY TRÌNH PHÒNG THỦ HOÀN TẤT', 'defense')
            self._emit_event('   → Xem "Backup & Khôi phục" để restore dữ liệu', 'info')
            self._emit_event('   → Xem "Báo cáo sự cố" để tổng kết', 'info')
            self._emit_event('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'defense')
            self._advance_phase('assessment')
            self._log(f'[OK] Auto-respond hoàn tất — {enc} file bị mã hóa, {safe} file an toàn')
            self._record_action(f'Đánh giá: {enc} file bị mã hóa, {safe} file an toàn', 'warning')
            self.root.after(0, self._update_defense_steps)

            def _show_warn_then_step5():
                messagebox.showwarning(
                    '🔴  CẢNH BÁO — Phát hiện Ransomware',
                    f'HIDS đã phát hiện và ứng phó tự động!\n\n'
                    f'📁  File bị mã hóa:    {enc}\n'
                    f'📁  File an toàn:       {safe}\n\n'
                    f'Đã thực hiện:\n'
                    f'  ✓ Xác nhận tấn công ransomware\n'
                    f'  ✓ Dừng tiến trình độc hại\n'
                    f'  ✓ Bật Maintenance Mode\n'
                    f'  ✓ Backup khẩn cấp dữ liệu\n\n'
                    f'→ Tiếp theo: tự động tìm backup sạch và khôi phục...'
                )
                self.root.after(2000, step5)

            self.root.after(500, _show_warn_then_step5)

        def step5():
            self._emit_event('', 'info')
            self._emit_event('♻ [BƯỚC 5/5] Tự động khôi phục dữ liệu', 'defense')
            self._set_phase_active('recovery')

            attack_time = self._get_attack_time()
            if attack_time is None:
                self._emit_event('   ⚠ Không xác định được thời điểm tấn công — bỏ qua auto-restore', 'warning')
                self._record_action('Auto-restore bỏ qua: không xác định attack_time', 'warning')
                self._advance_phase('recovery')
                return

            self._emit_event(f'   Thời điểm tấn công: {attack_time.strftime("%H:%M:%S %d/%m/%Y")}', 'info')

            mgr  = BackupManager(self._src_dir.get(), self._bak_dir.get())
            best = None
            for bk in mgr.list_backups():
                bk_time = self._parse_backup_time(bk)
                if bk_time and bk_time < attack_time:
                    best = bk

            if best is None:
                self._emit_event('   ⚠ Không có backup sạch nào trước thời điểm tấn công', 'warning')
                self._emit_event('   → Vui lòng restore thủ công trong "Backup & Khôi phục"', 'info')
                self._record_action('Auto-restore bỏ qua: không có backup trước tấn công', 'warning')
                self._advance_phase('recovery')
                return

            bk_time   = self._parse_backup_time(best)
            best_name = os.path.basename(best)
            self._emit_event(f'   Backup được chọn: {best_name}', 'info')
            self._emit_event(f'   Tạo lúc: {bk_time.strftime("%H:%M:%S %d/%m/%Y")}', 'info')
            self._emit_event('   Đây là backup sạch cuối cùng trước khi bị tấn công.', 'defense')

            if not messagebox.askyesno(
                '♻ Tự động khôi phục dữ liệu',
                f'Backup sạch trước tấn công:\n\n'
                f'  📦  {best_name}\n'
                f'  🕐  {bk_time.strftime("%H:%M:%S %d/%m/%Y")}\n\n'
                f'Khôi phục sẽ ghi đè dữ liệu hiện tại trong:\n'
                f'  {self._src_dir.get()}\n\n'
                f'Tiếp tục khôi phục?'
            ):
                self._emit_event('   → Người dùng từ chối khôi phục tự động', 'warning')
                self._record_action('Auto-restore bị từ chối bởi người dùng', 'warning')
                self._advance_phase('recovery')
                return

            self._emit_event('   → Đang khôi phục...', 'info')
            self._record_action(f'Bắt đầu auto-restore: {best_name}', 'defense')

            def _do_auto_restore():
                try:
                    mgr.restore(best, self._src_dir.get())
                    self._log(f'[OK] Auto-restore thành công: {best_name}')
                    self._record_action(f'Auto-restore thành công: {best_name}', 'defense')
                    self.root.after(0, lambda: self._emit_event('   ✓ KHÔI PHỤC HOÀN TẤT', 'defense'))
                    self._advance_phase('recovery')
                    self.root.after(0, self._try_refresh_backup_list)
                    self.root.after(0, lambda: messagebox.showinfo(
                        '✓ Khôi phục thành công',
                        f'Dữ liệu đã được khôi phục từ:\n{best_name}'))
                except Exception as e:
                    self._log(f'[LỖI] Auto-restore thất bại: {e}')
                    self._record_action(f'Auto-restore thất bại: {e}', 'attack')
                    self.root.after(0, lambda: self._emit_event(
                        f'   ✗ Restore thất bại: {e}', 'attack'))
                    self._advance_phase('recovery')

            threading.Thread(target=_do_auto_restore, daemon=True).start()

        self.root.after(3000, step1)  # 3s pause — cho người trình bày giải thích banner đỏ trước

    # ── Backup logic ─────────────────────────────────────────────────
    def _run_backup(self):
        src, bak = self._src_dir.get(), self._bak_dir.get()
        if not os.path.isdir(src):
            self._log(f'[LỖI] Thư mục nguồn không tồn tại: {src}')
            return
        try:
            os.makedirs(bak, exist_ok=True)
            mgr  = BackupManager(src, bak, max_backups=self._max_backups.get())
            path = mgr.backup()
            size = os.path.getsize(path) / 1024
            self._last_bk_time = datetime.now()
            self._last_bk_name = os.path.basename(path)
            self._log(f'[BACKUP] {os.path.basename(path)} ({size:.0f} KB)')
            self._record_action(f'Backup: {os.path.basename(path)}', 'defense')
            self._emit_event(f'💾 Backup thành công: {os.path.basename(path)}', 'defense')
            self.root.after(0, self._try_refresh_backup_list)
            if hasattr(self, '_bk_status_lbl'):
                self.root.after(0, lambda: self._bk_status_lbl.config(
                    text=f'✓ {datetime.now().strftime("%H:%M:%S")}', fg=GRN))
        except Exception as e:
            self._log(f'[LỖI] Backup thất bại: {e}')

    def _try_refresh_backup_list(self):
        if self._active_panel == 'backup' and hasattr(self, '_bk_list_frame'):
            self._refresh_backup_list()

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

    def _last_backup_display(self) -> str:
        if not self._last_bk_time:
            return 'Chưa có backup'
        return f'{self._last_bk_time.strftime("%H:%M %d/%m")} — {self._last_bk_name}'

    # ── Helpers ──────────────────────────────────────────────────────
    def _record_action(self, text: str, category: str = 'info'):
        self._incident_actions.append((datetime.now(), text, category))

    @staticmethod
    def _parse_backup_time(backup_path: str):
        stem = os.path.basename(backup_path)
        if stem.endswith('.tar.gz'):
            stem = stem[:-7]
        m = re.search(r'(\d{8}_\d{6})$', stem)
        if not m:
            return None
        try:
            return datetime.strptime(m.group(1), '%Y%m%d_%H%M%S')
        except ValueError:
            return None

    def _get_attack_time(self):
        if self._attack_detected_at is not None:
            return self._attack_detected_at
        flag = os.path.join(_root, 'MAINTENANCE.flag')
        try:
            with open(flag) as fh:
                m = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', fh.readline())
            if m:
                return datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
        except (OSError, ValueError):
            pass
        return None

    def _log(self, msg: str):
        ts   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f'[{ts}]  {msg}'
        self._log_lines.append(line)
        self._status_var.set(msg[:90])
        self.root.after(0, self._redraw_log)

    def _tick(self):
        self._clock_var.set(datetime.now().strftime('%H:%M:%S  %d/%m/%Y'))
        if self._active_panel == 'backup' and hasattr(self, '_next_bk_lbl'):
            self._next_bk_lbl.config(text=self._next_backup_str())
        if self._active_panel == 'dashboard':
            if hasattr(self, '_dash_bk_next_var'):
                self._dash_bk_next_var.set(self._next_backup_str())
            if hasattr(self, '_dash_bk_last_var'):
                self._dash_bk_last_var.set(self._last_backup_display())
        # Pulse the dot on dashboard live feed
        if self._active_panel == 'dashboard' and hasattr(self, '_attack_status_dot'):
            if self._attack_status_dot.winfo_exists():
                color = '#f87171' if self._under_attack else '#4ade80'
                cur = self._attack_status_dot.cget('fg')
                self._attack_status_dot.config(fg='#0d1117' if cur == color else color)
        if self._active_panel == 'timeline':
            self._redraw_timeline()
        self.root.after(1000, self._tick)

    def run(self):
        self._log('[OK] DefenderPro khởi động — Hệ thống HIDS sẵn sàng')
        self._log('[OK] Giai đoạn Chuẩn bị hoàn tất — đang giám sát shop_data/')
        self.root.mainloop()


if __name__ == '__main__':
    DefenderApp().run()
