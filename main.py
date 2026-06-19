import tkinter as tk
from tkinter import messagebox, font
import mysql.connector
import uuid
import random
import string
from datetime import datetime

# ─────────────────────────────────────────────
#  DB CONNECTION
# ─────────────────────────────────────────────
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="<your_password>",
        database="<your_database>"
    )

db = get_connection()

# ─────────────────────────────────────────────
#  ID GENERATORS
# ─────────────────────────────────────────────
def generate_customer_id():
    """CUS-XXXX-XXXX  (letters + digits)"""
    part = lambda n: ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))
    return f"CUS-{part(4)}-{part(4)}"

def generate_ticket_id():
    """TKT-XXXXXXXX  (8 hex chars from uuid4)"""
    return f"TKT-{uuid.uuid4().hex[:8].upper()}"

# ─────────────────────────────────────────────
#  DB HELPERS  (fresh cursor per call)
# ─────────────────────────────────────────────
def fetch_movies():
    cur = db.cursor()
    cur.execute("SELECT movie_id, movie_name FROM movies")
    rows = cur.fetchall()
    cur.close()
    return rows

def fetch_shows(movie_id):
    cur = db.cursor()
    cur.execute("SELECT show_id, show_time FROM shows WHERE movie_id=%s", (movie_id,))
    rows = cur.fetchall()
    cur.close()
    return rows

def get_or_create_user(name, email):
    cur = db.cursor()
    cur.execute("SELECT user_id, customer_id FROM users WHERE email=%s", (email,))
    row = cur.fetchone()
    cur.close()
    if row:
        return row[0], row[1]          # existing user_id, customer_id
    customer_id = generate_customer_id()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO users (name, email, customer_id) VALUES (%s, %s, %s)",
        (name, email, customer_id)
    )
    db.commit()
    user_id = cur.lastrowid
    cur.close()
    return user_id, customer_id

def seat_already_booked(show_id, seat_no):
    cur = db.cursor()
    cur.execute(
        "SELECT ticket_id FROM tickets WHERE show_id=%s AND seat_no=%s",
        (show_id, seat_no)
    )
    row = cur.fetchone()
    cur.close()
    return row is not None

