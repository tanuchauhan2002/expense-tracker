#!/usr/bin/env python
# coding: utf-8

# In[1]:


"""
Personal Expense Tracker (SQL Server) - Final with Date Filter + Clear Filter
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
import matplotlib.pyplot as plt
import datetime
from decimal import Decimal
import traceback

# ---------------------------
# Configuration
# ---------------------------
CONN_STR = (
    'DRIVER={SQL Server};'
    'SERVER=ROOTUSER\\SQLEXPRESS01;'
    'DATABASE=ExpenseTrackerDB;'
    'Trusted_Connection=yes;'
)

# ---------------------------
# Helpers
# ---------------------------
def get_connection():
    return pyodbc.connect(CONN_STR, timeout=5)

def _format_value_for_display(val):
    if val is None:
        return ""
    if isinstance(val, datetime.date):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, Decimal):
        return f"{val:.2f}"
    if isinstance(val, float):
        return f"{val:.2f}"
    return str(val)

# ---------------------------
# GUI action functions
# ---------------------------
def add_expense():
    date = date_entry.get().strip()
    category = category_entry.get().strip()
    amount = amount_entry.get().strip()
    desc = desc_entry.get().strip()

    if not (date and category and amount):
        messagebox.showwarning("Input Error", "Please fill Date, Category and Amount")
        return

    try:
        dt_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        date_str = dt_obj.strftime("%Y-%m-%d")
    except Exception:
        messagebox.showerror("Input Error", "Date must be in YYYY-MM-DD format")
        return

    try:
        amt = Decimal(amount)
        amt_float = float(amt)
    except Exception:
        messagebox.showerror("Input Error", "Amount must be numeric")
        return

    conn = cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO Expenses (Date, Category, Amount, Description) VALUES (?, ?, ?, ?)",
                    (date_str, category, amt_float, desc))
        conn.commit()
        messagebox.showinfo("Success", "Expense added successfully")
        clear_entries()
        view_expenses()
    except Exception as e:
        print("Error in add_expense():", e)
        traceback.print_exc()
        messagebox.showerror("Database Error", f"Failed to add expense:\n{e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()

def update_expense():
    sid = selected_id_var.get()
    if not sid:
        messagebox.showwarning("Select", "Select a row to update")
        return

    date = date_entry.get().strip()
    category = category_entry.get().strip()
    amount = amount_entry.get().strip()
    desc = desc_entry.get().strip()

    if not (date and category and amount):
        messagebox.showwarning("Input Error", "Please fill Date, Category and Amount")
        return

    try:
        dt_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        date_str = dt_obj.strftime("%Y-%m-%d")
        amt = Decimal(amount)
        amt_float = float(amt)
    except Exception:
        messagebox.showerror("Input Error", "Invalid input format")
        return

    conn = cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE Expenses SET Date=?, Category=?, Amount=?, Description=? WHERE ID=?",
                    (date_str, category, amt_float, desc, sid))
        conn.commit()
        messagebox.showinfo("Success", "Expense updated successfully")
        clear_entries()
        view_expenses()
    except Exception as e:
        print("Error in update_expense():", e)
        traceback.print_exc()
        messagebox.showerror("Database Error", f"Failed to update:\n{e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()

def delete_selected():
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Select", "Select a row to delete")
        return
    if not messagebox.askyesno("Confirm Delete", "Delete selected record(s)?"):
        return

    conn = cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        for s in sel:
            vals = tree.item(s, "values")
            rec_id = vals[0]
            cur.execute("DELETE FROM Expenses WHERE ID = ?", (rec_id,))
        conn.commit()
        messagebox.showinfo("Deleted", "Selected record(s) deleted")
        clear_entries()
        view_expenses()
    except Exception as e:
        print("Error in delete_selected():", e)
        traceback.print_exc()
        messagebox.showerror("Database Error", f"Failed to delete:\n{e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()

def view_expenses(filter_start=None, filter_end=None):
    for i in tree.get_children():
        tree.delete(i)
    conn = cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        if filter_start and filter_end:
            cur.execute("SELECT ID, Date, Category, Amount, Description FROM Expenses WHERE Date >= ? AND Date < ? ORDER BY ID DESC",
                        (filter_start.strftime("%Y-%m-%d"), filter_end.strftime("%Y-%m-%d")))
        else:
            cur.execute("SELECT ID, Date, Category, Amount, Description FROM Expenses ORDER BY ID DESC")
        rows = cur.fetchall()
        for row in rows:
            display_values = [_format_value_for_display(col) for col in row]
            tree.insert("", tk.END, values=display_values)
    except Exception as e:
        print("Error in view_expenses():", e)
        traceback.print_exc()
    finally:
        if cur: cur.close()
        if conn: conn.close()

def on_select_row(event):
    sel = tree.selection()
    if not sel:
        return
    vals = tree.item(sel[0], "values")
    selected_id_var.set(vals[0])
    date_entry.delete(0, tk.END); date_entry.insert(0, vals[1])
    category_entry.delete(0, tk.END); category_entry.insert(0, vals[2])
    amount_entry.delete(0, tk.END); amount_entry.insert(0, vals[3])
    desc_entry.delete(0, tk.END); desc_entry.insert(0, vals[4])
    add_update_btn.config(text="Update Expense", command=update_expense)

def clear_entries():
    date_entry.delete(0, tk.END)
    category_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)
    desc_entry.delete(0, tk.END)
    selected_id_var.set("")
    add_update_btn.config(text="Add Expense", command=add_expense)
    date_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))

def filter_by_month():
    text = filter_entry.get().strip()
    if not text:
        messagebox.showwarning("Input", "Enter month in YYYY-MM")
        return
    try:
        dt = datetime.datetime.strptime(text, "%Y-%m")
        start = dt.date().replace(day=1)
        if dt.month == 12:
            end = datetime.date(dt.year + 1, 1, 1)
        else:
            end = datetime.date(dt.year, dt.month + 1, 1)
        view_expenses(filter_start=start, filter_end=end)
    except Exception:
        messagebox.showerror("Input Error", "Invalid format. Use YYYY-MM")

def filter_by_date():
    text = date_filter_entry.get().strip()
    if not text:
        messagebox.showwarning("Input", "Enter date in YYYY-MM-DD")
        return
    try:
        target_date = datetime.datetime.strptime(text, "%Y-%m-%d").date()
        next_day = target_date + datetime.timedelta(days=1)
        view_expenses(filter_start=target_date, filter_end=next_day)
    except Exception:
        messagebox.showerror("Input Error", "Invalid format. Use YYYY-MM-DD")

# 🌟 New: Clear filter
def clear_filter():
    filter_entry.delete(0, tk.END)
    date_filter_entry.delete(0, tk.END)
    view_expenses()

def show_pie_chart():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT Category, SUM(Amount) FROM Expenses GROUP BY Category")
        data = cur.fetchall()

        if not data:
            messagebox.showinfo("No Data", "No data to visualize")
            return

        categories = [r[0] for r in data]
        amounts = [float(r[1]) for r in data]

        # Create new Tkinter window
        win = tk.Toplevel(root)
        win.title("Expense Pie Chart")
        win.geometry("600x500")

        fig = plt.Figure(figsize=(6, 5))
        ax = fig.add_subplot(111)
        ax.pie(amounts, labels=categories, autopct="%1.1f%%", startangle=140)
        ax.set_title("Expenses by Category")

        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    except Exception as e:
        print("Error in show_pie_chart():", e)
        traceback.print_exc()

def show_monthly_bar_chart():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT FORMAT(Date, 'yyyy-MM'), SUM(Amount) "
                    "FROM Expenses GROUP BY FORMAT(Date, 'yyyy-MM') "
                    "ORDER BY FORMAT(Date, 'yyyy-MM')")
        data = cur.fetchall()

        if not data:
            messagebox.showinfo("No Data", "No data to visualize")
            return

        months = [r[0] for r in data]
        totals = [float(r[1]) for r in data]

        # Create new Tkinter window
        win = tk.Toplevel(root)
        win.title("Monthly Expense Bar Chart")
        win.geometry("700x500")

        fig = plt.Figure(figsize=(7, 5))
        ax = fig.add_subplot(111)
        ax.bar(months, totals)
        ax.set_title("Monthly Spending Overview")
        ax.set_xlabel("Month (YYYY-MM)")
        ax.set_ylabel("Total Amount")
        ax.tick_params(axis='x', rotation=45)

        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    except Exception as e:
        print("Error in show_monthly_bar_chart():", e)
        traceback.print_exc()


# ---------------------------
# GUI setup
# ---------------------------
root = tk.Tk()
root.title("Personal Expense Tracker (SQL Server)")
root.geometry("950x640")
root.configure(bg="#f6f8fa")

selected_id_var = tk.StringVar()

title_lbl = tk.Label(root, text="Personal Expense Tracker", font=("Segoe UI", 18, "bold"), bg="#f6f8fa", fg="#2d3436")
title_lbl.pack(pady=10)

main_frame = tk.Frame(root, bg="#f6f8fa")
main_frame.pack(padx=12, pady=6, fill="x")

# ----- Left form frame -----
form_frame = tk.LabelFrame(main_frame, text="Add / Edit Expense", padx=10, pady=10)
form_frame.grid(row=0, column=0, sticky="nw")

tk.Label(form_frame, text="Date (YYYY-MM-DD)").grid(row=0, column=0, sticky="w", padx=4, pady=4)
date_entry = tk.Entry(form_frame, width=18)
date_entry.grid(row=0, column=1, padx=4, pady=4)
date_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))

tk.Label(form_frame, text="Category").grid(row=1, column=0, sticky="w", padx=4, pady=4)
category_entry = tk.Entry(form_frame, width=24)
category_entry.grid(row=1, column=1, padx=4, pady=4)
category_entry.insert(0, "Food")

tk.Label(form_frame, text="Amount").grid(row=2, column=0, sticky="w", padx=4, pady=4)
amount_entry = tk.Entry(form_frame, width=18)
amount_entry.grid(row=2, column=1, padx=4, pady=4)

tk.Label(form_frame, text="Description").grid(row=3, column=0, sticky="w", padx=4, pady=4)
desc_entry = tk.Entry(form_frame, width=40)
desc_entry.grid(row=3, column=1, padx=4, pady=4, columnspan=2)

add_update_btn = tk.Button(form_frame, text="Add Expense", width=16, command=add_expense, bg="#0984e3", fg="white")
add_update_btn.grid(row=4, column=0, pady=10, padx=4)
del_btn = tk.Button(form_frame, text="Delete Selected", width=16, command=delete_selected, bg="#d63031", fg="white")
del_btn.grid(row=4, column=1, pady=10, padx=4)
clear_btn = tk.Button(form_frame, text="Clear Fields", width=16, command=clear_entries)
clear_btn.grid(row=4, column=2, pady=10, padx=4)

# ----- Right filter & visualize frame -----
right_frame = tk.LabelFrame(main_frame, text="Filter & Visualize", padx=10, pady=10)
right_frame.grid(row=0, column=1, sticky="ne", padx=12)

# Month filter
tk.Label(right_frame, text="Filter by Month (YYYY-MM)").grid(row=0, column=0, sticky="w", padx=4)
filter_entry = tk.Entry(right_frame, width=12)
filter_entry.grid(row=0, column=1, padx=4)
tk.Button(right_frame, text="Apply", command=filter_by_month, width=10).grid(row=0, column=2, padx=4)

# Date filter
tk.Label(right_frame, text="Filter by Date (YYYY-MM-DD)").grid(row=1, column=0, sticky="w", padx=4)
date_filter_entry = tk.Entry(right_frame, width=12)
date_filter_entry.grid(row=1, column=1, padx=4)
tk.Button(right_frame, text="Apply", command=filter_by_date, width=10).grid(row=1, column=2, padx=4)

# 🌟 New Clear Filter Button
tk.Button(right_frame, text="Clear Filter", command=clear_filter, width=12, bg="#636e72", fg="white").grid(row=2, column=0, pady=8)

# Visual buttons
tk.Button(right_frame, text="Show Pie Chart", command=show_pie_chart, width=14).grid(row=2, column=1, pady=8)
tk.Button(right_frame, text="Show Monthly Bar Chart", command=show_monthly_bar_chart, width=20).grid(row=2, column=2, pady=8)

# ----- Table -----
table_frame = tk.LabelFrame(root, text="Expenses", padx=6, pady=6)
table_frame.pack(padx=12, pady=8, fill="both", expand=True)

cols = ("ID", "Date", "Category", "Amount", "Description")
tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=14)
for col in cols:
    tree.heading(col, text=col)
tree.column("ID", width=50, anchor="center")
tree.column("Date", width=100, anchor="center")
tree.column("Category", width=150, anchor="w")
tree.column("Amount", width=110, anchor="e")
tree.column("Description", width=300, anchor="w")
tree.pack(fill="both", expand=True, side="left")

vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=vsb.set)
vsb.pack(side="right", fill="y")
tree.bind("<<TreeviewSelect>>", on_select_row)

view_expenses()

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()







# In[ ]:





# In[ ]:




