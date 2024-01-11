import tkinter as tk
from tkinter import ttk,IntVar, messagebox,filedialog,Toplevel,Button, simpledialog, StringVar, Entry, Label, Button
from ttkthemes import ThemedTk
import subprocess
import mysql.connector
from datetime import date, timedelta
import os
import threading
import sys
from pathlib import Path
from ttkthemes import ThemedStyle
import pandas as pd
from tkinter import StringVar
from datetime import datetime
from datetime import date
import csv
from tkinter.simpledialog import askstring
import win32event
import win32api
import sys
from reportlab.lib.pagesizes import letter
import datetime
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle,Spacer,Paragraph
import pymysql
import schedule
import time
#save_invoice_var = IntVar()
opened_window = None  # Keep track of the currently opened window
opened_lists = {}  # Dictionary to keep track of opened list
# Initialize cart_medicines list
cart_medicines = []
# Define root globally
root = None


class SingleInstanceChecker:
    def __init__(self):
        self.mutex_name = "YourAppMutexName"
        self.mutex = None

    def is_another_instance_running(self):
        try:
            self.mutex = win32event.CreateMutex(None, 1, self.mutex_name)
            if win32api.GetLastError() == win32event.ERROR_ALREADY_EXISTS:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error creating mutex: {e}")
            return False

    def release_instance(self):
        if self.mutex:
            win32api.CloseHandle(self.mutex)



# MySQL Database Connection
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="pharmacy"
)

cursor = connection.cursor()


def open_sub_window(sub_window_name):
    global opened_window

    # Close the current window if open
    if opened_window is not None:
        opened_window.communicate()  # Wait for the subprocess to finish

    current_directory = os.path.dirname(sys.argv[0])  # Use sys.argv[0] to get the script path
    full_path = os.path.join(current_directory, sub_window_name)

    # Use the same Python interpreter that is running the current script
    python_executable = sys.executable

    try:
        # Use subprocess.Popen to store the subprocess object
        opened_window = subprocess.Popen([python_executable, full_path])
    except Exception as e:
        print(f"Unexpected error: {e}")

