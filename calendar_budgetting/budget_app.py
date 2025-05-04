import tkinter as tk
from tkinter import simpledialog, messagebox
import calendar
from datetime import datetime
import sqlite3

# === Database Setup ===
conn = sqlite3.connect("budget.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS budget (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    title TEXT,
    amount REAL,
    description TEXT
)
""")
conn.commit()

# === Main App ===
class BudgetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Budget Calendar")
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.month_colors = {
            1: "#FFDDEE",  # Soft Pink
            2: "#D0F0C0",  # Tea Green
            3: "#FFFACD",  # LemonChiffon
            4: "#E6E6FA",  # Lavender
            5: "#F0FFF0",  # Honeydew
            6: "#E0FFFF",  # LightCyan
            7: "#FFEFD5",  # PapayaWhip
            8: "#FFF0F5",  # LavenderBlush
            9: "#F5F5DC",  # Beige
            10: "#FDF5E6", # OldLace
            11: "#FAFAD2", # LightGoldenrodYellow
            12: "#F0F8FF"  # AliceBlue
        }
        self.load_ui()

    def get_entries(self, date):
        cursor.execute("SELECT * FROM budget WHERE date=?", (date,))
        return cursor.fetchall()

    def get_month_net(self):
        start = f"{self.current_year}-{self.current_month:02d}-01"
        end = f"{self.current_year}-{self.current_month:02d}-31"
        cursor.execute("SELECT SUM(amount) FROM budget WHERE date BETWEEN ? AND ?", (start, end))
        total = cursor.fetchone()[0]
        return total or 0

    def load_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        month_bg = self.month_colors.get(self.current_month, "#F0F0F0")
        self.root.configure(bg=month_bg)

        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(tuple(range(7)), weight=1)

        # Monthly Net Summary
        net_total = self.get_month_net()
        color = "green" if net_total >= 0 else "red"
        tk.Label(self.root, text=f"Net Total: ${net_total:.2f}", font=("Arial", 14, "bold"), fg=color, bg=month_bg)\
            .grid(row=0, column=0, columnspan=7, pady=(5, 10))

        # Month navigation
        tk.Button(self.root, text="<", command=self.prev_month, bg=month_bg).grid(row=1, column=0, padx=10)
        tk.Label(self.root, text=f"{calendar.month_name[self.current_month]} {self.current_year}", 
                 font=("Arial", 16, "bold"), bg=month_bg).grid(row=1, column=1, columnspan=5)
        tk.Button(self.root, text=">", command=self.next_month, bg=month_bg).grid(row=1, column=6, padx=10)

        # Day labels
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for idx, day in enumerate(days):
            fg = "#007BFF" if day in ["Sat", "Sun"] else "black"
            tk.Label(self.root, text=day, font=("Arial", 10, "bold"), fg=fg, bg=month_bg).grid(row=2, column=idx, pady=2)

        # Day cells
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.itermonthdays(self.current_year, self.current_month)
        row, col = 3, 0
        today = datetime.now().date()

        for day in month_days:
            if day == 0:
                tk.Label(self.root, text="", bg=month_bg).grid(row=row, column=col)
            else:
                date_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
                day_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                bg = "#FFDDDD" if day_date == today else month_bg

                frame = tk.Frame(self.root, bg=bg, borderwidth=1, relief="solid")
                frame.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
                self.root.grid_columnconfigure(col, weight=1)
                self.root.grid_rowconfigure(row, weight=1)

                tk.Label(frame, text=str(day), bg=bg, font=("Arial", 9, "bold")).pack(anchor="nw", padx=2, pady=2)

                for entry in self.get_entries(date_str):
                    entry_color = "#FF9999" if entry[3] < 0 else "#C3F3C3"
                    tk.Button(frame, text=f"{entry[2]}: ${entry[3]:.2f}", font=("Arial", 8),
                              bg=entry_color, command=lambda eid=entry[0]: self.edit_entry(eid))\
                        .pack(anchor="w", padx=2, pady=1)

                frame.bind("<Button-1>", lambda e, d=date_str: self.add_entry(d))
            col += 1
            if col > 6:
                col = 0
                row += 1

    def add_entry(self, date):
        title = simpledialog.askstring("Title", "Enter title:", parent=self.root)
        if not title:
            return
        amount = simpledialog.askfloat("Amount", "Enter amount:", parent=self.root)
        if amount is None:
            return
        description = simpledialog.askstring("Description", "Enter description:", parent=self.root)

        cursor.execute("INSERT INTO budget (date, title, amount, description) VALUES (?, ?, ?, ?)",
                       (date, title, amount, description))
        conn.commit()
        self.load_ui()

    def edit_entry(self, entry_id):
        cursor.execute("SELECT * FROM budget WHERE id=?", (entry_id,))
        entry = cursor.fetchone()
        if not entry:
            return

        popup = tk.Toplevel(self.root)
        popup.title("Edit Budget Entry")
        popup.geometry("300x250")

        popup.transient(self.root)
        popup.grab_set()
        popup.focus_force()
        popup.lift()

        tk.Label(popup, text="Title").pack(pady=5)
        title_entry = tk.Entry(popup)
        title_entry.pack()
        title_entry.insert(0, entry[2])

        tk.Label(popup, text="Amount").pack(pady=5)
        amount_entry = tk.Entry(popup)
        amount_entry.pack()
        amount_entry.insert(0, str(entry[3]))

        tk.Label(popup, text="Description").pack(pady=5)
        desc_entry = tk.Entry(popup)
        desc_entry.pack()
        desc_entry.insert(0, entry[4])

        def update_entry():
            new_title = title_entry.get()
            new_amount = float(amount_entry.get())
            new_desc = desc_entry.get()

            cursor.execute("UPDATE budget SET title=?, amount=?, description=? WHERE id=?",
                           (new_title, new_amount, new_desc, entry_id))
            conn.commit()
            popup.destroy()
            self.load_ui()

        def delete_entry():
            if messagebox.askyesno("Delete", "Are you sure you want to delete this entry?", parent=popup):
                cursor.execute("DELETE FROM budget WHERE id=?", (entry_id,))
                conn.commit()
                popup.destroy()
                self.load_ui()

        tk.Button(popup, text="Update", command=update_entry).pack(pady=5)
        tk.Button(popup, text="Delete", command=delete_entry).pack(pady=5)
        tk.Button(popup, text="Cancel", command=popup.destroy).pack(pady=5)

    def prev_month(self):
        self.current_month -= 1
        if self.current_month == 0:
            self.current_month = 12
            self.current_year -= 1
        self.load_ui()

    def next_month(self):
        self.current_month += 1
        if self.current_month == 13:
            self.current_month = 1
            self.current_year += 1
        self.load_ui()

# === Run the App ===
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = BudgetApp(root)
    root.mainloop()