def insert_ticket(user_id, show_id, seat_no):
    ticket_id = generate_ticket_id()
    cur = db.cursor()
    cur.execute(
        """INSERT INTO tickets (ticket_id, user_id, show_id, seat_no, payment_status, booked_at)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (ticket_id, user_id, show_id, seat_no, "Paid", datetime.now())
    )
    db.commit()
    cur.close()
    return ticket_id

# ─────────────────────────────────────────────
#  TICKET POPUP
# ─────────────────────────────────────────────
def show_ticket_popup(customer_id, ticket_ids, name, movie_name, show_time, seats):
    popup = tk.Toplevel(root)
    popup.title("Booking Confirmed")
    popup.geometry("480x520")
    popup.resizable(False, False)
    popup.configure(bg=BG)
    popup.grab_set()

    # Header bar
    header = tk.Frame(popup, bg=ACCENT, height=60)
    header.pack(fill="x")
    tk.Label(header, text="🎬  BOOKING CONFIRMED", font=(FONT_BOLD, 14),
             bg=ACCENT, fg="white").place(relx=0.5, rely=0.5, anchor="center")

    body = tk.Frame(popup, bg=BG, padx=30, pady=20)
    body.pack(fill="both", expand=True)

    def row(label, value, color=FG):
        f = tk.Frame(body, bg=BG)
        f.pack(fill="x", pady=4)
        tk.Label(f, text=label, font=(FONT, 10), bg=BG, fg=MUTED, anchor="w", width=16).pack(side="left")
        tk.Label(f, text=value, font=(FONT_BOLD, 10), bg=BG, fg=color, anchor="w").pack(side="left")

    # Divider
    def divider():
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=8)

    tk.Label(body, text="✔  Your ticket is ready!", font=(FONT_BOLD, 13),
             bg=BG, fg=SUCCESS).pack(anchor="w", pady=(0, 12))

    row("Customer ID",  customer_id, ACCENT)
    row("Name",         name)
    row("Movie",        movie_name)
    row("Show Time",    show_time)
    divider()
    row("Seats Booked", ", ".join(map(str, seats)))
    row("No. of Seats", str(len(seats)))
    divider()

    tk.Label(body, text="Ticket ID(s):", font=(FONT, 10), bg=BG, fg=MUTED, anchor="w").pack(fill="x")
    for tid in ticket_ids:
        tk.Label(body, text=f"  • {tid}", font=(FONT_MONO, 10), bg=BG, fg=ACCENT, anchor="w").pack(fill="x")

    divider()
    tk.Label(body, text="Payment Status:  PAID ✔", font=(FONT_BOLD, 10),
             bg=BG, fg=SUCCESS).pack(anchor="w")

    tk.Button(popup, text="Close", command=popup.destroy,
              bg=ACCENT, fg="white", font=(FONT_BOLD, 11),
              relief="flat", padx=20, pady=8, cursor="hand2").pack(pady=16)

# ─────────────────────────────────────────────
#  CORE BOOKING LOGIC
# ─────────────────────────────────────────────
def book_ticket():
    name  = name_entry.get().strip()
    email = email_entry.get().strip()
    seats_raw = seat_entry.get().strip()

    # ── Validation ──────────────────────────
    if not name:
        flash_error(name_entry, "Name is required")
        return
    if not email or "@" not in email:
        flash_error(email_entry, "Valid email is required")
        return
    if selected_movie_id.get() == "":
        messagebox.showerror("Error", "Please select a movie.")
        return
    if selected_show_id.get() == "":
        messagebox.showerror("Error", "Please select a show timing.")
        return
    if not seats_raw:
        flash_error(seat_entry, "Enter seat number(s)")
        return

    # Parse seats: accept comma-separated e.g. "A1, A2, B3"
    seats = [s.strip().upper() for s in seats_raw.split(",") if s.strip()]
    if not seats:
        flash_error(seat_entry, "Invalid seat format")
        return

    show_id    = selected_show_id.get()
    movie_name = selected_movie_name.get()
    show_time  = selected_show_time.get()

    # ── Duplicate seat check ─────────────────
    for seat in seats:
        if seat_already_booked(show_id, seat):
            messagebox.showerror("Seat Taken", f"Seat '{seat}' is already booked for this show.")
            return

    # ── DB write ─────────────────────────────
    try:
        user_id, customer_id = get_or_create_user(name, email)
        ticket_ids = []
        for seat in seats:
            tid = insert_ticket(user_id, show_id, seat)
            ticket_ids.append(tid)
    except mysql.connector.Error as e:
        db.rollback()
        messagebox.showerror("Database Error", str(e))
        return

    # ── Show ticket popup ────────────────────
    show_ticket_popup(customer_id, ticket_ids, name, movie_name, show_time, seats)
    clear_form()

def clear_form():
    seat_entry.delete(0, tk.END)
    # Keep name/email for repeat bookings — clear only seats

# ─────────────────────────────────────────────
#  LOAD DATA
# ─────────────────────────────────────────────
def load_movies():
    movie_listbox.delete(0, tk.END)
    movie_data.clear()
    for mid, mname in fetch_movies():
        movie_listbox.insert(tk.END, f"  {mname}")
        movie_data.append((str(mid), mname))

def on_movie_select(event):
    sel = movie_listbox.curselection()
    if not sel:
        return
    idx = sel[0]
    mid, mname = movie_data[idx]
    selected_movie_id.set(mid)
    selected_movie_name.set(mname)

    # Reset show selection
    selected_show_id.set("")
    selected_show_time.set("")
    show_listbox.delete(0, tk.END)
    show_data.clear()

    for sid, stime in fetch_shows(mid):
        show_listbox.insert(tk.END, f"  {stime}")
        show_data.append((str(sid), str(stime)))

    show_label.config(text=f"Select Show for  '{mname}'")

def on_show_select(event):
    sel = show_listbox.curselection()
    if not sel:
        return
    idx = sel[0]
    sid, stime = show_data[idx]
    selected_show_id.set(sid)
    selected_show_time.set(stime)

# ─────────────────────────────────────────────
#  UX HELPERS
# ─────────────────────────────────────────────
def flash_error(widget, msg):
    orig = widget.cget("highlightbackground") if widget.cget("highlightthickness") else BG
    widget.config(highlightthickness=2, highlightbackground=ERROR)
    messagebox.showerror("Validation Error", msg)
    widget.after(2000, lambda: widget.config(highlightthickness=0))

def on_entry_focus_in(e):
    e.widget.config(highlightthickness=2, highlightbackground=ACCENT)

def on_entry_focus_out(e):
    e.widget.config(highlightthickness=1, highlightbackground=BORDER)

def styled_entry(parent):
    e = tk.Entry(parent, font=(FONT, 11), bg=CARD, fg=FG,
                 insertbackground=FG, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER)
    e.bind("<FocusIn>",  on_entry_focus_in)
    e.bind("<FocusOut>", on_entry_focus_out)
    return e

def styled_listbox(parent, height=6):
    frame = tk.Frame(parent, bg=ACCENT, bd=1)
    lb = tk.Listbox(frame, font=(FONT, 11), bg=CARD, fg=FG,
                    selectbackground=ACCENT, selectforeground="white",
                    activestyle="none", relief="flat",
                    highlightthickness=0, height=height,
                    borderwidth=0)
    sb = tk.Scrollbar(frame, orient="vertical", command=lb.yview)
    lb.config(yscrollcommand=sb.set)
    lb.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return frame, lb

def section_label(parent, text):
    tk.Label(parent, text=text, font=(FONT_BOLD, 10),
             bg=BG, fg=MUTED).pack(anchor="w", pady=(14, 2))

# ─────────────────────────────────────────────
#  THEME
# ─────────────────────────────────────────────
BG      = "#0f1117"
CARD    = "#1a1d27"
ACCENT  = "#e63946"
FG      = "#eaeaea"
MUTED   = "#7a7f96"
BORDER  = "#2e3045"
ERROR   = "#ff4d6d"
SUCCESS = "#2ec27e"

FONT      = "Helvetica"
FONT_BOLD = "Helvetica"
FONT_MONO = "Courier"

# ─────────────────────────────────────────────
#  ROOT WINDOW
# ─────────────────────────────────────────────
root = tk.Tk()
root.title("CineBook")
root.geometry("520x740")
root.resizable(False, False)
root.configure(bg=BG)

# State
selected_movie_id   = tk.StringVar()
selected_movie_name = tk.StringVar()
selected_show_id    = tk.StringVar()
selected_show_time  = tk.StringVar()
movie_data = []   # [(movie_id, movie_name), ...]
show_data  = []   # [(show_id, show_time), ...]

# ── Header ──────────────────────────────────
header = tk.Frame(root, bg=ACCENT, height=64)
header.pack(fill="x")
header.pack_propagate(False)
tk.Label(header, text="🎬  CineBook", font=(FONT_BOLD, 20, "bold"),
         bg=ACCENT, fg="white").place(relx=0.5, rely=0.5, anchor="center")

# ── Main scroll canvas (optional future) ────
canvas = tk.Frame(root, bg=BG, padx=32, pady=20)
canvas.pack(fill="both", expand=True)

# Name
section_label(canvas, "FULL NAME  *")
name_entry = styled_entry(canvas)
name_entry.pack(fill="x", ipady=6)

# Email
section_label(canvas, "EMAIL ADDRESS  *")
email_entry = styled_entry(canvas)
email_entry.pack(fill="x", ipady=6)

# Movie list
section_label(canvas, "SELECT MOVIE")
movie_frame, movie_listbox = styled_listbox(canvas, height=5)
movie_frame.pack(fill="x")
movie_listbox.bind("<<ListboxSelect>>", on_movie_select)

# Show list
show_label_var = tk.StringVar(value="SELECT SHOW TIMING")
show_label = tk.Label(canvas, textvariable=show_label_var,
                      font=(FONT_BOLD, 10), bg=BG, fg=MUTED, anchor="w")

show_label.pack(anchor="w", pady=(14, 2))


show_frame, show_listbox = styled_listbox(canvas, height=4)
show_frame.pack(fill="x")
show_listbox.bind("<<ListboxSelect>>", on_show_select)

# Seats
section_label(canvas, "SEAT NUMBER(S)  — comma separated e.g. A1, A2")
seat_entry = styled_entry(canvas)
seat_entry.pack(fill="x", ipady=6)

# Book button
tk.Frame(canvas, bg=BG, height=10).pack()  # spacer
btn = tk.Button(canvas, text="BOOK TICKET  →",
                font=(FONT_BOLD, 13, "bold"),
                bg=ACCENT, fg="white", activebackground="#c1121f",
                activeforeground="white", relief="flat",
                cursor="hand2", command=book_ticket)
btn.pack(fill="x", ipady=12)

# Footer
tk.Label(root, text="© 2025 CineBook  •  All rights reserved",
         font=(FONT, 8), bg=BG, fg=MUTED).pack(pady=8)

# ── Load data ───────────────────────────────
load_movies()

root.mainloop()
db.close()