class Database:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor(dictionary=True)
        self.observers = []

    def add_observer(self, observer):
        self.observers.append(observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.update()

    def execute_query(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            self.notify_observers()  # Notify observers after a successful query
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

# Add a new class for synchronization
class Synchronizer:
    def __init__(self, database, callback):
        self.database = database
        self.callback = callback
        self.database.add_observer(self)

    def update(self):
        # Trigger the callback function for synchronization
        self.callback()

def add_user(user_management_button_frame):
    # Define the roles for the dropdown
    roles = ["Admin", "Pharmacist"]

    def register_user():
        username = username_entry.get()
        password = password_entry.get()
        role = selected_role.get()  # Get the selected role from the OptionMenu

        if len(username) < 6:
            messagebox.showerror("Error", "Username must be at least 6 characters long.")
        elif len(password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters long.")
        elif not role:
            messagebox.showerror("Error", "Role is required.")
        else:
            try:
                cursor = connection.cursor()
                query = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
                cursor.execute(query, (username, password, role))
                connection.commit()
                cursor.close()
                messagebox.showinfo("Success", "User registered successfully.")
                # Close the user registration window after successful registration
                user_registration_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

    # Create the user registration window
    user_registration_window = Toplevel(root)
    user_registration_window.title("User Registration")
    user_registration_window.geometry("400x250")
    # Apply the theme
    style = ThemedStyle(user_registration_window)
    style.set_theme("alt")
    # Title label
    title_label = ttk.Label(user_registration_window, text="User Registration", font=("Helvetica", 16))
    title_label.pack(pady=10)
    # Create a frame for the input fields and labels
    input_frame = ttk.Frame(user_registration_window)
    input_frame.pack(pady=10)
    # Username label and entry
    username_label = ttk.Label(input_frame, text="Username:")
    username_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
    username_entry = ttk.Entry(input_frame, width=30)
    username_entry.grid(row=0, column=1, padx=10, pady=5)
    # Password label and entry
    password_label = ttk.Label(input_frame, text="Password:")
    password_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    password_entry = ttk.Entry(input_frame, show="*", width=30)
    password_entry.grid(row=1, column=1, padx=10, pady=5)
    # Role label and dropdown
    role_label = ttk.Label(input_frame, text="Role:")
    role_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
    # Create a StringVar to store the selected role
    selected_role = tk.StringVar(user_registration_window)
    selected_role.set(roles[0])  # Set the default role
    # Create an OptionMenu with the roles
    role_menu = ttk.OptionMenu(input_frame, selected_role, *roles)
    role_menu.grid(row=2, column=1, padx=10, pady=5)
    # Register button
    register_button = ttk.Button(user_registration_window, text="Register", command=register_user, style="TButton", cursor="hand2")
    register_button.pack(pady=10)



def get_all_users():
    try:
        cursor = connection.cursor()
        query = "SELECT id, username, role FROM users"
        cursor.execute(query)
        users = cursor.fetchall()
        cursor.close()
        return users
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        return []


# Inside the display_dashboard function, modify the manage_users function:
def manage_users():
    users_window = tk.Toplevel(root)
    users_window.title("Manage Users")
    
    # Create Treeview widget
    tree = ttk.Treeview(users_window, columns=("ID", "Username", "Role"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Username", text="Username")
    tree.heading("Role", text="Role")
    
    # Fetch all users from the database
    users = get_all_users()
    
    # Insert data into the Treeview
    for user in users:
        tree.insert("", "end", values=user)   
    tree.pack(expand=True, fill="both")   
    # Add buttons for actions (Delete and Edit)
    delete_button = ttk.Button(users_window, text="Delete", command=lambda: delete_user(tree))
    delete_button.pack(side="left", padx=10, pady=10)    
    edit_button = ttk.Button(users_window, text="Edit", command=lambda: edit_user(tree))
    edit_button.pack(side="left", padx=10, pady=10)

def delete_user(tree):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "Please select a user to delete.")
        return
    user_id = tree.item(selected_item, "values")[0]
    # Ask for confirmation before deleting the user
    confirmation = messagebox.askyesno("Confirmation", "Are you sure you want to delete this user?")
    if not confirmation:
        return

    try:
        cursor = connection.cursor()
        query = "DELETE FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        connection.commit()
        cursor.close()

        # Refresh the Treeview after deletion
        tree.delete(*tree.get_children())
        users = get_all_users()
        for user in users:
            tree.insert("", "end", values=user)

        messagebox.showinfo("Success", "User deleted successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


def edit_user(tree):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "Please select a user to edit.")
        return

    user_id, username, role = tree.item(selected_item, "values")
    edit_window = Toplevel(root)
    edit_window.title("Edit User")
    # Create labels and entry widgets for editing
    ttk.Label(edit_window, text="Username:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    username_entry = ttk.Entry(edit_window, width=30)
    username_entry.insert(0, username)
    username_entry.grid(row=0, column=1, padx=10, pady=5)
    ttk.Label(edit_window, text="Role:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    role_entry = ttk.Entry(edit_window, width=30)
    role_entry.insert(0, role)
    role_entry.grid(row=1, column=1, padx=10, pady=5)
   
    def update_user():
        new_username = username_entry.get()
        new_role = role_entry.get()
        new_password = password_entry.get()

        if len(new_username) < 6:
            messagebox.showerror("Error", "Username must be at least 6 characters long.")
            return
        elif len(new_password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters long.")
            return

        try:
            cursor = connection.cursor()
            query = "UPDATE users SET username = %s, password = %s, role = %s WHERE id = %s"
            cursor.execute(query, (new_username, new_password, new_role, user_id))
            connection.commit()
            cursor.close()

            # Refresh the Treeview after update
            tree.delete(*tree.get_children())
            users = get_all_users()
            for user in users:
                tree.insert("", "end", values=user)

            edit_window.destroy()
            messagebox.showinfo("Success", "User updated successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    # Add a label and entry widget for password
    ttk.Label(edit_window, text="Password:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
    password_entry = ttk.Entry(edit_window, show="*", width=30)
    password_entry.grid(row=2, column=1, padx=10, pady=5)
    update_button = ttk.Button(edit_window, text="Update", command=update_user)
    update_button.grid(row=2, columnspan=2, pady=10)
    

def manage_stock():
    def delete_stock():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a stock entry to delete.")
            return

        stock_id = tree.item(selected_item, "values")[0]

        # Ask for confirmation before deleting the stock entry
        confirmation = messagebox.askyesno("Confirmation", "Are you sure you want to delete this stock entry?")
        if not confirmation:
            return

        try:
            cursor = connection.cursor()
            query = "DELETE FROM medicines_stock WHERE ID = %s"
            cursor.execute(query, (stock_id,))
            connection.commit()
            cursor.close()

            # Refresh the Treeview after deletion
            tree.delete(*tree.get_children())
            populate_stock_table()

            messagebox.showinfo("Success", "Stock entry deleted successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def edit_stock():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a stock entry to edit.")
            return

        stock_id, medicine_name, brand, mrp, rate, quantity, expiry_date = tree.item(selected_item, "values")

        edit_window = Toplevel(root)
        edit_window.title("Edit Stock")

        # Create labels and entry widgets for editing
        ttk.Label(edit_window, text="Medicine Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        medicine_name_entry = ttk.Entry(edit_window, width=30)
        medicine_name_entry.insert(0, medicine_name)
        medicine_name_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(edit_window, text="Brand:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        brand_entry = ttk.Entry(edit_window, width=30)
        brand_entry.insert(0, brand)
        brand_entry.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(edit_window, text="selling price:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        mrp_entry = ttk.Entry(edit_window, width=30)
        mrp_entry.insert(0, mrp)
        mrp_entry.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(edit_window, text="Buying price:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        rate_entry = ttk.Entry(edit_window, width=30)
        rate_entry.insert(0, rate)
        rate_entry.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(edit_window, text="Quantity:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        quantity_entry = ttk.Entry(edit_window, width=30)
        quantity_entry.insert(0, quantity)
        quantity_entry.grid(row=4, column=1, padx=10, pady=5)

        ttk.Label(edit_window, text="Expiry Date (DD-MM-YYYY):").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        expiry_date_entry = ttk.Entry(edit_window, width=30)
        expiry_date_entry.insert(0, expiry_date)
        expiry_date_entry.grid(row=5, column=1, padx=10, pady=5)

        def update_stock():
            new_medicine_name = medicine_name_entry.get()
            new_brand = brand_entry.get()
            new_mrp = mrp_entry.get()
            new_rate = rate_entry.get()
            new_quantity = quantity_entry.get()
            new_expiry_date = expiry_date_entry.get()

            if not new_medicine_name or not new_brand or not new_mrp or not new_rate or not new_quantity or not new_expiry_date:
                messagebox.showerror("Error", "Please fill in all the fields.")
                return

            if not is_number(new_mrp) or not is_number(new_rate) or not is_number(new_quantity):
                messagebox.showerror("Error", "Selling Price, Buying price, and Quantity must be numerical values.")
                return

            try:
                cursor = connection.cursor()
                query = "UPDATE medicines_stock SET NAME = %s, BRAND = %s, MRP = %s, RATE = %s, QUANTITY = %s, EXPIRY_DATE = %s WHERE ID = %s"
                cursor.execute(query, (new_medicine_name, new_brand, new_mrp, new_rate, new_quantity, new_expiry_date, stock_id))
                connection.commit()
                cursor.close()

                # Refresh the Treeview after update
                tree.delete(*tree.get_children())
                populate_stock_table()

                edit_window.destroy()
                messagebox.showinfo("Success", "Stock entry updated successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

        # Add an update button
        update_button = ttk.Button(edit_window, text="Update", command=update_stock)
        update_button.grid(row=6, columnspan=2, pady=10)

    def search_stock():
        search_term = search_var.get().strip().lower()

        # Clear existing entries in the Treeview
        tree.delete(*tree.get_children())

        # Populate the Treeview with search results
        try:
            cursor = connection.cursor()
            query = "SELECT ID, NAME, BRAND, MRP, RATE, QUANTITY, EXPIRY_DATE FROM medicines_stock WHERE LOWER(NAME) LIKE %s OR LOWER(BRAND) LIKE %s"
            cursor.execute(query, (f"%{search_term}%", f"%{search_term}%"))
            stocks = cursor.fetchall()
            cursor.close()

            for stock in stocks:
                tree.insert("", "end", values=stock)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def clear_search():
        search_var.set("")
        tree.delete(*tree.get_children())
        populate_stock_table()

    def populate_stock_table():
        try:
            cursor = connection.cursor()
            query = "SELECT ID, NAME, BRAND, MRP, RATE, QUANTITY, EXPIRY_DATE FROM medicines_stock"
            cursor.execute(query)
            stocks = cursor.fetchall()
            cursor.close()
            # Clear existing entries in the Treeview
            tree.delete(*tree.get_children())
            # Repopulate the Treeview with the updated data
            for stock in stocks:
                tree.insert("", "end", values=stock)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        

    # Create the "Manage Stock" window
    manage_stock_window = Toplevel(root)
    manage_stock_window.title("Manage Stock")
    manage_stock_window.geometry("800x400")
    # Apply the theme
    style = ThemedStyle(manage_stock_window)
    style.set_theme("alt")
    # Title label
    title_label = ttk.Label(manage_stock_window, text="Manage Stock", font=("Helvetica", 16))
    title_label.pack(pady=10)
    # Create a frame for search bar
    search_frame = ttk.Frame(manage_stock_window)
    search_frame.pack(pady=10)
    # Create a search bar
    search_var = StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
    search_entry.grid(row=0, column=0, padx=10, pady=5)
    # Create search and clear buttons
    search_button = ttk.Button(search_frame, text="Search", command=search_stock)
    search_button.grid(row=0, column=1, padx=5)
    clear_button = ttk.Button(search_frame, text="Clear", command=clear_search)
    clear_button.grid(row=0, column=2, padx=5)
    # Create Treeview widget
    tree = ttk.Treeview(manage_stock_window, columns=("ID", "Medicine Name", "Brand", "MRP", "Rate", "Quantity", "Expiry Date"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Medicine Name", text="Medicine Name")
    tree.heading("Brand", text="Brand")
    tree.heading("MRP", text="Selling Price")
    tree.heading("Rate", text="Buting Price")
    tree.heading("Quantity", text="Quantity")
    tree.heading("Expiry Date", text="Expiry Date")
    tree.pack(expand=True, fill="both")
    # Add buttons for actions (Delete and Edit)
    delete_button = ttk.Button(manage_stock_window, text="Delete", command=delete_stock)
    delete_button.pack(side="left", padx=10, pady=10)
    edit_button = ttk.Button(manage_stock_window, text="Edit", command=edit_stock)
    edit_button.pack(side="left", padx=10, pady=10)
    # Add a Refresh button
    refresh_button = ttk.Button(manage_stock_window, text="Refresh", command=populate_stock_table)
    refresh_button.pack(side="left", padx=10, pady=10)
    
def add_stock():
    # Function to add stock either manually or from a CSV file

    def save_stock_manually():
        name = name_entry.get()
        brand = brand_entry.get()
        expiry_date = expiry_date_entry.get()
        quantity = quantity_entry.get()
        mrp = mrp_entry.get()
        rate = rate_entry.get()

        # Check if all fields are filled
        if not name or not brand or not expiry_date or not quantity or not mrp or not rate:
            messagebox.showerror("Error", "Please fill in all the fields.")
            return

        # Check if numerical fields contain valid numbers
        if not quantity.isdigit() or not mrp.replace('.', '').isdigit() or not rate.replace('.', '').isdigit():
            messagebox.showerror("Error", "Quantity, Selling Price, and Buying Price must be numerical values.")
            return

        try:
            # Save stock to the database
            save_stock(name, brand, expiry_date, quantity, mrp, rate)

            # Clear entry fields for the next entry
            name_entry.delete(0, 'end')
            brand_entry.delete(0, 'end')
            expiry_date_entry.delete(0, 'end')
            quantity_entry.delete(0, 'end')
            mrp_entry.delete(0, 'end')
            rate_entry.delete(0, 'end')

            messagebox.showinfo("Success", "Stock entry saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def upload_csv():
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )

        if file_path:
            print(f"Uploading CSV: {file_path}")
            process_csv(file_path)
            messagebox.showinfo("Success", "CSV data uploaded successfully!")
            add_stock_window.destroy()

    def process_csv(file_path):
        with open(file_path, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip the header row
            for row in csv_reader:
                print(f"Processing CSV row: {row}")
                save_stock(*row)

    def save_stock(name, brand, expiry_date, quantity, mrp, rate):
        print(f"Saving stock: {name}, {brand}, {expiry_date}, {quantity}, {mrp}, {rate}")

        # Connect to the MySQL database
        cursor = None
        try:
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="pharmacy"
            )

            cursor = connection.cursor()

            # Example SQL query to insert data into the 'medicines_stock' table
            insert_query = "INSERT INTO medicines_stock (name, brand, expiry_date, quantity, mrp, rate) VALUES (%s, %s, %s, %s, %s, %s)"
            data = (name, brand, expiry_date, quantity, mrp, rate)

            # Execute the query and commit changes
            cursor.execute(insert_query, data)
            connection.commit()

        finally:
            if cursor:
                cursor.close()
            if connection.is_connected():
                connection.close()

    # Create the GUI window
    add_stock_window = tk.Toplevel()
    add_stock_window.title("Add Stock Manually")

    # Set the theme
    style = ttk.Style()
    style.theme_use("alt")  # Change this to other available themes like "vista", "xpnative", etc.
    # Create and place labels, entry widgets, and buttons in the window
    Label(add_stock_window, text="Medicine Name:").grid(row=0, column=0, sticky="e", pady=5, padx=5)
    name_entry = Entry(add_stock_window)
    name_entry.grid(row=0, column=1, pady=5, padx=5)
    Label(add_stock_window, text="Brand:").grid(row=1, column=0, sticky="e", pady=5, padx=5)
    brand_entry = Entry(add_stock_window)
    brand_entry.grid(row=1, column=1, pady=5, padx=5)
    Label(add_stock_window, text="Expiry Date:").grid(row=2, column=0, sticky="e", pady=5, padx=5)
    expiry_date_entry = Entry(add_stock_window)
    expiry_date_entry.grid(row=2, column=1, pady=5, padx=5)
    Label(add_stock_window, text="Quantity:").grid(row=3, column=0, sticky="e", pady=5, padx=5)
    quantity_entry = Entry(add_stock_window)
    quantity_entry.grid(row=3, column=1, pady=5, padx=5)
    Label(add_stock_window, text="Selling Price:").grid(row=4, column=0, sticky="e", pady=5, padx=5)
    mrp_entry = Entry(add_stock_window)
    mrp_entry.grid(row=4, column=1, pady=5, padx=5)
    Label(add_stock_window, text="Buying Price:").grid(row=5, column=0, sticky="e", pady=5, padx=5)
    rate_entry = Entry(add_stock_window)
    rate_entry.grid(row=5, column=1, pady=5, padx=5)
    save_button = Button(add_stock_window, text="Save", command=save_stock_manually, padx=10, pady=5, bg='#4CAF50', fg='white')
    save_button.grid(row=6, column=1, pady=10)
    upload_csv_button = Button(add_stock_window, text="Upload CSV", command=upload_csv, padx=10, pady=5, bg='#007BFF', fg='white')
    upload_csv_button.grid(row=7, column=1, pady=10)

def manage_invoices():
    def delete_invoice():
        selected_item = invoice_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select an invoice to delete.")
            return

        invoice_id = invoice_tree.item(selected_item, "values")[0]

        # Ask for confirmation before deleting the invoice
        confirmation = messagebox.askyesno("Confirmation", f"Are you sure you want to delete Invoice {invoice_id}?")
        if not confirmation:
            return

        try:
            cursor = connection.cursor()
            query = "DELETE FROM invoices WHERE INVOICE_ID = %s"
            cursor.execute(query, (invoice_id,))
            connection.commit()
            cursor.close()

            # Refresh the Treeview after deletion
            invoice_tree.delete(*invoice_tree.get_children())
            populate_invoice_table()

            messagebox.showinfo("Success", f"Invoice {invoice_id} deleted successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def print_invoice():
        selected_item = invoice_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select an invoice to print.")
            return

        invoice_id = invoice_tree.item(selected_item, "values")[0]

        # Implement your printing logic here
        # For example, you can open a new window with the invoice details for printing
        print(f"Printing Invoice {invoice_id}")

    def populate_invoice_table():
        try:
            cursor = connection.cursor()
            query = "SELECT INVOICE_ID, NET_TOTAL, AMOUNT_PAID, INVOICE_DATE, TOTAL_AMOUNT, TOTAL_DISCOUNT, BALANCE FROM invoices"
            cursor.execute(query)
            invoices = cursor.fetchall()
            cursor.close()

            for invoice in invoices:
                invoice_tree.insert("", "end", values=invoice)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def search_invoice(event):
        search_text = search_var.get().strip()

        if not search_text:
            return

        try:
            cursor = connection.cursor()
            query = "SELECT INVOICE_ID, NET_TOTAL, AMOUNT_PAID, INVOICE_DATE, TOTAL_AMOUNT, TOTAL_DISCOUNT, BALANCE FROM invoices WHERE INVOICE_ID LIKE %s"
            cursor.execute(query, (f"%{search_text}%",))
            search_results = cursor.fetchall()
            cursor.close()

            # Clear the existing entries in the Treeview
            invoice_tree.delete(*invoice_tree.get_children())

            # Insert the search results into the Treeview
            for result in search_results:
                invoice_tree.insert("", "end", values=result)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    # Create the "Manage Invoices" window
    manage_invoices_window = Toplevel(root)
    manage_invoices_window.title("Manage Invoices")
    manage_invoices_window.geometry("800x400")

    # Apply the theme
    style = ttk.Style(manage_invoices_window)
    style.theme_use("alt")

    # Title label
    title_label = ttk.Label(manage_invoices_window, text="Manage Invoices", font=("Helvetica", 16))
    title_label.pack(pady=10)

    # Label for searching by Invoice ID
    search_label = Label(manage_invoices_window, text="Search by Invoice ID:")
    search_label.pack(pady=5)

    # Create an Entry for searching by Invoice ID
    search_var = StringVar()
    search_entry = Entry(manage_invoices_window, textvariable=search_var, width=15)
    search_entry.pack(pady=5)
    search_entry.bind("<KeyRelease>", search_invoice)

    # Create Treeview widget for invoices with vertical and horizontal scrollbars
    invoice_tree = ttk.Treeview(manage_invoices_window, columns=("Invoice ID", "Net Total", "Amount Paid", "Invoice Date", "Total Amount", "Total Discount", "Balance"), show="headings")
    invoice_tree.heading("Invoice ID", text="Invoice ID")
    invoice_tree.heading("Net Total", text="Net Total")
    invoice_tree.heading("Amount Paid", text="Amount Paid")
    invoice_tree.heading("Invoice Date", text="Invoice Date")
    invoice_tree.heading("Total Amount", text="Total Amount")
    invoice_tree.heading("Total Discount", text="Total Discount")
    invoice_tree.heading("Balance", text="Balance")

    invoice_tree.pack(expand=True, fill="both")

    # Add vertical scrollbar
    vsb = ttk.Scrollbar(manage_invoices_window, orient="vertical", command=invoice_tree.yview)
    vsb.pack(side="right", fill="y")
    invoice_tree.configure(yscrollcommand=vsb.set)

    # Add horizontal scrollbar
    hsb = ttk.Scrollbar(manage_invoices_window, orient="horizontal", command=invoice_tree.xview)
    hsb.pack(side="bottom", fill="x")
    invoice_tree.configure(xscrollcommand=hsb.set)

    # Add buttons for actions (Delete and Print)
    delete_button = ttk.Button(manage_invoices_window, text="Delete", command=delete_invoice)
    delete_button.pack(side="left", padx=10, pady=10)

    print_button = ttk.Button(manage_invoices_window, text="Print", command=print_invoice)
    print_button.pack(side="left", padx=10, pady=10)

    # Populate the invoice table
    populate_invoice_table()

def is_number(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def add_invoice():
    
    global add_invoice_window_open
    add_invoice_window_open = False
    # Check if the window is already open
    if add_invoice_window_open:
        messagebox.showinfo("Info", "Add Invoice window is already open.")
        return  
    # Create the "Add Invoice" window
    add_invoice_window = Toplevel(root)
    add_invoice_window.title("Add Invoice")
    add_invoice_window.geometry("800x600")  # Increased height for the cart and additional labels
    # Apply the theme
    style = ttk.Style(add_invoice_window)
    style.theme_use("alt")
    # Title label
    title_label = ttk.Label(add_invoice_window, text="Add Invoice", font=("Helvetica", 16))
    title_label.pack(pady=10)
    # Create a frame for the totals, amount paid, and save button
    totals_and_amount_paid_frame = ttk.Frame(add_invoice_window)
    totals_and_amount_paid_frame.pack(pady=10)
    # Create labels for Net Total, Balance, Total Discount, and Total Amount
    labels_frame = ttk.Frame(totals_and_amount_paid_frame)
    labels_frame.grid(row=0, column=0, padx=5)
    net_total_label = ttk.Label(labels_frame, text="Net Total:")
    net_total_label.grid(row=0, column=0, padx=4)
    net_total_entry = Entry(labels_frame, state="readonly",foreground="red")
    net_total_entry.grid(row=0, column=1, padx=4)
    balance_label = ttk.Label(labels_frame, text="Balance:")
    balance_label.grid(row=0, column=2, padx=4)
    balance_entry = Entry(labels_frame, state="readonly",foreground="red")
    balance_entry.grid(row=0, column=3, padx=4)
    total_discount_label = ttk.Label(labels_frame, text="Total Discount:")
    total_discount_label.grid(row=0, column=4, padx=4)
    total_discount_entry = Entry(labels_frame, state="readonly",foreground="red")
    total_discount_entry.grid(row=0, column=5, padx=4)
    total_amount_label = ttk.Label(labels_frame, text="Total Amount:")
    total_amount_label.grid(row=0, column=6, padx=4)
    total_amount_entry = Entry(labels_frame, state="readonly",foreground="red")
    total_amount_entry.grid(row=0, column=7, padx=5)   
    # Create a frame for the medicine table and search bar
    medicine_frame = ttk.Frame(add_invoice_window)
    medicine_frame.pack(pady=10)
    # Create a search bar for medicines
    search_var = StringVar()
    search_entry = ttk.Entry(medicine_frame, textvariable=search_var, width=30)
    search_entry.grid(row=0, column=0, padx=10, pady=5)
    # Create Treeview widget for medicines with vertical scrollbar
    medicine_columns = ("Medicine Name", "Brand", "Quantity", "Selling Price")
    medicine_tree = ttk.Treeview(medicine_frame, columns=medicine_columns, show="headings", height=5)
    for col in medicine_columns:
        medicine_tree.heading(col, text=col)
    medicine_tree.grid(row=1, column=0, pady=5, sticky="nsew")
    # Add vertical scrollbar
    vsb_medicine = ttk.Scrollbar(medicine_frame, orient="vertical", command=medicine_tree.yview)
    vsb_medicine.grid(row=1, column=1, sticky="ns")
    medicine_tree.configure(yscrollcommand=vsb_medicine.set)
    # Make the treeview columns resize with the window
    medicine_frame.grid_columnconfigure(0, weight=1)
    medicine_frame.grid_rowconfigure(1, weight=1)    
    def refresh_medicines():
        update_medicine_tree()
    # Button to refresh medicines
    refresh_button = ttk.Button(medicine_frame, text="Refresh", command=refresh_medicines)
    refresh_button.grid(row=0, column=2, padx=5)   
 # Create labels and entry widgets for quantity and discount
    labels_and_entries_frame = ttk.Frame(totals_and_amount_paid_frame)
    labels_and_entries_frame.grid(row=1, column=0, padx=5)
    quantity_label = ttk.Label(labels_and_entries_frame, text="Quantity:")
    quantity_label.grid(row=0, column=0, padx=5)
    quantity_entry = Entry(labels_and_entries_frame)
    quantity_entry.grid(row=0, column=1, padx=5)
    discount_label = ttk.Label(labels_and_entries_frame, text="Discount:")
    discount_label.grid(row=0, column=2, padx=5)
    discount_entry = Entry(labels_and_entries_frame)
    discount_entry.grid(row=0, column=3, padx=5)
    # Label and entry for amount paid
    amount_paid_label = ttk.Label(labels_and_entries_frame, text="")
    amount_paid_label.grid(row=0, column=4, pady=10)
    amount_paid_entry = Entry(labels_and_entries_frame)  
    # Create Treeview widget for medicines with vertical scrollbar
    medicine_columns = ("Medicine Name", "Brand", "Expiry Date", "Quantity", "Selling Price", "Buying Price")
    medicine_tree = ttk.Treeview(medicine_frame, columns=medicine_columns, show="headings", height=5)
    for col in medicine_columns:
        medicine_tree.heading(col, text=col)
    medicine_tree.grid(row=1, column=0, pady=5, sticky="nsew")

    def update_medicine_tree():
        search_term = search_var.get().lower()
        # Fetch medicine data from the database based on the search term
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM medicines_stock WHERE LOWER(NAME) LIKE %s OR LOWER(BRAND) LIKE %s", (f"%{search_term}%", f"%{search_term}%"))
        medicines_data = cursor.fetchall()
        # Clear previous items in the treeview
        medicine_tree.delete(*medicine_tree.get_children())
        # Insert new medicine data into the treeview
        for medicine in medicines_data:
            medicine_tree.insert("", "end", values=(medicine["NAME"], medicine["BRAND"], medicine["EXPIRY_DATE"], medicine["QUANTITY"], medicine["MRP"], medicine["RATE"]))
    # Update medicine_tree when the search term changes
    search_var.trace_add("write", lambda *args: update_medicine_tree())    
    def update_totals():
    # Lists to store individual totals and discounts
        totals = []
        discounts = []
        for _, qty, mrp, discount, _ in cart_medicines:
            # Calculate individual total and discount
            total = qty * mrp
            individual_discount = discount
            # Append to lists
            totals.append(total)
            discounts.append(individual_discount)
        # Calculate total amount, total discount, net total, and balance
        total_amount = sum(totals)
        total_discount = sum(discounts)
        net_total = total_amount - total_discount
        # Update the labels with the calculated values
        total_amount_entry.config(state="normal")
        total_amount_entry.delete(0, "end")
        total_amount_entry.insert(0, total_amount)
        total_amount_entry.config(state="readonly")
        total_discount_entry.config(state="normal")
        total_discount_entry.delete(0, "end")
        total_discount_entry.insert(0, total_discount)
        total_discount_entry.config(state="readonly",)
        net_total_entry.config(state="normal")
        net_total_entry.delete(0, "end")
        # Set net total to 0 if amount_paid is not entered
        net_total_entry.insert(0, max(0, net_total))
        net_total_entry.config(state="readonly")
        # Retrieve the amount_paid value
        try:
            amount_paid = int(amount_paid_entry.get())
        except ValueError:
            # Handle the case where the amount paid is not a valid integer
            amount_paid = 0       
        # Calculate and update the balance
        balance = amount_paid - net_total
        # If the balance is initially negative, set it to 0
        if balance < 0:
            balance = 0
        # Update the balance entry
        balance_entry.config(state="normal")
        balance_entry.delete(0, "end")
        balance_entry.insert(0, balance)
        balance_entry.config(state="readonly")
    # Call update_totals to set initial values
    update_totals()
    # Bind the update_totals function to the <<KeyRelease>> event
    amount_paid_entry.bind("<KeyRelease>", lambda event: update_totals())
    #amount_paid_entry_cart.bind("<KeyRelease>", lambda event: update_totals())       
    def add_to_invoice():
        global cart_medicines  # Use the global cart_medicines
    # Get the selected item from the medicine treeview
        selected_item = medicine_tree.focus()
    # Check if an item is selected
        if selected_item:
        # Retrieve the values of the selected medicine
            medicine_values = medicine_tree.item(selected_item, "values")
            if medicine_values:
                try:
                # Convert quantity and discount to integers
                    quantity = int(quantity_entry.get())
                    discount = int(discount_entry.get() or 0)  # If discount is empty, default to 0
                # Perform input validation
                    if not (0 < quantity <= int(medicine_values[3])):
                        messagebox.showerror("Error", "Quantity must be greater than 0 and less than or equal to available quantity.")
                        return
                # Check for expiry date
                    expiry_date_str = medicine_values[2]  # Assuming column index for expiry date is 2
                    expiry_date = datetime.datetime.strptime(expiry_date_str, "%d/%m/%Y").date()

                    today = date.today()
                    if expiry_date < today:
                        messagebox.showerror("Error", "The selected medicine has expired.")
                        return

                # Calculate total amount
                    mrp = int(medicine_values[4])  # Assuming column index for MRP is 4
                    total_amount = quantity * mrp - discount

                # Check if the medicine is already in the cart
                    for i, (name, _, _, _, _) in enumerate(cart_medicines):
                        if name == medicine_values[0]:
                        # If found, update the existing entry
                            cart_medicines[i] = (name, quantity, mrp, discount, total_amount)

                        # Update the cart treeview
                            cart_tree.item(cart_tree.selection(), values=(name, quantity, mrp, discount, total_amount))

                        # Exit the function
                            break
                    else:
                    # If not found, add the medicine to the cart
                        cart_medicines.append((medicine_values[0], quantity, mrp, discount, total_amount))

                    # Update the cart treeview
                        cart_tree.insert("", "end", values=(medicine_values[0], quantity, mrp, discount, total_amount))

                    # Clear quantity and discount entries for the next input
                        quantity_entry.delete(0, "end")
                        discount_entry.delete(0, "end")

                    # Update totals
                        update_totals()
                        
                except ValueError:
                    messagebox.showerror("Error", "Please enter valid integer values for Quantity and Discount.")
    
    
    def update_quantity_sold(medicine_name, qty_sold):
        cursor = None
        try:
        # Establish a new cursor connection
            cursor = connection.cursor()

        # Update the available quantity in the medicines_stock table
            cursor.execute("UPDATE medicines_stock SET QUANTITY = QUANTITY - %s WHERE NAME = %s", (qty_sold, medicine_name))
            connection.commit()

        except Exception as e:
            connection.rollback()
            messagebox.showerror("Error", f"Failed to update quantity sold for {medicine_name}. Error: {e}")

        finally:
            if cursor:
            # Close the cursor after using it
                cursor.close()

    # Function to delete selected medicine from the cart
    def delete_selected_medicine():
        selected_item = cart_tree.selection()
        if selected_item:
            confirmation = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the selected medicine from the cart?")
            if confirmation:
                # Get the values of the selected medicine in the cart
                cart_values = cart_tree.item(selected_item, "values")
                # Remove the medicine from cart_medicines
                for i, (name, qty, mrp, discount, total_amount) in enumerate(cart_medicines):
                    if name == cart_values[0]:
                        del cart_medicines[i]
                        break

                # Update the cart treeview
                cart_tree.delete(selected_item)

                # Update totals
                update_totals()
  
    def save_and_print_invoice():
        global cart_medicines

        cursor = None
        try:
            if not cart_medicines:
                messagebox.showerror("Error", "Cannot save an empty cart.")
                return

            amount_paid_str = amount_paid_entry_cart.get().strip()
            if len(amount_paid_str) == 0 or not amount_paid_str.isdigit():
                messagebox.showerror("Error", "Please enter a valid amount paid.")
                return

            amount_paid_value = int(amount_paid_str)
            net_total_value = int(net_total_entry.get())

            if amount_paid_value < 0 or amount_paid_value < net_total_value:
                messagebox.showerror("Error", "Invalid amount paid.")
                return
            balance_value = amount_paid_value - net_total_value
            cursor = connection.cursor()
            invoice_query = "INSERT INTO invoices (NET_TOTAL, AMOUNT_PAID, TOTAL_AMOUNT, TOTAL_DISCOUNT, BALANCE) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(invoice_query, (net_total_value, amount_paid_value, float(total_amount_entry.get().strip() or 0), float(total_discount_entry.get().strip() or 0), float(balance_value)))
            invoice_id_query = "SELECT MAX(INVOICE_ID) FROM invoices"
            cursor.execute(invoice_id_query)
            invoice_id = cursor.fetchone()[0]
            unique_medicines = set()
            for i, (_, qty, mrp, discount, total) in enumerate(cart_medicines):
                medicine_name = cart_medicines[i][0]
                sales_query = "INSERT INTO sales (INVOICE_NUMBER, MEDICINE_NAME, QUANTITY, MRP, DISCOUNT, TOTAL) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sales_query, (invoice_id, medicine_name, qty, mrp, discount, total))
                unique_medicines.add(medicine_name)
            connection.commit()
            for medicine_name in unique_medicines:
                qty_sold = sum(qty for name, qty, _, _, _ in cart_medicines if name == medicine_name)
                update_quantity_sold(medicine_name, qty_sold)
            pharmacy_info_query = "SELECT * FROM pharmacy_info LIMIT 1"
            cursor.execute(pharmacy_info_query)
            pharmacy_info = cursor.fetchone()
            pharmacy_name = pharmacy_info[1]
            address = pharmacy_info[2]
            email = pharmacy_info[3]
            contact_number = pharmacy_info[4]
            invoice_details_query = "SELECT * FROM invoices WHERE INVOICE_ID = %s"
            cursor.execute(invoice_details_query, (invoice_id,))
            invoice_data = cursor.fetchone()
            invoice_date = invoice_data[2]
            net_total = invoice_data[1]
            amount_paid = invoice_data[3]
            sales_query = "SELECT MEDICINE_NAME, QUANTITY, MRP FROM sales WHERE INVOICE_NUMBER = %s"
            cursor.execute(sales_query, (invoice_id,))
            sales_data = cursor.fetchall()
            pdf_filename = f'invoice_{invoice_id}.pdf'
            page_width, page_height = 58 * mm, 210 * mm
            # Set margins for left, right, top, and bottom
            left_margin = 1 * mm
            right_margin = 1 * mm
            top_margin = 0.1 * mm  # Adjust this value to make the top margin smaller
            bottom_margin = 5 * mm
            # Create PDF
            pdf = SimpleDocTemplate(pdf_filename, pagesize=(page_width, page_height), rightMargin=right_margin, leftMargin=left_margin, topMargin=top_margin, bottomMargin=bottom_margin)
            elements = []
            elements.append(Spacer(1, 5))
            # Header Section
            header_table_data = [
                [f"{pharmacy_name}"],
                [f"{address}"],
                [f"{email}"],
                ["Contact:",f"{contact_number}"],
                ["Invoice NO:", f"{invoice_id}"],
                ["Date:", f"{invoice_date}"]
            ]
            # Create the header table without specifying row heights
            header_table = Table(header_table_data, colWidths=[60, 120])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                
        ]))
            elements.append(header_table)
            elements.append(Spacer(1, 10))  # Add space between header and body

            # Body Section (Medicine Details)
            body_table_data = [
                ["Drug", "Qty", "Price"]
            ]
            for medicine_name, qty, mrp in sales_data:
                truncated_name = medicine_name[:15]
                body_table_data.append([truncated_name, qty, mrp])
            body_table = Table(body_table_data, colWidths=[70, 30, 40], rowHeights=[15] * (len(sales_data) + 1))
            body_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Line below body
                
            ]))
            elements.append(body_table)
            elements.append(Spacer(1, 5))  # Add space between body and footer

            # Footer Section
            footer_table_data = [
                ["Total:", f"{net_total}"],
                ["Amount Paid:", f"{amount_paid}"],
                ["Balance:", f"{balance_value}"],
                ["Your trust means a lot."]
            ]
            footer_table = Table(footer_table_data, colWidths=[70, 60], rowHeights=[15] * len(footer_table_data))
            footer_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Line below footer
            ]))
            elements.append(footer_table)

            pdf.build(elements)

            print_command = f"start {pdf_filename}"
            subprocess.run(print_command, shell=True)

            cart_medicines.clear()
            cart_tree.delete(*cart_tree.get_children())
            amount_paid_entry_cart.delete(0, "end")
            update_totals()
            messagebox.showinfo("Success", "Invoice saved successfully. Cart cleared.")
            refresh_window()

        except Exception as e:
            connection.rollback()
            error_message = f"An error occurred: {e}\n\n{repr(e)}"
            print(error_message, file=sys.stderr)
            messagebox.showerror("Error", error_message)
        finally:
            if cursor:
                cursor.close()
  
    def refresh_window():
        try:
            if medicine_tree.winfo_exists():
            # Update the medicine tree (list) when the window is refreshed
                update_medicine_tree()
        except Exception as e:
        # Handle exceptions if any
            print(f"Error refreshing window: {e}")

    
    
    
    add_to_invoice_button = Button(labels_and_entries_frame, text="Add to Invoice", command=add_to_invoice)
    add_to_invoice_button.grid(row=0, column=6, pady=10, padx=5)
    # Create a frame for the cart
    cart_frame = ttk.Frame(add_invoice_window)
    cart_frame.pack(pady=0)

# Create a label for the cart
    cart_label = ttk.Label(cart_frame, text="Cart")
    cart_label.grid(row=0, column=0, columnspan=6, pady=5)

# Create Treeview widget for the cart with horizontal and vertical scrollbar
    cart_columns = ("Medicine Name", "Quantity", "Price", "Discount", "Total")
    cart_tree = ttk.Treeview(cart_frame, columns=cart_columns, show="headings", height=5)
    for col in cart_columns:
        cart_tree.heading(col, text=col)
    cart_tree.grid(row=1, column=0, columnspan=6, pady=5, sticky="nsew")
# Add horizontal scrollbar
    hsb_cart = ttk.Scrollbar(cart_frame, orient="horizontal", command=cart_tree.xview)
    hsb_cart.grid(row=2, column=0, columnspan=6, sticky="ew")
    cart_tree.configure(xscrollcommand=hsb_cart.set)
# Add vertical scrollbar
    vsb_cart = ttk.Scrollbar(cart_frame, orient="vertical", command=cart_tree.yview)
    vsb_cart.grid(row=1, column=4, sticky="ns")
    cart_tree.configure(yscrollcommand=vsb_cart.set)
# Make the treeview columns resize with the window
    cart_frame.grid_columnconfigure(0, weight=1)
    cart_frame.grid_rowconfigure(1, weight=1)
# Create buttons for deleting and editing medicines in the cart
    delete_button = Button(cart_frame, text="Delete", command=delete_selected_medicine)
    delete_button.grid(row=3, column=0, pady=5, padx=5)
# Label and entry for amount paid in cart frame
    amount_paid_label_cart = ttk.Label(cart_frame, text="Amount Paid:")
    amount_paid_label_cart.grid(row=4, column=0, pady=5, padx=5)
    amount_paid_entry_cart = Entry(cart_frame)
    amount_paid_entry_cart.grid(row=4, column=1, pady=5, padx=5)
    # Create a frame for the save and print button
    save_print_frame = ttk.Frame(cart_frame)
    save_print_frame.grid(row=5, column=0, columnspan=3, pady=0)

    # Button to save and print the invoice
    save_print_button = Button(save_print_frame, text="Save and Print", command=save_and_print_invoice)
    save_print_button.grid(row=0, column=0, padx=5)


def pharmacy_info_settings():
    global connection

    try:
        if not connection or connection.is_closed():
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="pharmacy"
            )

        with connection.cursor() as cursor:
            # Fetch existing pharmacy information
            cursor.execute("SELECT * FROM pharmacy_info LIMIT 1")
            pharmacy_info = cursor.fetchone()

        # Create a separate window for modifying pharmacy information
        pharmacy_info_window = tk.Toplevel(root)
        pharmacy_info_window.title("Pharmacy Information")

        # Create a frame for input fields and labels
        input_frame = ttk.Frame(pharmacy_info_window)
        input_frame.pack(pady=10)

        # Pharmacy Name label and entry
        pharmacy_name_label = ttk.Label(input_frame, text="Pharmacy Name:")
        pharmacy_name_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        pharmacy_name_entry = ttk.Entry(input_frame, width=30)
        pharmacy_name_entry.grid(row=0, column=1, padx=10, pady=5)
        pharmacy_name_entry.insert(0, pharmacy_info[1])  # Insert existing pharmacy name

        # Address label and entry
        address_label = ttk.Label(input_frame, text="Address:")
        address_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        address_entry = ttk.Entry(input_frame, width=30)
        address_entry.grid(row=1, column=1, padx=10, pady=5)
        address_entry.insert(0, pharmacy_info[2])  # Insert existing address

        # Email label and entry
        email_label = ttk.Label(input_frame, text="Email:")
        email_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        email_entry = ttk.Entry(input_frame, width=30)
        email_entry.grid(row=2, column=1, padx=10, pady=5)
        email_entry.insert(0, pharmacy_info[3])  # Insert existing email

        # Contact Number label and entry
        contact_number_label = ttk.Label(input_frame, text="Contact Number:")
        contact_number_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")

        contact_number_entry = ttk.Entry(input_frame, width=30)
        contact_number_entry.grid(row=3, column=1, padx=10, pady=5)
        contact_number_entry.insert(0, pharmacy_info[4])  # Insert existing contact number

        # Modify button
        def modify_pharmacy_info():
            try:
                new_pharmacy_name = pharmacy_name_entry.get()
                new_address = address_entry.get()
                new_email = email_entry.get()
                new_contact_number = contact_number_entry.get()

                # Reconnect to the database
                with connection.cursor() as cursor:
                    # Update existing pharmacy information in the database
                    cursor.execute("UPDATE pharmacy_info SET PHARMACY_NAME=%s, ADDRESS=%s, EMAIL=%s, CONTACT_NUMBER=%s WHERE ID=%s",
                                   (new_pharmacy_name, new_address, new_email, new_contact_number, pharmacy_info[0]))
                    connection.commit()

                messagebox.showinfo("Success", "Pharmacy information updated successfully.")
            except Exception as e:
                print("Error during update:", e)
                messagebox.showerror("Error", f"An error occurred: {e}")

        # Add Modify button
        modify_button = ttk.Button(pharmacy_info_window, text="Modify", command=modify_pharmacy_info, style="TButton", cursor="hand2")
        modify_button.pack(pady=10)

        # Add buttons to delete all stocks and invoices
        delete_stocks_button = ttk.Button(pharmacy_info_window, text="Delete All Stocks", command=delete_all_stocks, style="TButton", cursor="hand2")
        delete_stocks_button.pack(pady=5)

        delete_invoices_button = ttk.Button(pharmacy_info_window, text="Delete All Invoices", command=delete_all_invoices, style="TButton", cursor="hand2")
        delete_invoices_button.pack(pady=5)

    except Exception as e:
        print("Error during connection:", e)
        messagebox.showerror("Error", f"An error occurred: {e}")


def delete_all_stocks():
    # Ask for admin credentials
    admin_username, admin_password = ask_for_admin_credentials()

    # Check if the provided credentials are correct
    if admin_username and admin_password and verify_admin_credentials(admin_username, admin_password):
        # Implement logic to delete all stocks from the database
        cursor.execute("DELETE FROM medicines_stock")
        connection.commit()
        messagebox.showinfo("Delete Stocks", "All stocks deleted successfully.")
    else:
        messagebox.showwarning("Authentication Failed", "Invalid admin credentials.")

def delete_all_invoices():
    # Ask for admin credentials
    admin_username, admin_password = ask_for_admin_credentials()

    # Check if the provided credentials are correct
    if admin_username and admin_password and verify_admin_credentials(admin_username, admin_password):
        # Implement logic to delete all invoices from the database
        cursor.execute("DELETE FROM invoices")
        connection.commit()
        messagebox.showinfo("Delete Invoices", "All invoices deleted successfully.")
    else:
        messagebox.showwarning("Authentication Failed", "Invalid admin credentials.")

def ask_for_admin_credentials():
    # Prompt the user for admin credentials
    admin_username = simpledialog.askstring("Admin Authentication", "Enter admin username:")
    admin_password = simpledialog.askstring("Admin Authentication", "Enter admin password:", show='*')
    return admin_username, admin_password

def verify_admin_credentials(username, password):
    # Check if the provided credentials are correct by querying the "users" table
    query = "SELECT * FROM users WHERE username=%s AND password=%s"
    cursor.execute(query, (username, password))
    result = cursor.fetchone()
    return result is not None


def generate_reports(query):
    def apply_date_filter(*args):
        start_date = start_date_var.get()
        end_date = end_date_var.get()

        try:
            # Convert the dates to the correct format
            base_query = """
                SELECT
                    sales.MEDICINE_NAME AS "Medicine_Name",
                    sales.QUANTITY AS "Qty",
                    sales.TOTAL AS "Total",
                    sales.DISCOUNT AS "Discount",
                    sales.DATE AS "Date"
                FROM sales
            """
            total_sales_query = "SELECT SUM(TOTAL) FROM sales"
            total_discounts_query = "SELECT SUM(DISCOUNT) FROM sales"
            
            date_filter = ""
            if start_date and end_date:
                date_filter = f"WHERE sales.DATE BETWEEN '{start_date}' AND '{end_date}'"
                base_query += f" {date_filter}"
                total_sales_query += f" {date_filter}"
                total_discounts_query += f" {date_filter}"

            refresh_report(base_query, total_sales_query, total_discounts_query)
        except ValueError:
            # Handle invalid date format
            pass

    def refresh_report(filtered_query, total_sales_query, total_discounts_query):
        tree.delete(*tree.get_children())

        try:
            cursor = connection.cursor(dictionary=True)  # Use dictionary cursor for named column access

            cursor.execute(filtered_query)
            filtered_report_data = cursor.fetchall()

            total_sales = sum(row["Total"] for row in filtered_report_data)
            total_discounts = sum(row["Discount"] for row in filtered_report_data)

            total_label.config(text=f"Total Sales: Shs.{total_sales:.2f}, Total Discounts: Shs.{total_discounts:.2f}")

            for sale in filtered_report_data:
                tree.insert("", "end", values=(sale["Medicine_Name"], sale["Qty"], sale["Total"], sale["Date"]))

            cursor.close()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def save_report_as_pdf(query, file_path, start_date, end_date):
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            report_data = cursor.fetchall()

            pdf = SimpleDocTemplate(file_path, pagesize=letter)

            # Add content to PDF
            content = []
            
            # Determine header text based on date filter
            if start_date and end_date:
                header_text = f"Sales Report ({start_date} to {end_date})"
            else:
                header_text = "Sales Report"
            
            # Add header
            header_style = ('Helvetica-Bold', 16)
            content.append(Paragraph(header_text, header_style))
            content.append(Spacer(1, 12))  # Add some space after the header

            # Convert report_data to a list of lists for the table
            table_data = [
                ["Medicine Name", "Quantity", "Total", "Date"],
                *[list(row.values()) for row in report_data]
            ]

            # Create a Table object
            table = Table(table_data)

            # Apply styles to the table
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ])
            table.setStyle(style)

            content.append(table)

            # Add total sales and discounts below the table
            total_sales = sum(row["TOTAL"] for row in report_data)
            total_discounts = sum(row["DISCOUNT"] for row in report_data)

            total_style = ('Helvetica-Bold', 12)
            content.append(Spacer(1, 12))  # Add some space before the totals
            content.append(Paragraph(f"Total Sales: Shs.{total_sales:.2f}", total_style))
            content.append(Paragraph(f"Total Discounts: Shs.{total_discounts:.2f}", total_style))

            # Build the PDF
            pdf.build(content)

            cursor.close()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving the report as PDF: {e}")

    def reload_report():
        start_date_var.set("")  # Clear start date entry
        end_date_var.set("")    # Clear end date entry
        apply_date_filter()     # Reload all sales data

    try:
        cursor = connection.cursor(dictionary=True)  # Use dictionary cursor for named column access

        report_window = tk.Toplevel(root)
        report_window.title("All sales")
        tree_frame = ttk.Frame(report_window)
        tree_frame.pack(expand=True, fill="both")
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")

        tree = ttk.Treeview(
            tree_frame,
            columns=("Medicine_Name", "Qty", "Total", "Date"),
            show="headings",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )
        tree.heading("Medicine_Name", text="Medicine Name")
        tree.heading("Qty", text="Quantity")
        tree.heading("Total", text="Total")
        tree.heading("Date", text="Date")
        tree_scroll_y.config(command=tree.yview)
        tree_scroll_x.config(command=tree.xview)
        total_sales_query = "SELECT SUM(TOTAL) FROM sales"
        total_discounts_query = "SELECT SUM(DISCOUNT) FROM sales"
        cursor.execute(total_sales_query)
        total_sales_result = cursor.fetchone()
        total_sales = total_sales_result["SUM(TOTAL)"] if total_sales_result and "SUM(TOTAL)" in total_sales_result else 0.0
        cursor.execute(total_discounts_query)
        total_discounts_result = cursor.fetchone()
        total_discounts = total_discounts_result["SUM(DISCOUNT)"] if total_discounts_result and "SUM(DISCOUNT)" in total_discounts_result else 0.0
        total_label = ttk.Label(
            report_window,
            text=f"Total Sales: Shs.{total_sales:.2f}, Total Discounts: Shs.{total_discounts:.2f}"
        )
        total_label.pack(side="top", fill="x", padx=10, pady=5)
        cursor.execute(query)
        report_data = cursor.fetchall()
        for sale in report_data:
            tree.insert("", "end", values=(sale["MEDICINE_NAME"], sale["QUANTITY"], sale["TOTAL"], sale["DATE"]))
        tree.pack(side="left", fill="both", expand=True)
        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x.pack(side="bottom", fill="x")
        filter_frame = ttk.Frame(report_window)
        filter_frame.pack(side="top", pady=10)
        start_date_label = ttk.Label(filter_frame, text="From Date:")
        start_date_label.grid(row=0, column=0, padx=5)
        start_date_var = tk.StringVar()
        start_date_entry = ttk.Entry(filter_frame, textvariable=start_date_var)
        start_date_entry.grid(row=0, column=1, padx=5)
        end_date_label = ttk.Label(filter_frame, text="To Date:")
        end_date_label.grid(row=0, column=2, padx=5)
        end_date_var = tk.StringVar()
        end_date_entry = ttk.Entry(filter_frame, textvariable=end_date_var)
        end_date_entry.grid(row=0, column=3, padx=5)
        # Add trace to call apply_date_filter when the start or end date changes
        start_date_var.trace_add("write", apply_date_filter)
        end_date_var.trace_add("write", apply_date_filter)
        reload_button = ttk.Button(filter_frame, text="Reload", command=reload_report)
        reload_button.grid(row=0, column=4, padx=5)    
       # download_button = ttk.Button(filter_frame, text="Download", command=lambda: save_report_as_pdf(query, "Sales_Report.pdf", start_date_var.get(), end_date_var.get()))
        #download_button.grid(row=0, column=5, padx=5)
        cursor.close()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
    


def pharmacy_info():
    print("Implement Pharmacy Info functionality")

def get_today_sales():
    # Connect to the database
    cursor = connection.cursor()
    # Fetch today's sales from the invoices table
    today = date.today()
    cursor.execute("SELECT SUM(NET_TOTAL) FROM invoices WHERE DATE(INVOICE_DATE) = %s", (today,))
    today_sales = cursor.fetchone()[0] or 0  # Use 0 if there are no sales
    # Close the database cursor
    cursor.close()

    return today_sales

def get_yesterday_sales():
    # Connect to the database
    cursor = connection.cursor()

    # Fetch yesterday's sales from the invoices table
    yesterday = date.today() - timedelta(days=1)
    cursor.execute("SELECT SUM(NET_TOTAL) FROM invoices WHERE DATE(INVOICE_DATE) = %s", (yesterday,))
    yesterday_sales = cursor.fetchone()[0] or 0  # Use 0 if there are no sales

    # Close the database cursor
    cursor.close()

    return yesterday_sales

def update_sales_labels(today_label, yesterday_label):
    # Fetch and update today's sales
    today_sales = get_today_sales()
    today_label.config(text=f"Today's Sales: Shs.{today_sales:.2f}")

    # Fetch and update yesterday's sales
    yesterday_sales = get_yesterday_sales()
    yesterday_label.config(text=f"Yesterday's Sales: Shs.{yesterday_sales:.2f}")
def refresh_sales_labels_periodically(today_label, yesterday_label):
    # Function to refresh sales labels periodically
    update_sales_labels(today_label, yesterday_label)
    root.after(30000, lambda: refresh_sales_labels_periodically(today_label, yesterday_label))  # Refresh every 30 seconds

def display_most_selling_drugs():
    # Get the date 30 days ago from today
    thirty_days_ago = date.today() - timedelta(days=30)

    # Connect to the database
    cursor = connection.cursor()

    # Fetch the most selling drugs within the last 30 days
    cursor.execute("""
        SELECT MEDICINE_NAME, COUNT(INVOICE_NUMBER) as purchase_count
        FROM sales
        WHERE DATE >= %s
        GROUP BY medicine_name
        ORDER BY purchase_count DESC
    """, (thirty_days_ago,))

    most_selling_drugs = cursor.fetchall()

    # Close the database cursor
    cursor.close()

    # Display the list of most selling drugs
    if most_selling_drugs:
        display_list("Most Selling Drugs (Last 30 Days)", most_selling_drugs)
    else:
        messagebox.showinfo("Most Selling Drugs (Last 30 Days)", "No data available.")

def display_out_of_stock():
    # Fetch out-of-stock medicines from the database
    out_of_stock_medicines = get_out_of_stock_medicines()
    if out_of_stock_medicines:
        display_list("Out of Stock Medicines", [(medicine,) for medicine in out_of_stock_medicines])
    else:
        messagebox.showinfo("Out of Stock", "No out-of-stock medicines.")

def display_about_to_get_out_of_stock():
    # Fetch medicines about to get out of stock from the database
    about_to_get_out_of_stock_medicines = get_about_to_get_out_of_stock_medicines()
    if about_to_get_out_of_stock_medicines:
        display_list("About to Get Out of Stock", [(medicine,) for medicine in about_to_get_out_of_stock_medicines])
    else:
        messagebox.showinfo("About to Get Out of Stock", "No medicines about to get out of stock.")

def display_expired():
    # Fetch expired medicines from the database
    expired_medicines = get_expired_medicines()
    if expired_medicines:
        display_list("Expired Medicines", [(medicine,) for medicine in expired_medicines])
    else:
        messagebox.showinfo("Expired Medicines", "No expired medicines.")

def get_out_of_stock_medicines():
    # Connect to the database
    cursor = connection.cursor()

    # Fetch medicines that are out of stock
    cursor.execute("SELECT NAME FROM medicines_stock WHERE QUANTITY = 0")
    out_of_stock_medicines = [row[0] for row in cursor.fetchall()]

    # Close the database cursor
    cursor.close()

    return out_of_stock_medicines

def get_about_to_get_out_of_stock_medicines():
    # Connect to the database
    cursor = connection.cursor()

    # Fetch medicines that will be out of stock (quantity < 5)
    cursor.execute("SELECT NAME FROM medicines_stock WHERE QUANTITY > 0 AND QUANTITY < 5")
    about_to_get_out_of_stock_medicines = [row[0] for row in cursor.fetchall()]

    # Close the database cursor
    cursor.close()

    return about_to_get_out_of_stock_medicines

def get_expired_medicines():
    # Connect to the database
    cursor = connection.cursor()

    # Fetch medicines that have expired
    cursor.execute("SELECT NAME FROM medicines_stock WHERE STR_TO_DATE(EXPIRY_DATE, '%d/%m/%Y') <= CURDATE()")
    expired_medicines = [row[0] for row in cursor.fetchall()]

    # Close the database cursor
    cursor.close()

    return expired_medicines

def on_closing():
    global opened_window

    # Close the subprocess if it is running
    if opened_window is not None:
        opened_window.terminate()  # Use terminate() to forcefully close the subprocess

    # Close the main window
    root.destroy()

def display_list(title, data):
    list_window = tk.Toplevel(root)
    list_window.title(title)

    # Create a text widget for displaying the list
    list_text = tk.Text(list_window, wrap="none", height=20, width=50)
    list_text.pack(expand=True, fill="both")

    # Insert data into the text widget
    for index, item in enumerate(data, start=1):
        list_text.insert(tk.END, f"{index}. {item[0]}\n")

    # Create a close button
    close_button = ttk.Button(list_window, text="Close", command=list_window.destroy)
    close_button.pack(pady=10)

    # Add the list window to the opened_lists dictionary
    opened_lists[title] = list_window

    # Set the protocol to call del_opened_list when the window is closed
    list_window.protocol("WM_DELETE_WINDOW", lambda: del_opened_list(title))

def del_opened_list(title):
    opened_lists.pop(title, None)

def apply_date_filter(report_window, base_query, start_date, end_date):
        generate_reports(
            f"{base_query} WHERE STR_TO_DATE(INVOICE_DATE, '%d/%m/%Y') BETWEEN STR_TO_DATE('{start_date}', '%d/%m/%Y') AND STR_TO_DATE('{end_date}', '%d/%m/%Y')",
            report_window
    )
 
def check_admin_password(password):
    # Connect to the database and check if the entered password matches the admin password
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Your MySQL password
        database="pharmacy"
    )

    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT password FROM users WHERE role = 'Admin'")
    
    # Fetch all results
    admin_passwords = cursor.fetchall()

    # Check if any admin password matches
    is_admin = any(admin['password'] == password for admin in admin_passwords)

    # Close the cursor and the connection
    cursor.close()
    connection.close()

    return is_admin

def authenticate_admin():
    # Prompt the user for the admin password
    password = askstring("Authorization", "Enter Admin Password:", show='*')

    # Check if the entered password matches the admin password in the database
    if check_admin_password(password):
        print("Authentication successful")
        return True
    else:
        messagebox.showerror("Authorization Failed", "Invalid Admin Password.")
        return False

def check_admin_password(password):
    # Connect to the database and check if the entered password matches the admin password
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Your MySQL password
        database="pharmacy"
    )

    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT password FROM users WHERE role = 'Admin'")
    
    # Fetch all results
    admin_passwords = cursor.fetchall()

    # Check if any admin password matches
    is_admin = any(admin['password'] == password for admin in admin_passwords)

    # Close the cursor and the connection
    cursor.close()
    connection.close()

    return is_admin

def authenticate_admin():
    while True:
        # Prompt the user for the admin password
        password = askstring("Authorization", "Enter Admin Password:", show='*')

        # Check if the entered password matches the admin password in the database
        if check_admin_password(password):
            print("Authentication successful") 
            return True
        else:
            retry = messagebox.askretrycancel("Authorization Failed", "Invalid Admin Password. Retry?")
            if not retry:
                return False


def backup_database():
    # MySQL database connection configuration
    mysql_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'pharmacy',
    }

    # Specify the backup directory on the D drive
    backup_directory = "D:/backup"  # Update this with your desired backup directory on the D drive

    # Ensure the backup directory exists, create it if necessary
    os.makedirs(backup_directory, exist_ok=True)

    # Generate a timestamp for the backup file
    timestamp = time.strftime("%Y%m%d%H%M%S")
    backup_file = f"backup_{timestamp}.sql"

    try:
        # Create the full path for the backup file
        backup_path = os.path.join(backup_directory, backup_file)

        # Remove existing backup file if it exists
        if os.path.exists(backup_path):
            os.remove(backup_path)

        print(f"Backup scheduled at {timestamp}")
        print(f"Backup file path: {backup_path}")

        # Specify the full path to mysqldump executable (update with your XAMPP installation path)
        mysqldump_path = r"C:\xampp\mysql\bin\mysqldump"

        # Construct the mysqldump command
        mysqldump_cmd = f"{mysqldump_path} -h {mysql_config['host']} -u {mysql_config['user']} {'-p' + mysql_config['password'] if mysql_config['password'] else ''} {mysql_config['database']} > {backup_path}"

        # Print the mysqldump command for debugging
        print(f"Executing mysqldump command: {mysqldump_cmd}")

        # Execute the mysqldump command using subprocess
        subprocess.run(mysqldump_cmd, shell=True, check=True)

        print(f"Backup successful. Backup saved to {backup_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during backup. Exit code: {e.returncode}")
    except Exception as e:
        print(f"Unexpected error during backup: {str(e)}")


def display_about_to_get_expired():

    
    cursor = connection.cursor()

    # Define the query to fetch medicines about to get expired within the next 90 days
    query = """
        SELECT NAME, BRAND, EXPIRY_DATE
        FROM medicines_stock
        WHERE STR_TO_DATE(EXPIRY_DATE, '%d/%m/%Y') BETWEEN CURDATE() AND CURDATE() + INTERVAL 90 DAY
    """

    cursor.execute(query)
    results = cursor.fetchall()

    # Close the database connection
    cursor.close()
    

    # Display the fetched results with a Treeview and scrollbar
    if results:
        # Create a new window
        display_window = tk.Toplevel(root)
        display_window.title("About to Get Expired Within 90 Days")

        # Create a Treeview
        tree = ttk.Treeview(display_window, columns=("Name", "Brand", "Expiry Date"), show="headings", height=10)

        # Add headings to the Treeview
        tree.heading("Name", text="Name")
        tree.heading("Brand", text="Brand")
        tree.heading("Expiry Date", text="Expiry Date")

        # Insert data into the Treeview
        for row_index, (name, brand, expiry_date) in enumerate(results, start=1):
            tree.insert("", "end", values=(name, brand, expiry_date))

        # Add a vertical scrollbar
        scrollbar = ttk.Scrollbar(display_window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Pack the Treeview and scrollbar
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    else:
        messagebox.showinfo("No Data", "No medicines found about to get expired within the next 90 days.")

def display_dashboard():
   
    # Check if the user is authorized
    if not authenticate_admin():
        print("Authentication failed")
        return
    print("Ending display_dashboard()")
    global tree, opened_window, root
    
    root = ThemedTk(theme="calm")  # Using a different theme for a modern look
    root.title("Pharmacy Dashboard")
    root.geometry("1200x1000")

    # Set background color for the main window
    root.tk_setPalette(background="#02022D")

    # Set the protocol to call on_closing() when the window is closed
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Create a frame for the side navigation bar
    side_frame = ttk.Frame(root, width=200, height=600, relief="raised", borderwidth=2)
    side_frame.pack(side="left", fill="y")

    # Add labels for sections (headers) with improved styling and alignment
    section_label_style = ttk.Style()
    section_label_style.configure("TLabel", font=('Arial', 14, 'bold'), background="#000F2C", foreground="#0F0E0E")

    user_management_label = ttk.Label(side_frame, text="User Management", style="TLabel")
    invoice_management_label = ttk.Label(side_frame, text="Invoice Management", style="TLabel")
    stock_management_label = ttk.Label(side_frame, text="Stock Management", style="TLabel")
    reports_management_label = ttk.Label(side_frame, text="Reports Management", style="TLabel")
    settings_label = ttk.Label(side_frame, text="Settings", style="TLabel")

    user_management_label.pack(pady=10)
    # Add buttons for User Management section
    user_management_button_frame = ttk.Frame(side_frame)
    user_management_button_frame.pack()

    # Inside your existing display_dashboard function, add_user button creation
    add_user_button = ttk.Button(user_management_button_frame, text="Add User", command=lambda: add_user(user_management_button_frame))

    add_user_button.pack(pady=5)
    


    add_user_button = ttk.Button(user_management_button_frame, text="Manage Users", command=manage_users)
    add_user_button.pack(pady=5)

    invoice_management_label.pack(pady=10)
    # Add buttons for Invoice Management section
    invoice_management_button_frame = ttk.Frame(side_frame)
    invoice_management_button_frame.pack()

   # Assuming invoice_management_button_frame is your frame containing the "Add Invoice" button
    add_invoice_button = ttk.Button(invoice_management_button_frame, text="Add Invoice",command=add_invoice)
    add_invoice_button.pack(pady=5)
    manage_invoices_button = ttk.Button(invoice_management_button_frame, text="Manage Invoices", command=manage_invoices)
    manage_invoices_button.pack(pady=5)

    stock_management_label.pack(pady=10)
    # Add buttons for Stock Management section
    stock_management_button_frame = ttk.Frame(side_frame)
    stock_management_button_frame.pack()

    add_stock_button = ttk.Button(stock_management_button_frame, text="Add Stock", command=add_stock)
    add_stock_button.pack(pady=5)

    manage_stock_button = ttk.Button(stock_management_button_frame, text="Manage Stock", command=manage_stock)
    manage_stock_button.pack(pady=5)

    reports_management_label.pack(pady=10)
    # Add buttons for Reports Management section
    reports_management_button_frame = ttk.Frame(side_frame)
    reports_management_button_frame.pack()
    # Modify the generate_reports_button to open the window with all invoices
    generate_reports_button = ttk.Button(
        reports_management_button_frame,
        text="Generate Reports",
        command=lambda: generate_reports("SELECT MEDICINE_NAME, QUANTITY, TOTAL,DISCOUNT, DATE FROM sales")
    )
    generate_reports_button.pack(pady=5)


    settings_label.pack(pady=10)
    # Add buttons for Settings section
    settings_button_frame = ttk.Frame(side_frame)
    settings_button_frame.pack()

    pharmacy_info_button = ttk.Button(settings_button_frame, text="Pharmacy Info", command=pharmacy_info_settings)
    pharmacy_info_button.pack(pady=5)


    # Add Quit button
    quit_button = ttk.Button(root, text="Quit", command=root.destroy, style="TButton")
    quit_button.pack(side="bottom", pady=10)

    # Add labels for sales with improved styling and alignment
    label_style = ttk.Style()
    label_style.configure("TLabel", font=('Arial', 12), background="#F6F7F8", foreground="#000405")

    today_label = ttk.Label(root, text="", style="TLabel")
    yesterday_label = ttk.Label(root, text="", style="TLabel")
    today_label.pack(side="bottom", fill="x", padx=10, pady=5)
    yesterday_label.pack(side="bottom", fill="x", padx=10, pady=5)

    # Add buttons for additional functionalities with improved styling
    button_style = ttk.Style()
    button_style.configure("TButton", padding=5, relief="flat", background="#010142", foreground="#090909", font=('Arial', 10))

    # Create a frame for the additional functionalities buttons
    additional_buttons_frame = ttk.Frame(root)
    additional_buttons_frame.pack(side="top", pady=10)

    # Define a function to create and pack buttons with a consistent style
    def create_button(text, command):
        return ttk.Button(additional_buttons_frame, text=text, command=command, style="TButton", width=20)

    # Add buttons for additional functionalities in one row with four columns
    out_of_stock_button = create_button("Out of Stock", display_out_of_stock)
    about_to_get_out_of_stock_button = create_button("About to Get Out of Stock", display_about_to_get_out_of_stock)
    expired_button = create_button("Expired", display_expired)
    most_selling_drugs_button = create_button("Most Selling Drugs (Last 30 Days)", display_most_selling_drugs)
    about_to_get_expired_button = create_button("About to Get Expired (Within 90 Days)", display_about_to_get_expired)
    # Pack the buttons in the frame
    out_of_stock_button.grid(row=0, column=0, padx=5)
    about_to_get_out_of_stock_button.grid(row=0, column=1, padx=5)
    expired_button.grid(row=0, column=2, padx=5)
    most_selling_drugs_button.grid(row=0, column=3, padx=5)
    about_to_get_expired_button.grid(row=0, column=4, padx=5)

    update_sales_labels(today_label, yesterday_label)   
    # Schedule the periodic refresh of sales labels
    refresh_sales_labels_periodically(today_label, yesterday_label)
    
    # Start the backup scheduler
    schedule.every().day.at("10:00").do(backup_database)  # Schedule backup at 10:00 am

    schedule.every().day.at("21:00").do(backup_database)  # Schedule backup at 9pm
    
     # Create a thread for running scheduled tasks
    scheduler_thread = threading.Thread(target=run_scheduled_tasks, daemon=True)
    scheduler_thread.start()

    
    root.mainloop()
def run_scheduled_tasks():
    
    try:
        schedule.run_pending()
    except Exception as e:
        print(f"Exception during scheduled tasks: {e}")
    root.after(1000, run_scheduled_tasks)

if __name__ == '__main__':
    display_dashboard()
   
