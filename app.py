import tkinter as tk
from tkinter import messagebox, filedialog
from keygen import generate_key
import db
import auth

db.init_db()
db.delete_expired()

root.configure(bg="#1e1e1e")
root = tk.Tk()
root.title("VIP PANEL ADMIN")
root.geometry("600x500")

# ===== LOGIN =====
login_frame = tk.Frame(root)
login_frame.pack(pady=50)

tk.Label(root, text="Admin Login", bg="#1e1e1e", fg="white").pack()

user = tk.Entry(login_frame)
user.pack()

pw = tk.Entry(login_frame, show="*")
pw.pack()

def do_login():
    if auth.login(user.get(), pw.get()):
        login_frame.pack_forget()
        main_frame.pack(fill="both", expand=True)
        refresh_keys()
    else:
        messagebox.showerror("Error", "Login gagal")

tk.Button(login_frame, text="Login", command=do_login).pack(pady=10)

# ===== MAIN =====
main_frame = tk.Frame(root)

var = tk.StringVar()

tk.Radiobutton(main_frame, text="1D", variable=var, value="1D").pack()
tk.Radiobutton(main_frame, text="7D", variable=var, value="7D").pack()
tk.Radiobutton(main_frame, text="30D", variable=var, value="30D").pack()
tk.Radiobutton(main_frame, text="LIFE", variable=var, value="LIFE").pack()

text = tk.Text(main_frame, height=5)
text.pack()

def generate_keys():
    key_type = var.get()

    if not key_type:
        return

    duration = {
        "1D": 86400000,
        "7D": 7*86400000,
        "30D": 30*86400000,
        "LIFE": 0
    }

    text.delete("1.0", tk.END)

    for i in range(10):
        key = generate_key(key_type)
        db.save_key(key, key_type, duration[key_type])
        text.insert(tk.END, key + "\n")

    refresh_keys()

tk.Button(main_frame, text="Generate 10 Keys", command=generate_keys).pack()

search_var = tk.StringVar()

tk.Entry(main_frame, textvariable=search_var).pack()

def search_key():
    keyword = search_var.get()
    listbox.delete(0, tk.END)

    for k in db.get_all_keys():
        if keyword.lower() in k[0].lower():
            listbox.insert(tk.END, f"{k[0]} | {k[2]} | {k[5]}")

tk.Button(main_frame, text="Search", command=search_key).pack()

# ===== LIST KEY =====
listbox = tk.Listbox(main_frame)
listbox.pack(fill="both", expand=True)

def refresh_keys():
    listbox.delete(0, tk.END)
    for k in db.get_all_keys():
        listbox.insert(tk.END, f"{k[0]} | {k[2]} | {k[5]}")

tk.Button(main_frame, text="Refresh", command=refresh_keys).pack()

# ===== ACTION =====
def delete_selected():
    sel = listbox.get(tk.ACTIVE)
    key = sel.split(" | ")[0]
    db.delete_key(key)
    refresh_keys()

def blacklist_selected():
    sel = listbox.get(tk.ACTIVE)
    key = sel.split(" | ")[0]
    db.blacklist_key(key)
    refresh_keys()

def export_keys():
    file = filedialog.asksaveasfilename(defaultextension=".txt")
    if file:
        with open(file, "w") as f:
            for k in db.get_all_keys():
                f.write(k[0] + "\n")

tk.Button(main_frame, text="Delete Key", command=delete_selected).pack()
tk.Button(main_frame, text="Blacklist Key", command=blacklist_selected).pack()
tk.Button(main_frame, text="Export Keys", command=export_keys).pack()

root.mainloop()