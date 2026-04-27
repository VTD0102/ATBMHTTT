import os
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
BG2    = '#1a0000'
BORDER = '#ff3333'

FONT       = ('Courier New', 10)
FONT_BOLD  = ('Courier New', 10, 'bold')
FONT_BIG   = ('Courier New', 16, 'bold')
FONT_HUGE  = ('Courier New', 28, 'bold')
FONT_SMALL = ('Courier New', 9)
FONT_TIMER = ('Courier New', 32, 'bold')


class FakeRansomApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('⚠ YOUR FILES HAVE BEEN ENCRYPTED')
        self.root.geometry('700x700')
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        # Outer border wrapper
        outer = tk.Frame(self.root, relief='solid', bd=2, bg=BORDER)
        outer.pack(fill='both', expand=True, padx=4, pady=4)
        inner = tk.Frame(outer, bg=BG)
        inner.pack(fill='both', expand=True, padx=2, pady=2)

        # Scrollable canvas so all content fits
        canvas = tk.Canvas(inner, bg=BG, highlightthickness=0)
        canvas.pack(fill='both', expand=True)
        content = tk.Frame(canvas, bg=BG)
        canvas.create_window((350, 0), window=content, anchor='n')

        def _on_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))

        content.bind('<Configure>', _on_configure)

        main = tk.Frame(content, bg=BG)
        main.pack(padx=30, pady=20)

        # ── 1. Skull + title ──────────────────────────────
        tk.Label(main, text='\U0001f480', font=('Courier New', 48),
                 bg=BG, fg=FG).pack()

        self._title_label = tk.Label(
            main, text='YOUR FILES HAVE BEEN ENCRYPTED',
            font=FONT_BIG, bg=BG, fg=FG
        )
        self._title_label.pack(pady=(4, 10))

        # ── 2. Message ────────────────────────────────────
        msg = (
            'All data in your system has been encrypted.\n'
            'Files: invoice_2024.txt, customer_data.csv, contract.txt\n'
            'have been converted to .encrypted format.'
        )
        tk.Label(main, text=msg, font=FONT, bg=BG, fg=FG_DIM,
                 justify='center').pack(pady=(0, 14))

        # ── 3. Timer ──────────────────────────────────────
        self._seconds_left = 72 * 3600 - 1
        self._timer_var = tk.StringVar()
        self._update_timer_display()
        tk.Label(main, textvariable=self._timer_var, font=FONT_TIMER,
                 bg=BG, fg=AMBER).pack()

        # ── 4. Warning ────────────────────────────────────
        tk.Label(
            main,
            text='You have 72 hours to pay. After deadline, the key will be permanently deleted.',
            font=FONT, bg=BG, fg=FG_DIM, wraplength=620, justify='center'
        ).pack(pady=(8, 16))

        # ── 5. Payment section ────────────────────────────
        pay_frame = tk.Frame(main, bg=BG2)
        pay_frame.pack(fill='x', padx=0, pady=(0, 16))
        pay_inner = tk.Frame(pay_frame, bg=BG2, padx=16, pady=12)
        pay_inner.pack(fill='x')

        tk.Label(
            pay_inner,
            text='\U0001f4b3 PAYMENT INFORMATION TO RECEIVE DECRYPT CODE',
            font=FONT_BOLD, bg=BG2, fg=FG
        ).pack(anchor='w', pady=(0, 6))

        # Horizontal separator
        tk.Frame(pay_inner, bg=FG, height=1).pack(fill='x', pady=(0, 8))

        try:
            computer_name = socket.gethostname()
        except Exception:
            computer_name = 'YOUR-PC'

        rows = [
            ('Bank',            'BIDV — PGD Moc Chau'),
            ('Account Owner',   'VU TRUNG DUC'),
            ('Account Number',  '4120271561'),
            ('Transfer Note',   f'UNLOCK {computer_name}'),
            ('After payment',   'Email: support@promanager.io'),
        ]
        for label_text, value_text in rows:
            row = tk.Frame(pay_inner, bg=BG2)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=label_text, font=FONT, bg=BG2, fg=FG_MUT,
                     width=18, anchor='w').pack(side='left')
            tk.Label(row, text=value_text, font=FONT, bg=BG2, fg=FG_DIM,
                     anchor='w').pack(side='left')

        # Total row
        total_row = tk.Frame(pay_inner, bg=BG2)
        total_row.pack(fill='x', pady=(8, 0))
        tk.Label(total_row, text='TOTAL AMOUNT', font=FONT_BOLD, bg=BG2, fg=FG,
                 width=18, anchor='w').pack(side='left')
        tk.Label(total_row, text='59,000,000 VND',
                 font=('Courier New', 18, 'bold'), bg=BG2, fg=AMBER,
                 anchor='w').pack(side='left')

        # ── 6. Unlock input section ───────────────────────
        tk.Label(main, text='Enter decrypt code:', font=FONT,
                 bg=BG, fg=FG_MUT).pack(pady=(0, 4))

        self._code_var = tk.StringVar()
        entry = tk.Entry(
            main, textvariable=self._code_var,
            bg='#1a1a1a', fg=FG, insertbackground=FG,
            font=FONT, relief='flat', bd=1,
            highlightthickness=1, highlightcolor=FG,
            highlightbackground='#330000', width=30
        )
        entry.pack(pady=(0, 8))
        entry.bind('<Return>', lambda e: self._check_code())

        tk.Button(
            main, text='UNLOCK FILES',
            bg=FG, fg='#000000', font=FONT_BOLD,
            relief='flat', padx=20, pady=8,
            activebackground='#cc0000', activeforeground='#000000',
            cursor='hand2', command=self._check_code
        ).pack(pady=(0, 6))

        self._result_var = tk.StringVar()
        self._result_label = tk.Label(
            main, textvariable=self._result_var,
            font=FONT, bg=BG, fg=FG
        )
        self._result_label.pack()

        # ── 7. DEMO badge (fixed bottom-right) ───────────
        badge = tk.Label(
            self.root, text='  ⚠ DEMO ONLY  ',
            font=FONT_SMALL, bg='#1a3a1a', fg=GRN,
            bd=1, relief='solid'
        )
        badge.place(relx=1.0, rely=1.0, anchor='se', x=-8, y=-8)

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
                ' Run: python attacker/ransomware_simulator.py decrypt'
            )
        else:
            attempts_left = random.randint(1, 5)
            self._result_label.configure(fg=FG)
            self._result_var.set(
                f'✗ Wrong code. {attempts_left} attempts remaining.'
            )

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    FakeRansomApp().run()
